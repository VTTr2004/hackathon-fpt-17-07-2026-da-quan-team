from typing import Any


def number(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return None


def build_features(snapshot: dict[str, Any]) -> dict[str, Any]:
    facts = snapshot.get("facts") or {}
    cash = number(facts.get("current_cash"))
    monthly_expense = number(facts.get("monthly_expense"))
    runway = number(facts.get("runway_months"))
    if runway is None and cash is not None and monthly_expense and monthly_expense > 0:
        runway = cash / monthly_expense
    return {
        "name": snapshot.get("name"),
        "industry": snapshot.get("industry"),
        "subsector": facts.get("subsector") or facts.get("business_type"),
        "stage": snapshot.get("stage"),
        "location": snapshot.get("primary_location") or facts.get("exact_location"),
        "fundraising_amount": number(facts.get("fundraising_amount") or facts.get("funding_need_amount")),
        "fundraising_need": facts.get("fundraising_need") or facts.get("funding_need"),
        "monthly_revenue": number(facts.get("monthly_revenue")),
        "revenue_growth": number(facts.get("revenue_growth") or facts.get("monthly_revenue_growth")),
        "runway_months": runway,
        "gross_margin": number(facts.get("gross_margin")),
        "traction_summary": facts.get("traction_summary") or facts.get("traction"),
        "scalability": facts.get("scalability") or facts.get("expansion_plan"),
        "needed_capabilities": facts.get("needed_capabilities") or facts.get("support_needs") or [],
    }
