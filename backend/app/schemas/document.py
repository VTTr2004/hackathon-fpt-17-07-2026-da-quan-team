from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    startup_id: UUID
    filename: str
    content_type: str | None
    status: str
    extractable: bool
    visibility: str
    category: str
    categorized_by: str
    created_at: datetime


class DocumentVisibilityUpdate(BaseModel):
    visibility: str
