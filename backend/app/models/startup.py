from typing import Any

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Startup(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "startups"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    industry: Mapped[str | None] = mapped_column(String(120))
    stage: Mapped[str | None] = mapped_column(String(80))
    primary_location: Mapped[str | None] = mapped_column(String(500))
    facts: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)

    documents: Mapped[list["Document"]] = relationship(  # noqa: F821
        back_populates="startup", cascade="all, delete-orphan"
    )
    analyses: Mapped[list["Analysis"]] = relationship(  # noqa: F821
        back_populates="startup", cascade="all, delete-orphan"
    )
    chat_messages: Mapped[list["ChatMessage"]] = relationship(  # noqa: F821
        back_populates="startup", cascade="all, delete-orphan"
    )
