from decimal import Decimal

from .schemas import CashFlowDataset, CashFlowTransaction


def remove_duplicates(transactions: list[CashFlowTransaction]) -> tuple[list[CashFlowTransaction], list[str]]:
    result, seen, possible_duplicates, warnings = [], set(), set(), []
    for item in transactions:
        key = None
        if item.document_id and item.row_number is not None:
            key = ("document_row", item.document_id, item.sheet, item.row_number)
        elif item.source_ref:
            key = ("source_ref", item.source_ref)

        if key is not None and key in seen:
            warnings.append(f"Duplicate transaction excluded: {item.period} {item.amount}")
            continue

        if key is not None:
            seen.add(key)
        else:
            fingerprint = (
                item.period,
                item.date,
                item.amount,
                item.direction,
                item.activity,
                item.category,
                item.description,
            )
            if fingerprint in possible_duplicates:
                warnings.append(
                    f"Possible duplicate preserved because source identity is missing: {item.period} {item.amount}"
                )
            possible_duplicates.add(fingerprint)
        result.append(item)
    return result, warnings


def reconcile_balance(dataset: CashFlowDataset, tolerance: Decimal = Decimal(1000)) -> dict:
    inflows = sum((x.amount for x in dataset.transactions if x.direction == "inflow"), Decimal(0))
    outflows = sum((x.amount for x in dataset.transactions if x.direction == "outflow"), Decimal(0))
    expected = dataset.opening_cash + inflows - outflows if dataset.opening_cash is not None else None
    reported = dataset.reported_ending_cash
    difference = expected - reported if expected is not None and reported is not None else None
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
