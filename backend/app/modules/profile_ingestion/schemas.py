from typing import Any, Literal

from pydantic import BaseModel, Field

ExtractionStatus = Literal["found", "not_found", "ambiguous", "conflicting"]


class EvidenceBlock(BaseModel):
    block_id: str
    document_id: str
    filename: str
    text: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class LLMEvidenceReference(BaseModel):
    block_id: str
    quote: str = ""


class LLMCandidate(BaseModel):
    field_key: str
    proposed_value: str | list[str] | None = None
    extraction_status: ExtractionStatus = "not_found"
    evidence: list[LLMEvidenceReference] = Field(default_factory=list, max_length=5)
    warnings: list[str] = Field(default_factory=list)


class LLMExtractionResult(BaseModel):
    candidates: list[LLMCandidate] = Field(default_factory=list)


class ValidatedCandidate(BaseModel):
    field_key: str
    proposed_value: Any | None = None
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    confidence: float = Field(default=0, ge=0, le=1)
    status: ExtractionStatus = "not_found"
    warnings: list[str] = Field(default_factory=list)
