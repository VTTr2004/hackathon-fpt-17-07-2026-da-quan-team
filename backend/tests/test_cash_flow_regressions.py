import asyncio
from decimal import Decimal

from app.modules.cash_flow.analyzer import CashFlowAnalyzer
from app.modules.cash_flow.classification import classify_transaction
from app.modules.cash_flow.normalizer import normalize_cash_flow_input
from app.modules.cash_flow.reconciliation import reconcile_balance, remove_duplicates
from app.modules.cash_flow.schemas import (
    CashActivity,
    CashDirection,
    CashFlowDataset,
    CashFlowPeriodSummary,
    CashFlowTransaction,
)
from app.modules.cash_flow.scoring import score_cash_flow
from app.modules.cash_flow.tools.calculators import calculate_burn_metrics


def test_required_ui_monthly_summary_normalizes_to_one_period() -> None:
    dataset = normalize_cash_flow_input(
        {
            "currency": "VND",
            "cash_as_of": "2026-07-19",
            "current_cash": 500_000_000,
            "monthly_revenue": 200_000_000,
            "fixed_monthly_costs": 100_000_000,
            "variable_costs": 150_000_000,
        }
    )

    assert dataset is not None
    assert dataset.currency == "VND"
    assert dataset.reported_ending_cash == Decimal(500_000_000)
    assert [(item.period, item.direction, item.amount) for item in dataset.transactions] == [
        ("2026-07", CashDirection.INFLOW, Decimal(200_000_000)),
        ("2026-07", CashDirection.OUTFLOW, Decimal(250_000_000)),
    ]
    assert any("one month of average revenue and expense" in warning for warning in dataset.warnings)


def test_required_ui_monthly_summary_rejects_invalid_cash_date() -> None:
    dataset = normalize_cash_flow_input(
        {
            "cash_as_of": "not-a-date",
            "current_cash": 500,
            "monthly_revenue": 100,
            "fixed_monthly_costs": 50,
            "variable_costs": 100,
        }
    )

    assert dataset is None


def test_analyzer_records_derived_inputs_tool_call() -> None:
    report = asyncio.run(
        CashFlowAnalyzer().analyze(
            {
                "currency": "VND",
                "cash_as_of": "2026-07-19",
                "current_cash": 500,
                "monthly_revenue": 200,
                "fixed_monthly_costs": 100,
                "variable_costs": 50,
            },
            [],
            {"use_gemini": False},
        )
    )

    call = next(item for item in report.tool_calls if item.name == "cash_derived_inputs_calculator")
    assert call.output["monthly_expense"] == Decimal(150)
    assert call.output["variable_cost_ratio"] == Decimal("0.25")


def test_reported_zero_cash_is_used_for_runway_and_scenarios() -> None:
    facts = {
        "cash_flow_dataset": {
            "opening_cash": "100",
            "reported_ending_cash": "0",
            "transactions": [
                {
                    "period": "2026-01",
                    "direction": "outflow",
                    "activity": "operating",
                    "amount": "10",
                }
            ],
        }
    }

    report = asyncio.run(CashFlowAnalyzer().analyze(facts, [], {}))

    assert report.details["metrics"]["base_runway_months"] == Decimal(0)
    assert report.details["scenarios"]["base"]["monthly_projection"][0]["starting_cash"] == Decimal(0)
    assert "runway cơ sở 0 tháng" in report.summary


def test_expected_cash_is_used_only_when_reported_cash_is_missing() -> None:
    facts = {
        "cash_flow_dataset": {
            "opening_cash": "100",
            "transactions": [
                {
                    "period": "2026-01",
                    "direction": "outflow",
                    "activity": "operating",
                    "amount": "10",
                }
            ],
        }
    }

    report = asyncio.run(CashFlowAnalyzer().analyze(facts, [], {}))

    assert report.details["reconciliation"]["expected_ending_cash"] == Decimal(90)
    assert report.details["metrics"]["base_runway_months"] == Decimal(9)


def test_similar_transactions_without_source_identity_are_preserved() -> None:
    transactions = [
        CashFlowTransaction(
            period="2026-01",
            date="2026-01-02",
            direction=CashDirection.OUTFLOW,
            activity=CashActivity.OPERATING,
            category="supplies",
            amount=Decimal(100),
        ),
        CashFlowTransaction(
            period="2026-01",
            date="2026-01-02",
            direction=CashDirection.OUTFLOW,
            activity=CashActivity.OPERATING,
            category="supplies",
            amount=Decimal(100),
        ),
    ]

    kept, warnings = remove_duplicates(transactions)

    assert len(kept) == 2
    assert warnings == ["Possible duplicate preserved because source identity is missing: 2026-01 100"]


def test_document_row_identity_is_deduplicated() -> None:
    transaction = CashFlowTransaction(
        period="2026-01",
        direction=CashDirection.INFLOW,
        activity=CashActivity.OPERATING,
        amount=Decimal(100),
        document_id="doc-1",
        sheet="Cashbook",
        row_number=7,
    )

    kept, warnings = remove_duplicates([transaction, transaction.model_copy()])

    assert len(kept) == 1
    assert warnings == ["Duplicate transaction excluded: 2026-01 100"]


def test_source_reference_identity_is_deduplicated() -> None:
    transaction = CashFlowTransaction(
        period="2026-01",
        direction=CashDirection.INFLOW,
        activity=CashActivity.OPERATING,
        amount=Decimal(100),
        source_ref="bank-transaction-1",
    )

    kept, warnings = remove_duplicates([transaction, transaction.model_copy()])

    assert len(kept) == 1
    assert warnings == ["Duplicate transaction excluded: 2026-01 100"]


