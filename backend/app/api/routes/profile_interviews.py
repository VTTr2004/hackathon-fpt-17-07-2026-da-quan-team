from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user, get_owned_startup
from app.db.session import get_db
from app.llm.gemini import GeminiNotConfiguredError, get_llm_client
from app.models.audit_log import AuditLog
from app.models.profile_interview import ProfileInterviewSession
from app.models.startup import Startup
from app.models.user import User
from app.modules.profile_interview.registry import INTERVIEW_FIELDS, REQUIRED_INTERVIEW_KEYS
from app.modules.profile_interview.service import (
    analyze_answer,
    missing_required,
    next_required_question,
    normalize_interview_value,
    profile_values,
)
from app.schemas.profile_interview import (
    ProfileInterviewAnswer,
    ProfileInterviewConfirm,
    ProfileInterviewProposalRead,
    ProfileInterviewRead,
)
from app.schemas.startup import StartupRead

router = APIRouter()


def _session_read(session: ProfileInterviewSession) -> ProfileInterviewRead:
    proposals = []
    for key, proposal in session.proposals.items():
        field = INTERVIEW_FIELDS.get(key)
        if field is None:
            continue
        proposals.append(
            ProfileInterviewProposalRead(
                field_key=key,
                label=field.label,
                priority=field.priority,
                value_type=field.value_type,
                proposed_value=proposal["proposed_value"],
                confidence=proposal["confidence"],
                source_quote=proposal["source_quote"],
                reasoning=proposal.get("reasoning", ""),
            )
        )
    order = {"required": 0, "major": 1, "optional": 2}
    proposals.sort(key=lambda item: (order[item.priority], item.label))
    return ProfileInterviewRead(
        id=session.id,
        startup_id=session.startup_id,
        status=session.status,
        required_field_keys=session.required_field_keys,
        pending_required_keys=session.pending_required_keys,
        current_question=session.current_question,
        transcript=session.transcript,
        proposals=proposals,
        based_on_startup_updated_at=session.based_on_startup_updated_at,
        created_at=session.created_at,
        completed_at=session.completed_at,
        applied_at=session.applied_at,
    )


async def _owned_session(startup_id: UUID, interview_id: UUID, user: User, db: AsyncSession) -> ProfileInterviewSession:
    session = await db.get(ProfileInterviewSession, interview_id)
    if session is None or session.startup_id != startup_id or session.created_by_id != user.id:
        raise HTTPException(status_code=404, detail="Phiên phỏng vấn không tồn tại")
    return session


