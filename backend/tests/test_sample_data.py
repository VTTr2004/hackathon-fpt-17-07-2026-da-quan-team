import json
from pathlib import Path

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


def test_goc_ho_sample_data_matches_current_profile_and_cashflow_contract() -> None:
    sample_dir = Path(__file__).resolve().parents[2] / "sample-data" / "goc-ho-coffee"
    truth = json.loads((sample_dir / "ground_truth.json").read_text(encoding="utf-8"))
    profile = truth["profile"]
    cash_flow = truth["cash_flow"]

    startup_fields = {"name", "industry", "stage", "location"}
    fact_fields = {key for key, _label in REQUIRED_FIELDS} - startup_fields
    combined = {**profile, **cash_flow}
    assert all(combined.get(key) not in (None, "", []) for key in startup_fields | fact_fields)

    assert cash_flow["computed"]["monthly_expense"] == (
        cash_flow["fixed_monthly_costs"] + cash_flow["variable_costs"]
    )
    assert cash_flow["computed"]["variable_cost_ratio"] == (
        cash_flow["variable_costs"] / cash_flow["monthly_revenue"]
    )
    assert truth["reconciliation"]["ending_cash"] == cash_flow["current_cash"]
