from types import SimpleNamespace

import pytest

from app.modules.profile_interview.schemas import LLMInterviewProposal, LLMInterviewResult
from app.modules.profile_interview.service import (
    analyze_answer,
    missing_required,
    next_required_question,
    normalize_interview_value,
)


def test_required_questions_follow_missing_groups() -> None:
    pending = ["problem", "solution", "target_customers", "monthly_revenue"]
    question = next_required_question(pending)
    assert question is not None
    assert "giải quyết vấn đề" in question
    assert "Doanh thu trung bình tháng" not in question


def test_existing_and_proposed_values_reduce_required_fields() -> None:
    values = {"name": "Mộc Coffee"}
    proposals = {"industry": "F&B"}
    pending = missing_required(values, proposals)
    assert "name" not in pending
    assert "industry" not in pending
    assert "problem" in pending


def test_interview_value_normalization_rejects_negative_finance() -> None:
    with pytest.raises(ValueError):
        normalize_interview_value("current_cash", -1)
    assert normalize_interview_value("target_customers", "Sinh viên; nhân viên văn phòng") == [
        "Sinh viên",
        "nhân viên văn phòng",
    ]


@pytest.mark.asyncio
async def test_answer_can_propose_required_and_optional_fields() -> None:
    answer = "Chúng tôi bán cà phê mang đi cho sinh viên qua cửa hàng và ứng dụng."
    llm = SimpleNamespace(
        generate_structured=lambda **_: _result(
            LLMInterviewProposal(
                field_key="target_customers",
                proposed_value=["Sinh viên"],
                supporting_quote="cho sinh viên",
                confidence=0.95,
                reasoning="Nhóm khách hàng được nói trực tiếp.",
            ),
            LLMInterviewProposal(
                field_key="sales_channels",
                proposed_value=["Cửa hàng", "Ứng dụng"],
                supporting_quote="qua cửa hàng và ứng dụng",
                confidence=0.9,
                reasoning="Các kênh bán được nói trực tiếp.",
            ),
        )
    )
    proposals = await analyze_answer(
        llm,
        answer=answer,
        current_question="Khách hàng và kênh bán là gì?",
        existing_values={},
    )
    assert {item.field_key for item in proposals} == {"target_customers", "sales_channels"}


async def _result(*proposals: LLMInterviewProposal) -> LLMInterviewResult:
    return LLMInterviewResult(proposals=list(proposals))
