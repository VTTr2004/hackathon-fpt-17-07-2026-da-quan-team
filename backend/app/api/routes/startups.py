from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_accessible_startup, get_current_user, get_owned_startup
from app.db.session import get_db
from app.models.audit_log import AuditLog
from app.models.document import Document
from app.models.investor_pipeline import InvestorPipelineItem
from app.models.startup import Startup
from app.models.startup_access import StartupAccess
from app.models.startup_version import StartupVersion
from app.models.user import User
from app.schemas.investor import AccessRequestCreate
from app.schemas.startup import (
    AccessGrantRequest,
    AccessRead,
    CompletenessRead,
    DiscoveryUpdate,
    StartupCreate,
    StartupRead,
    StartupUpdate,
    StartupVersionRead,
    VersionDiffRead,
)

router = APIRouter()

REQUIRED_FIELDS: tuple[tuple[str, str], ...] = (
    ("name", "Tên startup"),
    ("industry", "Lĩnh vực"),
    ("stage", "Giai đoạn"),
    ("location", "Địa điểm chính xác"),
    ("problem", "Nhu cầu hoặc vấn đề khách hàng"),
    ("solution", "Giải pháp"),
    ("target_customers", "Khách hàng mục tiêu"),
    ("core_products", "Sản phẩm/dịch vụ chính"),
    ("revenue_model", "Nguồn doanh thu"),
    ("currency", "Đơn vị tiền tệ"),
    ("cash_as_of", "Ngày chốt số dư"),
    ("current_cash", "Tiền mặt hiện có"),
    ("monthly_revenue", "Doanh thu trung bình tháng"),
    ("fixed_monthly_costs", "Chi phí cố định"),
    ("variable_costs", "Chi phí biến đổi"),
)


def _has_value(value: Any) -> bool:
    if isinstance(value, (list, dict)):
        return bool(value)
    return value is not None and str(value).strip() != ""


def _snapshot(startup: Startup) -> dict[str, Any]:
    return {
        "name": startup.name,
        "industry": startup.industry,
        "stage": startup.stage,
        "primary_location": startup.primary_location,
        "facts": startup.facts,
    }


def _read_from_snapshot(startup: Startup, version: StartupVersion) -> StartupRead:
    data = version.snapshot
    return StartupRead(
        id=startup.id,
        owner_id=startup.owner_id,
        name=data.get("name", startup.name),
        industry=data.get("industry"),
        stage=data.get("stage"),
        primary_location=data.get("primary_location"),
        facts=data.get("facts") or {},
        status=version.status,
        current_version=version.version_number,
        discoverable=startup.discoverable,
        public_summary=startup.public_summary or {},
        created_at=startup.created_at,
        updated_at=version.submitted_at,
    )


async def _latest_version(startup_id: UUID, db: AsyncSession) -> StartupVersion | None:
    return await db.scalar(
        select(StartupVersion)
        .where(StartupVersion.startup_id == startup_id)
        .order_by(StartupVersion.version_number.desc())
        .limit(1)
    )


async def _completeness(startup: Startup, db: AsyncSession) -> CompletenessRead:
    facts = startup.facts or {}
    values = {
        "name": startup.name,
        "industry": startup.industry,
        "stage": startup.stage,
        "location": startup.primary_location or facts.get("exact_location"),
        **facts,
    }
    missing_fields = [label for key, label in REQUIRED_FIELDS if not _has_value(values.get(key))]
    document_count = await db.scalar(
        select(Document.id).where(Document.startup_id == startup.id, Document.visibility == "shared").limit(1)
    )
    missing_documents = [] if document_count else ["Ít nhất một tài liệu nền (PDF, DOCX, PPTX hoặc XLSX)"]
    format_errors: list[str] = []
    cash = facts.get("current_cash")
    if _has_value(cash):
        try:
            if float(cash) < 0:
                format_errors.append("Tiền mặt hiện có không được âm")
        except (TypeError, ValueError):
            format_errors.append("Tiền mặt hiện có phải là số")
    complete = not missing_fields and not missing_documents and not format_errors
    return CompletenessRead(
        complete=complete,
        completed_fields=len(REQUIRED_FIELDS) - len(missing_fields),
        total_fields=len(REQUIRED_FIELDS),
        missing_fields=missing_fields,
        missing_documents=missing_documents,
        format_errors=format_errors,
        can_submit=complete and startup.status == "draft",
    )


