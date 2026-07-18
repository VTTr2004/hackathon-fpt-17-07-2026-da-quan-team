from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_accessible_startup, get_current_user, get_owned_startup
from app.db.session import get_db
from app.models.analysis import Analysis
from app.models.audit_log import AuditLog
from app.models.document import Document
from app.models.startup_version import StartupVersion
from app.models.user import User
from app.schemas.analysis import AnalysisRead, AnalysisRequest
from app.schemas.common import AnalysisModule
from app.services.analysis_service import run_analysis

router = APIRouter()


async def _investor_version(startup_id: UUID, user: User, db: AsyncSession) -> StartupVersion:
    if user.role != "investor":
        raise HTTPException(status_code=403, detail="Chỉ Nhà đầu tư được phân tích phiên bản đã nộp")
    await get_accessible_startup(startup_id, user, db)
    version = await db.scalar(
        select(StartupVersion)
        .where(StartupVersion.startup_id == startup_id)
        .order_by(StartupVersion.version_number.desc())
        .limit(1)
    )
    if version is None:
        raise HTTPException(status_code=409, detail="Startup chưa nộp phiên bản hồ sơ")
    return version


@router.get("/{startup_id}/analyses", response_model=list[AnalysisRead])
async def list_analyses(
    startup_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Analysis]:
    if user.role == "startup":
        await get_owned_startup(startup_id, user, db)
        query = select(Analysis).where(
            Analysis.startup_id == startup_id,
            Analysis.created_by_id == user.id,
            Analysis.startup_version_id.is_(None),
            Analysis.module == AnalysisModule.CASH_FLOW.value,
        )
    else:
        version = await _investor_version(startup_id, user, db)
        query = select(Analysis).where(
            Analysis.startup_id == startup_id,
            Analysis.startup_version_id == version.id,
            Analysis.created_by_id == user.id,
        )
    return list(await db.scalars(query.order_by(Analysis.created_at.desc())))


@router.post(
    "/{startup_id}/analyses/{module}",
    response_model=AnalysisRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_analysis(
    startup_id: UUID,
    module: AnalysisModule,
    payload: AnalysisRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Analysis:
    if user.role == "startup":
        if module is not AnalysisModule.CASH_FLOW:
            raise HTTPException(
                status_code=403,
                detail="Startup chỉ được phân tích Cash Flow trên bản nháp",
            )
        startup = await get_owned_startup(startup_id, user, db, require_draft=True)
        version = None
        startup_facts = {
            "name": startup.name,
            "industry": startup.industry,
            "stage": startup.stage,
            "primary_location": startup.primary_location,
            **(startup.facts or {}),
        }
        docs = list(await db.scalars(select(Document).where(Document.startup_id == startup_id)))
        profile_version: int | str = "draft"
    else:
        version = await _investor_version(startup_id, user, db)
        snapshot = version.snapshot
        startup_facts = {
            "name": snapshot.get("name"),
            "industry": snapshot.get("industry"),
            "stage": snapshot.get("stage"),
            "primary_location": snapshot.get("primary_location"),
            **(snapshot.get("facts") or {}),
        }
        document_ids = [UUID(item) for item in version.document_ids]
        docs = list(
            await db.scalars(
                select(Document).where(
                    Document.id.in_(document_ids),
                    Document.startup_id == startup_id,
                    Document.visibility == "shared",
                )
            )
        )
        profile_version = version.version_number

    report = await run_analysis(
        module=module,
        startup_facts=startup_facts,
        documents=[
            {
                "id": str(doc.id),
                "filename": doc.filename,
                "text": doc.extracted_text,
                "storage_path": doc.storage_path,
                "content_type": doc.content_type,
            }
            for doc in docs
        ],
        options=payload.options,
    )
    analysis = Analysis(
        startup_id=startup_id,
        startup_version_id=version.id if version is not None else None,
        created_by_id=user.id,
        module=module.value,
        version=report.version,
        status=report.status.value,
        score=report.score,
        summary=report.summary,
        report=report.model_dump(mode="json"),
    )
    db.add(analysis)
    await db.flush()
    db.add(
        AuditLog(
            actor_id=user.id,
            action="analysis.created",
            resource_type="analysis",
            resource_id=analysis.id,
            details={"module": module.value, "profile_version": profile_version},
        )
    )
    await db.commit()
    await db.refresh(analysis)
    return analysis
