from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


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


class ChatMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    role: str
    content: str
    citations: list[Citation] = Field(default_factory=list)
    created_at: datetime
