from app.modules.business_model.tools import calculate_market_size, calculate_unit_economics


def test_market_size_calculator() -> None:
    result = calculate_market_size(
        total_customers=1000,
        annual_revenue_per_customer=100,
        reachable_share=0.5,
        target_share=0.1,
    )
    assert result == {"tam": 100000.0, "sam": 50000.0, "som": 5000.0}


def test_unit_economics_calculator() -> None:
    result = calculate_unit_economics(
        revenue_per_customer=100,
        variable_cost_per_customer=40,
        cac=120,
        churn_rate=0.1,
    )
    assert result["gross_margin"] == 0.6
    assert result["ltv_cac_ratio"] == 5.0
