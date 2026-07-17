from functools import lru_cache
from typing import TypeVar

from google import genai
from google.genai import types
from pydantic import BaseModel

from app.core.config import get_settings

ResponseT = TypeVar("ResponseT", bound=BaseModel)


class GeminiNotConfiguredError(RuntimeError):
    pass


class GeminiClient:
    """Single Gemini boundary used by analyzers and RAG generation."""

    def __init__(self) -> None:
        settings = get_settings()
        self.model = settings.gemini_model
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

    async def generate_text(self, *, prompt: str, system_instruction: str) -> str:
        client = self._require_client()
        response = await client.aio.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.2,
            ),
        )
        return response.text or ""

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
