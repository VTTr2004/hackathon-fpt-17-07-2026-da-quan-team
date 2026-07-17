from typing import Any, Protocol

from app.schemas.common import ModuleReport


class Analyzer(Protocol):
    async def analyze(
        self,
        startup_facts: dict[str, Any],
        documents: list[dict[str, Any]],
        options: dict[str, Any],
    ) -> ModuleReport: ...
