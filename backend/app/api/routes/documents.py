from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import get_db
from app.models.document import Document
from app.models.startup import Startup
from app.schemas.document import DocumentRead
from app.services.document_parser import extract_text

router = APIRouter()
ALLOWED_SUFFIXES = {".pdf", ".docx", ".pptx", ".xlsx", ".txt", ".md", ".csv", ".json"}


@router.get("/{startup_id}/documents", response_model=list[DocumentRead])
async def list_documents(startup_id: UUID, db: AsyncSession = Depends(get_db)) -> list[Document]:
    result = await db.scalars(
        select(Document).where(Document.startup_id == startup_id).order_by(Document.created_at.desc())
    )
    return list(result)


@router.post("/{startup_id}/documents", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def upload_document(
    startup_id: UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> Document:
    if await db.get(Startup, startup_id) is None:
        raise HTTPException(status_code=404, detail="Startup không tồn tại")
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
    try:
        text = extract_text(path)
    except Exception as exc:
        path.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail=f"Không thể đọc tài liệu: {exc}") from exc
    document = Document(
        startup_id=startup_id,
        filename=original_name,
        content_type=file.content_type,
        storage_path=str(path),
        extracted_text=text,
        status="processed",
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)
    return document
