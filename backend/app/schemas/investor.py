from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class InvestorPreferenceUpdate(BaseModel):
    preferred_industries: list[str] | None = None
    preferred_subsectors: list[str] | None = None
    preferred_stages: list[str] | None = None
    preferred_locations: list[str] | None = None
    ticket_min: int | None = Field(default=None, ge=0)
    ticket_max: int | None = Field(default=None, ge=0)
    minimum_monthly_revenue: float | None = Field(default=None, ge=0)
    minimum_revenue_growth: float | None = None
    maximum_runway_months: float | None = Field(default=None, ge=0)
    required_capabilities: list[str] | None = None
    strategic_capabilities: list[str] | None = None
    exclusion_rules: dict[str, Any] | None = None
    weights: dict[str, float] | None = None

    @model_validator(mode="after")
    def validate_ticket_range(self):
        if self.ticket_min is not None and self.ticket_max is not None and self.ticket_min > self.ticket_max:
            raise ValueError("ticket_min must be less than or equal to ticket_max")
        return self


class InvestorPreferenceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    preferred_industries: list[str]
    preferred_subsectors: list[str]
    preferred_stages: list[str]
    preferred_locations: list[str]
    ticket_min: int | None
    ticket_max: int | None
    minimum_monthly_revenue: float | None
    minimum_revenue_growth: float | None
    maximum_runway_months: float | None
    required_capabilities: list[str]
    strategic_capabilities: list[str]
    exclusion_rules: dict[str, Any]
    weights: dict[str, float]


class CandidateRead(BaseModel):
    startup_id: UUID
    name: str
    industry: str | None
    subsector: str | None
    stage: str | None
    location: str | None
    traction_summary: str | None
    fundraising_need: str | None
    runway_months: float | None
    revenue_growth: float | None
    fit_score: float
    confidence_score: float
    score_breakdown: dict[str, float]
    matched_reasons: list[str]
    mismatched_reasons: list[str]
    missing_evidence: list[str]
    recommended_action: str
    access_status: Literal["none", "pending", "active", "rejected", "revoked"]
    pipeline_status: str


class CompareRequest(BaseModel):
    startup_ids: list[UUID] = Field(min_length=2, max_length=5)


class PipelineUpdate(BaseModel):
    status: Literal["discovered", "shortlisted", "access_requested", "reviewing", "interested", "passed"]
    note: str | None = Field(default=None, max_length=2000)


class PipelineRead(BaseModel):
    id: UUID
    startup_id: UUID
    startup_name: str
    status: str
    note: str | None
    fit_score: float | None
    confidence_score: float | None
    access_status: str
    created_at: datetime
    updated_at: datetime


class AccessRequestCreate(BaseModel):
    reason: str | None = Field(default=None, max_length=1000)
