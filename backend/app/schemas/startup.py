from datetime import datetime
from typing import Any
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


class StartupRead(StartupCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime
