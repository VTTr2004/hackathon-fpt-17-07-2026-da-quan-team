from typing import Any


def calculate_market_size(
    *, total_customers: float, annual_revenue_per_customer: float, reachable_share: float, target_share: float
) -> dict[str, float]:
    if total_customers < 0 or annual_revenue_per_customer < 0:
        raise ValueError("Market size inputs must be non-negative")
    if not 0 <= reachable_share <= 1 or not 0 <= target_share <= 1:
        raise ValueError("Shares must be between 0 and 1")
    tam = total_customers * annual_revenue_per_customer
    sam = tam * reachable_share
    som = sam * target_share
    return {"tam": round(tam, 2), "sam": round(sam, 2), "som": round(som, 2)}


def calculate_unit_economics(
    *, revenue_per_customer: float, variable_cost_per_customer: float, cac: float, churn_rate: float
) -> dict[str, float | None]:
    if min(revenue_per_customer, variable_cost_per_customer, cac, churn_rate) < 0:
        raise ValueError("Unit economics inputs must be non-negative")
    gross_profit = revenue_per_customer - variable_cost_per_customer
    ltv = gross_profit / churn_rate if churn_rate > 0 else None
    return {
        "gross_profit_per_customer": round(gross_profit, 2),
        "gross_margin": round(gross_profit / revenue_per_customer, 4) if revenue_per_customer else None,
        "ltv": round(ltv, 2) if ltv is not None else None,
        "ltv_cac_ratio": round(ltv / cac, 2) if ltv is not None and cac > 0 else None,
        "cac_payback_periods": round(cac / gross_profit, 2) if gross_profit > 0 else None,
    }


def score_business_model(facts: dict[str, Any]) -> dict[str, Any]:
    fields = [
        "problem",
        "solution",
        "target_customers",
        "revenue_model",
        "traction",
        "competitors",
        "market_size",
    ]
    present = [field for field in fields if facts.get(field)]
    missing = [field for field in fields if field not in present]
    score = round(len(present) / len(fields) * 100, 2)
    return {"score": score, "present_fields": present, "missing_fields": missing}
