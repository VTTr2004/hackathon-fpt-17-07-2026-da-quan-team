from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ExtractionJob(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "extraction_jobs"

    startup_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("startups.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[str] = mapped_column(String(30), default="pending", nullable=False, index=True)
    document_ids: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    field_keys: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    schema_version: Mapped[str] = mapped_column(String(30), default="profile-v1", nullable=False)
    based_on_startup_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_by_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), index=True)
    warnings: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    error: Mapped[str | None] = mapped_column(Text)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ExtractionCandidate(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "extraction_candidates"
    __table_args__ = (
        UniqueConstraint("extraction_job_id", "field_key", name="uq_extraction_candidate_job_field"),
    )

    extraction_job_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("extraction_jobs.id", ondelete="CASCADE"), index=True
    )
    field_key: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    proposed_value: Mapped[Any | None] = mapped_column(JSONB)
    evidence: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="not_found", nullable=False)
    warnings: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    user_decision: Mapped[str | None] = mapped_column(String(30))
    confirmed_value: Mapped[Any | None] = mapped_column(JSONB)
    confirmed_by_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
