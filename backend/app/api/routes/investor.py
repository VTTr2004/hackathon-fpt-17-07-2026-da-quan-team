from collections.abc import Iterable
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import require_role
from app.db.session import get_db
from app.models.investor_pipeline import InvestorPipelineItem
from app.models.investor_preference import InvestorPreference
from app.models.startup import Startup
from app.models.startup_access import StartupAccess
from app.models.startup_match import StartupMatch
from app.models.startup_version import StartupVersion
from app.models.user import User
from app.modules.matching import score_match
from app.modules.matching.hard_filters import hard_filter_reasons
from app.schemas.investor import (
    CandidateRead,
    CompareRequest,
    InvestorPreferenceRead,
    InvestorPreferenceUpdate,
    PipelineRead,
    PipelineUpdate,
)

router = APIRouter()


async def _preference(user: User, db: AsyncSession) -> InvestorPreference:
    preference = await db.scalar(select(InvestorPreference).where(InvestorPreference.investor_id == user.id))
    if preference is None:
        preference = InvestorPreference(investor_id=user.id)
        db.add(preference)
        await db.flush()
    return preference


async def _discovery_rows(db: AsyncSession, startup_ids: Iterable[UUID] | None = None):
    # current_version identifies the immutable public snapshot; draft fields are never selected.
    query = (
        select(Startup, StartupVersion)
        .join(
            StartupVersion,
            (StartupVersion.startup_id == Startup.id) & (StartupVersion.version_number == Startup.current_version),
        )
        .where(Startup.status == "submitted", Startup.discoverable.is_(True), Startup.current_version > 0)
    )
    if startup_ids is not None:
        query = query.where(Startup.id.in_(list(startup_ids)))
    return (await db.execute(query)).all()


async def _maps(user: User, startup_ids: list[UUID], db: AsyncSession):
    accesses = (
        list(
            await db.scalars(
                select(StartupAccess).where(
                    StartupAccess.investor_id == user.id, StartupAccess.startup_id.in_(startup_ids)
                )
            )
        )
        if startup_ids
        else []
    )
    pipeline = (
        list(
            await db.scalars(
                select(InvestorPipelineItem).where(
                    InvestorPipelineItem.investor_id == user.id, InvestorPipelineItem.startup_id.in_(startup_ids)
                )
            )
        )
        if startup_ids
        else []
    )
    return ({item.startup_id: item.status for item in accesses}, {item.startup_id: item.status for item in pipeline})


def _candidate(startup: Startup, result, access_status: str, pipeline_status: str) -> CandidateRead:
    f = result.features
    return CandidateRead(
        startup_id=startup.id,
        name=f["name"],
        industry=f["industry"],
        subsector=f["subsector"],
        stage=f["stage"],
        location=f["location"],
        traction_summary=f["traction_summary"],
        fundraising_need=f["fundraising_need"],
        runway_months=f["runway_months"],
        revenue_growth=f["revenue_growth"],
        fit_score=result.fit_score,
        confidence_score=result.confidence_score,
        score_breakdown=result.score_breakdown,
        matched_reasons=result.matched_reasons,
        mismatched_reasons=result.mismatched_reasons,
        missing_evidence=result.missing_evidence,
        recommended_action=result.recommended_action,
        access_status=access_status,
        pipeline_status=pipeline_status,
    )


async def _build_candidates(user: User, db: AsyncSession, startup_ids: Iterable[UUID] | None = None):
    preference = await _preference(user, db)
    rows = await _discovery_rows(db, startup_ids)
    ids = [startup.id for startup, _ in rows]
    access_map, pipeline_map = await _maps(user, ids, db)
    candidates = []
    for startup, version in rows:
        result = score_match(version.snapshot, preference)
        if hard_filter_reasons(result.features, preference):
            continue
        candidates.append(
            _candidate(startup, result, access_map.get(startup.id, "none"), pipeline_map.get(startup.id, "discovered"))
        )
    return candidates, rows


@router.get("/preferences", response_model=InvestorPreferenceRead)
async def get_preferences(
    user: User = Depends(require_role("investor")), db: AsyncSession = Depends(get_db)
) -> InvestorPreference:
    preference = await _preference(user, db)
    await db.commit()
    await db.refresh(preference)
    return preference


@router.patch("/preferences", response_model=InvestorPreferenceRead)
async def update_preferences(
    payload: InvestorPreferenceUpdate,
    user: User = Depends(require_role("investor")),
    db: AsyncSession = Depends(get_db),
) -> InvestorPreference:
    preference = await _preference(user, db)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(preference, key, value)
    if (
        preference.ticket_min is not None
        and preference.ticket_max is not None
        and preference.ticket_min > preference.ticket_max
    ):
        raise HTTPException(status_code=422, detail="Ticket tối thiểu không được lớn hơn ticket tối đa")
    await db.commit()
    await db.refresh(preference)
    return preference


@router.post("/matches", response_model=list[CandidateRead])
async def generate_matches(
    user: User = Depends(require_role("investor")), db: AsyncSession = Depends(get_db)
) -> list[CandidateRead]:
    candidates, rows = await _build_candidates(user, db)
    versions = {startup.id: version for startup, version in rows}
    for candidate in candidates:
        version = versions[candidate.startup_id]
        match = await db.scalar(
            select(StartupMatch).where(
                StartupMatch.investor_id == user.id,
                StartupMatch.startup_id == candidate.startup_id,
                StartupMatch.startup_version_id == version.id,
            )
        )
        values = candidate.model_dump(
            include={
                "fit_score",
                "confidence_score",
                "score_breakdown",
                "matched_reasons",
                "mismatched_reasons",
                "missing_evidence",
                "recommended_action",
            }
        )
        if match is None:
            match = StartupMatch(
                investor_id=user.id, startup_id=candidate.startup_id, startup_version_id=version.id, **values
            )
            db.add(match)
        else:
            for key, value in values.items():
                setattr(match, key, value)
    await db.commit()
    return candidates


