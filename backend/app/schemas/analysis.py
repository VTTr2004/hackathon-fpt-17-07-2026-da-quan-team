from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import AnalysisModule


class AnalysisRequest(BaseModel):
    options: dict[str, Any] = Field(default_factory=dict)


class AnalysisRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    startup_id: UUID
    startup_version_id: UUID | None
    created_by_id: UUID | None
    module: AnalysisModule
    version: str
    status: str
    score: float | None
    summary: str
    report: dict[str, Any]
    rubric_version: str
    created_at: datetime
