from functools import lru_cache
from threading import Lock
from typing import TypeVar

from google import genai
from google.genai import errors, types
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

    async def _generate_content(self, *, prompt: str, config: types.GenerateContentConfig):
        last_key_error: errors.APIError | None = None
        attempts = self._client_attempts()
        for position, (index, client) in enumerate(attempts):
            try:
                response = await client.aio.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=config,
                )
            except errors.APIError as exc:
                if not self._should_try_next_key(exc) or position == len(attempts) - 1:
                    raise
                last_key_error = exc
                continue
            self._set_active_client(index)
            return response
        # Defensive fallback; the final failed attempt normally raises above.
        assert last_key_error is not None
        raise last_key_error

    async def generate_text(self, *, prompt: str, system_instruction: str) -> str:
        response = await self._generate_content(
            prompt=prompt,
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
