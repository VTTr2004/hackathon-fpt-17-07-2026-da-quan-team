from typing import Any

from pydantic import BaseModel, Field


class LLMInterviewProposal(BaseModel):
    field_key: str
    proposed_value: str | float | int | list[str] | None = None
    supporting_quote: str = ""
    confidence: float = Field(default=0, ge=0, le=1)
    reasoning: str = ""


class LLMInterviewResult(BaseModel):
    proposals: list[LLMInterviewProposal] = Field(default_factory=list)


class ValidatedInterviewProposal(BaseModel):
    field_key: str
    proposed_value: Any
    confidence: float
    source_quote: str
    reasoning: str
