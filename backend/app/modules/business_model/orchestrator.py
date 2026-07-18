import asyncio
import json
from typing import Any

from app.llm.base import LLMClient
from app.modules.business_model.facts import DOMAIN_FIELDS, select_domain_facts
from app.modules.business_model.prompts import load_prompt
from app.modules.business_model.schemas import (
    AgentAnswer,
    AgentFlowResult,
    AuditResult,
    ComposedReport,
    SubagentResult,
)
from app.modules.business_model.sources import SOURCES

DOMAIN_QUESTIONS: dict[str, list[dict[str, str]]] = {
    "customer_value": [
        {"id": "CVP-01", "question": "Nhu cầu, nhóm khách hàng và dịp mua có đủ cụ thể và liên kết không?"},
        {"id": "CVP-02", "question": "Giải pháp và sản phẩm chủ lực giải quyết nhu cầu đã nêu như thế nào?"},
        {"id": "CVP-03", "question": "Giá trị khác biệt có cụ thể, phù hợp khách hàng và có evidence không?"},
        {"id": "CVP-04", "question": "Traction hiện tại hỗ trợ hoặc chưa hỗ trợ giả định giá trị nào?"},
    ],
    "retail_channels": [
        {"id": "RET-01", "question": "Sản phẩm, nguồn doanh thu và pricing có logic thu giữ giá trị rõ không?"},
        {"id": "RET-02", "question": "Mỗi kênh bán có vai trò cụ thể hay mới chỉ là danh sách?"},
        {"id": "RET-03", "question": "Nhà cung cấp và đối tác có phù hợp sản phẩm/kênh không?"},
        {"id": "RET-04", "question": "Kế hoạch mở kênh có mục tiêu, giả định thử nghiệm và điều kiện cần không?"},
    ],
    "economics_market": [
        {"id": "ECO-01", "question": "Tool output cho biết gì và không cho phép kết luận gì về economics cấp đơn?"},
        {"id": "ECO-02", "question": "Dữ liệu hiện tại có đủ để tính TAM/SAM/SOM có kiểm chứng không?"},
        {"id": "ECO-03", "question": "Traction có kỳ đo và metric đủ rõ để làm market evidence không?"},
        {"id": "ECO-04", "question": "Thông tin đối thủ hỗ trợ đánh giá nào và còn thiếu evidence gì?"},
    ],
    "development_plan": [
        {"id": "DEV-01", "question": "Mục tiêu và milestone có baseline, target, deadline, metric không?"},
        {"id": "DEV-02", "question": "Kế hoạch sản phẩm, khách hàng và kênh có hypothesis/thử nghiệm đo được không?"},
        {"id": "DEV-03", "question": "Năng lực vận hành nào đã hoặc cần chuẩn hóa để nhân rộng?"},
        {"id": "DEV-04", "question": "Phụ thuộc nào thuộc Cash Flow/Surrounding Area và cần chuyển aggregator?"},
    ],
}

DOMAIN_SOURCE_IDS: dict[str, set[str]] = {
    "customer_value": {"SRC-CVP-PAYNE-2017", "SRC-BM-TEECE-2010", "SRC-MKT-NARVER-1990"},
    "retail_channels": {"SRC-RETAIL-SORESCU-2011", "SRC-BM-TEECE-2010", "SRC-CHANNEL-VERHOEF-2015"},
    "economics_market": {"SRC-UNIT-NOONE-2020", "SRC-BM-TEECE-2010", "SRC-MKT-NARVER-1990"},
    "development_plan": {"SRC-SCALE-WINTER-2001", "SRC-LEARN-SOSNA-2010"},
}


