from pathlib import Path

PROMPT_DIR = Path(__file__).parent
PROMPT_NAMES = frozenset(
    {"customer_value", "retail_channels", "economics_market", "development_plan", "auditor", "composer"}
)


def load_prompt(name: str) -> str:
    if name not in PROMPT_NAMES:
        raise ValueError(f"Business Model system prompt không hợp lệ: {name}")
    path = PROMPT_DIR / f"{name}.system.md"
    if not path.is_file():
        raise ValueError(f"Business Model system prompt không tồn tại: {name}")
    return path.read_text(encoding="utf-8")


__all__ = ["load_prompt"]
