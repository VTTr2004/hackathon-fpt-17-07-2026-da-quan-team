from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class ProfileInterviewProposalRead(BaseModel):
    field_key: str
    label: str
    priority: Literal["required", "major", "optional"]
    value_type: str
    proposed_value: Any
    confidence: float
    source_quote: str
    reasoning: str


class ProfileInterviewRead(BaseModel):
    id: UUID
    startup_id: UUID
    status: str
    required_field_keys: list[str]
    pending_required_keys: list[str]
    current_question: str | None
    transcript: list[dict[str, Any]]
    proposals: list[ProfileInterviewProposalRead]
    based_on_startup_updated_at: datetime
    created_at: datetime
    completed_at: datetime | None
    applied_at: datetime | None


class ProfileInterviewAnswer(BaseModel):
    answer: str = Field(min_length=1, max_length=10000)


class ProfileInterviewDecision(BaseModel):
    field_key: str
    action: Literal["accept", "edit", "reject"]
    value: Any | None = None


class ProfileInterviewConfirm(BaseModel):
    decisions: list[ProfileInterviewDecision] = Field(min_length=1, max_length=100)
