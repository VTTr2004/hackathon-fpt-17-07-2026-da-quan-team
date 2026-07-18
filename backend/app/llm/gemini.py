import asyncio
import json
import re
from functools import lru_cache
from threading import Lock
from typing import TypeVar

from google import genai
from google.genai import errors, types
from pydantic import BaseModel

from app.core.config import get_settings

ResponseT = TypeVar("ResponseT", bound=BaseModel)

# Map the retrieval-neutral input_type used by the RAG layer to Gemini task types.
_EMBED_TASK = {"passage": "RETRIEVAL_DOCUMENT", "query": "RETRIEVAL_QUERY"}


def _is_transient(exc: errors.APIError) -> bool:
    """Quota/rate-limit or server errors — worth backing off and retrying the key rotation."""
    return exc.code in {429, 500, 503} or (exc.status or "").upper() == "RESOURCE_EXHAUSTED"


class GeminiNotConfiguredError(RuntimeError):
    pass


class GeminiClient:
    """Single Gemini boundary used by analyzers and RAG (generation + embeddings + rerank).

    Supports multiple API keys (``GEMINI_API_KEY`` comma-separated) with failover: a 429 or
    key-specific auth error rotates to the next key; if every key fails with a transient error the
    whole rotation is retried with exponential backoff. Failover covers both chat and embeddings.
    """

    def __init__(self) -> None:
        settings = get_settings()
        self.model = settings.gemini_model
        self.embed_model = settings.gemini_embed_model
        self._embed_dim = settings.gemini_embed_dim
        self._clients = [
            genai.Client(
                api_key=api_key,
                http_options=types.HttpOptions(timeout=int(settings.gemini_timeout_seconds * 1000)),
            )
            for api_key in settings.gemini_api_keys
        ]
        self._active_client_index = 0
        self._client_index_lock = Lock()

    def _require_clients(self) -> list[genai.Client]:
        if not self._clients:
            raise GeminiNotConfiguredError(
                "GEMINI_API_KEY chưa được cấu hình; hệ thống sẽ dùng kết quả deterministic."
            )
        return self._clients

    def _client_attempts(self) -> list[tuple[int, genai.Client]]:
        clients = self._require_clients()
        with self._client_index_lock:
            start = self._active_client_index
        indices = ((start + offset) % len(clients) for offset in range(len(clients)))
        return [(index, clients[index]) for index in indices]

    def _set_active_client(self, index: int) -> None:
        with self._client_index_lock:
            self._active_client_index = index

    @staticmethod
    def _should_try_next_key(exc: errors.APIError) -> bool:
        """Only rotate for quota/rate-limit or key-specific authentication errors."""
        status = (exc.status or "").upper()
        if exc.code == 429 or status == "RESOURCE_EXHAUSTED":
            return True
        if exc.code in {401, 403} or status in {"UNAUTHENTICATED", "PERMISSION_DENIED"}:
            return True
        error_text = f"{exc.message or ''} {exc.details!s}".lower()
        return exc.code == 400 and "api key" in error_text and any(
            marker in error_text for marker in ("invalid", "expired", "revoked", "leaked")
        )

    async def _invoke(self, make_call, *, retries: int = 3):
        """Run ``make_call(client)`` with per-key failover and transient backoff.

        make_call must build and return a fresh awaitable each time it is called (it may run once
        per key and once per retry round).
        """
        last_error: errors.APIError | None = None
        for round_index in range(retries):
            attempts = self._client_attempts()
            for index, client in attempts:
                try:
                    response = await make_call(client)
                except errors.APIError as exc:
                    last_error = exc
                    if not self._should_try_next_key(exc):
                        raise  # non-retryable (e.g. malformed request) — surface immediately
                    continue  # rotate to the next key
                self._set_active_client(index)
                return response
            # Every key failed this round with a rotatable error.
            if round_index == retries - 1 or last_error is None or not _is_transient(last_error):
                break
            await asyncio.sleep(2**round_index)
        assert last_error is not None
        raise last_error

    async def _generate_content(self, *, prompt: str, config: types.GenerateContentConfig):
        return await self._invoke(
            lambda client: client.aio.models.generate_content(
                model=self.model,
                contents=prompt,
                config=config,
            )
        )

    async def generate_text(self, *, prompt: str, system_instruction: str, max_tokens: int | None = None) -> str:
        response = await self._generate_content(
            prompt=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.2,
                max_output_tokens=max_tokens,
            ),
        )
        return response.text or ""

    async def embed_texts(self, texts: list[str], *, input_type: str, batch_size: int = 100) -> list[list[float]]:
        """Embed passages ('passage') or a query ('query'). Matches NvidiaClient.embed_texts."""
        self._require_clients()
        task_type = _EMBED_TASK.get(input_type, "RETRIEVAL_DOCUMENT")
        config = types.EmbedContentConfig(task_type=task_type, output_dimensionality=self._embed_dim)
        vectors: list[list[float]] = []
        for start in range(0, len(texts), batch_size):
            batch = texts[start : start + batch_size]
            response = await self._invoke(
                lambda client, payload=batch: client.aio.models.embed_content(
                    model=self.embed_model,
                    contents=payload,
                    config=config,
                )
            )
            vectors.extend(list(embedding.values) for embedding in response.embeddings)
        return vectors

    async def rerank(self, question: str, passages: list[str], *, top_n: int = 10) -> list[int]:
        """LLM listwise reranker (mirrors NvidiaClient.rerank); returns passage indices best-first."""
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

    async def generate_structured(
        self,
        *,
        prompt: str,
        system_instruction: str,
        response_model: type[ResponseT],
    ) -> ResponseT:
        response = await self._generate_content(
            prompt=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.1,
                response_mime_type="application/json",
                response_schema=response_model,
            ),
        )
        if response.parsed is not None:
            return response.parsed
        return response_model.model_validate_json(response.text or "{}")


@lru_cache
def get_llm_client() -> GeminiClient:
    return GeminiClient()
