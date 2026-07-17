from app.modules.cash_flow.tools import calculate_cash_metrics, simulate_cash_scenario


def test_cash_metrics() -> None:
    result = calculate_cash_metrics([{"period": "M1", "inflow": 100, "outflow": 150}], current_cash=500)
    assert result["net_burn"] == 50
    assert result["runway_periods"] == 10


def test_cash_scenario() -> None:
    result = simulate_cash_scenario(current_cash=500, monthly_inflow=100, monthly_outflow=150, months=2)
    assert result["ending_cash"] == 400
