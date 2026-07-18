from typing import Any


def score_cash_flow(metrics: dict[str, Any], reconciliation: dict[str, Any], dataset_source: str) -> dict[str, Any]:
    if reconciliation["status"] == "critical_mismatch" or metrics.get("base_runway_months") is None:
        return {
            "total_score": None,
            "components": {},
            "warnings": ["Score unavailable because data quality is insufficient."],
        }
    runway = min(float(metrics["base_runway_months"]) / 18 * 100, 100)
    quality = 70 if dataset_source == "legacy" else 100
    return {
        "total_score": round(runway * 0.7 + quality * 0.3, 2),
        "components": {
            "runway": {"score": round(runway, 2), "weight": 0.7},
            "data_quality": {"score": quality, "weight": 0.3},
        },
        "warnings": [],
    }
