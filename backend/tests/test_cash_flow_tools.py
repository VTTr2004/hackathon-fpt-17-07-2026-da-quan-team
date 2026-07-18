from decimal import Decimal

from app.modules.cash_flow.autofill import CASH_FLOW_AUTOFILL_FIELDS
from app.modules.cash_flow.tools import (
    calculate_cash_metrics,
    calculate_derived_cash_inputs,
    simulate_cash_scenario,
)


def test_autofill_does_not_own_calculated_fields() -> None:
    assert {"monthly_expense", "variable_cost_ratio"}.isdisjoint(CASH_FLOW_AUTOFILL_FIELDS)


def test_derived_cash_inputs() -> None:
    result = calculate_derived_cash_inputs(
        monthly_revenue=200,
        fixed_monthly_costs=100,
        variable_costs=50,
    )

    assert result == {
        "monthly_expense": Decimal(150),
        "variable_cost_ratio": Decimal("0.25"),
    }


def test_cash_metrics() -> None:
    result = calculate_cash_metrics([{"period": "M1", "inflow": 100, "outflow": 150}], current_cash=500)
    assert result["net_burn"] == 50
    assert result["runway_periods"] == 10


def test_cash_scenario() -> None:
    result = simulate_cash_scenario(current_cash=500, monthly_inflow=100, monthly_outflow=150, months=2)
    assert result["ending_cash"] == 400
