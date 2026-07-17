from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class AnalysisModule(StrEnum):
    BUSINESS_MODEL = "business_model"
    CASH_FLOW = "cash_flow"
    SURROUNDING_AREA = "surrounding_area"


class AnalysisStatus(StrEnum):
    COMPLETED = "completed"
    PARTIAL = "partial"
    INSUFFICIENT_DATA = "insufficient_data"
    NOT_APPLICABLE = "not_applicable"
    FAILED = "failed"


class Evidence(BaseModel):
    evidence_id: str
    source_type: str
    title: str
    publisher: str | None = None
    url: str | None = None
    document_id: str | None = None
    page: int | None = None
    quote: str | None = None
    accessed_at: datetime | None = None
    reliability: str = "medium"
    notes: str | None = None


class ToolCall(BaseModel):
    name: str
    version: str
    input: dict[str, Any]
    output: dict[str, Any]
    warnings: list[str] = Field(default_factory=list)


class Finding(BaseModel):
    title: str
    detail: str
    evidence_ids: list[str] = Field(default_factory=list)
    confidence: str = "medium"


class ModuleReport(BaseModel):
    module: AnalysisModule
    version: str = "0.1.0"
    status: AnalysisStatus
    score: float | None = Field(default=None, ge=0, le=100)
    summary: str
    findings: list[Finding] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    missing_data: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    recommended_questions: list[str] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    methodology: list[str] = Field(default_factory=list)
    tool_calls: list[ToolCall] = Field(default_factory=list)
    details: dict[str, Any] = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=lambda: datetime.now().astimezone())
