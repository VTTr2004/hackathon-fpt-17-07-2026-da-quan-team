import json
from typing import Any

import pytest

from app.modules.business_model.facts import DOMAIN_FIELDS
from app.modules.business_model.orchestrator import DOMAIN_QUESTIONS, BusinessModelOrchestrator
from app.modules.business_model.schemas import (
    AgentAnswer,
    AuditedFinding,
    AuditResult,
    ComposedReport,
    ResearchBasis,
    StartupEvidence,
    SubagentResult,
)

SOURCE_BY_AGENT = {
    "customer_value": "SRC-CVP-PAYNE-2017",
    "retail_channels": "SRC-RETAIL-SORESCU-2011",
    "economics_market": "SRC-UNIT-NOONE-2020",
    "development_plan": "SRC-SCALE-WINTER-2001",
}


class FakeFlowLLM:
    def __init__(self) -> None:
        self.domain_payloads: dict[str, dict[str, Any]] = {}
        self.calls: list[str] = []

    async def generate_text(self, *, prompt: str, system_instruction: str) -> str:
        raise AssertionError("Flow must only use structured generation")

    async def generate_structured(
        self,
        *,
        prompt: str,
        system_instruction: str,
        response_model: type[Any],
    ) -> Any:
        payload = json.loads(prompt)
        if response_model is SubagentResult:
            agent_id = payload["agent_id"]
            self.calls.append(agent_id)
            self.domain_payloads[agent_id] = payload
            field = next(iter(payload["startup_facts"]), None)
            evidence = []
            if field is not None:
                evidence = [StartupEvidence(field=field, value_summary="Dữ kiện đầu vào")]
            if agent_id == "economics_market" and payload.get("tool_outputs"):
                evidence = [
                    StartupEvidence(field="tool_outputs", value_summary="Kết quả tool", verification="tool_output")
                ]
            question_id = DOMAIN_QUESTIONS[agent_id][0]["id"]
            return SubagentResult(
                agent_id="LLM cannot choose the effective agent id",
                answers=[
                    AgentAnswer(
                        question_id=question_id,
                        status="supported",
                        conclusion="Có cơ sở",
                        analysis="Đánh giá có giới hạn",
                        startup_evidence=evidence,
                        research_basis=[
                            ResearchBasis(
                                source_id=SOURCE_BY_AGENT[agent_id],
                                principle_used="Nguyên tắc",
                                application="Áp dụng",
                                limitation="Không chứng minh hiệu quả tài chính",
                            )
                        ],
                        confidence="high",
                    ),
                    AgentAnswer(
                        question_id="INJECTED-QUESTION",
                        status="supported",
                        conclusion="Phải bị loại",
                        analysis="Ngoài câu hỏi điều phối",
                    ),
                ],
            )
        if response_model is AuditResult:
            self.calls.append("auditor")
            findings = []
            for agent_id in SOURCE_BY_AGENT:
                findings.append(
                    AuditedFinding(
                        agent_id=agent_id,
                        question_id=DOMAIN_QUESTIONS[agent_id][0]["id"],
                        title=f"Finding {agent_id}",
                        detail="Đã audit",
                        source_ids=[SOURCE_BY_AGENT[agent_id]],
                        confidence="medium",
                    )
                )
            findings.append(
                AuditedFinding(
                    agent_id="customer_value",
                    question_id="CVP-01",
                    title="Nguồn bịa",
                    detail="Phải bị gate loại",
                    source_ids=["SRC-NOT-REAL"],
                )
            )
            return AuditResult(accepted_findings=findings)
        if response_model is ComposedReport:
            self.calls.append("composer")
            return ComposedReport(summary="Báo cáo đã ghép", findings=[], assumptions=["Giả định mẫu"])
        raise AssertionError(f"Unexpected response model: {response_model}")


@pytest.mark.asyncio
async def test_orchestrator_scopes_payloads_gates_outputs_and_composes() -> None:
    llm = FakeFlowLLM()
    facts = {field: f"value-{field}" for fields in DOMAIN_FIELDS.values() for field in fields}
    facts.update(
        {
            "current_cash": 1_000_000,
            "financial_periods": [{"period": "2026-01"}],
            "exact_location": "Không được lộ",
        }
    )
    tools = {"order_economics": {"contribution_per_order": 43_000}}

    flow = await BusinessModelOrchestrator(llm).run(business_facts=facts, tool_outputs=tools)

    assert set(llm.domain_payloads) == set(DOMAIN_FIELDS)
    for agent_id, payload in llm.domain_payloads.items():
        assert set(payload["startup_facts"]) == set(DOMAIN_FIELDS[agent_id])
        serialized = json.dumps(payload, ensure_ascii=False)
        assert "current_cash" not in serialized
        assert "financial_periods" not in serialized
        assert "exact_location" not in serialized
        assert payload["provenance"].startswith("Các startup_facts là user_provided")
        if agent_id == "economics_market":
            assert payload["tool_outputs"] == tools
        else:
            assert "tool_outputs" not in payload

    assert all(len(result.answers) == 1 for result in flow.subagent_results)
    assert len(flow.audit.accepted_findings) == 4
    assert flow.report.summary == "Báo cáo đã ghép"
    assert flow.report.findings == flow.audit.accepted_findings
    assert llm.calls.count("auditor") == 1
    assert llm.calls.count("composer") == 1


@pytest.mark.asyncio
async def test_domain_gate_downgrades_unsupported_answer_and_user_only_high_confidence() -> None:
    answer_without_research = AgentAnswer(
        question_id="CVP-01",
        status="supported",
        conclusion="Kết luận thiếu nghiên cứu",
        analysis="",
        startup_evidence=[StartupEvidence(field="problem", value_summary="Có vấn đề")],
        confidence="high",
    )
    gated = BusinessModelOrchestrator._gate_domain_result(
        SubagentResult(agent_id="customer_value", answers=[answer_without_research]),
        {"problem": "Cần nhanh"},
        {},
    )
    assert gated.answers[0].status == "insufficient_data"
    assert gated.answers[0].confidence == "low"

    supported = AgentAnswer(
        question_id="CVP-01",
        status="supported",
        conclusion="Có cơ sở giới hạn",
        analysis="",
        startup_evidence=[StartupEvidence(field="problem", value_summary="Có vấn đề")],
        research_basis=[
            ResearchBasis(
                source_id="SRC-CVP-PAYNE-2017",
                principle_used="CVP",
                application="Kiểm tra liên kết",
                limitation="Không chứng minh PMF",
            )
        ],
        confidence="high",
    )
    gated = BusinessModelOrchestrator._gate_domain_result(
        SubagentResult(agent_id="customer_value", answers=[supported]),
        {"problem": "Cần nhanh"},
        {},
    )
    assert gated.answers[0].status == "supported"
    assert gated.answers[0].confidence == "medium"
