from typing import Literal

from pydantic import BaseModel, Field

AgentAnswerStatus = Literal[
    "supported",
    "partial",
    "insufficient_data",
    "deferred_to_aggregator",
    "out_of_scope",
]
Confidence = Literal["low", "medium", "high"]


class ResearchBasis(BaseModel):
    source_id: str
    principle_used: str
    application: str
    limitation: str


class StartupEvidence(BaseModel):
    field: str
    value_summary: str
    verification: Literal["user_provided", "document_supported", "tool_output"] = "user_provided"


class AgentAnswer(BaseModel):
    question_id: str
    status: AgentAnswerStatus
    conclusion: str
    analysis: str
    startup_evidence: list[StartupEvidence] = Field(default_factory=list)
    research_basis: list[ResearchBasis] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    missing_data: list[str] = Field(default_factory=list)
    recommended_questions: list[str] = Field(default_factory=list)
    confidence: Confidence = "low"


class SubagentResult(BaseModel):
    agent_id: str
    answers: list[AgentAnswer] = Field(default_factory=list)


class AuditedFinding(BaseModel):
    agent_id: str
    question_id: str
    title: str
    detail: str
    source_ids: list[str] = Field(default_factory=list)
    confidence: Confidence = "low"


class AuditResult(BaseModel):
    accepted_findings: list[AuditedFinding] = Field(default_factory=list)
    rejected_claims: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    missing_data: list[str] = Field(default_factory=list)
    recommended_questions: list[str] = Field(default_factory=list)


class ComposedReport(BaseModel):
    summary: str
    findings: list[AuditedFinding] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    missing_data: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    recommended_questions: list[str] = Field(default_factory=list)


class AgentFlowResult(BaseModel):
    subagent_results: list[SubagentResult]
    audit: AuditResult
    report: ComposedReport
