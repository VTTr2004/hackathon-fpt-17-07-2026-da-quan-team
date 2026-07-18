from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_accessible_startup, get_current_user, get_owned_startup
from app.core.config import get_settings
from app.db.session import get_db
from app.models.audit_log import AuditLog
from app.models.document import Document
from app.models.startup_version import StartupVersion
from app.models.user import User
from app.schemas.document import DocumentRead, DocumentVisibilityUpdate
from app.services.chat_service import ensure_startup_index, startup_profile
from app.services.document_parser import extract_text, has_extractable_text
from app.services.ocr_service import OCR_SUFFIXES, ocr_document

router = APIRouter()
ALLOWED_SUFFIXES = {
    ".pdf",
    ".docx",
    ".pptx",
    ".xlsx",
    ".txt",
    ".md",
    ".csv",
    ".json",
    ".png",
    ".jpg",
    ".jpeg",
}


async def _latest_version(startup_id: UUID, db: AsyncSession) -> StartupVersion | None:
    return await db.scalar(
        select(StartupVersion)
        .where(StartupVersion.startup_id == startup_id)
        .order_by(StartupVersion.version_number.desc())
        .limit(1)
    )


async def _document_is_version_locked(startup_id: UUID, document_id: UUID, db: AsyncSession) -> bool:
    """Return whether a submitted snapshot already references this document."""
    version_id = await db.scalar(
        select(StartupVersion.id)
        .where(
            StartupVersion.startup_id == startup_id,
            StartupVersion.document_ids.contains([str(document_id)]),
        )
        .limit(1)
    )
    return version_id is not None


@router.get("/{startup_id}/documents", response_model=list[DocumentRead])
async def list_documents(
    startup_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Document]:
    await get_accessible_startup(startup_id, user, db)
    query = select(Document).where(Document.startup_id == startup_id)
    if user.role == "investor":
        version = await _latest_version(startup_id, db)
        if version is None:
            return []
        document_ids = [UUID(item) for item in version.document_ids]
        query = query.where(Document.id.in_(document_ids), Document.visibility == "shared")
    return list(await db.scalars(query.order_by(Document.created_at.desc())))


@router.post("/{startup_id}/documents", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def upload_document(
    startup_id: UUID,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Document:
    startup = await get_owned_startup(startup_id, user, db, require_draft=True)
    settings = get_settings()
    original_name = Path(file.filename or "document").name
    suffix = Path(original_name).suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(status_code=415, detail="Định dạng tài liệu chưa được hỗ trợ")
    content = await file.read(settings.max_upload_mb * 1024 * 1024 + 1)
    if len(content) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Tài liệu vượt quá giới hạn dung lượng")
    upload_dir = Path(settings.upload_dir) / str(startup_id)
    upload_dir.mkdir(parents=True, exist_ok=True)
    path = upload_dir / f"{uuid4()}{suffix}"
    path.write_bytes(content)
    text = ""
    parser_error: Exception | None = None
    if suffix not in {".png", ".jpg", ".jpeg"}:
        try:
            text = extract_text(path)
        except Exception as exc:
            parser_error = exc
    ocr_used = False
    ocr_error: str | None = None
    if not has_extractable_text(text) and suffix in OCR_SUFFIXES:
        try:
            text = await ocr_document(path, file.content_type)
            ocr_used = True
        except Exception as exc:
            ocr_error = str(exc)[:500]
    if parser_error is not None and suffix not in OCR_SUFFIXES:
        path.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail=f"Không thể đọc tài liệu: {parser_error}") from parser_error
    document = Document(
        startup_id=startup_id,
        uploaded_by_id=user.id,
        filename=original_name,
        content_type=file.content_type,
        storage_path=str(path),
        extracted_text=text,
        status="processed" if has_extractable_text(text) else "needs_ocr",
        visibility="shared",
    )
    db.add(document)
    await db.flush()
    db.add(
        AuditLog(
            actor_id=user.id,
            action="document.uploaded",
            resource_type="document",
            resource_id=document.id,
            details={
                "filename": original_name,
                "ocr_model": settings.gemini_ocr_model if ocr_used else None,
                "ocr_error": ocr_error,
            },
        )
    )
    await db.commit()
    await db.refresh(document)

    # Best effort: prebuild the owner's draft index so the first chat is fast.
    # Investor/version indexes use submitted snapshots and are built under separate keys.
    try:
        all_docs = list(await db.scalars(select(Document).where(Document.startup_id == startup_id)))
        await ensure_startup_index(
            f"{startup_id}:draft",
            startup_profile(startup),
            [
                {
                    "id": str(item.id),
                    "filename": item.filename,
                    "text": item.extracted_text,
                    "storage_path": item.storage_path,
                }
                for item in all_docs
            ],
        )
    except Exception:
        pass
    return document


@router.patch("/{startup_id}/documents/{document_id}", response_model=DocumentRead)
async def update_document_visibility(
    startup_id: UUID,
    document_id: UUID,
    payload: DocumentVisibilityUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Document:
    await get_owned_startup(startup_id, user, db, require_draft=True)
    if payload.visibility not in {"private", "shared", "restricted"}:
        raise HTTPException(status_code=422, detail="Mức chia sẻ không hợp lệ")
    document = await db.get(Document, document_id)
    if document is None or document.startup_id != startup_id:
        raise HTTPException(status_code=404, detail="Tài liệu không tồn tại")
    if document.visibility == payload.visibility:
        return document
    if await _document_is_version_locked(startup_id, document_id, db):
        raise HTTPException(
            status_code=409,
            detail="Tài liệu đã được khóa trong phiên bản đã nộp; hãy tải lên một bản tài liệu mới.",
        )
    document.visibility = payload.visibility
    db.add(
        AuditLog(
            actor_id=user.id,
            action="document.visibility_updated",
            resource_type="document",
            resource_id=document.id,
            details={"visibility": payload.visibility},
        )
    )
    await db.commit()
    await db.refresh(document)
    return document
