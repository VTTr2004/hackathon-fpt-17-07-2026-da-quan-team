from typing import Any
from uuid import UUID

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Analysis(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "analyses"

    startup_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("startups.id", ondelete="CASCADE"), index=True
    )
    startup_version_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("startup_versions.id", ondelete="CASCADE"), index=True, nullable=True
    )
    created_by_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id"), index=True, nullable=True
    )
    module: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    version: Mapped[str] = mapped_column(String(30), default="0.1.0", nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    score: Mapped[float | None] = mapped_column(Float)
    summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    report: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    rubric_version: Mapped[str] = mapped_column(String(30), default="default-v1", nullable=False)

    startup: Mapped["Startup"] = relationship(back_populates="analyses")  # noqa: F821