@router.post(
    "/{startup_id}/profile-interviews",
    response_model=ProfileInterviewRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_profile_interview(
    startup_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProfileInterviewRead:
    startup = await get_owned_startup(startup_id, user, db, require_draft=True)
    pending = missing_required(profile_values(startup))
    if not pending:
        raise HTTPException(status_code=409, detail="Các trường bắt buộc đã đầy đủ; không cần phỏng vấn AI")
    existing_session = await db.scalar(
        select(ProfileInterviewSession)
        .where(
            ProfileInterviewSession.startup_id == startup_id,
            ProfileInterviewSession.created_by_id == user.id,
            ProfileInterviewSession.status.in_(["active", "review"]),
        )
        .order_by(ProfileInterviewSession.created_at.desc())
        .limit(1)
    )
    if existing_session and existing_session.based_on_startup_updated_at == startup.updated_at:
        return _session_read(existing_session)
    question = next_required_question(pending)
    session = ProfileInterviewSession(
        startup_id=startup_id,
        created_by_id=user.id,
        status="active",
        based_on_startup_updated_at=startup.updated_at,
        required_field_keys=list(REQUIRED_INTERVIEW_KEYS),
        pending_required_keys=pending,
        current_question=question,
        transcript=[{"role": "assistant", "content": question}] if question else [],
        proposals={},
    )
    db.add(session)
    await db.flush()
    db.add(
        AuditLog(
            actor_id=user.id,
            action="profile.interview_started",
            resource_type="profile_interview",
            resource_id=session.id,
            details={"pending_required_keys": pending},
        )
    )
    await db.commit()
    await db.refresh(session)
    return _session_read(session)


@router.post(
    "/{startup_id}/profile-interviews/{interview_id}/answer",
    response_model=ProfileInterviewRead,
)
async def answer_profile_interview(
    startup_id: UUID,
    interview_id: UUID,
    payload: ProfileInterviewAnswer,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProfileInterviewRead:
    startup = await get_owned_startup(startup_id, user, db, require_draft=True)
    session = await _owned_session(startup_id, interview_id, user, db)
    if session.status != "active" or not session.current_question:
        raise HTTPException(status_code=409, detail="Phiên phỏng vấn không còn nhận câu trả lời")
    if len(session.transcript) >= 30:
        raise HTTPException(status_code=409, detail="Phiên phỏng vấn đã đạt giới hạn lượt; hãy bắt đầu lại")
    if startup.updated_at != session.based_on_startup_updated_at:
        raise HTTPException(status_code=409, detail="Hồ sơ đã thay đổi; hãy bắt đầu phiên phỏng vấn mới")

    existing = profile_values(startup)
    existing.update({key: item["proposed_value"] for key, item in session.proposals.items()})
    try:
        extracted = await analyze_answer(
            get_llm_client(),
            answer=payload.answer,
            current_question=session.current_question,
            existing_values=existing,
        )
    except GeminiNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail="AI chưa được cấu hình. Hãy thiết lập GEMINI_API_KEY.") from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI chưa thể xử lý câu trả lời: {str(exc)[:300]}") from exc

    proposals = dict(session.proposals)
    for item in extracted:
        if INTERVIEW_FIELDS[item.field_key].priority == "required" and item.confidence < 0.7:
            continue
        proposals[item.field_key] = item.model_dump(mode="json")
    session.proposals = proposals
    transcript = list(session.transcript)
    transcript.append({"role": "user", "content": payload.answer})
    pending = missing_required(
        profile_values(startup), {key: item["proposed_value"] for key, item in proposals.items()}
    )
    session.pending_required_keys = pending
    session.current_question = next_required_question(pending)
    if session.current_question:
        transcript.append({"role": "assistant", "content": session.current_question})
    else:
        session.status = "review"
        session.completed_at = datetime.now(UTC)
        transcript.append(
            {"role": "assistant", "content": "Đã đủ dữ liệu bắt buộc. Hãy kiểm tra các đề xuất trước khi áp dụng."}
        )
    session.transcript = transcript
    await db.commit()
    await db.refresh(session)
    return _session_read(session)


@router.post(
    "/{startup_id}/profile-interviews/{interview_id}/confirm",
    response_model=StartupRead,
)
async def confirm_profile_interview(
    startup_id: UUID,
    interview_id: UUID,
    payload: ProfileInterviewConfirm,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Startup:
    await get_owned_startup(startup_id, user, db, require_draft=True)
    startup = await db.scalar(select(Startup).where(Startup.id == startup_id).with_for_update())
    if startup is None:
        raise HTTPException(status_code=404, detail="Startup không tồn tại")
    session = await _owned_session(startup_id, interview_id, user, db)
    if session.status != "review":
        raise HTTPException(status_code=409, detail="Phiên phỏng vấn chưa sẵn sàng để áp dụng")
    if startup.updated_at != session.based_on_startup_updated_at:
        raise HTTPException(status_code=409, detail="Hồ sơ đã thay đổi; không thể áp dụng phiên phỏng vấn cũ")
    decisions = {item.field_key: item for item in payload.decisions}
    if len(decisions) != len(payload.decisions) or any(key not in session.proposals for key in decisions):
        raise HTTPException(status_code=422, detail="Quyết định field không hợp lệ hoặc bị trùng")

    fixed_patch: dict[str, object] = {}
    facts_patch: dict[str, object] = {}
    applied_fields: list[str] = []
    for key, proposal in session.proposals.items():
        decision = decisions.get(key)
        if decision is None or decision.action == "reject":
            continue
        raw_value = proposal["proposed_value"] if decision.action == "accept" else decision.value
        try:
            value = normalize_interview_value(key, raw_value)
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        field = INTERVIEW_FIELDS[key]
        if field.target == "startup":
            fixed_patch[key] = value
        else:
            facts_patch[key] = value
        applied_fields.append(key)
    if not applied_fields:
        raise HTTPException(status_code=422, detail="Hãy chọn ít nhất một đề xuất để áp dụng")
    for key, value in fixed_patch.items():
        setattr(startup, key, value)
    if facts_patch:
        startup.facts = {**(startup.facts or {}), **facts_patch}
    session.status = "applied"
    session.applied_at = datetime.now(UTC)
    db.add(
        AuditLog(
            actor_id=user.id,
            action="profile.interview_applied",
            resource_type="profile_interview",
            resource_id=session.id,
            details={"applied_fields": applied_fields},
        )
    )
    await db.commit()
    await db.refresh(startup)
    return startup
