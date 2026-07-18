"""NVIDIA NIM boundary (OpenAI-compatible) used by the RAG chatbot.

Exposes chat generation, query/passage embeddings, and an optional LLM-as-reranker.
All network access to NVIDIA goes through this single class so the rest of the app
never talks to the provider directly.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache

import httpx

from app.core.config import get_settings


class NvidiaNotConfiguredError(RuntimeError):
    pass


class NvidiaClient:
    def __init__(self) -> None:
        settings = get_settings()
        self._base = settings.nvidia_base_url.rstrip("/")
        self.chat_model = settings.nvidia_chat_model
        self.embed_model = settings.nvidia_embed_model
        self._key = settings.nvidia_api_key
        self._timeout = settings.nvidia_timeout_seconds

    @property
    def model(self) -> str:
        return self.chat_model

    def _headers(self) -> dict[str, str]:
        if not self._key:
            raise NvidiaNotConfiguredError(
                "NVIDIA_API_KEY chưa được cấu hình; RAG sẽ dùng retrieval lexical và fallback extractive."
            )
        return {"Authorization": f"Bearer {self._key}", "Content-Type": "application/json"}

    async def _post(self, path: str, payload: dict) -> dict:
        headers = self._headers()
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(f"{self._base}{path}", headers=headers, json=payload)
            response.raise_for_status()
            return response.json()

    async def generate_text(self, *, prompt: str, system_instruction: str, max_tokens: int = 1024) -> str:
        data = await self._post(
            "/chat/completions",
            {
                "model": self.chat_model,
                "temperature": 0.2,
                "max_tokens": max_tokens,
                "messages": [
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": prompt},
                ],
            },
        )
        return data["choices"][0]["message"].get("content") or ""

    async def embed_texts(self, texts: list[str], *, input_type: str, batch_size: int = 16) -> list[list[float]]:
        """input_type is 'passage' when indexing documents, 'query' when embedding a question."""
        vectors: list[list[float]] = []
        for start in range(0, len(texts), batch_size):
            chunk = texts[start : start + batch_size]
            data = await self._post(
                "/embeddings",
                {"model": self.embed_model, "input": chunk, "input_type": input_type, "truncate": "END"},
            )
            ordered = sorted(data["data"], key=lambda item: item["index"])
            vectors.extend(item["embedding"] for item in ordered)
        return vectors

    async def rerank(self, question: str, passages: list[str], *, top_n: int = 10) -> list[int]:
        """LLM listwise reranker: returns passage indices best-first.

        No dedicated rerank NIM is exposed on integrate.api.nvidia.com, so the chat model
        reorders the shortlist. Falls back to the original order on any parse failure.
        """
        shortlist = passages[:top_n]
        listing = "\n".join(f"[{i}] {text}" for i, text in enumerate(shortlist))
        try:
            raw = await self.generate_text(
                prompt=f"Question: {question}\n\nPassages:\n{listing}",
                system_instruction=(
                    "You are a search reranker. Given a question and numbered passages, return the passage "
                    "indices from most to least relevant as a JSON list of integers, e.g. [3,0,1]. "
                    "Output only the JSON list."
                ),
                max_tokens=200,
            )
            order = json.loads(re.search(r"\[.*\]", raw, re.S).group(0))
        except Exception:
            return list(range(len(shortlist)))
        seen: set[int] = set()
        ranked: list[int] = []
        for value in order:
            if isinstance(value, int) and 0 <= value < len(shortlist) and value not in seen:
                seen.add(value)
                ranked.append(value)
        ranked.extend(i for i in range(len(shortlist)) if i not in seen)
        return ranked


@lru_cache
def get_nvidia_client() -> NvidiaClient:
    return NvidiaClient()
