from dataclasses import dataclass
from typing import Any

from app.modules.matching.confidence import confidence_score
from app.modules.matching.explanations import explain
from app.modules.matching.feature_builder import build_features

MAXIMA = {
    "industry_fit": 15.0,
    "stage_fit": 10.0,
    "ticket_fit": 10.0,
    "location_fit": 5.0,
    "traction_fit": 15.0,
    "unit_economics_fit": 15.0,
    "scalability_fit": 10.0,
    "funding_timing_fit": 10.0,
    "capability_need_fit": 10.0,
}


@dataclass
class MatchResult:
    features: dict[str, Any]
    fit_score: float
    confidence_score: float
    score_breakdown: dict[str, float]
    matched_reasons: list[str]
    mismatched_reasons: list[str]
    missing_evidence: list[str]
    recommended_action: str


def _match(value: str | None, options: list[str]) -> bool:
    if not options:
        return True
    if not value:
        return False
    value_cf = (value or "").casefold()
    for item in options:
        option = item.casefold()
        if option in value_cf or value_cf in option:
            return True
        if option in {"f&b", "food & beverage", "food and beverage"} and any(
            token in value_cf for token in ("food", "beverage", "coffee", "restaurant", "café", "cafe")
        ):
            return True
    return False


def _ratio(value: float | None, minimum: float | None) -> float:
    if value is None:
        return 0.5
    if minimum is None or minimum <= 0:
        return 1.0
    return min(1.0, max(0.0, value / minimum))


def score_match(snapshot: dict[str, Any], preference: Any) -> MatchResult:
    f = build_features(snapshot)
    industry_ratio = float(_match(f["industry"], preference.preferred_industries))
    if preference.preferred_subsectors:
        subsector_ratio = float(_match(f["subsector"], preference.preferred_subsectors))
        industry_ratio = (industry_ratio + subsector_ratio) / 2
    traction_ratio = (
        _ratio(f["monthly_revenue"], preference.minimum_monthly_revenue)
        + _ratio(f["revenue_growth"], preference.minimum_revenue_growth)
    ) / 2
    amount = f["fundraising_amount"]
    ticket_fit = (
        0.5
        if amount is None
        else float(
            (preference.ticket_min is None or amount >= preference.ticket_min)
            and (preference.ticket_max is None or amount <= preference.ticket_max)
        )
    )
    runway = f["runway_months"]
    runway_fit = (
        0.5
        if runway is None
        else float(preference.maximum_runway_months is None or runway <= preference.maximum_runway_months)
    )
    needs = f["needed_capabilities"] if isinstance(f["needed_capabilities"], list) else [f["needed_capabilities"]]
    capabilities = preference.strategic_capabilities or []
    capability_fit = (
        0.5 if not needs or not capabilities else float(any(_match(str(need), capabilities) for need in needs))
    )
    breakdown = {
        "industry_fit": MAXIMA["industry_fit"] * industry_ratio,
        "stage_fit": MAXIMA["stage_fit"] * float(_match(f["stage"], preference.preferred_stages)),
        "ticket_fit": MAXIMA["ticket_fit"] * ticket_fit,
        "location_fit": MAXIMA["location_fit"] * float(_match(f["location"], preference.preferred_locations)),
        "traction_fit": MAXIMA["traction_fit"] * traction_ratio,
        "unit_economics_fit": MAXIMA["unit_economics_fit"] * (1.0 if f["gross_margin"] is not None else 0.5),
        "scalability_fit": MAXIMA["scalability_fit"] * (1.0 if f["scalability"] else 0.5),
        "funding_timing_fit": MAXIMA["funding_timing_fit"] * runway_fit,
        "capability_need_fit": MAXIMA["capability_need_fit"] * capability_fit,
    }
    breakdown = {key: round(value, 1) for key, value in breakdown.items()}
    total = round(min(100.0, max(0.0, sum(breakdown.values()))), 1)
    breakdown["total"] = total
    confidence, missing = confidence_score(f)
    matched, mismatched = explain(breakdown, MAXIMA)
    action = "request_access" if total >= 75 and confidence >= 50 else "review" if total >= 50 else "pass"
    return MatchResult(f, total, confidence, breakdown, matched, mismatched, missing, action)
