"""Build, persist, and load per-startup hybrid indexes.

Embeddings come from the NVIDIA boundary. When NVIDIA is not configured (or fails), the index
is built lexical-only (BM25), so the chatbot degrades gracefully instead of breaking.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import numpy as np

from app.core.config import get_settings
from app.llm.nvidia import get_nvidia_client
from app.modules.document_chatbot.retrieval import HybridIndex


def index_dir() -> Path:
    return Path(get_settings().upload_dir) / "rag_index"


def documents_signature(documents: list[dict[str, Any]]) -> str:
    """Stable fingerprint of a startup's documents; changes when content is added/edited."""
    payload = "\n".join(f"{doc['id']}:{len(doc.get('text', ''))}" for doc in documents)
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()  # noqa: S324 - cache key, not security


def stored_signature(key: str) -> str | None:
    sig_path = index_dir() / f"{key}.sig"
    return sig_path.read_text(encoding="utf-8").strip() if sig_path.exists() else None


async def build_index(
    key: str, chunks: list[dict[str, Any]], *, persist: bool = True, signature: str | None = None
) -> HybridIndex:
    embeddings: np.ndarray | None = None
    if chunks:
        try:
            vectors = await get_nvidia_client().embed_texts(
                [chunk["text"] for chunk in chunks], input_type="passage"
            )
            embeddings = np.array(vectors, dtype=np.float32)
        except Exception:
            embeddings = None  # graceful degradation: BM25-only index
    index = HybridIndex(chunks, embeddings)
    if persist and chunks:
        index.save(index_dir(), key)
        if signature is not None:
            (index_dir() / f"{key}.sig").write_text(signature, encoding="utf-8")
    return index


def load_index(key: str) -> HybridIndex | None:
    return HybridIndex.load(index_dir(), key)
