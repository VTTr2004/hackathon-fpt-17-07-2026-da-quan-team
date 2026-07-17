from typing import Any

from app.modules.business_model.tools import score_business_model
from app.schemas.common import (
    AnalysisModule,
    AnalysisStatus,
    Finding,
    ModuleReport,
    ToolCall,
)


class BusinessModelAnalyzer:
    async def analyze(
        self,
        startup_facts: dict[str, Any],
        documents: list[dict[str, Any]],
        options: dict[str, Any],
    ) -> ModuleReport:
        result = score_business_model(startup_facts)
        missing = result["missing_fields"]
        status = AnalysisStatus.COMPLETED if not missing else AnalysisStatus.PARTIAL
        findings = [
            Finding(
                title="Mức độ hoàn thiện dữ liệu mô hình kinh doanh",
                detail=f"Đã có {len(result['present_fields'])}/7 nhóm dữ liệu cốt lõi.",
                confidence="high",
            )
        ]
        return ModuleReport(
            module=AnalysisModule.BUSINESS_MODEL,
            status=status,
            score=result["score"],
            summary=(
                "Đánh giá sơ bộ dựa trên mức độ hoàn thiện dữ liệu; "
                "cần Gemini và nguồn nghiên cứu để tổng hợp định tính chuyên sâu."
            ),
            findings=findings,
            missing_data=missing,
            recommended_questions=[f"Startup vui lòng bổ sung thông tin: {field}." for field in missing],
            methodology=["Business Model completeness rubric v0.1"],
            tool_calls=[
                ToolCall(
                    name="business_model_score_calculator",
                    version="0.1.0",
                    input={"facts": startup_facts},
                    output=result,
                )
            ],
            details={"documents_available": len(documents), "options": options},
        )
