import math

import pytest

from app.modules.business_model.facts import (
    BUSINESS_FIELDS,
    DOMAIN_FIELDS,
    has_value,
    missing_business_fields,
    select_business_facts,
    select_domain_facts,
)
from app.modules.business_model.tools import (
    calculate_market_size,
    calculate_order_economics,
    score_business_model,
)


def test_business_fields_match_ui_contract_and_exclude_other_modules() -> None:
    assert len(BUSINESS_FIELDS) == 27
    assert set().union(*map(set, DOMAIN_FIELDS.values())) == set(BUSINESS_FIELDS)
    assert BUSINESS_FIELDS.isdisjoint(
        {"current_cash", "financial_periods", "exact_location", "area_claims", "primary_location"}
    )


def test_select_business_facts_whitelists_scope_and_keeps_zero() -> None:
    selected = select_business_facts(
        {
            "name": "Quán thử nghiệm",
            "industry": "F&B",
            "stage": "Seed",
            "problem": "  Cần bữa sáng nhanh  ",
            "average_order_value": 0,
            "target_customers": [],
            "solution": "   ",
            "current_cash": 500_000_000,
            "financial_periods": [{"period": "2026-01"}],
            "exact_location": "Quận 1",
            "area_claims": ["đông văn phòng"],
            "primary_location": "TP.HCM",
            "unknown": "không được truyền",
        }
    )

    assert selected == {
        "name": "Quán thử nghiệm",
        "industry": "F&B",
        "stage": "Seed",
        "problem": "  Cần bữa sáng nhanh  ",
        "average_order_value": 0,
    }
    assert has_value(0)
    assert has_value(False)  # bool is still a supplied value at the fact boundary.


def test_select_domain_facts_only_exposes_agent_owned_fields() -> None:
    facts = {field: f"value-{field}" for field in BUSINESS_FIELDS}
    facts["name"] = "Shared identity is not a domain claim"

    for agent_id, fields in DOMAIN_FIELDS.items():
        selected = select_domain_facts(agent_id, facts)
        assert set(selected) == set(fields)
        assert "name" not in selected


def test_missing_and_score_use_all_business_fields() -> None:
    facts = {"problem": "Nhu cầu", "average_order_value": 0}

    missing = missing_business_fields(select_business_facts(facts))
    score = score_business_model(facts)

    assert len(missing) == 25
    assert score["present_fields"] == ["average_order_value", "problem"]
    assert score["score"] == round(2 / 27 * 100, 2)


def test_retired_order_cost_is_legacy_optional_not_a_missing_ui_field() -> None:
    selected = select_business_facts({"variable_cost_per_order": 42_000})

    assert selected["variable_cost_per_order"] == 42_000
    assert "variable_cost_per_order" not in BUSINESS_FIELDS
    assert "variable_cost_per_order" not in missing_business_fields(selected)


def test_new_ui_business_fields_cross_the_module_boundary() -> None:
    facts = {
        "problem_owner": "Nhân viên văn phòng",
        "users_and_payers": "Người dùng cũng là người trả tiền",
        "acquisition_channels": ["Facebook"],
        "fundraising_need": "Vốn mở rộng vận hành",
    }

    assert select_business_facts(facts) == facts


def test_order_economics_for_positive_and_negative_contribution() -> None:
    positive = calculate_order_economics(average_order_value=85_000, variable_cost_per_order=42_000)
    negative = calculate_order_economics(average_order_value=40_000, variable_cost_per_order=50_000)

    assert positive == {
        "average_order_value": 85_000.0,
        "variable_cost_per_order": 42_000.0,
        "contribution_per_order": 43_000.0,
        "contribution_margin": 0.5059,
        "variable_cost_ratio": 0.4941,
    }
    assert negative["contribution_per_order"] == -10_000.0
    assert negative["contribution_margin"] == -0.25


def test_order_economics_zero_revenue_does_not_divide() -> None:
    result = calculate_order_economics(average_order_value=0, variable_cost_per_order=0)
    assert result["contribution_margin"] is None
    assert result["variable_cost_ratio"] is None


@pytest.mark.parametrize("bad_value", [-1, True, math.nan, math.inf, "85000"])
def test_order_economics_rejects_invalid_input(bad_value: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        calculate_order_economics(average_order_value=bad_value, variable_cost_per_order=1)  # type: ignore[arg-type]


def test_market_size_requires_structured_valid_numbers() -> None:
    assert calculate_market_size(
        total_customers=1_000,
        annual_revenue_per_customer=100,
        reachable_share=0.5,
        target_share=0.1,
    ) == {"tam": 100_000.0, "sam": 50_000.0, "som": 5_000.0}

    with pytest.raises(ValueError):
        calculate_market_size(
            total_customers=1_000,
            annual_revenue_per_customer=100,
            reachable_share=1.1,
            target_share=0.1,
        )
