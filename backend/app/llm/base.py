from typing import Protocol, TypeVar

from pydantic import BaseModel

ResponseT = TypeVar("ResponseT", bound=BaseModel)


class LLMClient(Protocol):
    async def generate_text(self, *, prompt: str, system_instruction: str) -> str: ...

    async def generate_structured(
        self,
        *,
        prompt: str,
        system_instruction: str,
        response_model: type[ResponseT],
    ) -> ResponseT: ...
