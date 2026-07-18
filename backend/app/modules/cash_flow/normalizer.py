from decimal import Decimal, InvalidOperation
from typing import Any

from .schemas import CashActivity, CashDirection, CashFlowDataset, CashFlowTransaction
from .tools.calculators import calculate_derived_cash_inputs


def normalize_period(period: str) -> str:
    text = str(period).strip()
    if len(text) == 7 and text[4] == "-" and text[:4].isdigit() and text[5:].isdigit() and 1 <= int(text[5:]) <= 12:
        return text
    raise ValueError("period must use YYYY-MM")


def normalize_amount(value: Any) -> Decimal:
    try:
        amount = Decimal(str(value).replace(",", "").strip())
    except (InvalidOperation, AttributeError) as exc:
        raise ValueError("amount must be numeric") from exc
    if not amount.is_finite() or amount < 0:
        raise ValueError("amount must be finite and non-negative")
    return amount


def legacy_periods_to_dataset(
    current_cash: Any,
    periods: list[dict[str, Any]],
    *,
    opening_cash: Any = None,
    reported_ending_cash: Any = None,
    currency: str = "VND",
    cash_as_of: Any = None,
) -> CashFlowDataset:
    transactions: list[CashFlowTransaction] = []
    for item in periods:
        period = normalize_period(item["period"])
        transactions.extend(
            [
                CashFlowTransaction(
                    period=period,
                    direction=CashDirection.INFLOW,
                    activity=CashActivity.OPERATING,
                    category="legacy_inflow",
                    amount=normalize_amount(item.get("inflow", 0)),
                ),
                CashFlowTransaction(
                    period=period,
                    direction=CashDirection.OUTFLOW,
                    activity=CashActivity.OPERATING,
                    category="legacy_outflow",
                    amount=normalize_amount(item.get("outflow", 0)),
                ),
            ]
        )
    return CashFlowDataset(
        currency=currency or "VND",
        opening_cash=normalize_amount(opening_cash) if opening_cash is not None else None,
        reported_ending_cash=normalize_amount(
            reported_ending_cash if reported_ending_cash is not None else current_cash
        ),
        cash_as_of=cash_as_of,
        transactions=transactions,
        source_type="legacy",
        warnings=["Legacy input does not separate financing and investing cash flow."],
        assumptions=["Legacy financial_periods are temporarily treated as operating cash flow."],
    )


def normalize_cash_flow_input(
    startup_facts: dict[str, Any], extracted_dataset: CashFlowDataset | None = None
) -> CashFlowDataset | None:
    raw = startup_facts.get("cash_flow_dataset")
    if raw:
        dataset = CashFlowDataset.model_validate(raw)
        dataset.transactions = [
            transaction.model_copy(
                update={"period": normalize_period(transaction.period), "amount": normalize_amount(transaction.amount)}
            )
            for transaction in dataset.transactions
        ]
        return dataset
    if extracted_dataset and extracted_dataset.transactions:
        # A workbook commonly contains transactions but omits the current balance.
        # Preserve a manually declared balance instead of replacing it with a
        # synthetic balance calculated from a zero opening balance.
        if extracted_dataset.reported_ending_cash is None and startup_facts.get("current_cash") is not None:
            extracted_dataset.reported_ending_cash = normalize_amount(startup_facts["current_cash"])
            extracted_dataset.warnings.append(
                "Reported ending cash was supplied from current_cash because the workbook did not contain "
                "an ending balance."
            )
        return extracted_dataset
    periods = startup_facts.get("financial_periods") or []
    if periods and startup_facts.get("current_cash") is not None:
        return legacy_periods_to_dataset(
            startup_facts["current_cash"],
            periods,
            opening_cash=startup_facts.get("opening_cash"),
            reported_ending_cash=startup_facts.get("reported_ending_cash"),
            currency=str(startup_facts.get("currency") or "VND"),
            cash_as_of=startup_facts.get("cash_as_of"),
        )
    monthly_revenue = startup_facts.get("monthly_revenue")
    monthly_expense = startup_facts.get("monthly_expense")
    if (
        monthly_expense is None
        and monthly_revenue is not None
        and startup_facts.get("fixed_monthly_costs") is not None
        and startup_facts.get("variable_costs") is not None
    ):
        monthly_expense = calculate_derived_cash_inputs(
            monthly_revenue=monthly_revenue,
            fixed_monthly_costs=startup_facts["fixed_monthly_costs"],
            variable_costs=startup_facts["variable_costs"],
        )["monthly_expense"]
    cash_as_of = startup_facts.get("cash_as_of")
    if (
        startup_facts.get("current_cash") is not None
        and monthly_revenue is not None
        and monthly_expense is not None
        and cash_as_of is not None
    ):
        period = str(cash_as_of).strip()[:7]
        try:
            normalize_period(period)
        except ValueError:
            return None
        dataset = legacy_periods_to_dataset(
            startup_facts["current_cash"],
            [{"period": period, "inflow": monthly_revenue, "outflow": monthly_expense}],
            currency=str(startup_facts.get("currency") or "VND"),
            cash_as_of=cash_as_of,
        )
        dataset.warnings.append(
            "Cash flow was estimated from one month of average revenue and expense; "
            "upload period data for trend analysis."
        )
        dataset.assumptions.append(
            "monthly_revenue and monthly_expense are treated as operating cash inflow and outflow for cash_as_of month."
        )
        return dataset
    return None
