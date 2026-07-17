import json
from typing import Any

from pydantic import BaseModel, Field

from app.llm.gemini import GeminiNotConfiguredError, get_llm_client
from app.modules.registry import get_analyzer
from app.schemas.common import AnalysisModule, ModuleReport


class AnalysisNarrative(BaseModel):
    summary: str
    risks: list[str] = Field(default_factory=list)
    recommended_questions: list[str] = Field(default_factory=list)


async def run_analysis(
    *,
    module: AnalysisModule,
    startup_facts: dict[str, Any],
    documents: list[dict[str, Any]],
    options: dict[str, Any],
) -> ModuleReport:
    report = await get_analyzer(module).analyze(startup_facts, documents, options)
    if not options.get("use_gemini", True):
        return report

    context = "\n\n".join(f"Tài liệu: {doc['filename']}\n{doc.get('text', '')[:6000]}" for doc in documents[:5])
    prompt = (
        "Hãy tổng hợp phần diễn giải cho báo cáo phân tích startup bên dưới. "
        "Không tự tính lại điểm, không thay đổi output của tool, không tạo dữ kiện. "
        "Nếu thiếu bằng chứng, hãy nêu rõ.\n\n"
        f"MODULE REPORT:\n{json.dumps(report.model_dump(mode='json'), ensure_ascii=False)}\n\n"
        f"STARTUP DOCUMENTS:\n{context}"
    )
    try:
        narrative = await get_llm_client().generate_structured(
            prompt=prompt,
            system_instruction=(
                "Bạn là trợ lý thẩm định startup. Chỉ diễn giải evidence và kết quả tool được cung cấp. "
                "Không thực hiện phép tính và không đưa ra quyết định đầu tư cuối cùng."
            ),
            response_model=AnalysisNarrative,
        )
    except GeminiNotConfiguredError:
        return report
    report.summary = narrative.summary
    report.risks = list(dict.fromkeys([*report.risks, *narrative.risks]))
    report.recommended_questions = list(
        dict.fromkeys([*report.recommended_questions, *narrative.recommended_questions])
    )
    report.details["llm"] = {"provider": "gemini", "model": get_llm_client().model}
    return report
