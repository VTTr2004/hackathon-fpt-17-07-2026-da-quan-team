from typing import Any
from uuid import UUID

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ChatMessage(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "chat_messages"

    startup_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("startups.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=True
    )
    startup_version_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("startup_versions.id", ondelete="SET NULL"), index=True, nullable=True
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    citations: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list, nullable=False)

    startup: Mapped["Startup"] = relationship(back_populates="chat_messages")  # noqa: F821
