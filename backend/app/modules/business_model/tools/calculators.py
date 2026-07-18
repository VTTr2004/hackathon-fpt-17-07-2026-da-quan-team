import math
from typing import Any


def _finite_number(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number")
    return float(value)


def calculate_market_size(
    *, total_customers: float, annual_revenue_per_customer: float, reachable_share: float, target_share: float
) -> dict[str, float]:
    total_customers = _finite_number(total_customers, "total_customers")
    annual_revenue_per_customer = _finite_number(annual_revenue_per_customer, "annual_revenue_per_customer")
    reachable_share = _finite_number(reachable_share, "reachable_share")
    target_share = _finite_number(target_share, "target_share")
    if total_customers < 0 or annual_revenue_per_customer < 0:
        raise ValueError("Market size inputs must be non-negative")
    if not 0 <= reachable_share <= 1 or not 0 <= target_share <= 1:
        raise ValueError("Shares must be between 0 and 1")
    tam = total_customers * annual_revenue_per_customer
    sam = tam * reachable_share
    som = sam * target_share
    return {"tam": round(tam, 2), "sam": round(sam, 2), "som": round(som, 2)}


def calculate_order_economics(*, average_order_value: float, variable_cost_per_order: float) -> dict[str, float | None]:
    """Tính economics cấp đơn hàng cho F&B/bán lẻ; không suy ra cash flow hay lợi nhuận toàn doanh nghiệp."""
    revenue = _finite_number(average_order_value, "average_order_value")
    variable_cost = _finite_number(variable_cost_per_order, "variable_cost_per_order")
    if revenue < 0 or variable_cost < 0:
        raise ValueError("Order economics inputs must be non-negative")
    contribution = revenue - variable_cost
    return {
        "average_order_value": round(revenue, 2),
        "variable_cost_per_order": round(variable_cost, 2),
        "contribution_per_order": round(contribution, 2),
        "contribution_margin": round(contribution / revenue, 4) if revenue else None,
        "variable_cost_ratio": round(variable_cost / revenue, 4) if revenue else None,
    }


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
    from app.modules.business_model.facts import BUSINESS_FIELDS, has_value

    fields = sorted(BUSINESS_FIELDS)
    present = [field for field in fields if has_value(facts.get(field))]
    missing = [field for field in fields if field not in present]
    score = round(len(present) / len(fields) * 100, 2)
    return {"score": score, "present_fields": present, "missing_fields": missing}
