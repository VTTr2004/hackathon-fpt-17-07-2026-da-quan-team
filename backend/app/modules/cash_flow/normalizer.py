from decimal import Decimal, InvalidOperation
from typing import Any

from .schemas import CashActivity, CashDirection, CashFlowDataset, CashFlowTransaction


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


def legacy_periods_to_dataset(current_cash: Any, periods: list[dict[str, Any]]) -> CashFlowDataset:
    transactions: list[CashFlowTransaction] = []
    for item in periods:
        period = normalize_period(item["period"])
        transactions.extend([
            CashFlowTransaction(period=period, direction=CashDirection.INFLOW, activity=CashActivity.OPERATING,
                                category="legacy_inflow", amount=normalize_amount(item.get("inflow", 0))),
            CashFlowTransaction(period=period, direction=CashDirection.OUTFLOW, activity=CashActivity.OPERATING,
                                category="legacy_outflow", amount=normalize_amount(item.get("outflow", 0))),
        ])
    return CashFlowDataset(reported_ending_cash=normalize_amount(current_cash), transactions=transactions,
        source_type="legacy", warnings=["Legacy input does not separate financing and investing cash flow."],
        assumptions=["Legacy financial_periods are temporarily treated as operating cash flow."])


def normalize_cash_flow_input(startup_facts: dict[str, Any], extracted_dataset: CashFlowDataset | None = None) -> CashFlowDataset | None:
    raw = startup_facts.get("cash_flow_dataset")
    if raw:
        dataset = CashFlowDataset.model_validate(raw)
        dataset.transactions = [transaction.model_copy(update={"period": normalize_period(transaction.period), "amount": normalize_amount(transaction.amount)}) for transaction in dataset.transactions]
        return dataset
    if extracted_dataset and extracted_dataset.transactions:
        return extracted_dataset
    periods = startup_facts.get("financial_periods") or []
    if periods and startup_facts.get("current_cash") is not None:
        return legacy_periods_to_dataset(startup_facts["current_cash"], periods)
    return None
