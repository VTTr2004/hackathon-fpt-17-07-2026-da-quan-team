import pytest

from app.modules.business_model.prompts import load_prompt

PROMPT_NAMES = (
    "customer_value",
    "retail_channels",
    "economics_market",
    "development_plan",
    "auditor",
    "composer",
)


@pytest.mark.parametrize("name", PROMPT_NAMES)
def test_prompt_loader_reads_each_embedded_vietnamese_prompt(name: str) -> None:
    prompt = load_prompt(name)
    assert len(prompt) > 250
    assert "Không" in prompt or "không" in prompt


@pytest.mark.parametrize("name", ["missing", "../missing", "", "cash_flow", "surrounding_area"])
def test_prompt_loader_rejects_unknown_or_out_of_scope_prompt(name: str) -> None:
    with pytest.raises(ValueError, match="không hợp lệ"):
        load_prompt(name)
