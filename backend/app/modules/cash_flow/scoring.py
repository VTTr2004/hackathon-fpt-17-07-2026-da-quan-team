from typing import Any

def score_cash_flow(metrics: dict[str, Any], reconciliation: dict[str, Any], dataset_source: str) -> dict[str, Any]:
    if reconciliation["status"] == "critical_mismatch":
        return {"total_score": None, "components": {}, "warnings": ["Score unavailable because data quality is insufficient."]}
    if metrics.get("cash_flow_state") in {"generating", "break_even"}:
        runway = 100.0
    elif metrics.get("base_runway_months") is not None:
        runway = min(float(metrics["base_runway_months"]) / 18 * 100, 100)
    else:
        return {"total_score": None, "components": {}, "warnings": ["Score unavailable because data quality is insufficient."]}
    quality = 70 if dataset_source == "legacy" else 100
    return {"total_score": round(runway * .7 + quality * .3, 2), "components": {"runway": {"score": round(runway, 2), "weight": .7}, "data_quality": {"score": quality, "weight": .3}}, "warnings": []}
