from decimal import Decimal
from typing import Any

from app.llm.base import LLMClient
from app.llm.gemini import get_llm_client
from app.schemas.common import AnalysisModule, AnalysisStatus, Evidence, Finding, ModuleReport, ToolCall

from .classification import classify_transactions
from .extractor import extract_cash_flow_documents
from .ingestion_agent import CashFlowIngestionAgent
from .ingestion_schemas import CashFlowIngestionResult
from .matching_signals import build_matching_signals
from .normalizer import normalize_cash_flow_input
from .reconciliation import reconcile_balance, remove_duplicates
from .scenarios import run_scenarios
from .scoring import score_cash_flow
from .tools.calculators import (
    aggregate_cash_flow_by_period,
    calculate_break_even,
    calculate_burn_metrics,
    calculate_derived_cash_inputs,
    calculate_working_capital,
)


def _derived_inputs_tool(startup_facts: dict[str, Any]) -> tuple[dict[str, Any], ToolCall]:
    tool_input = {
        "monthly_revenue": startup_facts.get("monthly_revenue"),
        "fixed_monthly_costs": startup_facts.get("fixed_monthly_costs"),
        "variable_costs": startup_facts.get("variable_costs"),
    }
    if None in tool_input.values():
        output = {
            "available": False,
            "missing_data": [field for field, value in tool_input.items() if value is None],
        }
    else:
        try:
            output = {"available": True, **calculate_derived_cash_inputs(**tool_input)}
        except (TypeError, ValueError) as exc:
            output = {"available": False, "error": str(exc)}
    return output, ToolCall(
        name="cash_derived_inputs_calculator",
        version="1.0.0",
        input=tool_input,
        output=output,
    )


def _break_even_tool(startup_facts: dict[str, Any]) -> tuple[dict[str, Any], ToolCall]:
    tool_input = {
        "fixed_monthly_costs": startup_facts.get("fixed_monthly_costs"),
        "variable_cost_ratio": startup_facts.get("variable_cost_ratio"),
    }
    if None in tool_input.values():
        output = {
            "available": False,
            "missing_data": [field for field, value in tool_input.items() if value is None],
        }
    else:
        try:
            output = {"available": True, **calculate_break_even(**tool_input)}
        except (TypeError, ValueError) as exc:
            output = {"available": False, "error": str(exc)}
    return output, ToolCall(
        name="break_even_calculator",
        version="1.0.0",
        input=tool_input,
        output=output,
    )


def _working_capital_tool(startup_facts: dict[str, Any]) -> tuple[dict[str, Any], ToolCall]:
    tool_input = {
        "accounts_receivable": startup_facts.get("accounts_receivable"),
        "accounts_payable": startup_facts.get("accounts_payable"),
        "inventory": startup_facts.get("inventory"),
        "period_revenue": startup_facts.get("working_capital_period_revenue"),
        "period_cogs": startup_facts.get("working_capital_period_cogs"),
        "period_days": startup_facts.get("working_capital_period_days"),
    }
    try:
        output = calculate_working_capital(**tool_input)
    except (TypeError, ValueError) as exc:
        output = {"available": False, "error": str(exc)}
    return output, ToolCall(
        name="working_capital_calculator",
        version="1.0.0",
        input=tool_input,
        output=output,
    )


def _ingestion_details(ingestion: CashFlowIngestionResult | None) -> dict[str, Any]:
    if ingestion is None:
        return {"status": "not_run", "autofill_proposals": []}
    return {
        "status": "completed",
        "preview_id": ingestion.preview_id,
        "plan_source": ingestion.plan_source,
        "plan": ingestion.plan.model_dump(mode="json"),
        "supporting_metrics": ingestion.supporting_metrics,
        "autofill_proposals": [proposal.model_dump(mode="json") for proposal in ingestion.proposals],
        "warnings": ingestion.warnings,
    }


