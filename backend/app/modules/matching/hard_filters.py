from typing import Any


def _contains(value: str | None, options: list[str]) -> bool:
    if not options:
        return True
    if not value:
        return False
    normalized = (value or "").casefold()
    for item in options:
        option = item.casefold()
        if option in normalized or normalized in option:
            return True
        if option in {"f&b", "food & beverage", "food and beverage"} and any(
            token in normalized for token in ("food", "beverage", "coffee", "restaurant", "café", "cafe")
        ):
            return True
    return False


def hard_filter_reasons(features: dict[str, Any], preference: Any) -> list[str]:
    reasons: list[str] = []
    if preference.preferred_industries and not _contains(features.get("industry"), preference.preferred_industries):
        reasons.append("industry")
    if preference.preferred_stages and not _contains(features.get("stage"), preference.preferred_stages):
        reasons.append("stage")
    amount = features.get("fundraising_amount")
    if amount is not None:
        if preference.ticket_min is not None and amount < preference.ticket_min:
            reasons.append("ticket")
        if preference.ticket_max is not None and amount > preference.ticket_max:
            reasons.append("ticket")
    excluded_locations = (preference.exclusion_rules or {}).get("locations", [])
    if excluded_locations and _contains(features.get("location"), excluded_locations):
        reasons.append("location_excluded")
    return sorted(set(reasons))
