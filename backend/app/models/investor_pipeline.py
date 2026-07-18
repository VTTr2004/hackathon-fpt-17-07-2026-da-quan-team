from uuid import UUID

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class InvestorPipelineItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "investor_pipeline_items"
    __table_args__ = (UniqueConstraint("investor_id", "startup_id", name="uq_investor_pipeline_startup"),)

    investor_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    startup_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("startups.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[str] = mapped_column(String(30), default="discovered", nullable=False)
    note: Mapped[str | None] = mapped_column(String(2000), nullable=True)
