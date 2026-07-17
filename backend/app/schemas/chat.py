from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(min_length=2, max_length=4000)


class Citation(BaseModel):
    document_id: str
    filename: str
    excerpt: str
    page: int | None = None
    locator: str | None = None  # human-readable source position, e.g. "row 5", "slide 2"


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]
    grounded: bool
    model: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
