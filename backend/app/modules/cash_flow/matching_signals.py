from typing import Any

def build_matching_signals(metrics: dict[str, Any], scenarios: dict[str, Any], score: dict[str, Any]) -> dict[str, Any]:
    stress = scenarios.get("severe", {}); runway = stress.get("runway_months")
    urgency = "critical" if runway is not None and runway < 3 else "high" if runway is not None and runway < 6 else "medium" if runway is not None and runway < 12 else "low"
    capital = ["equity"] if metrics.get("net_burn", 0) > 0 else []
    if stress.get("funding_gap", 0) > 0: capital.append("working_capital_loan")
    return {"financial_health_score": score.get("total_score"), "capital_urgency": urgency, "operating_burn_monthly": metrics.get("net_burn"), "base_runway_months": metrics.get("base_runway_months"), "stress_runway_months": runway, "funding_gap": stress.get("funding_gap"), "funding_needed_by": stress.get("funding_needed_by"), "recommended_capital_types": capital, "recommended_partner_types": ["investor", "financial_institution"] if capital else [], "partner_needs": ["Reduce operating costs"] if metrics.get("net_burn", 0) > 0 else [], "risk_flags": []}