class CashFlowAnalyzer:
    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self._llm_client = llm_client

    async def analyze(
        self, startup_facts: dict[str, Any], documents: list[dict[str, Any]], options: dict[str, Any]
    ) -> ModuleReport:
        analysis_facts = dict(startup_facts)
        derived_inputs, derived_inputs_call = _derived_inputs_tool(analysis_facts)
        if derived_inputs.get("available"):
            analysis_facts.update(
                {
                    "monthly_expense": derived_inputs["monthly_expense"],
                    "variable_cost_ratio": derived_inputs["variable_cost_ratio"],
                }
            )
        ingestion: CashFlowIngestionResult | None = None
        if documents and options.get("use_cash_flow_ingestion_agent", True):
            llm_client = self._llm_client or get_llm_client()
            ingestion = await CashFlowIngestionAgent(llm_client).ingest(
                documents,
                use_ai=options.get("use_cash_flow_mapping_ai", options.get("use_gemini", True)),
            )
        if ingestion is not None and ingestion.dataset is not None:
            extracted = ingestion.dataset
            evidence = ingestion.evidence
            extraction_warnings = ingestion.warnings
        else:
            extracted, evidence, extraction_warnings = extract_cash_flow_documents(documents)
        dataset = normalize_cash_flow_input(analysis_facts, extracted)
        if dataset is None:
            return ModuleReport(
                module=AnalysisModule.CASH_FLOW,
                version="1.0.0",
                status=AnalysisStatus.INSUFFICIENT_DATA,
                score=None,
                summary="Chưa đủ dữ liệu dòng tiền để phân tích.",
                missing_data=[
                    "cash_flow_dataset, hoặc current_cash + cash_as_of + monthly_revenue + fixed_monthly_costs + "
                    "variable_costs"
                ],
                recommended_questions=[
                    "Vui lòng nhập tiền mặt hiện có, ngày chốt số dư, doanh thu, chi phí cố định và chi phí biến đổi; "
                    "hoặc tải dữ liệu dòng tiền theo kỳ."
                ],
                evidence=evidence,
                tool_calls=[*(ingestion.tool_calls if ingestion else []), derived_inputs_call],
                details={"ingestion": _ingestion_details(ingestion)},
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
                recommended_questions=["Vui lòng bổ sung số dư tiền mặt hiện tại hoặc số dư cuối kỳ của sổ thu chi."],
                evidence=evidence,
                details={
                    "reconciliation": reconciliation,
                    "warnings": [*dataset.warnings, *extraction_warnings, *duplicate_warnings],
                    "ingestion": _ingestion_details(ingestion),
                },
                tool_calls=[*(ingestion.tool_calls if ingestion else []), derived_inputs_call],
            )

        metrics = calculate_burn_metrics(periods, available_cash)
        scenarios = run_scenarios(periods, available_cash, options, analysis_facts) if periods else {}
        score_data = score_cash_flow(metrics, reconciliation, dataset.source_type)
        matching = build_matching_signals(metrics, scenarios, score_data) if scenarios else {}
        break_even, break_even_call = _break_even_tool(analysis_facts)
        working_capital, working_capital_call = _working_capital_tool(analysis_facts)
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
            *(ingestion.tool_calls if ingestion else []),
            derived_inputs_call,
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
            break_even_call,
            working_capital_call,
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
        calculation_evidence = [
            Evidence(
                evidence_id="calc:cash_metrics:v1",
                source_type="calculation",
                title="Cash metrics calculator v1.0.0",
                reliability="high",
                notes="Calculated deterministically from normalized operating cash-flow periods.",
            ),
            Evidence(
                evidence_id="calc:cash_reconciliation:v1",
                source_type="calculation",
                title="Cash reconciliation v1.0.0",
                reliability="high",
                notes="Opening cash plus inflows minus outflows compared with reported ending cash.",
            ),
            Evidence(
                evidence_id="calc:cash_scenarios:v1",
                source_type="calculation",
                title="Cash scenario simulator v1.0.0",
                reliability="high",
                notes="Base, best, downside and severe projections use explicit tool assumptions.",
            ),
        ]

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
                    evidence_ids=["calc:cash_metrics:v1"],
                    confidence="high",
                ),
                Finding(
                    title="Runway",
                    detail=f"Runway cơ sở: {runway_text}.",
                    evidence_ids=["calc:cash_metrics:v1", "calc:cash_scenarios:v1"],
                    confidence="high",
                ),
                Finding(
                    title="Reconciliation",
                    detail=f"Trạng thái đối soát: {reconciliation['status']}.",
                    evidence_ids=["calc:cash_reconciliation:v1"],
                    confidence="high",
                ),
            ],
            risks=risks,
            missing_data=[]
            if len(periods) >= 2
            else ["At least two operating periods are required for reliable trend analysis."],
            assumptions=dataset.assumptions,
            recommended_questions=["Bổ sung working-capital balances để tính DSO/DPO và cash conversion cycle."],
            evidence=[*evidence, *calculation_evidence],
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
                "break_even": break_even,
                "working_capital": working_capital,
                "matching_signals": matching,
                "warnings": [*dataset.warnings, *extraction_warnings, *duplicate_warnings],
                "ingestion": _ingestion_details(ingestion),
            },
        )
