from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.analysis import Analysis
from app.models.document import Document
from app.models.startup import Startup
from app.schemas.analysis import AnalysisRead, AnalysisRequest
from app.schemas.common import AnalysisModule
from app.services.analysis_service import run_analysis

router = APIRouter()


@router.get("/{startup_id}/analyses", response_model=list[AnalysisRead])
async def list_analyses(startup_id: UUID, db: AsyncSession = Depends(get_db)) -> list[Analysis]:
    result = await db.scalars(
        select(Analysis).where(Analysis.startup_id == startup_id).order_by(Analysis.created_at.desc())
    )
    return list(result)


@router.post(
    "/{startup_id}/analyses/{module}",
    response_model=AnalysisRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_analysis(
    startup_id: UUID,
    module: AnalysisModule,
    payload: AnalysisRequest,
    db: AsyncSession = Depends(get_db),
) -> Analysis:
    startup = await db.get(Startup, startup_id)
    if startup is None:
        raise HTTPException(status_code=404, detail="Startup không tồn tại")
    docs = list(await db.scalars(select(Document).where(Document.startup_id == startup_id)))
    report = await run_analysis(
        module=module,
        startup_facts={
            "name": startup.name,
            "industry": startup.industry,
            "stage": startup.stage,
            "primary_location": startup.primary_location,
            **startup.facts,
        },
        documents=[{"id": str(doc.id), "filename": doc.filename, "text": doc.extracted_text} for doc in docs],
        options=payload.options,
    )
    analysis = Analysis(
        startup_id=startup_id,
        module=module.value,
        version=report.version,
        status=report.status.value,
        score=report.score,
        summary=report.summary,
        report=report.model_dump(mode="json"),
    )
    db.add(analysis)
    await db.commit()
    await db.refresh(analysis)
    return analysis
