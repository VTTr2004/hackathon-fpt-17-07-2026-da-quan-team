from decimal import Decimal, InvalidOperation
from typing import Any

from app.schemas.common import AnalysisModule, AnalysisStatus, Finding, ModuleReport, ToolCall

from .classification import classify_transactions
from .extractor import extract_cash_flow_documents
from .matching_signals import build_matching_signals
from .normalizer import normalize_cash_flow_input
from .reconciliation import reconcile_balance, remove_duplicates
from .scenarios import run_scenarios
from .scoring import score_cash_flow
from .tools.calculators import aggregate_cash_flow_by_period, calculate_burn_metrics


def _calculate_break_even(startup_facts: dict[str, Any]) -> dict[str, Any]:
    fixed_costs = startup_facts.get("fixed_monthly_costs")
    variable_cost_ratio = startup_facts.get("variable_cost_ratio")
    if fixed_costs is None or variable_cost_ratio is None:
        return {"available": False, "reason": "Missing fixed costs or variable cost ratio."}

    try:
        fixed_costs_decimal = Decimal(str(fixed_costs))
        ratio_decimal = Decimal(str(variable_cost_ratio))
        if not fixed_costs_decimal.is_finite() or fixed_costs_decimal < 0:
            return {"available": False, "reason": "Fixed monthly costs must be a non-negative number."}
        if not ratio_decimal.is_finite() or not Decimal(0) <= ratio_decimal < Decimal(1):
            return {"available": False, "reason": "Variable-cost ratio must be between 0 and 1."}
        break_even_revenue = fixed_costs_decimal / (Decimal(1) - ratio_decimal)
    except (InvalidOperation, TypeError, ValueError):
        return {"available": False, "reason": "Fixed costs and variable-cost ratio must be numeric."}

    return {
        "available": True,
        "fixed_monthly_costs": float(fixed_costs_decimal),
        "variable_cost_ratio": float(ratio_decimal),
        "break_even_revenue": float(break_even_revenue),
    }