class BusinessModelOrchestrator:
    def __init__(self, llm_client: LLMClient) -> None:
        self.llm_client = llm_client

    async def run(
        self,
        *,
        business_facts: dict[str, Any],
        tool_outputs: dict[str, Any],
    ) -> AgentFlowResult:
        results = await asyncio.gather(
            *(self._run_domain_agent(agent_id, business_facts, tool_outputs) for agent_id in DOMAIN_QUESTIONS),
            return_exceptions=True,
        )
        subagent_results: list[SubagentResult] = []
        failures: list[str] = []
        for agent_id, result in zip(DOMAIN_QUESTIONS, results, strict=True):
            if isinstance(result, BaseException):
                failures.append(f"{agent_id}: {type(result).__name__}")
                subagent_results.append(SubagentResult(agent_id=agent_id))
            else:
                result.agent_id = agent_id
                subagent_results.append(self._gate_domain_result(result, business_facts, tool_outputs))

        audit = await self._run_auditor(subagent_results, failures)
        audit = self._gate_audit(audit, subagent_results)
        report = await self._run_composer(audit)
        report.findings = audit.accepted_findings
        return AgentFlowResult(subagent_results=subagent_results, audit=audit, report=report)

    async def _run_domain_agent(
        self,
        agent_id: str,
        business_facts: dict[str, Any],
        tool_outputs: dict[str, Any],
    ) -> SubagentResult:
        domain_facts = select_domain_facts(agent_id, business_facts)
        payload: dict[str, Any] = {
            "agent_id": agent_id,
            "questions": DOMAIN_QUESTIONS[agent_id],
            "startup_facts": domain_facts,
            "provenance": "Các startup_facts là user_provided và chưa được xác minh độc lập.",
        }
        if agent_id == "economics_market":
            payload["tool_outputs"] = tool_outputs
        return await self.llm_client.generate_structured(
            prompt=json.dumps(payload, ensure_ascii=False, default=str),
            system_instruction=load_prompt(agent_id),
            response_model=SubagentResult,
        )

    async def _run_auditor(self, results: list[SubagentResult], failures: list[str]) -> AuditResult:
        payload = {
            "subagent_results": [result.model_dump(mode="json") for result in results],
            "failed_subagents": failures,
            "source_catalog": {
                source_id: {"title": source.title, "doi": source.doi} for source_id, source in SOURCES.items()
            },
        }
        return await self.llm_client.generate_structured(
            prompt=json.dumps(payload, ensure_ascii=False),
            system_instruction=load_prompt("auditor"),
            response_model=AuditResult,
        )

    async def _run_composer(self, audit: AuditResult) -> ComposedReport:
        return await self.llm_client.generate_structured(
            prompt=json.dumps(audit.model_dump(mode="json"), ensure_ascii=False),
            system_instruction=load_prompt("composer"),
            response_model=ComposedReport,
        )

    @staticmethod
    def _gate_domain_result(
        result: SubagentResult,
        business_facts: dict[str, Any],
        tool_outputs: dict[str, Any],
    ) -> SubagentResult:
        agent_id = result.agent_id if result.agent_id in DOMAIN_FIELDS else ""
        if not agent_id:
            return SubagentResult(agent_id="invalid_agent")
        allowed_questions = {question["id"] for question in DOMAIN_QUESTIONS[agent_id]}
        allowed_fields = set(DOMAIN_FIELDS[agent_id])
        if agent_id == "economics_market" and tool_outputs:
            allowed_fields.add("tool_outputs")

        gated_answers: list[AgentAnswer] = []
        for answer in result.answers:
            if answer.question_id not in allowed_questions:
                continue
            answer.research_basis = [
                basis for basis in answer.research_basis if basis.source_id in DOMAIN_SOURCE_IDS[agent_id]
            ]
            answer.startup_evidence = [
                evidence
                for evidence in answer.startup_evidence
                if evidence.field in allowed_fields
                and (evidence.field == "tool_outputs" or evidence.field in business_facts)
            ]
            if answer.status in {"supported", "partial"} and (not answer.research_basis or not answer.startup_evidence):
                answer.status = "insufficient_data"
                answer.confidence = "low"
                answer.conclusion = "Chưa đủ bằng chứng hợp lệ để kết luận."
            if answer.confidence == "high" and all(
                evidence.verification == "user_provided" for evidence in answer.startup_evidence
            ):
                answer.confidence = "medium"
            gated_answers.append(answer)
        return SubagentResult(agent_id=agent_id, answers=gated_answers)

    @staticmethod
    def _gate_audit(audit: AuditResult, results: list[SubagentResult]) -> AuditResult:
        allowed: dict[tuple[str, str], set[str]] = {}
        for result in results:
            for answer in result.answers:
                if answer.status in {"supported", "partial"}:
                    allowed[(result.agent_id, answer.question_id)] = {
                        basis.source_id for basis in answer.research_basis
                    }
        audit.accepted_findings = [
            finding
            for finding in audit.accepted_findings
            if (finding.agent_id, finding.question_id) in allowed
            and bool(finding.source_ids)
            and set(finding.source_ids).issubset(allowed[(finding.agent_id, finding.question_id)])
            and set(finding.source_ids).issubset(SOURCES)
        ]
        return audit
