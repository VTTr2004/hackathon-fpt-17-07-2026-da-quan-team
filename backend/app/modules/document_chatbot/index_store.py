"""Build, persist, and load per-startup hybrid indexes.

Embeddings come from the active RAG provider (Gemini or NVIDIA). When the provider is not
configured (or fails), the index is built lexical-only (BM25), so the chatbot degrades gracefully
instead of breaking. Persisted files are namespaced by provider + embedding model so switching
providers never mixes incompatible vector dimensions.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import numpy as np

from app.core.config import get_settings
from app.llm.rag_client import active_embed_model, active_provider, get_rag_client
from app.modules.document_chatbot.retrieval import HybridIndex


def index_dir() -> Path:
    return Path(get_settings().upload_dir) / "rag_index"


def _index_name(key: str) -> str:
    """Namespace an index by provider + embed model (dims differ across providers)."""
    slug = f"{active_provider()}-{active_embed_model()}".replace("/", "-").replace(".", "-")
    return f"{key}__{slug}"


def documents_signature(documents: list[dict[str, Any]]) -> str:
    """Stable fingerprint of a startup's documents; changes when content is added/edited."""
    payload = "\n".join(f"{doc['id']}:{len(doc.get('text', ''))}" for doc in documents)
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()  # noqa: S324 - cache key, not security


def stored_signature(key: str) -> str | None:
    sig_path = index_dir() / f"{_index_name(key)}.sig"
    return sig_path.read_text(encoding="utf-8").strip() if sig_path.exists() else None


async def build_index(
    key: str, chunks: list[dict[str, Any]], *, persist: bool = True, signature: str | None = None
) -> HybridIndex:
    embeddings: np.ndarray | None = None
    if chunks:
        try:
            vectors = await get_rag_client().embed_texts(
                [chunk["text"] for chunk in chunks], input_type="passage"
            )
            embeddings = np.array(vectors, dtype=np.float32)
        except Exception:
            embeddings = None  # graceful degradation: BM25-only index
    index = HybridIndex(chunks, embeddings)
    if persist and chunks:
        name = _index_name(key)
        index.save(index_dir(), name)
        if signature is not None:
            (index_dir() / f"{name}.sig").write_text(signature, encoding="utf-8")
    return index


def load_index(key: str) -> HybridIndex | None:
    return HybridIndex.load(index_dir(), _index_name(key))
