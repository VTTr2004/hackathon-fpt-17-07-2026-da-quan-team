from typing import Any

from app.llm.base import LLMClient
from app.llm.gemini import GeminiNotConfiguredError, get_llm_client
from app.modules.business_model.facts import missing_business_fields, select_business_facts
from app.modules.business_model.orchestrator import BusinessModelOrchestrator
from app.modules.business_model.schemas import AgentFlowResult
from app.modules.business_model.sources import evidence_for
from app.modules.business_model.tools import (
    calculate_market_size,
    calculate_order_economics,
    score_business_model,
)
from app.schemas.common import (
    AnalysisModule,
    AnalysisStatus,
    Evidence,
    Finding,
    ModuleReport,
    ToolCall,
)


class BusinessModelAnalyzer:
    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self._llm_client = llm_client

    async def analyze(
        self,
        startup_facts: dict[str, Any],
        documents: list[dict[str, Any]],
        options: dict[str, Any],
    ) -> ModuleReport:
        original_options = dict(options)
        business_facts = select_business_facts(startup_facts)
        tool_calls, tool_outputs = self._run_tools(business_facts, original_options)
        completeness = score_business_model(business_facts)
        report = self._deterministic_report(
            business_facts=business_facts,
            completeness=completeness,
            tool_calls=tool_calls,
            tool_outputs=tool_outputs,
            documents=documents,
            options=original_options,
        )

        use_agents = original_options.get("use_business_agents", original_options.get("use_gemini", True))
        if not use_agents:
            report.details["agent_flow"] = {"status": "disabled", "composed": False}
            return report

        # analysis_service gọi một narrative Gemini dùng chung sau analyzer. Business Model đã có
        # Auditor + Composer riêng nên tắt vòng thứ hai trên đúng object options của request.
        options["use_gemini"] = False
        try:
            llm_client = self._llm_client or get_llm_client()
            flow = await BusinessModelOrchestrator(llm_client).run(
                business_facts=business_facts,
                tool_outputs=tool_outputs,
            )
        except GeminiNotConfiguredError as exc:
            report.details["agent_flow"] = {
                "status": "deterministic_fallback",
                "composed": False,
                "reason": str(exc),
            }
            return report
        except Exception as exc:  # LLM/provider failure must not take down deterministic analysis.
            report.risks.append("Luồng AI không hoàn tất; báo cáo hiện chỉ dùng kiểm tra deterministic.")
            report.details["agent_flow"] = {
                "status": "deterministic_fallback",
                "composed": False,
                "reason": type(exc).__name__,
            }
            return report

        return self._apply_agent_flow(report, flow, business_facts)

    @staticmethod
    def _run_tools(
        business_facts: dict[str, Any],
        options: dict[str, Any],
    ) -> tuple[list[ToolCall], dict[str, Any]]:
        calls: list[ToolCall] = []
        outputs: dict[str, Any] = {}

        if "average_order_value" in business_facts and "variable_cost_per_order" in business_facts:
            tool_input = {
                "average_order_value": business_facts["average_order_value"],
                "variable_cost_per_order": business_facts["variable_cost_per_order"],
            }
            try:
                output = calculate_order_economics(**tool_input)
                outputs["order_economics"] = output
                calls.append(
                    ToolCall(
                        name="business_model_order_economics",
                        version="1.0.0",
                        input=tool_input,
                        output=output,
                        warnings=["Chỉ phản ánh contribution cấp đơn; không phải cash flow hay lợi nhuận ròng."],
                    )
                )
            except (TypeError, ValueError) as exc:
                outputs["order_economics_error"] = str(exc)

        market_input = options.get("market_size_inputs")
        required_market_fields = {
            "total_customers",
            "annual_revenue_per_customer",
            "reachable_share",
            "target_share",
        }
        if isinstance(market_input, dict) and required_market_fields.issubset(market_input):
            clean_input = {field: market_input[field] for field in required_market_fields}
            try:
                output = calculate_market_size(**clean_input)
                outputs["market_size"] = output
                calls.append(
                    ToolCall(
                        name="business_model_market_size",
                        version="1.0.0",
                        input=clean_input,
                        output=output,
                        warnings=["Kết quả phụ thuộc hoàn toàn vào các giả định đầu vào có cấu trúc."],
                    )
                )
            except (TypeError, ValueError) as exc:
                outputs["market_size_error"] = str(exc)
        elif business_facts.get("market_size"):
            outputs["market_size_status"] = (
                "Textarea market_size chỉ là mô tả; chưa đủ input có cấu trúc để tính TAM/SAM/SOM."
            )
        return calls, outputs

    @staticmethod
    def _deterministic_report(
        *,
        business_facts: dict[str, Any],
        completeness: dict[str, Any],
        tool_calls: list[ToolCall],
        tool_outputs: dict[str, Any],
        documents: list[dict[str, Any]],
        options: dict[str, Any],
    ) -> ModuleReport:
        missing = missing_business_fields(business_facts)
        if not completeness["present_fields"]:
            status = AnalysisStatus.INSUFFICIENT_DATA
            summary = "Chưa có dữ liệu Business Model để phân tích."
        else:
            status = AnalysisStatus.COMPLETED if not missing else AnalysisStatus.PARTIAL
            summary = (
                "Báo cáo deterministic hiện chỉ đo độ đầy đủ dữ liệu Business Model và các chỉ số "
                "cấp đơn hàng có input hợp lệ; chưa có đánh giá định tính từ các subagent."
            )
        findings = [
            Finding(
                title="Độ đầy đủ dữ liệu Business Model",
                detail=(
                    f"Có {len(completeness['present_fields'])}/{len(completeness['present_fields']) + len(missing)} "
                    "trường Business Model hiện có dữ liệu. Điểm này không đo chất lượng hay khả năng thành công."
                ),
                confidence="high",
            )
        ]
        return ModuleReport(
            module=AnalysisModule.BUSINESS_MODEL,
            version="1.0.0",
            status=status,
            score=completeness["score"],
            summary=summary,
            findings=findings,
            missing_data=missing,
            recommended_questions=[f"Vui lòng bổ sung dữ liệu Business Model: {field}." for field in missing],
            methodology=[
                "Business Model data-completeness rubric v1.0",
                "Deterministic order-level contribution analysis",
            ],
            tool_calls=tool_calls,
            details={
                "score_meaning": "data_completeness_only",
                "tool_outputs": tool_outputs,
                "documents_available_but_not_auto_cited": len(documents),
                "options": options,
                "scope": "business_model_only",
            },
        )

    @staticmethod
    def _apply_agent_flow(
        report: ModuleReport,
        flow: AgentFlowResult,
        business_facts: dict[str, Any],
    ) -> ModuleReport:
        answers = {
            (result.agent_id, answer.question_id): answer
            for result in flow.subagent_results
            for answer in result.answers
        }
        source_ids: set[str] = set()
        startup_evidence: dict[str, Evidence] = {}
        tool_evidence: Evidence | None = None
        findings: list[Finding] = []
        finding_research_map: dict[str, Any] = {}

        for index, audited in enumerate(flow.report.findings, start=1):
            answer = answers.get((audited.agent_id, audited.question_id))
            if answer is None:
                continue
            source_ids.update(audited.source_ids)
            fact_ids: list[str] = []
            for item in answer.startup_evidence:
                if item.field == "tool_outputs":
                    fact_ids.append("tool:business_model")
                    tool_evidence = Evidence(
                        evidence_id="tool:business_model",
                        source_type="deterministic_tool",
                        title="Business Model deterministic tool outputs",
                        reliability="high",
                        notes="Giá trị được lấy từ tool_calls của cùng báo cáo.",
                    )
                    continue
                evidence_id = f"fact:{item.field}"
                fact_ids.append(evidence_id)
                startup_evidence[evidence_id] = Evidence(
                    evidence_id=evidence_id,
                    source_type="user_input",
                    title=f"Dữ liệu hồ sơ: {item.field}",
                    quote=str(business_facts.get(item.field, ""))[:500],
                    reliability="medium",
                    notes="Dữ liệu do người dùng cung cấp; chưa được xác minh độc lập.",
                )
            finding_id = f"finding-{index}"
            findings.append(
                Finding(
                    title=audited.title,
                    detail=audited.detail,
                    evidence_ids=[*fact_ids, *audited.source_ids],
                    confidence=audited.confidence,
                )
            )
            finding_research_map[finding_id] = {
                "agent_id": audited.agent_id,
                "question_id": audited.question_id,
                "source_ids": audited.source_ids,
                "limitations": [basis.limitation for basis in answer.research_basis],
            }

        report.summary = flow.report.summary
        report.findings = findings or report.findings
        report.risks = list(dict.fromkeys(flow.report.risks))
        report.missing_data = list(dict.fromkeys([*report.missing_data, *flow.report.missing_data]))
        report.assumptions = list(dict.fromkeys(flow.report.assumptions))
        report.recommended_questions = list(
            dict.fromkeys([*report.recommended_questions, *flow.report.recommended_questions])
        )
        report.evidence = [
            *startup_evidence.values(),
            *([tool_evidence] if tool_evidence is not None else []),
            *evidence_for(source_ids),
        ]
        report.methodology = [
            "Four-domain Business Model agent analysis v1.0",
            "Citation and evidence audit",
            "Audited report composition",
            *report.methodology,
        ]
        report.details["finding_research_map"] = finding_research_map
        report.details["agent_flow"] = {
            "status": "completed",
            "composed": True,
            "subagents": [result.model_dump(mode="json") for result in flow.subagent_results],
            "audit": flow.audit.model_dump(mode="json"),
        }
        if any(not result.answers for result in flow.subagent_results) or not findings:
            if report.status != AnalysisStatus.INSUFFICIENT_DATA:
                report.status = AnalysisStatus.PARTIAL
            report.risks.append("Ít nhất một subagent chưa trả được kết quả đã qua kiểm duyệt.")
        return report
