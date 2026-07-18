from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user, get_owned_startup
from app.db.session import get_db
from app.llm.gemini import get_llm_client
from app.models.audit_log import AuditLog
from app.models.document import Document
from app.models.extraction import ExtractionCandidate, ExtractionJob
from app.models.startup import Startup
from app.models.user import User
from app.modules.profile_ingestion.extractor import extract_profile_candidates
from app.modules.profile_ingestion.field_registry import DEFAULT_FIELD_KEYS, FIELD_REGISTRY, SCHEMA_VERSION
from app.modules.profile_ingestion.normalizers import normalize_profile_value
from app.modules.profile_ingestion.service import SUPPORTED_SUFFIXES, build_evidence_blocks
from app.schemas.extraction import (
    ExtractionCandidateRead,
    ExtractionConfirm,
    ExtractionCreate,
    ExtractionJobRead,
)
from app.schemas.startup import StartupRead
from app.services.ocr_service import OCR_SUFFIXES, ocr_document

router = APIRouter()


def _job_read(job: ExtractionJob, candidates: list[ExtractionCandidate]) -> ExtractionJobRead:
    ordered = {key: index for index, key in enumerate(job.field_keys)}
    return ExtractionJobRead(
        id=job.id,
        startup_id=job.startup_id,
        status=job.status,
        document_ids=job.document_ids,
        field_keys=job.field_keys,
        schema_version=job.schema_version,
        based_on_startup_updated_at=job.based_on_startup_updated_at,
        warnings=job.warnings,
        error=job.error,
        completed_at=job.completed_at,
        applied_at=job.applied_at,
        created_at=job.created_at,
        candidates=[
            ExtractionCandidateRead(
                id=candidate.id,
                field_key=candidate.field_key,
                label=FIELD_REGISTRY[candidate.field_key].label,
                value_type=FIELD_REGISTRY[candidate.field_key].value_type,
                proposed_value=candidate.proposed_value,
                evidence=candidate.evidence,
                confidence=candidate.confidence,
                status=candidate.status,
                warnings=candidate.warnings,
                user_decision=candidate.user_decision,
                confirmed_value=candidate.confirmed_value,
            )
            for candidate in sorted(candidates, key=lambda item: ordered.get(item.field_key, 999))
        ],
    )


async def _job_candidates(job_id: UUID, db: AsyncSession) -> list[ExtractionCandidate]:
    return list(
        await db.scalars(
            select(ExtractionCandidate).where(ExtractionCandidate.extraction_job_id == job_id)
        )
    )


@router.get("/{startup_id}/extractions", response_model=list[ExtractionJobRead])
async def list_extractions(
    startup_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ExtractionJobRead]:
    await get_owned_startup(startup_id, user, db)
    jobs = list(
        await db.scalars(
            select(ExtractionJob)
            .where(ExtractionJob.startup_id == startup_id, ExtractionJob.created_by_id == user.id)
            .order_by(ExtractionJob.created_at.desc())
            .limit(20)
        )
    )
    if not jobs:
        return []
    candidates = list(
        await db.scalars(
            select(ExtractionCandidate).where(
                ExtractionCandidate.extraction_job_id.in_([job.id for job in jobs])
            )
        )
    )
    grouped: dict[UUID, list[ExtractionCandidate]] = defaultdict(list)
    for candidate in candidates:
        grouped[candidate.extraction_job_id].append(candidate)
    return [_job_read(job, grouped[job.id]) for job in jobs]


