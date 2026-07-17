from typing import Any

from app.modules.surrounding_area.tools import score_location
from app.schemas.common import AnalysisModule, AnalysisStatus, Finding, ModuleReport, ToolCall


class SurroundingAreaAnalyzer:
    async def analyze(
        self,
        startup_facts: dict[str, Any],
        documents: list[dict[str, Any]],
        options: dict[str, Any],
    ) -> ModuleReport:
        location = startup_facts.get("location") or {}
        if location.get("lat") is None or location.get("lon") is None:
            return ModuleReport(
                module=AnalysisModule.SURROUNDING_AREA,
                status=AnalysisStatus.NOT_APPLICABLE,
                score=None,
                summary="Chưa có tọa độ đủ chính xác để phân tích khu vực.",
                missing_data=["location.lat", "location.lon"],
            )
        metrics = startup_facts.get("location_metrics") or {}
        if not metrics:
            return ModuleReport(
                module=AnalysisModule.SURROUNDING_AREA,
                status=AnalysisStatus.INSUFFICIENT_DATA,
                score=None,
                summary="Đã có tọa độ nhưng chưa có dữ liệu POI/khu vực để chấm điểm.",
                missing_data=["location_metrics"],
                details={"location": location},
            )
        weights = options.get("weights") or {
            "customer_density": 0.4,
            "accessibility": 0.3,
            "supporting_amenities": 0.2,
            "competition_balance": 0.1,
        }
        result = score_location(metrics, weights)
        return ModuleReport(
            module=AnalysisModule.SURROUNDING_AREA,
            status=AnalysisStatus.COMPLETED,
            score=result["score"],
            summary="Điểm vị trí được tính từ các chỉ số khu vực và trọng số đã công bố.",
            findings=[
                Finding(
                    title="Location score",
                    detail=f"Điểm tổng hợp khu vực: {result['score']}/100.",
                    confidence="medium",
                )
            ],
            methodology=["Weighted location score v0.1"],
            tool_calls=[
                ToolCall(
                    name="location_score_calculator",
                    version="0.1.0",
                    input={"metrics": metrics, "weights": weights},
                    output=result,
                )
            ],
            details={"location": location, "metrics": metrics},
        )
