import json
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from app.modules.cash_flow.analyzer import CashFlowAnalyzer
from app.modules.cash_flow.ingestion_agent import CashFlowIngestionAgent, build_heuristic_plan
from app.modules.cash_flow.ingestion_schemas import (
    CashFlowIngestionPlan,
    IngestionToolName,
    IngestionToolRequest,
)
from app.modules.cash_flow.normalizer import normalize_cash_flow_input
from app.modules.cash_flow.workbook_profiler import (
    MAX_PROFILE_COLUMNS,
    MAX_PROFILE_ROWS,
    profile_cash_flow_workbooks,
)

SAMPLE_ROOT = Path(__file__).resolve().parents[5] / "sample-data" / "goc-ho-coffee"


def _sample_documents() -> list[dict[str, Any]]:
    return [
        {
            "id": path.stem,
            "filename": path.name,
            "storage_path": str(path),
        }
        for path in sorted(SAMPLE_ROOT.glob("*.xlsx"))
    ]


def _document(documents: list[dict[str, Any]], prefix: str) -> dict[str, Any]:
    return next(document for document in documents if str(document["filename"]).startswith(prefix))


def _call_by_tool(plan: CashFlowIngestionPlan, tool: IngestionToolName) -> IngestionToolRequest:
    return next(call for call in plan.calls if call.tool == tool)


class FakeMappingLLM:
    def __init__(self, plan: CashFlowIngestionPlan) -> None:
        self.plan = plan
        self.payload: dict[str, Any] | None = None
        self.system_instruction = ""

    async def generate_text(self, *, prompt: str, system_instruction: str) -> str:
        raise AssertionError("Cash-flow mapping must use structured generation")

    async def generate_structured(
        self,
        *,
        prompt: str,
        system_instruction: str,
        response_model: type[Any],
    ) -> Any:
        assert response_model is CashFlowIngestionPlan
        self.payload = json.loads(prompt)
        self.system_instruction = system_instruction
        return self.plan


def test_profiler_and_heuristic_plan_discover_sample_tables() -> None:
    documents = _sample_documents()

    profiles, warnings = profile_cash_flow_workbooks(documents)
    plan = build_heuristic_plan(profiles)

    assert warnings == []
    assert profiles
    assert all(len(profile.sampled_rows) <= MAX_PROFILE_ROWS for profile in profiles)
    assert all(len(row.values) <= MAX_PROFILE_COLUMNS for profile in profiles for row in profile.sampled_rows)

    cashbook = _call_by_tool(plan, IngestionToolName.NORMALIZE_CASHBOOK)
    assert cashbook.sheet == "Sổ thu chi"
    assert cashbook.header_row == 4
    assert cashbook.columns["date"] == 1
    assert cashbook.columns["inflow"] == 7
    assert cashbook.columns["outflow"] == 8

    sales = _call_by_tool(plan, IngestionToolName.SUMMARIZE_SALES)
    assert sales.sheet == "Giao dịch"
    assert sales.header_row == 4
    assert "order_id" not in sales.columns

    purchases = _call_by_tool(plan, IngestionToolName.SUMMARIZE_PURCHASES)
    assert purchases.sheet == "Mua hàng chi phí"
    assert purchases.header_row == 4


@pytest.mark.asyncio
async def test_ai_plan_selects_and_executes_deterministic_tool_call() -> None:
    documents = _sample_documents()
    sales_document = _document(documents, "03_")
    plan = CashFlowIngestionPlan(
        calls=[
            IngestionToolRequest(
                tool=IngestionToolName.SUMMARIZE_SALES,
                document_id=str(sales_document["id"]),
                sheet="Giao dịch",
                header_row=4,
                columns={
                    "date": 1,
                    "quantity": 6,
                    "net_amount": 10,
                    "channel": 11,
                    "payment_method": 12,
                },
                notes="AI only maps columns; the tool performs all calculations.",
            )
        ]
    )
    llm = FakeMappingLLM(plan)

    result = await CashFlowIngestionAgent(llm).ingest([sales_document], use_ai=True)

    assert result.plan_source == "ai"
    assert llm.payload is not None
    assert llm.payload["sheet_profiles"]
    assert {tool["name"] for tool in llm.payload["tool_catalog"]} >= {
        "normalize_cashbook",
        "summarize_sales",
    }
    assert "không thực hiện phép tính" in llm.system_instruction
    assert [call.name for call in result.tool_calls] == ["cash_flow_summarize_sales"]
    sales = result.supporting_metrics["sales"][0]
    assert sales["net_sales"] == Decimal("671303450")
    assert sales["quantity"] == Decimal("14854")