class CashFlowAnalyzer:
    async def analyze(
        self, startup_facts: dict[str, Any], documents: list[dict[str, Any]], options: dict[str, Any]
    ) -> ModuleReport:
        extracted, evidence, extraction_warnings = extract_cash_flow_documents(documents)
        dataset = normalize_cash_flow_input(startup_facts, extracted)
        if dataset is None:
            return ModuleReport(
                module=AnalysisModule.CASH_FLOW,
                version="1.0.0",
                status=AnalysisStatus.INSUFFICIENT_DATA,
                score=None,
                summary="Chưa đủ dữ liệu dòng tiền để phân tích.",
                missing_data=["cash_flow_dataset hoặc current_cash và financial_periods"],
                recommended_questions=["Vui lòng bổ sung số dư tiền mặt và ít nhất hai kỳ dòng tiền."],
            )

        dataset.transactions = classify_transactions(dataset.transactions)
        dataset.transactions, duplicate_warnings = remove_duplicates(dataset.transactions)
        reconciliation = reconcile_balance(dataset, Decimal(str(options.get("reconciliation_tolerance", 1000))))
        periods = aggregate_cash_flow_by_period(dataset)
        available_cash = (
            dataset.reported_ending_cash
            if dataset.reported_ending_cash is not None
            else reconciliation["expected_ending_cash"]
        )
        if available_cash is None:
            return ModuleReport(
                module=AnalysisModule.CASH_FLOW,
                version="1.0.0",
                status=AnalysisStatus.INSUFFICIENT_DATA,
                score=None,
                summary="Chưa có số dư tiền mặt để tính runway và stress scenario.",
                missing_data=["current_cash hoặc reported_ending_cash"],
                recommended_questions=[
                    "Vui lòng bổ sung số dư tiền mặt hiện tại hoặc số dư cuối kỳ của sổ thu chi."
                ],
                evidence=evidence,
                details={
                    "reconciliation": reconciliation,
                    "warnings": [*dataset.warnings, *extraction_warnings, *duplicate_warnings],
                },
            )

        metrics = calculate_burn_metrics(periods, available_cash)
        scenarios = run_scenarios(periods, available_cash, options, startup_facts) if periods else {}
        score_data = score_cash_flow(metrics, reconciliation, dataset.source_type)
        matching = build_matching_signals(metrics, scenarios, score_data) if scenarios else {}
        unclassified = sum(
            (item.amount for item in dataset.transactions if item.activity.value == "unclassified"),
            Decimal(0),
        )

        risks: list[str] = []
        if reconciliation["status"] == "critical_mismatch":
            risks.append("HIGH — Dữ liệu dòng tiền không đối soát.")
        if (metrics.get("net_burn") or Decimal(0)) > 0:
            risks.append("MEDIUM — Dòng tiền hoạt động đang âm.")
        severe_runway = scenarios.get("severe", {}).get("runway_months")
        if severe_runway is not None and severe_runway < 6:
            risks.append("HIGH — Stress runway dưới 6 tháng.")

        status = (
            AnalysisStatus.PARTIAL
            if dataset.source_type == "legacy"
            or reconciliation["status"] == "critical_mismatch"
            or len(periods) < 2
            or unclassified
            else AnalysisStatus.COMPLETED
        )
        calls = [
            ToolCall(
                name="cash_flow_normalizer",
                version="1.0.0",
                input={},
                output={"source_type": dataset.source_type},
                warnings=dataset.warnings,
            ),
            ToolCall(
                name="cash_reconciliation",
                version="1.0.0",
                input={},
                output=reconciliation,
                warnings=duplicate_warnings,
            ),
            ToolCall(name="cash_metrics_calculator", version="1.0.0", input={}, output=metrics),
            ToolCall(name="cash_scenario_simulator", version="1.0.0", input={}, output=scenarios),
            ToolCall(name="cash_flow_scoring", version="1.0.0", input={}, output=score_data),
        ]
        if evidence:
            calls.insert(
                0,
                ToolCall(
                    name="cash_flow_extractor",
                    version="1.0.0",
                    input={"documents": len(documents)},
                    output={"transactions": len(dataset.transactions)},
                ),
            )

        cash_flow_label = {
            "burning": "âm",
            "generating": "dương",
            "break_even": "hòa vốn",
            "insufficient_data": "chưa đủ dữ liệu",
        }.get(metrics.get("cash_flow_state"), "chưa đủ dữ liệu")
        base_runway = metrics.get("base_runway_months")
        runway_text = "không áp dụng" if base_runway is None else f"{base_runway} tháng"

        return ModuleReport(
            module=AnalysisModule.CASH_FLOW,
            version="1.0.0",
            status=status,
            score=score_data["total_score"],
            summary=f"Dòng tiền hoạt động {cash_flow_label}; runway cơ sở {runway_text}.",
            findings=[
                Finding(
                    title="Operating cash flow",
                    detail=f"Net burn trung bình: {metrics.get('net_burn')} {dataset.currency}/tháng.",
                    confidence="high",
                ),
                Finding(title="Runway", detail=f"Runway cơ sở: {runway_text}.", confidence="high"),
                Finding(
                    title="Reconciliation",
                    detail=f"Trạng thái đối soát: {reconciliation['status']}.",
                    confidence="high",
                ),
            ],
            risks=risks,
            missing_data=[]
            if len(periods) >= 2
            else ["At least two operating periods are required for reliable trend analysis."],
            assumptions=dataset.assumptions,
            recommended_questions=[
                "Bổ sung working-capital balances để tính DSO/DPO và cash conversion cycle."
            ],
            evidence=evidence,
            methodology=[
                "Deterministic Decimal ledger calculation",
                "Financing inflows are excluded from operating burn",
            ],
            tool_calls=calls,
            details={
                "cash_flow": {"currency": dataset.currency, "source_type": dataset.source_type},
                "metrics": metrics,
                "periods": periods,
                "reconciliation": reconciliation,
                "scenarios": scenarios,
                "break_even": _calculate_break_even(startup_facts),
                "working_capital": {"available": False, "missing_data": ["working_capital"]},
                "matching_signals": matching,
                "warnings": [*dataset.warnings, *extraction_warnings, *duplicate_warnings],
            },
        )
