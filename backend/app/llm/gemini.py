import asyncio
import json
import re
from functools import lru_cache
from typing import TypeVar

from google import genai
from google.genai import types
from pydantic import BaseModel

from app.core.config import get_settings

ResponseT = TypeVar("ResponseT", bound=BaseModel)

# Map the retrieval-neutral input_type used by the RAG layer to Gemini task types.
_EMBED_TASK = {"passage": "RETRIEVAL_DOCUMENT", "query": "RETRIEVAL_QUERY"}


async def _with_retry(call, *, tries: int = 4):
    """Retry transient Gemini failures (429 quota / 5xx) with exponential backoff."""
    for attempt in range(tries):
        try:
            return await call()
        except Exception as error:  # google.genai raises ClientError/APIError subclasses
            transient = any(code in str(error) for code in ("429", "RESOURCE_EXHAUSTED", "503", "500"))
            if not transient or attempt == tries - 1:
                raise
            await asyncio.sleep(2**attempt)
    raise RuntimeError("unreachable")


class GeminiNotConfiguredError(RuntimeError):
    pass


class GeminiClient:
    """Single Gemini boundary used by analyzers and RAG generation."""

    def __init__(self) -> None:
        settings = get_settings()
        self.model = settings.gemini_model
        self.embed_model = settings.gemini_embed_model
        self._embed_dim = settings.gemini_embed_dim
        self._api_key = settings.gemini_api_key
        self._client = (
            genai.Client(
                api_key=self._api_key,
                http_options=types.HttpOptions(timeout=int(settings.gemini_timeout_seconds * 1000)),
            )
            if self._api_key
            else None
        )

    def _require_client(self) -> genai.Client:
        if self._client is None:
            raise GeminiNotConfiguredError("GEMINI_API_KEY chưa được cấu hình; hệ thống sẽ dùng kết quả deterministic.")
        return self._client

    async def generate_text(self, *, prompt: str, system_instruction: str, max_tokens: int | None = None) -> str:
        client = self._require_client()
        response = await _with_retry(
            lambda: client.aio.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.2,
                    max_output_tokens=max_tokens,
                ),
            )
        )
        return response.text or ""

    async def embed_texts(self, texts: list[str], *, input_type: str, batch_size: int = 100) -> list[list[float]]:
        """Embed passages ('passage') or a query ('query'). Matches NvidiaClient.embed_texts."""
        client = self._require_client()
        task_type = _EMBED_TASK.get(input_type, "RETRIEVAL_DOCUMENT")
        vectors: list[list[float]] = []
        for start in range(0, len(texts), batch_size):
            batch = texts[start : start + batch_size]
            response = await _with_retry(
                lambda batch=batch: client.aio.models.embed_content(
                    model=self.embed_model,
                    contents=batch,
                    config=types.EmbedContentConfig(
                        task_type=task_type,
                        output_dimensionality=self._embed_dim,
                    ),
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
        client = self._require_client()
        response = await client.aio.models.generate_content(
            model=self.model,
            contents=prompt,
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
