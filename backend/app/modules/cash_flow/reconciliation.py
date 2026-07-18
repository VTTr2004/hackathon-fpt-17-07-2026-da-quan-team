from decimal import Decimal

from .schemas import CashFlowDataset, CashFlowTransaction


def remove_duplicates(transactions: list[CashFlowTransaction]) -> tuple[list[CashFlowTransaction], list[str]]:
    result, seen, warnings = [], set(), []
    for item in transactions:
        key = (
            (item.document_id, item.sheet, item.row_number)
            if item.document_id and item.row_number
            else (item.date, item.amount, item.direction, item.source_ref)
        )
        if key in seen:
            warnings.append(f"Duplicate transaction excluded: {item.period} {item.amount}")
        else:
            seen.add(key)
            result.append(item)
    return result, warnings


def reconcile_balance(dataset: CashFlowDataset, tolerance: Decimal = Decimal(1000)) -> dict:
    inflows = sum((x.amount for x in dataset.transactions if x.direction == "inflow"), Decimal(0))
    outflows = sum((x.amount for x in dataset.transactions if x.direction == "outflow"), Decimal(0))
    expected = (dataset.opening_cash or Decimal(0)) + inflows - outflows
    reported = dataset.reported_ending_cash
    difference = expected - reported if reported is not None and dataset.opening_cash is not None else None
    movement = inflows + outflows
    if difference is None:
        severity = "not_available" if dataset.opening_cash is None else "matched"
    elif abs(difference) <= tolerance:
        severity = "matched"
    elif abs(difference) > max(tolerance, movement * Decimal(".01")):
        severity = "critical_mismatch"
    else:
        severity = "warning"
    return {
        "opening_cash": dataset.opening_cash,
        "total_inflows": inflows,
        "total_outflows": outflows,
        "expected_ending_cash": expected,
        "reported_ending_cash": reported,
        "difference": difference,
        "matched": severity == "matched",
        "status": severity,
    }
