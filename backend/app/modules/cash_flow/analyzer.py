from typing import Any

from app.modules.cash_flow.tools import calculate_cash_metrics, simulate_cash_scenario
from app.schemas.common import AnalysisModule, AnalysisStatus, Finding, ModuleReport, ToolCall


class CashFlowAnalyzer:
    async def analyze(
        self,
        startup_facts: dict[str, Any],
        documents: list[dict[str, Any]],
        options: dict[str, Any],
    ) -> ModuleReport:
        periods = startup_facts.get("financial_periods") or []
        current_cash = startup_facts.get("current_cash")
        if not periods or current_cash is None:
            missing = []
            if not periods:
                missing.append("financial_periods")
            if current_cash is None:
                missing.append("current_cash")
            return ModuleReport(
                module=AnalysisModule.CASH_FLOW,
                status=AnalysisStatus.INSUFFICIENT_DATA,
                score=None,
                summary="Chưa đủ dữ liệu để chạy tool phân tích dòng tiền.",
                missing_data=missing,
                recommended_questions=[f"Vui lòng bổ sung {field}." for field in missing],
            )
        metrics = calculate_cash_metrics(periods, float(current_cash))
        scenario = simulate_cash_scenario(
            current_cash=float(current_cash),
            monthly_inflow=float(metrics["average_inflow"]),
            monthly_outflow=float(metrics["average_outflow"]) * 1.15,
            months=int(options.get("scenario_months", 12)),
        )
        runway = metrics["runway_periods"]
        score = 80.0 if runway is None else min(100.0, float(runway) / 18 * 100)
        return ModuleReport(
            module=AnalysisModule.CASH_FLOW,
            status=AnalysisStatus.COMPLETED,
            score=round(score, 2),
            summary="Các chỉ số được tính bằng tool deterministic từ dữ liệu dòng tiền đã cung cấp.",
            findings=[
                Finding(
                    title="Runway",
                    detail="Không ghi nhận net burn." if runway is None else f"Runway ước tính {runway} kỳ.",
                    confidence="high",
                )
            ],
            methodology=["Cash flow calculator v0.1", "15% outflow stress scenario"],
            tool_calls=[
                ToolCall(
                    name="cash_metrics_calculator",
                    version="0.1.0",
                    input={"periods": periods, "current_cash": current_cash},
                    output=metrics,
                ),
                ToolCall(
                    name="cash_scenario_simulator",
                    version="0.1.0",
                    input={"stress_outflow_multiplier": 1.15},
                    output=scenario,
                ),
            ],
            details={"metrics": metrics, "stress_scenario": scenario},
        )
