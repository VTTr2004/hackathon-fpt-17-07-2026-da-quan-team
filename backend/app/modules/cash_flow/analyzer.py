from decimal import Decimal
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
        available_cash = dataset.reported_ending_cash or reconciliation["expected_ending_cash"]
        metrics = calculate_burn_metrics(periods, available_cash)
        scenarios = run_scenarios(periods, available_cash, options, startup_facts) if periods else {}
        score_data = score_cash_flow(metrics, reconciliation, dataset.source_type)
        matching = build_matching_signals(metrics, scenarios, score_data) if scenarios else {}
        unclassified = sum(
            (item.amount for item in dataset.transactions if item.activity.value == "unclassified"), Decimal(0)
        )
        risks = []
        if reconciliation["status"] == "critical_mismatch":
            risks.append("HIGH — Dữ liệu dòng tiền không đối soát.")
        if metrics.get("net_burn", Decimal(0)) > 0:
            risks.append("MEDIUM — Dòng tiền hoạt động đang âm.")
        if scenarios.get("severe", {}).get("runway_months") is not None and scenarios["severe"]["runway_months"] < 6:
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
        flow_label = "âm" if metrics.get("net_burn") else "tạo tiền"
        runway_label = metrics.get("base_runway_months") or "không áp dụng"
        summary = f"Dòng tiền hoạt động {flow_label}; runway cơ sở {runway_label} tháng."
        return ModuleReport(
            module=AnalysisModule.CASH_FLOW,
            version="1.0.0",
            status=status,
            score=score_data["total_score"],
            summary=summary,
            findings=[
                Finding(
                    title="Operating cash flow",
                    detail=f"Net burn trung bình: {metrics.get('net_burn')} {dataset.currency}/tháng.",
                    confidence="high",
                ),
                Finding(
                    title="Runway",
                    detail=f"Runway cơ sở: {metrics.get('base_runway_months')} tháng.",
                    confidence="high",
                ),
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
            recommended_questions=["Bổ sung working-capital balances để tính DSO/DPO và cash conversion cycle."],
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
                "break_even": {"available": False, "reason": "Missing fixed costs or variable cost ratio."},
                "working_capital": {"available": False, "missing_data": ["working_capital"]},
                "matching_signals": matching,
                "warnings": [*dataset.warnings, *extraction_warnings, *duplicate_warnings],
            },
        )