def test_positive_cash_flow_receives_a_score() -> None:
    periods = [
        CashFlowPeriodSummary(
            period="2026-01",
            operating_inflow=Decimal(150),
            operating_outflow=Decimal(100),
            net_operating_cash_flow=Decimal(50),
        )
    ]
    metrics = calculate_burn_metrics(periods, Decimal(500))

    score = score_cash_flow(metrics, {"status": "matched"}, "structured_facts")

    assert metrics["cash_flow_state"] == "generating"
    assert metrics["cash_generating"] is True
    assert metrics["base_runway_months"] is None
    assert score["total_score"] == 100


def test_break_even_cash_flow_is_not_labeled_as_cash_generating() -> None:
    periods = [
        CashFlowPeriodSummary(
            period="2026-01",
            operating_inflow=Decimal(100),
            operating_outflow=Decimal(100),
            net_operating_cash_flow=Decimal(0),
        )
    ]
    metrics = calculate_burn_metrics(periods, Decimal(500))

    score = score_cash_flow(metrics, {"status": "matched"}, "structured_facts")

    assert metrics["cash_flow_state"] == "break_even"
    assert metrics["cash_generating"] is False
    assert score["total_score"] == 100


def test_missing_periods_still_produce_no_score() -> None:
    metrics = calculate_burn_metrics([], Decimal(500))

    score = score_cash_flow(metrics, {"status": "matched"}, "structured_facts")

    assert metrics["cash_flow_state"] == "insufficient_data"
    assert score["total_score"] is None


def test_empty_structured_dataset_returns_partial_report_instead_of_crashing() -> None:
    facts = {
        "cash_flow_dataset": {
            "opening_cash": "100",
            "reported_ending_cash": "100",
            "transactions": [],
        }
    }

    report = asyncio.run(CashFlowAnalyzer().analyze(facts, [], {}))

    assert report.score is None
    assert report.details["metrics"]["cash_flow_state"] == "insufficient_data"
    assert report.details["scenarios"] == {}


def test_mismatch_uses_reported_cash_for_scenario_but_has_no_score() -> None:
    facts = {
        "cash_flow_dataset": {
            "opening_cash": "100",
            "reported_ending_cash": "5",
            "transactions": [
                {
                    "period": "2026-01",
                    "direction": "outflow",
                    "activity": "operating",
                    "amount": "10",
                }
            ],
        }
    }

    report = asyncio.run(
        CashFlowAnalyzer().analyze(facts, [], {"reconciliation_tolerance": 0})
    )

    assert report.details["reconciliation"]["status"] == "critical_mismatch"
    assert report.details["scenarios"]["base"]["monthly_projection"][0]["starting_cash"] == Decimal(5)
    assert report.score is None


def test_workbook_transactions_keep_manual_current_cash_when_balance_is_missing() -> None:
    facts = {
        "current_cash": 500,
        "financial_periods": [{"period": "2026-01", "inflow": 100, "outflow": 150}],
    }
    extracted = CashFlowDataset(
        source_type="cashbook",
        transactions=[
            CashFlowTransaction(
                period="2026-01",
                direction=CashDirection.OUTFLOW,
                activity=CashActivity.OPERATING,
                amount=Decimal(50),
            )
        ],
    )

    dataset = normalize_cash_flow_input(facts, extracted)

    assert dataset is not None
    assert dataset.reported_ending_cash == Decimal(500)
    assert "current_cash" in dataset.warnings[0]


def test_reconciliation_without_opening_cash_is_not_calculated_from_zero() -> None:
    dataset = CashFlowDataset(
        reported_ending_cash=Decimal(500),
        transactions=[
            CashFlowTransaction(
                period="2026-01",
                direction=CashDirection.OUTFLOW,
                activity=CashActivity.OPERATING,
                amount=Decimal(50),
            )
        ],
    )

    result = reconcile_balance(dataset)

    assert result["status"] == "not_available"
    assert result["expected_ending_cash"] is None
    assert result["difference"] is None


def test_dataset_without_any_cash_balance_returns_insufficient_data() -> None:
    facts = {
        "cash_flow_dataset": {
            "transactions": [
                {
                    "period": "2026-01",
                    "direction": "outflow",
                    "activity": "operating",
                    "amount": "50",
                }
            ]
        }
    }

    report = asyncio.run(CashFlowAnalyzer().analyze(facts, [], {}))

    assert report.status.value == "insufficient_data"
    assert report.missing_data == ["current_cash hoặc reported_ending_cash"]
    assert report.details["reconciliation"]["expected_ending_cash"] is None


def test_interest_payment_is_operating_cash_flow() -> None:
    transaction = CashFlowTransaction(
        period="2026-06",
        direction=CashDirection.OUTFLOW,
        amount=Decimal(100),
        description="trả lãi vay tháng 6",
    )

    assert classify_transaction(transaction).activity == CashActivity.OPERATING


def test_fixed_asset_investment_is_investing_cash_flow() -> None:
    transaction = CashFlowTransaction(
        period="2026-06",
        direction=CashDirection.OUTFLOW,
        amount=Decimal(100),
        description="đầu tư tài sản cố định",
    )

    assert classify_transaction(transaction).activity == CashActivity.INVESTING