@router.get("/candidates", response_model=list[CandidateRead])
async def list_candidates(
    industry: str | None = None,
    stage: str | None = None,
    location: str | None = None,
    min_score: float = Query(default=0, ge=0, le=100),
    sort: str = "fit_score",
    user: User = Depends(require_role("investor")),
    db: AsyncSession = Depends(get_db),
) -> list[CandidateRead]:
    candidates, _ = await _build_candidates(user, db)

    def contains(actual: str | None, expected: str | None) -> bool:
        return not expected or expected.casefold() in (actual or "").casefold()

    filtered = [
        item
        for item in candidates
        if item.fit_score >= min_score
        and contains(item.industry, industry)
        and contains(item.stage, stage)
        and contains(item.location, location)
    ]
    key = "confidence_score" if sort == "confidence_score" else "fit_score"
    return sorted(filtered, key=lambda item: getattr(item, key), reverse=True)


@router.get("/candidates/{startup_id}", response_model=CandidateRead)
async def get_candidate(
    startup_id: UUID, user: User = Depends(require_role("investor")), db: AsyncSession = Depends(get_db)
) -> CandidateRead:
    candidates, _ = await _build_candidates(user, db, [startup_id])
    if not candidates:
        raise HTTPException(status_code=404, detail="Ứng viên không tồn tại hoặc không phù hợp bộ lọc bắt buộc")
    return candidates[0]


@router.post("/compare", response_model=list[CandidateRead])
async def compare_candidates(
    payload: CompareRequest, user: User = Depends(require_role("investor")), db: AsyncSession = Depends(get_db)
) -> list[CandidateRead]:
    candidates, _ = await _build_candidates(user, db, payload.startup_ids)
    return sorted(candidates, key=lambda item: item.fit_score, reverse=True)


async def _pipeline_item(user: User, startup_id: UUID, db: AsyncSession) -> InvestorPipelineItem:
    item = await db.scalar(
        select(InvestorPipelineItem).where(
            InvestorPipelineItem.investor_id == user.id, InvestorPipelineItem.startup_id == startup_id
        )
    )
    if item is None:
        item = InvestorPipelineItem(investor_id=user.id, startup_id=startup_id)
        db.add(item)
        await db.flush()
    return item


@router.post("/candidates/{startup_id}/shortlist", response_model=PipelineRead, status_code=status.HTTP_201_CREATED)
async def shortlist_candidate(
    startup_id: UUID, user: User = Depends(require_role("investor")), db: AsyncSession = Depends(get_db)
) -> PipelineRead:
    candidates, _ = await _build_candidates(user, db, [startup_id])
    if not candidates:
        raise HTTPException(status_code=404, detail="Startup không còn khả dụng trong discovery")
    item = await _pipeline_item(user, startup_id, db)
    item.status = "shortlisted"
    await db.commit()
    await db.refresh(item)
    return await _pipeline_read(item, candidates[0], db)


async def _pipeline_read(item: InvestorPipelineItem, candidate: CandidateRead | None, db: AsyncSession) -> PipelineRead:
    startup = await db.get(Startup, item.startup_id)
    access = await db.scalar(
        select(StartupAccess).where(
            StartupAccess.investor_id == item.investor_id, StartupAccess.startup_id == item.startup_id
        )
    )
    return PipelineRead(
        id=item.id,
        startup_id=item.startup_id,
        startup_name=startup.name if startup else "Startup",
        status=item.status,
        note=item.note,
        fit_score=candidate.fit_score if candidate else None,
        confidence_score=candidate.confidence_score if candidate else None,
        access_status=access.status if access else "none",
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


@router.patch("/pipeline/{item_id}", response_model=PipelineRead)
async def update_pipeline(
    item_id: UUID,
    payload: PipelineUpdate,
    user: User = Depends(require_role("investor")),
    db: AsyncSession = Depends(get_db),
) -> PipelineRead:
    item = await db.get(InvestorPipelineItem, item_id)
    if item is None or item.investor_id != user.id:
        raise HTTPException(status_code=404, detail="Pipeline item không tồn tại")
    item.status, item.note = payload.status, payload.note
    await db.commit()
    await db.refresh(item)
    candidates, _ = await _build_candidates(user, db, [item.startup_id])
    return await _pipeline_read(item, candidates[0] if candidates else None, db)


@router.get("/pipeline", response_model=list[PipelineRead])
async def list_pipeline(
    user: User = Depends(require_role("investor")), db: AsyncSession = Depends(get_db)
) -> list[PipelineRead]:
    items = list(
        await db.scalars(
            select(InvestorPipelineItem)
            .where(InvestorPipelineItem.investor_id == user.id)
            .order_by(InvestorPipelineItem.updated_at.desc())
        )
    )
    candidate_list, _ = await _build_candidates(user, db, [item.startup_id for item in items])
    candidates = {item.startup_id: item for item in candidate_list}
    return [await _pipeline_read(item, candidates.get(item.startup_id), db) for item in items]
