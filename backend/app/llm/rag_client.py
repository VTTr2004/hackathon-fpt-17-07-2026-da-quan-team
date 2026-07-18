"""Provider selection for the RAG chatbot.

Returns whichever LLM boundary the ``LLM_PROVIDER`` setting selects. Both GeminiClient and
NvidiaClient expose the same trio used by retrieval + generation: ``generate_text``,
``embed_texts(..., input_type=...)`` and ``rerank(...)``, plus a ``model`` / ``embed_model`` attr.
"""
from __future__ import annotations

from app.core.config import get_settings
from app.llm.gemini import GeminiClient, GeminiNotConfiguredError, get_llm_client
from app.llm.nvidia import NvidiaClient, NvidiaNotConfiguredError, get_nvidia_client

# Catch either provider's "not configured" error at the call site.
LLMNotConfiguredError = (GeminiNotConfiguredError, NvidiaNotConfiguredError)

RagClient = GeminiClient | NvidiaClient


def get_rag_client() -> RagClient:
    if get_settings().llm_provider.lower() == "nvidia":
        return get_nvidia_client()
    return get_llm_client()


def active_provider() -> str:
    return "nvidia" if get_settings().llm_provider.lower() == "nvidia" else "gemini"


def active_embed_model() -> str:
    settings = get_settings()
    return settings.nvidia_embed_model if active_provider() == "nvidia" else settings.gemini_embed_model
