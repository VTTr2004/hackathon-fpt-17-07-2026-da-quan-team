import json
import re
from datetime import date
from typing import Any

from app.llm.base import LLMClient

from .registry import INTERVIEW_FIELDS, REQUIRED_INTERVIEW_KEYS, has_value
from .schemas import LLMInterviewResult, ValidatedInterviewProposal

SYSTEM_INSTRUCTION = """Bạn là trợ lý phỏng vấn để hoàn thiện hồ sơ startup.
Chỉ trích xuất thông tin được người dùng nói trực tiếp trong latest_answer hoặc được suy ra chắc chắn
từ chính câu trả lời đó. Không dùng kiến thức bên ngoài, không bịa số, ngày, tiền hoặc tỷ lệ.
Existing_profile chỉ cung cấp ngữ cảnh và không phải nguồn cho đề xuất mới.
Mỗi đề xuất phải có supporting_quote là một đoạn nguyên văn liên tục trong latest_answer hỗ trợ cho giá trị.
Có thể đề xuất cả field bắt buộc, field quan trọng và field tùy chọn nếu câu trả lời thực sự đủ thông tin.
Không trả field đã có trong existing_profile. Không tính toán trường dẫn xuất.
Nếu chưa đủ dữ liệu thì không tạo proposal.
Trường list trả danh sách chuỗi; trường number/integer trả số; các trường khác trả chuỗi."""

QUESTION_GROUPS: tuple[tuple[tuple[str, ...], str], ...] = (
    (
        ("name", "industry", "stage", "primary_location"),
        "Bạn hãy cho biết tên startup, lĩnh vực hoạt động, giai đoạn hiện tại và địa điểm hoạt động chính?",
    ),
    (
        ("problem", "solution", "target_customers"),
        "Startup đang giải quyết vấn đề gì, cho nhóm khách hàng nào và giải pháp cụ thể là gì?",
    ),
    (
        ("core_products", "revenue_model"),
        "Sản phẩm hoặc dịch vụ chính của startup là gì và doanh nghiệp tạo doanh thu bằng cách nào?",
    ),
    (
        ("currency", "cash_as_of", "current_cash"),
        "Bạn đang dùng đơn vị tiền tệ nào, số dư tiền mặt hiện có là bao nhiêu và con số đó được chốt vào ngày nào?",
    ),
    (
        ("monthly_revenue", "fixed_monthly_costs", "variable_costs"),
        "Trung bình mỗi tháng startup có bao nhiêu doanh thu, chi phí cố định và chi phí biến đổi?",
    ),
)


def profile_values(startup: Any) -> dict[str, Any]:
    return {
        **(startup.facts or {}),
        "name": startup.name,
        "industry": startup.industry,
        "stage": startup.stage,
        "primary_location": startup.primary_location,
    }


def missing_required(values: dict[str, Any], proposals: dict[str, Any] | None = None) -> list[str]:
    proposals = proposals or {}
    return [
        key for key in REQUIRED_INTERVIEW_KEYS if not has_value(values.get(key)) and not has_value(proposals.get(key))
    ]


def next_required_question(pending_keys: list[str]) -> str | None:
    pending = set(pending_keys)
    if not pending:
        return None
    for keys, question in QUESTION_GROUPS:
        labels = [INTERVIEW_FIELDS[key].label for key in keys if key in pending]
        if labels:
            return f"{question}\n\nThông tin cần làm rõ: {', '.join(labels)}."
    key = pending_keys[0]
    return f"Bạn vui lòng cung cấp thông tin cho trường bắt buộc: {INTERVIEW_FIELDS[key].label}?"


def _quote_matches(quote: str, answer: str) -> bool:
    def normalize(value: str) -> str:
        return re.sub(r"\s+", " ", value).strip().casefold()

    clean = normalize(quote)
    return len(clean) >= 2 and clean in normalize(answer)


def normalize_interview_value(field_key: str, value: Any) -> Any:
    field = INTERVIEW_FIELDS[field_key]
    if field.value_type == "list":
        raw = value if isinstance(value, list) else re.split(r"[,;\n•]+", str(value))
        items = list(dict.fromkeys(str(item).strip() for item in raw if str(item).strip()))
        if not items:
            raise ValueError(f"{field.label} không được để trống")
        return items
    if field.value_type in {"number", "integer"}:
        if isinstance(value, bool):
            raise ValueError(f"{field.label} phải là số")
        number = float(str(value).replace(",", "").strip())
        if number < 0:
            raise ValueError(f"{field.label} không được âm")
        return int(number) if field.value_type == "integer" else number
    clean = str(value).strip()
    if not clean:
        raise ValueError(f"{field.label} không được để trống")
    if field.value_type == "select" and field.options:
        by_folded = {item.casefold(): item for item in field.options}
        if clean.casefold() not in by_folded:
            raise ValueError(f"{field.label} phải là một trong: {', '.join(field.options)}")
        return by_folded[clean.casefold()]
    if field.value_type == "date":
        try:
            return date.fromisoformat(clean).isoformat()
        except ValueError as exc:
            raise ValueError(f"{field.label} phải theo định dạng YYYY-MM-DD") from exc
    return clean


async def analyze_answer(
    llm_client: LLMClient,
    *,
    answer: str,
    current_question: str,
    existing_values: dict[str, Any],
) -> list[ValidatedInterviewProposal]:
    missing_fields = [
        {
            "field_key": key,
            "label": field.label,
            "description": field.description,
            "priority": field.priority,
            "value_type": field.value_type,
            "options": list(field.options),
        }
        for key, field in INTERVIEW_FIELDS.items()
        if not has_value(existing_values.get(key))
    ]
    result = await llm_client.generate_structured(
        prompt=json.dumps(
            {
                "current_question": current_question,
                "latest_answer": answer,
                "existing_profile": existing_values,
                "eligible_missing_fields": missing_fields,
            },
            ensure_ascii=False,
        ),
        system_instruction=SYSTEM_INSTRUCTION,
        response_model=LLMInterviewResult,
    )
    validated: list[ValidatedInterviewProposal] = []
    seen: set[str] = set()
    for proposal in result.proposals:
        key = proposal.field_key
        if key in seen or key not in INTERVIEW_FIELDS or has_value(existing_values.get(key)):
            continue
        seen.add(key)
        if proposal.proposed_value is None or not _quote_matches(proposal.supporting_quote, answer):
            continue
        try:
            value = normalize_interview_value(key, proposal.proposed_value)
        except (TypeError, ValueError):
            continue
        validated.append(
            ValidatedInterviewProposal(
                field_key=key,
                proposed_value=value,
                confidence=round(proposal.confidence, 2),
                source_quote=proposal.supporting_quote.strip(),
                reasoning=proposal.reasoning.strip(),
            )
        )
    return validated
