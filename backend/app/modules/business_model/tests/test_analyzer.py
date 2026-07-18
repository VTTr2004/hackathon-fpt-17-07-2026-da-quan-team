from typing import Any

import pytest

from app.llm.gemini import GeminiNotConfiguredError
from app.modules.business_model.analyzer import BusinessModelAnalyzer
from app.modules.business_model.tests.test_orchestrator import SOURCE_BY_AGENT, FakeFlowLLM
from app.schemas.common import AnalysisModule, AnalysisStatus


class FailingLLM:
    def __init__(self, error: Exception) -> None:
        self.error = error
        self.calls = 0

    async def generate_text(self, *, prompt: str, system_instruction: str) -> str:
        raise self.error

    async def generate_structured(
        self,
        *,
        prompt: str,
        system_instruction: str,
        response_model: type[Any],
    ) -> Any:
        self.calls += 1
        raise self.error


@pytest.mark.asyncio
async def test_analyzer_disabled_is_deterministic_and_does_not_mutate_options() -> None:
    llm = FailingLLM(AssertionError("must not be called"))
    options = {"use_gemini": False}
    report = await BusinessModelAnalyzer(llm).analyze(
        {"problem": "Khách cần nhanh", "current_cash": 100, "exact_location": "Quận 1"},
        [],
        options,
    )

    assert llm.calls == 0
    assert options == {"use_gemini": False}
    assert report.module is AnalysisModule.BUSINESS_MODEL
    assert report.status is AnalysisStatus.PARTIAL
    assert report.details["scope"] == "business_model_only"
    assert report.details["agent_flow"] == {"status": "disabled", "composed": False}
    assert "current_cash" not in report.missing_data
    assert "exact_location" not in report.missing_data


@pytest.mark.asyncio
async def test_analyzer_empty_facts_is_insufficient() -> None:
    report = await BusinessModelAnalyzer().analyze({}, [], {"use_gemini": False})
    assert report.status is AnalysisStatus.INSUFFICIENT_DATA
    assert report.score == 0
    assert len(report.missing_data) == 27


@pytest.mark.asyncio
async def test_analyzer_fake_agent_flow_composes_evidence_tools_and_stops_second_llm() -> None:
    llm = FakeFlowLLM()
    options = {"use_gemini": True}
    facts = {
        "problem": "Nhân viên cần bữa sáng nhanh",
        "core_products": ["Cà phê"],
        "average_order_value": 85_000,
        "variable_cost_per_order": 42_000,
        "planning_horizon_months": 12,
        "current_cash": 999_999,
        "exact_location": "Không thuộc module",
    }

    report = await BusinessModelAnalyzer(llm).analyze(facts, [{"filename": "sample.pdf"}], options)

    assert options["use_gemini"] is False
    assert report.summary == "Báo cáo đã ghép"
    assert report.details["agent_flow"]["status"] == "completed"
    assert report.details["agent_flow"]["composed"] is True
    assert report.details["documents_available_but_not_auto_cited"] == 1
    assert len(report.findings) == 4
    assert {item.evidence_id for item in report.evidence}.issuperset(set(SOURCE_BY_AGENT.values()))
    order_call = next(call for call in report.tool_calls if call.name == "business_model_order_economics")
    assert order_call.output["contribution_per_order"] == 43_000
    serialized_report = report.model_dump_json()
    assert "current_cash" not in serialized_report
    assert "exact_location" not in serialized_report


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("error", "expected_reason"),
    [
        (GeminiNotConfiguredError("missing key"), "missing key"),
        (RuntimeError("provider down"), "RuntimeError"),
    ],
)
async def test_analyzer_llm_failure_returns_deterministic_fallback(
    error: Exception,
    expected_reason: str,
) -> None:
    options = {"use_business_agents": True, "use_gemini": True}
    report = await BusinessModelAnalyzer(FailingLLM(error)).analyze(
        {"problem": "Có dữ liệu"},
        [],
        options,
    )

    assert options["use_gemini"] is False
    assert report.status is AnalysisStatus.PARTIAL
    assert report.details["agent_flow"]["status"] == "deterministic_fallback"
    assert report.details["agent_flow"]["reason"] == expected_reason
    if isinstance(error, RuntimeError) and not isinstance(error, GeminiNotConfiguredError):
        assert report.risks
