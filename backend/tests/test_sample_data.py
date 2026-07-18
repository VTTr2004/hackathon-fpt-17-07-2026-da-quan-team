from app.api.routes.startups import REQUIRED_FIELDS
from app.db.seed import SAMPLE_FACTS
from app.modules.business_model.facts import missing_business_fields
from app.modules.cash_flow.normalizer import normalize_cash_flow_input


def test_sample_facts_cover_business_and_cash_flow_modules() -> None:
    assert missing_business_fields(SAMPLE_FACTS) == []

    dataset = normalize_cash_flow_input(SAMPLE_FACTS)

    assert dataset is not None
    assert len(dataset.transactions) == 12
    assert dataset.currency == "VND"


def test_required_profile_contract_matches_double_star_ui_fields() -> None:
    assert [key for key, _label in REQUIRED_FIELDS] == [
        "name",
        "industry",
        "stage",
        "location",
        "problem",
        "solution",
        "target_customers",
        "core_products",
        "revenue_model",
        "currency",
        "cash_as_of",
        "current_cash",
        "monthly_revenue",
        "fixed_monthly_costs",
        "variable_costs",
    ]
