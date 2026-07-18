from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class StartupCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    industry: str | None = Field(default=None, max_length=120)
    stage: str | None = Field(default=None, max_length=80)
    primary_location: str | None = Field(default=None, max_length=500)
    facts: dict[str, Any] = Field(default_factory=dict)


class StartupUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    industry: str | None = Field(default=None, max_length=120)
    stage: str | None = Field(default=None, max_length=80)
    primary_location: str | None = Field(default=None, max_length=500)
    facts: dict[str, Any] | None = None


class DiscoveryUpdate(BaseModel):
    discoverable: bool
    public_summary: dict[str, bool] | None = None


class StartupRead(StartupCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    owner_id: UUID | None
    status: str
    current_version: int
    discoverable: bool
    public_summary: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class CompletenessRead(BaseModel):
    complete: bool
    completed_fields: int
    total_fields: int
    missing_fields: list[str]
    missing_documents: list[str]
    format_errors: list[str]
    can_submit: bool


class StartupVersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    startup_id: UUID
    version_number: int
    status: str
    snapshot: dict[str, Any]
    document_ids: list[str]
    created_by_id: UUID
    submitted_at: datetime
    locked_at: datetime


class VersionDiffRead(BaseModel):
    from_version: int
    to_version: int
    changes: list[dict[str, Any]]


class AccessGrantRequest(BaseModel):
    investor_id: UUID


class AccessRead(BaseModel):
    investor_id: UUID
    investor_name: str
    investor_email: str
    status: Literal["pending", "active", "rejected", "revoked"]
    request_reason: str | None = None
