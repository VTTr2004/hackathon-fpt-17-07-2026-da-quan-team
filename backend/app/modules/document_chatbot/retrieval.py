"""Startup-scoped hybrid retrieval index.

Fuses dense (embedding cosine) and lexical (BM25) rankings with Reciprocal Rank Fusion.
The eval in docs/methodology.md showed hybrid >= dense on this data and is more robust when
one signal fails, so it is the default. Reranking is applied by the caller (chat_service),
which owns the LLM boundary.

The legacy ``retrieve()`` lexical function is kept as a no-embedding fallback.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import numpy as np
from rank_bm25 import BM25Okapi

_TOKEN = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


def _rrf(rank_lists: list[list[int]], k: int = 60) -> list[int]:
    scores: dict[int, float] = {}
    for ranks in rank_lists:
        for position, doc in enumerate(ranks):
            scores[doc] = scores.get(doc, 0.0) + 1.0 / (k + position + 1)
    return [doc for doc, _ in sorted(scores.items(), key=lambda item: -item[1])]


class HybridIndex:
    """In-memory index for one startup. Small corpora (hundreds of chunks) only — no ANN needed."""

    def __init__(self, chunks: list[dict[str, Any]], embeddings: np.ndarray | None) -> None:
        self.chunks = chunks
        self._bm25 = BM25Okapi([_tokenize(chunk["text"]) for chunk in chunks]) if chunks else None
        if embeddings is not None and len(embeddings):
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            self._unit = embeddings / (norms + 1e-9)
        else:
            self._unit = None

    def _dense_ranks(self, query_embedding: np.ndarray) -> list[int]:
        # Guard against a query embedded by a different provider/model than the index.
        if self._unit is None or query_embedding.shape[-1] != self._unit.shape[1]:
            return []
        query = query_embedding / (np.linalg.norm(query_embedding) + 1e-9)
        sims = self._unit @ query
        return list(np.argsort(-sims))

    def _lexical_ranks(self, question: str) -> list[int]:
        if self._bm25 is None:
            return []
        scores = self._bm25.get_scores(_tokenize(question))
        return list(np.argsort(-scores))

    def search(self, question: str, query_embedding: np.ndarray | None, *, limit: int = 10) -> list[dict[str, Any]]:
        lexical = self._lexical_ranks(question)
        dense = self._dense_ranks(query_embedding) if query_embedding is not None else []
        if lexical and dense:
            fused = _rrf([[int(i) for i in dense], [int(i) for i in lexical]])
        else:
            fused = [int(i) for i in (dense or lexical)]
        return [self.chunks[i] for i in fused[:limit]]

    # ---- persistence (one startup per index file pair under UPLOAD_DIR/rag_index) ----
    def save(self, directory: Path, key: str) -> None:
        directory.mkdir(parents=True, exist_ok=True)
        (directory / f"{key}.json").write_text(
            json.dumps(self.chunks, ensure_ascii=False), encoding="utf-8"
        )
        if self._unit is not None:
            np.save(directory / f"{key}.npy", self._unit.astype(np.float32))

    @classmethod
    def load(cls, directory: Path, key: str) -> HybridIndex | None:
        meta = directory / f"{key}.json"
        if not meta.exists():
            return None
        chunks = json.loads(meta.read_text(encoding="utf-8"))
        emb_path = directory / f"{key}.npy"
        embeddings = np.load(emb_path) if emb_path.exists() else None
        return cls(chunks, embeddings)


def retrieve(question: str, documents: list[dict[str, Any]], limit: int = 5) -> list[dict[str, Any]]:
    """Startup-scoped lexical baseline used when embeddings are unavailable."""
    terms = {term.lower() for term in re.findall(r"\w+", question, flags=re.UNICODE) if len(term) > 2}
    candidates: list[tuple[int, dict[str, Any]]] = []
    for document in documents:
        text = document.get("text", "")
        chunks = [text[index : index + 1200] for index in range(0, len(text), 1000)]
        for chunk in chunks:
            lower = chunk.lower()
            score = sum(lower.count(term) for term in terms)
            if score:
                candidates.append((score, {**document, "excerpt": chunk.strip()}))
    candidates.sort(key=lambda item: item[0], reverse=True)
    return [candidate for _, candidate in candidates[:limit]]
