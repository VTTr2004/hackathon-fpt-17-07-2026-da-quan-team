from typing import Any
from uuid import UUID

from sqlalchemy import BigInteger, Float, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class InvestorPreference(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "investor_preferences"

    investor_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True
    )
    preferred_industries: Mapped[list[str]] = mapped_column(JSONB, default=lambda: ["F&B", "Retail"], nullable=False)
    preferred_subsectors: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    preferred_stages: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    preferred_locations: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    ticket_min: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    ticket_max: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    minimum_monthly_revenue: Mapped[float | None] = mapped_column(Float, nullable=True)
    minimum_revenue_growth: Mapped[float | None] = mapped_column(Float, nullable=True)
    maximum_runway_months: Mapped[float | None] = mapped_column(Float, nullable=True)
    required_capabilities: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    strategic_capabilities: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    exclusion_rules: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    weights: Mapped[dict[str, float]] = mapped_column(JSONB, default=dict, nullable=False)