@router.get("", response_model=list[StartupRead])
async def list_startups(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> list[StartupRead]:
    if user.role == "startup":
        startups = list(
            await db.scalars(select(Startup).where(Startup.owner_id == user.id).order_by(Startup.created_at.desc()))
        )
        return [StartupRead.model_validate(item) for item in startups]

    startups = list(
        await db.scalars(
            select(Startup)
            .join(StartupAccess, StartupAccess.startup_id == Startup.id)
            .where(StartupAccess.investor_id == user.id, StartupAccess.status == "active")
            .order_by(Startup.created_at.desc())
        )
    )
    result: list[StartupRead] = []
    for startup in startups:
        version = await _latest_version(startup.id, db)
        if version:
            result.append(_read_from_snapshot(startup, version))
    return result


@router.post("", response_model=StartupRead, status_code=status.HTTP_201_CREATED)
async def create_startup(
    payload: StartupCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> Startup:
    if user.role != "startup":
        raise HTTPException(status_code=403, detail="Chỉ Startup được tạo hồ sơ")
    startup = Startup(owner_id=user.id, **payload.model_dump())
    db.add(startup)
    await db.flush()
    db.add(AuditLog(actor_id=user.id, action="startup.created", resource_type="startup", resource_id=startup.id))
    await db.commit()
    await db.refresh(startup)
    return startup


@router.get("/{startup_id}", response_model=StartupRead)
async def get_startup(
    startup_id: UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> StartupRead:
    startup = await get_accessible_startup(startup_id, user, db)
    if user.role == "investor":
        version = await _latest_version(startup_id, db)
        if version is None:
            raise HTTPException(status_code=404, detail="Hồ sơ chưa được nộp")
        return _read_from_snapshot(startup, version)
    return StartupRead.model_validate(startup)


@router.patch("/{startup_id}", response_model=StartupRead)
async def update_startup(
    startup_id: UUID,
    payload: StartupUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Startup:
    startup = await get_owned_startup(startup_id, user, db, require_draft=True)
    changed = payload.model_dump(exclude_unset=True)
    for key, value in changed.items():
        setattr(startup, key, value)
    db.add(
        AuditLog(
            actor_id=user.id,
            action="startup.draft_updated",
            resource_type="startup",
            resource_id=startup.id,
            details={"fields": list(changed)},
        )
    )
    await db.commit()
    await db.refresh(startup)
    return startup


@router.patch("/{startup_id}/discovery", response_model=StartupRead)
async def update_discovery(
    startup_id: UUID,
    payload: DiscoveryUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Startup:
    startup = await get_owned_startup(startup_id, user, db)
    if payload.discoverable and startup.current_version < 1:
        raise HTTPException(status_code=409, detail="Hồ sơ phải được nộp ít nhất một phiên bản trước khi bật khám phá")
    startup.discoverable = payload.discoverable
    if payload.public_summary is not None:
        startup.public_summary = payload.public_summary
    db.add(
        AuditLog(actor_id=user.id, action="startup.discovery_updated", resource_type="startup", resource_id=startup.id)
    )
    await db.commit()
    await db.refresh(startup)
    return startup


@router.get("/{startup_id}/completeness", response_model=CompletenessRead)
async def check_completeness(
    startup_id: UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> CompletenessRead:
    # This reads the mutable live draft. Investors must remain scoped to a
    # submitted snapshot and therefore cannot inspect draft completeness.
    startup = await get_owned_startup(startup_id, user, db)
    return await _completeness(startup, db)


@router.post("/{startup_id}/submit", response_model=StartupVersionRead, status_code=status.HTTP_201_CREATED)
async def submit_startup(
    startup_id: UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> StartupVersion:
    startup = await get_owned_startup(startup_id, user, db, require_draft=True)
    completeness = await _completeness(startup, db)
    if not completeness.complete:
        raise HTTPException(status_code=422, detail="Hồ sơ chưa đầy đủ. Hãy kiểm tra danh sách thông tin còn thiếu.")
    documents = list(await db.scalars(select(Document).where(Document.startup_id == startup.id)))
    next_number = startup.current_version + 1
    version = StartupVersion(
        startup_id=startup.id,
        version_number=next_number,
        snapshot=_snapshot(startup),
        document_ids=[str(item.id) for item in documents if item.visibility == "shared"],
        created_by_id=user.id,
    )
    db.add(version)
    startup.current_version = next_number
    startup.status = "submitted"
    await db.flush()
    db.add(
        AuditLog(
            actor_id=user.id,
            action="startup.submitted",
            resource_type="startup_version",
            resource_id=version.id,
            details={"version_number": next_number},
        )
    )
    await db.commit()
    await db.refresh(version)
    return version


@router.post("/{startup_id}/draft", response_model=StartupRead)
async def create_next_draft(
    startup_id: UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> Startup:
    startup = await get_owned_startup(startup_id, user, db)
    if startup.status == "draft":
        return startup
    startup.status = "draft"
    db.add(
        AuditLog(
            actor_id=user.id,
            action="startup.next_draft_created",
            resource_type="startup",
            resource_id=startup.id,
            details={"based_on_version": startup.current_version},
        )
    )
    await db.commit()
    await db.refresh(startup)
    return startup


@router.get("/{startup_id}/versions", response_model=list[StartupVersionRead])
async def list_versions(
    startup_id: UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> list[StartupVersion]:
    await get_accessible_startup(startup_id, user, db)
    return list(
        await db.scalars(
            select(StartupVersion)
            .where(StartupVersion.startup_id == startup_id)
            .order_by(StartupVersion.version_number.desc())
        )
    )


def _flatten(snapshot: dict[str, Any]) -> dict[str, Any]:
    facts = snapshot.get("facts") or {}
    return {key: value for key, value in snapshot.items() if key != "facts"} | {
        f"facts.{key}": value for key, value in facts.items()
    }


@router.get("/{startup_id}/versions/diff", response_model=VersionDiffRead)
async def compare_versions(
    startup_id: UUID,
    from_version: int,
    to_version: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> VersionDiffRead:
    await get_accessible_startup(startup_id, user, db)
    versions = list(
        await db.scalars(
            select(StartupVersion).where(
                StartupVersion.startup_id == startup_id,
                StartupVersion.version_number.in_([from_version, to_version]),
            )
        )
    )
    by_number = {item.version_number: item for item in versions}
    if from_version not in by_number or to_version not in by_number:
        raise HTTPException(status_code=404, detail="Phiên bản không tồn tại")
    old, new = _flatten(by_number[from_version].snapshot), _flatten(by_number[to_version].snapshot)
    changes = [
        {"field": key, "before": old.get(key), "after": new.get(key)}
        for key in sorted(old.keys() | new.keys())
        if old.get(key) != new.get(key)
    ]
    return VersionDiffRead(from_version=from_version, to_version=to_version, changes=changes)


@router.get("/{startup_id}/access", response_model=list[AccessRead])
async def list_access(
    startup_id: UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> list[AccessRead]:
    await get_owned_startup(startup_id, user, db)
    rows = await db.execute(
        select(StartupAccess, User)
        .join(User, User.id == StartupAccess.investor_id)
        .where(StartupAccess.startup_id == startup_id)
    )
    return [
        AccessRead(
            investor_id=investor.id,
            investor_name=investor.full_name,
            investor_email=investor.email,
            status=access.status,
            request_reason=access.request_reason,
        )
        for access, investor in rows.all()
    ]


@router.post("/{startup_id}/access", response_model=AccessRead)
async def grant_access(
    startup_id: UUID,
    payload: AccessGrantRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AccessRead:
    await get_owned_startup(startup_id, user, db)
    investor = await db.get(User, payload.investor_id)
    if investor is None or investor.role != "investor":
        raise HTTPException(status_code=404, detail="Nhà đầu tư không tồn tại")
    access = await db.scalar(
        select(StartupAccess).where(StartupAccess.startup_id == startup_id, StartupAccess.investor_id == investor.id)
    )
    if access:
        access.status = "active"
        access.revoked_at = None
        access.granted_at = datetime.now(UTC)
        access.granted_by_id = user.id
    else:
        access = StartupAccess(
            startup_id=startup_id,
            investor_id=investor.id,
            granted_by_id=user.id,
            status="active",
            granted_at=datetime.now(UTC),
        )
        db.add(access)
    db.add(
        AuditLog(
            actor_id=user.id,
            action="startup.access_granted",
            resource_type="startup",
            resource_id=startup_id,
            details={"investor_id": str(investor.id)},
        )
    )
    await db.commit()
    return AccessRead(
        investor_id=investor.id,
        investor_name=investor.full_name,
        investor_email=investor.email,
        status="active",
        request_reason=access.request_reason,
    )


@router.post("/{startup_id}/access-request", response_model=AccessRead, status_code=status.HTTP_201_CREATED)
async def request_access(
    startup_id: UUID,
    payload: AccessRequestCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AccessRead:
    if user.role != "investor":
        raise HTTPException(status_code=403, detail="Chỉ nhà đầu tư được gửi yêu cầu mở Data Room")
    startup = await db.get(Startup, startup_id)
    if startup is None or startup.status != "submitted" or not startup.discoverable or startup.current_version < 1:
        raise HTTPException(status_code=404, detail="Startup không khả dụng trong discovery")
    access = await db.scalar(
        select(StartupAccess).where(StartupAccess.startup_id == startup_id, StartupAccess.investor_id == user.id)
    )
    if access and access.status == "active":
        raise HTTPException(status_code=409, detail="Bạn đã có quyền truy cập startup này")
    if access:
        access.status = "pending"
        access.request_reason = payload.reason
        access.granted_by_id = None
        access.granted_at = None
        access.revoked_at = None
    else:
        access = StartupAccess(
            startup_id=startup_id,
            investor_id=user.id,
            granted_by_id=None,
            status="pending",
            request_reason=payload.reason,
            granted_at=None,
        )
        db.add(access)
    pipeline = await db.scalar(
        select(InvestorPipelineItem).where(
            InvestorPipelineItem.investor_id == user.id, InvestorPipelineItem.startup_id == startup_id
        )
    )
    if pipeline is None:
        pipeline = InvestorPipelineItem(investor_id=user.id, startup_id=startup_id)
        db.add(pipeline)
    pipeline.status = "access_requested"
    db.add(
        AuditLog(
            actor_id=user.id,
            action="startup.access_requested",
            resource_type="startup",
            resource_id=startup_id,
            details={"reason": payload.reason},
        )
    )
    await db.commit()
    return AccessRead(
        investor_id=user.id,
        investor_name=user.full_name,
        investor_email=user.email,
        status="pending",
        request_reason=payload.reason,
    )


async def _decide_access(
    startup_id: UUID,
    investor_id: UUID,
    decision: str,
    user: User,
    db: AsyncSession,
) -> AccessRead:
    await get_owned_startup(startup_id, user, db)
    row = await db.execute(
        select(StartupAccess, User)
        .join(User, User.id == StartupAccess.investor_id)
        .where(StartupAccess.startup_id == startup_id, StartupAccess.investor_id == investor_id)
    )
    record = row.first()
    if record is None:
        raise HTTPException(status_code=404, detail="Yêu cầu truy cập không tồn tại")
    access, investor = record
    if access.status != "pending":
        raise HTTPException(status_code=409, detail="Yêu cầu này không còn ở trạng thái chờ")
    access.status = decision
    if decision == "active":
        access.granted_by_id = user.id
        access.granted_at = datetime.now(UTC)
        access.revoked_at = None
        pipeline = await db.scalar(
            select(InvestorPipelineItem).where(
                InvestorPipelineItem.investor_id == investor_id,
                InvestorPipelineItem.startup_id == startup_id,
            )
        )
        if pipeline:
            pipeline.status = "reviewing"
    db.add(
        AuditLog(
            actor_id=user.id,
            action=f"startup.access_{'approved' if decision == 'active' else 'rejected'}",
            resource_type="startup",
            resource_id=startup_id,
            details={"investor_id": str(investor_id)},
        )
    )
    await db.commit()
    return AccessRead(
        investor_id=investor.id,
        investor_name=investor.full_name,
        investor_email=investor.email,
        status=access.status,
        request_reason=access.request_reason,
    )


@router.post("/{startup_id}/access/{investor_id}/approve", response_model=AccessRead)
async def approve_access(
    startup_id: UUID, investor_id: UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> AccessRead:
    return await _decide_access(startup_id, investor_id, "active", user, db)


@router.post("/{startup_id}/access/{investor_id}/reject", response_model=AccessRead)
async def reject_access(
    startup_id: UUID, investor_id: UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> AccessRead:
    return await _decide_access(startup_id, investor_id, "rejected", user, db)


@router.delete("/{startup_id}/access/{investor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_access(
    startup_id: UUID,
    investor_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await get_owned_startup(startup_id, user, db)
    access = await db.scalar(
        select(StartupAccess).where(StartupAccess.startup_id == startup_id, StartupAccess.investor_id == investor_id)
    )
    if access is None:
        raise HTTPException(status_code=404, detail="Quyền truy cập không tồn tại")
    access.status = "revoked"
    access.revoked_at = datetime.now(UTC)
    db.add(
        AuditLog(
            actor_id=user.id,
            action="startup.access_revoked",
            resource_type="startup",
            resource_id=startup_id,
            details={"investor_id": str(investor_id)},
        )
    )
    await db.commit()
