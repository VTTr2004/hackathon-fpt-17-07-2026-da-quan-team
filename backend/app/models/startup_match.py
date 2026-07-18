from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Float, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class StartupMatch(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "startup_matches"
    __table_args__ = (
        UniqueConstraint("investor_id", "startup_id", "startup_version_id", name="uq_investor_startup_version_match"),
    )

    investor_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    startup_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("startups.id", ondelete="CASCADE"), index=True
    )
    startup_version_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("startup_versions.id", ondelete="CASCADE")
    )
    fit_score: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    score_breakdown: Mapped[dict[str, float]] = mapped_column(JSONB, default=dict, nullable=False)
    matched_reasons: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    mismatched_reasons: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    missing_evidence: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    recommended_action: Mapped[str] = mapped_column(default="review")
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
