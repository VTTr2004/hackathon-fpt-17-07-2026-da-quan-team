from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ExtractionCreate(BaseModel):
    document_ids: list[UUID] = Field(default_factory=list, max_length=50)
    field_keys: list[str] = Field(default_factory=list, max_length=30)


class ExtractionCandidateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    field_key: str
    label: str
    value_type: str
    proposed_value: Any | None
    evidence: list[dict[str, Any]]
    confidence: float
    status: str
    warnings: list[str]
    user_decision: str | None
    confirmed_value: Any | None


class ExtractionJobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    startup_id: UUID
    status: str
    document_ids: list[str]
    field_keys: list[str]
    schema_version: str
    based_on_startup_updated_at: datetime
    warnings: list[str]
    error: str | None
    completed_at: datetime | None
    applied_at: datetime | None
    created_at: datetime
    candidates: list[ExtractionCandidateRead] = Field(default_factory=list)


class ExtractionDecision(BaseModel):
    candidate_id: UUID
    action: Literal["accept", "edit", "reject"]
    value: Any | None = None


class ExtractionConfirm(BaseModel):
    decisions: list[ExtractionDecision] = Field(min_length=1, max_length=30)