@router.post(
    "/{startup_id}/extractions",
    response_model=ExtractionJobRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_extraction(
    startup_id: UUID,
    payload: ExtractionCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ExtractionJobRead:
    startup = await get_owned_startup(startup_id, user, db, require_draft=True)
    field_keys = list(dict.fromkeys(payload.field_keys or DEFAULT_FIELD_KEYS))
    unknown_fields = [key for key in field_keys if key not in FIELD_REGISTRY]
    if unknown_fields:
        raise HTTPException(status_code=422, detail=f"Field không hỗ trợ: {', '.join(unknown_fields)}")

    query = select(Document).where(Document.startup_id == startup_id, Document.visibility == "shared")
    if payload.document_ids:
        query = query.where(Document.id.in_(payload.document_ids))
    documents = list(await db.scalars(query.order_by(Document.created_at.asc())))
    if payload.document_ids and len(documents) != len(set(payload.document_ids)):
        raise HTTPException(status_code=422, detail="Tài liệu extraction phải tồn tại và có mức chia sẻ 'shared'")
    if not documents:
        raise HTTPException(status_code=422, detail="Hãy tải lên ít nhất một tài liệu trước khi trích xuất")
    if not any(Path(document.filename).suffix.lower() in SUPPORTED_SUFFIXES for document in documents):
        raise HTTPException(
            status_code=422,
            detail="Profile extraction hỗ trợ PDF, PNG, JPEG, DOCX, PPTX, TXT và Markdown",
        )

    job = ExtractionJob(
        startup_id=startup_id,
        status="running",
        document_ids=[str(document.id) for document in documents],
        field_keys=field_keys,
        schema_version=SCHEMA_VERSION,
        based_on_startup_updated_at=startup.updated_at,
        created_by_id=user.id,
    )
    db.add(job)
    await db.flush()
    db.add(
        AuditLog(
            actor_id=user.id,
            action="profile.extraction_started",
            resource_type="extraction_job",
            resource_id=job.id,
            details={"document_ids": job.document_ids, "field_keys": field_keys},
        )
    )
    await db.commit()
    await db.refresh(job)

    try:
        ocr_warnings: list[str] = []
        for document in documents:
            suffix = Path(document.filename).suffix.lower()
            if document.extractable or suffix not in OCR_SUFFIXES:
                continue
            try:
                document.extracted_text = await ocr_document(Path(document.storage_path), document.content_type)
                document.status = "processed"
                db.add(
                    AuditLog(
                        actor_id=user.id,
                        action="document.ocr_completed",
                        resource_type="document",
                        resource_id=document.id,
                        details={"model": get_llm_client().ocr_model, "filename": document.filename},
                    )
                )
            except Exception as exc:
                document.status = "needs_ocr"
                ocr_warnings.append(f"{document.filename}: Gemini OCR thất bại ({str(exc)[:300]}).")
        blocks, parser_warnings = await build_evidence_blocks(
            [
                {
                    "id": document.id,
                    "filename": document.filename,
                    "storage_path": document.storage_path,
                    "text": document.extracted_text,
                }
                for document in documents
            ]
        )
        warnings = [*ocr_warnings, *parser_warnings]
        if not blocks:
            detail = " ".join(warnings) or "Không tạo được evidence block từ các tài liệu đã chọn"
            raise ValueError(detail)
        results = await extract_profile_candidates(get_llm_client(), blocks, field_keys)
        for result in results:
            db.add(
                ExtractionCandidate(
                    extraction_job_id=job.id,
                    field_key=result.field_key,
                    proposed_value=result.proposed_value,
                    evidence=result.evidence,
                    confidence=result.confidence,
                    status=result.status,
                    warnings=result.warnings,
                )
            )
        job.status = "completed"
        job.warnings = warnings
        job.completed_at = datetime.now(UTC)
        db.add(
            AuditLog(
                actor_id=user.id,
                action="profile.extraction_completed",
                resource_type="extraction_job",
                resource_id=job.id,
                details={"candidate_count": len(results), "warnings": warnings},
            )
        )
    except Exception as exc:
        job.status = "failed"
        job.error = str(exc)[:1000]
        job.completed_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(job)
    return _job_read(job, await _job_candidates(job.id, db))


@router.get("/{startup_id}/extractions/{extraction_id}", response_model=ExtractionJobRead)
async def get_extraction(
    startup_id: UUID,
    extraction_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ExtractionJobRead:
    await get_owned_startup(startup_id, user, db)
    job = await db.get(ExtractionJob, extraction_id)
    if job is None or job.startup_id != startup_id or job.created_by_id != user.id:
        raise HTTPException(status_code=404, detail="Extraction không tồn tại")
    return _job_read(job, await _job_candidates(job.id, db))


@router.post("/{startup_id}/extractions/{extraction_id}/confirm", response_model=StartupRead)
async def confirm_extraction(
    startup_id: UUID,
    extraction_id: UUID,
    payload: ExtractionConfirm,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Startup:
    await get_owned_startup(startup_id, user, db, require_draft=True)
    startup = await db.scalar(select(Startup).where(Startup.id == startup_id).with_for_update())
    if startup is None:
        raise HTTPException(status_code=404, detail="Startup không tồn tại")
    job = await db.get(ExtractionJob, extraction_id)
    if job is None or job.startup_id != startup_id or job.created_by_id != user.id:
        raise HTTPException(status_code=404, detail="Extraction không tồn tại")
    if job.status != "completed":
        raise HTTPException(status_code=409, detail="Extraction không ở trạng thái có thể áp dụng")
    if startup.updated_at != job.based_on_startup_updated_at:
        raise HTTPException(
            status_code=409,
            detail="Bản nháp đã thay đổi sau khi trích xuất. Hãy chạy extraction mới để tránh ghi đè dữ liệu.",
        )

    candidates = await _job_candidates(job.id, db)
    by_id = {candidate.id: candidate for candidate in candidates}
    decisions = {decision.candidate_id: decision for decision in payload.decisions}
    if len(decisions) != len(payload.decisions):
        raise HTTPException(status_code=422, detail="Candidate decision bị trùng")
    if any(candidate_id not in by_id for candidate_id in decisions):
        raise HTTPException(status_code=422, detail="Candidate không thuộc extraction này")
    actionable = {candidate.id for candidate in candidates if candidate.proposed_value is not None}
    if not actionable.issubset(decisions):
        raise HTTPException(status_code=422, detail="Cần accept, edit hoặc reject mọi candidate có giá trị")

    fixed_patch: dict[str, str | list[str]] = {}
    facts_patch: dict[str, str | list[str]] = {}
    accepted_fields: list[str] = []
    edited_fields: list[str] = []
    rejected_fields: list[str] = []
    now = datetime.now(UTC)
    for candidate in candidates:
        decision = decisions.get(candidate.id)
        if decision is None:
            candidate.user_decision = "reject"
            candidate.confirmed_at = now
            candidate.confirmed_by_id = user.id
            rejected_fields.append(candidate.field_key)
            continue
        if decision.action == "reject":
            candidate.user_decision = "reject"
            rejected_fields.append(candidate.field_key)
        else:
            if decision.action == "accept":
                if candidate.status != "found" or candidate.proposed_value is None:
                    raise HTTPException(
                        status_code=422,
                        detail=f"{candidate.field_key} cần được chỉnh sửa vì chưa phải candidate found",
                    )
                raw_value = candidate.proposed_value
                accepted_fields.append(candidate.field_key)
            else:
                raw_value = decision.value
                edited_fields.append(candidate.field_key)
            try:
                value = normalize_profile_value(candidate.field_key, raw_value)
            except ValueError as exc:
                raise HTTPException(status_code=422, detail=str(exc)) from exc
            definition = FIELD_REGISTRY[candidate.field_key]
            if definition.target == "startup":
                fixed_patch[candidate.field_key] = value
            else:
                facts_patch[candidate.field_key] = value
            candidate.user_decision = decision.action
            candidate.confirmed_value = value
        candidate.confirmed_at = now
        candidate.confirmed_by_id = user.id

    if not fixed_patch and not facts_patch:
        raise HTTPException(status_code=422, detail="Hãy chọn ít nhất một candidate để áp dụng")
    for key, value in fixed_patch.items():
        setattr(startup, key, value)
    if facts_patch:
        startup.facts = {**(startup.facts or {}), **facts_patch}
    job.status = "applied"
    job.applied_at = now
    db.add(
        AuditLog(
            actor_id=user.id,
            action="profile.extraction_applied",
            resource_type="extraction_job",
            resource_id=job.id,
            details={
                "accepted_fields": accepted_fields,
                "edited_fields": edited_fields,
                "rejected_fields": rejected_fields,
            },
        )
    )
    await db.commit()
    await db.refresh(startup)
    return startup
