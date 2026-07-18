from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class StartupVersion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "startup_versions"
    __table_args__ = (UniqueConstraint("startup_id", "version_number", name="uq_startup_version_number"),)

    startup_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("startups.id", ondelete="CASCADE"), index=True
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="submitted", nullable=False)
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    document_ids: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    created_by_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    locked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
