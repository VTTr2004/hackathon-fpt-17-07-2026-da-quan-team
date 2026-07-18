from uuid import UUID

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.services.document_parser import has_extractable_text


class Document(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "documents"

    startup_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("startups.id", ondelete="CASCADE"), index=True
    )
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(150))
    storage_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="processed", nullable=False)
    visibility: Mapped[str] = mapped_column(String(30), default="shared", nullable=False)
    uploaded_by_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id"), index=True, nullable=True
    )
    extracted_text: Mapped[str] = mapped_column(Text, default="", nullable=False)

    @property
    def extractable(self) -> bool:
        return has_extractable_text(self.extracted_text)

    startup: Mapped["Startup"] = relationship(back_populates="documents")  # noqa: F821