@pytest.mark.asyncio
async def test_invalid_ai_mappings_are_rejected_without_guessing() -> None:
    documents = _sample_documents()
    cashbook_document = _document(documents, "05_")
    plan = CashFlowIngestionPlan(
        calls=[
            IngestionToolRequest(
                tool=IngestionToolName.NORMALIZE_CASHBOOK,
                document_id=str(cashbook_document["id"]),
                sheet="Sheet do AI bịa",
                header_row=4,
                columns={"date": 1, "inflow": 7, "outflow": 8},
            ),
            IngestionToolRequest(
                tool=IngestionToolName.NORMALIZE_CASHBOOK,
                document_id=str(cashbook_document["id"]),
                sheet="Sổ thu chi",
                header_row=4,
                columns={"date": 1, "inflow": 7},
            ),
        ]
    )

    result = await CashFlowIngestionAgent(FakeMappingLLM(plan)).ingest(
        [cashbook_document],
        use_ai=True,
    )

    assert result.dataset is None
    assert result.tool_calls == []
    assert any("Rejected mapping to unavailable sheet" in warning for warning in result.warnings)
    assert any("missing column mappings: outflow" in warning for warning in result.warnings)


@pytest.mark.asyncio
async def test_sample_folder_end_to_end_reconciles_and_builds_support_metrics() -> None:
    result = await CashFlowIngestionAgent().ingest(_sample_documents(), use_ai=False)

    assert result.plan_source == "heuristic"
    assert result.dataset is not None
    assert result.dataset.opening_cash == Decimal("380000000")
    assert result.dataset.reported_ending_cash == Decimal("439372410")
    assert len(result.dataset.transactions) == 260

    sales = result.supporting_metrics["sales"][0]
    assert sales["net_sales"] == Decimal("671303450")
    assert sales["quantity"] == Decimal("14854")
    assert sales["row_count"] == 910
    assert sales["order_count"] is None
    assert sales["average_order_value"] is None
    assert any("Average order value was not calculated" in warning for warning in result.warnings)

    purchases = result.supporting_metrics["purchases"][0]
    assert purchases["total_purchases_and_expenses"] == Decimal("761931040")
    assert purchases["row_count"] == 77
    assert purchases["by_period"]
    assert purchases["by_category"]
    assert purchases["by_supplier"]

    proposals = {proposal.field: proposal for proposal in result.proposals}
    assert proposals["current_cash"].value == Decimal("439372410")
    assert proposals["cash_flow_dataset"].status == "proposed"
    assert proposals["cash_flow_dataset"].sources


@pytest.mark.asyncio
async def test_analyzer_uses_tools_for_break_even_working_capital_and_best_case() -> None:
    facts = {
        "fixed_monthly_costs": 120_000_000,
        "variable_cost_ratio": "0.40",
        "accounts_receivable": 30_000_000,
        "accounts_payable": 20_000_000,
        "inventory": 40_000_000,
        "working_capital_period_revenue": 300_000_000,
        "working_capital_period_cogs": 180_000_000,
        "working_capital_period_days": 90,
        "minimum_cash_buffer": 100_000_000,
        "scenario_months": 2,
        "best_inflow_change": "0.20",
        "best_outflow_change": "-0.10",
    }

    report = await CashFlowAnalyzer().analyze(
        facts,
        _sample_documents(),
        {
            "use_gemini": False,
            "use_cash_flow_mapping_ai": False,
        },
    )

    break_even = report.details["break_even"]
    assert break_even["available"] is True
    assert break_even["contribution_margin_ratio"] == Decimal("0.60")
    assert break_even["break_even_revenue"] == Decimal("200000000")

    working_capital = report.details["working_capital"]
    assert working_capital["available"] is True
    assert working_capital["net_working_capital"] == Decimal("50000000")
    assert working_capital["dso_days"] == Decimal("9")
    assert working_capital["dpo_days"].quantize(Decimal("0.0001")) == Decimal("10.0000")
    assert working_capital["inventory_days"] == Decimal("20")
    assert working_capital["cash_conversion_cycle_days"].quantize(Decimal("0.0001")) == Decimal("19.0000")

    scenarios = report.details["scenarios"]
    assert set(scenarios) == {"base", "best", "downside", "severe"}
    assert scenarios["best"]["assumptions"] == {
        "operating_inflow_change": Decimal("0.20"),
        "operating_outflow_change": Decimal("-0.10"),
    }
    assert len(scenarios["best"]["monthly_projection"]) == 2

    tool_names = {call.name for call in report.tool_calls}
    assert {
        "break_even_calculator",
        "working_capital_calculator",
        "cash_scenario_simulator",
    } <= tool_names


def test_manual_periods_preserve_reconciliation_fields() -> None:
    dataset = normalize_cash_flow_input(
        {
            "currency": "VND",
            "cash_as_of": "2026-02-28",
            "opening_cash": 380_000_000,
            "reported_ending_cash": 439_372_410,
            "current_cash": 450_000_000,
            "financial_periods": [
                {"period": "2026-01", "inflow": 100_000_000, "outflow": 80_000_000},
                {"period": "2026-02", "inflow": 90_000_000, "outflow": 50_627_590},
            ],
        }
    )

    assert dataset is not None
    assert dataset.opening_cash == Decimal("380000000")
    assert dataset.reported_ending_cash == Decimal("439372410")
    assert dataset.cash_as_of.isoformat() == "2026-02-28"
