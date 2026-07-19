from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ProfileInterviewSession(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "profile_interview_sessions"

    startup_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("startups.id", ondelete="CASCADE"), index=True
    )
    created_by_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), index=True)
    status: Mapped[str] = mapped_column(String(30), default="active", nullable=False, index=True)
    based_on_startup_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    required_field_keys: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    pending_required_keys: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    current_question: Mapped[str | None] = mapped_column(Text)
    transcript: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list, nullable=False)
    proposals: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
