from typing import Any

EVIDENCE_FIELDS = (
    "industry",
    "subsector",
    "stage",
    "location",
    "fundraising_amount",
    "monthly_revenue",
    "revenue_growth",
    "runway_months",
    "gross_margin",
    "scalability",
)


def confidence_score(features: dict[str, Any]) -> tuple[float, list[str]]:
    missing = [key for key in EVIDENCE_FIELDS if features.get(key) in (None, "", [])]
    available = len(EVIDENCE_FIELDS) - len(missing)
    # Missing evidence lowers confidence but never turns business fit into zero.
    return round(max(25.0, available / len(EVIDENCE_FIELDS) * 100), 1), missing
