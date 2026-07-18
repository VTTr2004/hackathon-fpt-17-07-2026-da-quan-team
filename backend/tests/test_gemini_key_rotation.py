from types import SimpleNamespace

import pytest
from google.genai import errors
from pydantic import BaseModel

from app.core.config import Settings
from app.llm import gemini


class StructuredAnswer(BaseModel):
    answer: str


class FakeModels:
    def __init__(self, outcomes: list[object]) -> None:
        self.outcomes = outcomes
        self.calls = 0

    async def generate_content(self, **_: object) -> object:
        self.calls += 1
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome


class FakeClient:
    def __init__(self, outcomes: list[object]) -> None:
        self.aio = SimpleNamespace(models=FakeModels(outcomes))


def api_error(code: int, status: str, message: str) -> errors.APIError:
    return errors.APIError(code, {"error": {"code": code, "status": status, "message": message}})


def build_client(monkeypatch: pytest.MonkeyPatch, clients: list[FakeClient]) -> gemini.GeminiClient:
    settings = Settings(gemini_api_key=",".join(f"key-{index}" for index in range(len(clients))))
    monkeypatch.setattr(gemini, "get_settings", lambda: settings)
    pending = iter(clients)
    monkeypatch.setattr(gemini.genai, "Client", lambda **_: next(pending))
    return gemini.GeminiClient()


def test_settings_parses_and_deduplicates_comma_separated_keys() -> None:
    settings = Settings(gemini_api_key=" first, second,first, ,third ")

    assert settings.gemini_api_keys == ["first", "second", "third"]


@pytest.mark.asyncio
async def test_text_call_rotates_on_quota_error_and_keeps_working_key(monkeypatch: pytest.MonkeyPatch) -> None:
    first = FakeClient([api_error(429, "RESOURCE_EXHAUSTED", "Quota exceeded")])
    second = FakeClient([SimpleNamespace(text="ok"), SimpleNamespace(text="ok again")])
    client = build_client(monkeypatch, [first, second])

    assert await client.generate_text(prompt="hello", system_instruction="system") == "ok"
    assert await client.generate_text(prompt="hello", system_instruction="system") == "ok again"
    assert first.aio.models.calls == 1
    assert second.aio.models.calls == 2


@pytest.mark.asyncio
async def test_structured_call_rotates_on_invalid_key(monkeypatch: pytest.MonkeyPatch) -> None:
    first = FakeClient([api_error(400, "INVALID_ARGUMENT", "API key expired")])
    second = FakeClient([SimpleNamespace(parsed=StructuredAnswer(answer="ok"), text=None)])
    client = build_client(monkeypatch, [first, second])

    result = await client.generate_structured(
        prompt="hello",
        system_instruction="system",
        response_model=StructuredAnswer,
    )

    assert result.answer == "ok"


@pytest.mark.asyncio
async def test_non_key_error_does_not_rotate(monkeypatch: pytest.MonkeyPatch) -> None:
    bad_request = api_error(400, "INVALID_ARGUMENT", "Invalid response schema")
    first = FakeClient([bad_request])
    second = FakeClient([SimpleNamespace(text="must not be used")])
    client = build_client(monkeypatch, [first, second])

    with pytest.raises(errors.APIError) as caught:
        await client.generate_text(prompt="hello", system_instruction="system")

    assert caught.value is bad_request
    assert second.aio.models.calls == 0
