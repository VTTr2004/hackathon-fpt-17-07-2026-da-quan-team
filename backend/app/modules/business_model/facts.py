from typing import Any

DOMAIN_FIELDS: dict[str, tuple[str, ...]] = {
    "customer_value": (
        "problem",
        "solution",
        "target_customers",
        "core_products",
        "customer_purchase_occasions",
        "differentiation",
        "traction",
    ),
    "retail_channels": (
        "core_products",
        "revenue_model",
        "sales_channels",
        "pricing_model",
        "key_suppliers_partners",
        "differentiation",
        "channel_expansion_plan",
    ),
    "economics_market": (
        "average_order_value",
        "variable_cost_per_order",
        "market_size",
        "traction",
        "competitors",
    ),
    "development_plan": (
        "planning_horizon_months",
        "development_objectives",
        "product_plan",
        "customer_growth_plan",
        "channel_expansion_plan",
        "outlet_expansion_plan",
        "operating_capability_plan",
        "development_milestones",
        "development_dependencies",
    ),
}

BUSINESS_FIELDS = frozenset(field for fields in DOMAIN_FIELDS.values() for field in fields)
IDENTITY_FIELDS = frozenset({"name", "industry", "stage"})


def has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


def select_business_facts(startup_facts: dict[str, Any]) -> dict[str, Any]:
    allowed = BUSINESS_FIELDS | IDENTITY_FIELDS
    return {key: value for key, value in startup_facts.items() if key in allowed and has_value(value)}


def select_domain_facts(agent_id: str, business_facts: dict[str, Any]) -> dict[str, Any]:
    fields = DOMAIN_FIELDS[agent_id]
    return {key: business_facts[key] for key in fields if key in business_facts}


def missing_business_fields(business_facts: dict[str, Any]) -> list[str]:
    return sorted(field for field in BUSINESS_FIELDS if field not in business_facts)
