from decimal import Decimal
from statistics import median
from typing import Any

from ..schemas import CashActivity, CashDirection, CashFlowDataset, CashFlowPeriodSummary


def _non_negative_decimal(value: Any, field: str) -> Decimal:
    try:
        number = Decimal(str(value))
    except Exception as exc:
        raise ValueError(f"{field} must be numeric") from exc
    if not number.is_finite() or number < 0:
        raise ValueError(f"{field} must be finite and non-negative")
    return number


def calculate_break_even(*, fixed_monthly_costs: Any, variable_cost_ratio: Any) -> dict[str, Any]:
    fixed_costs = _non_negative_decimal(fixed_monthly_costs, "fixed_monthly_costs")
    ratio = _non_negative_decimal(variable_cost_ratio, "variable_cost_ratio")
    if ratio >= 1:
        raise ValueError("variable_cost_ratio must be less than 1")
    contribution_margin_ratio = Decimal(1) - ratio
    return {
        "fixed_monthly_costs": fixed_costs,
        "variable_cost_ratio": ratio,
        "contribution_margin_ratio": contribution_margin_ratio,
        "break_even_revenue": fixed_costs / contribution_margin_ratio,
    }


def calculate_working_capital(
    *,
    accounts_receivable: Any | None,
    accounts_payable: Any | None,
    inventory: Any | None,
    period_revenue: Any | None = None,
    period_cogs: Any | None = None,
    period_days: int | None = None,
) -> dict[str, Any]:
    raw_balances = {
        "accounts_receivable": accounts_receivable,
        "accounts_payable": accounts_payable,
        "inventory": inventory,
    }
    missing = [field for field, value in raw_balances.items() if value is None]
    balances = {
        field: _non_negative_decimal(value, field) for field, value in raw_balances.items() if value is not None
    }
    output: dict[str, Any] = {
        "available": not missing,
        "missing_data": missing,
        **balances,
        "net_working_capital": None,
        "dso_days": None,
        "dpo_days": None,
        "inventory_days": None,
        "cash_conversion_cycle_days": None,
    }
    if not missing:
        output["net_working_capital"] = (
            balances["accounts_receivable"] + balances["inventory"] - balances["accounts_payable"]
        )
    if period_days is None:
        return output
    if isinstance(period_days, bool) or not 1 <= period_days <= 366:
        raise ValueError("period_days must be between 1 and 366")
    revenue = _non_negative_decimal(period_revenue, "period_revenue") if period_revenue is not None else None
    cogs = _non_negative_decimal(period_cogs, "period_cogs") if period_cogs is not None else None
    days = Decimal(period_days)
    if revenue and accounts_receivable is not None:
        output["dso_days"] = balances["accounts_receivable"] / revenue * days
    if cogs:
        if accounts_payable is not None:
            output["dpo_days"] = balances["accounts_payable"] / cogs * days
        if inventory is not None:
            output["inventory_days"] = balances["inventory"] / cogs * days
    if all(output[field] is not None for field in ("dso_days", "dpo_days", "inventory_days")):
        output["cash_conversion_cycle_days"] = output["dso_days"] + output["inventory_days"] - output["dpo_days"]
    return output


def aggregate_cash_flow_by_period(dataset: CashFlowDataset) -> list[CashFlowPeriodSummary]:
    rows: dict[str, CashFlowPeriodSummary] = {}
    for item in dataset.transactions:
        row = rows.setdefault(item.period, CashFlowPeriodSummary(period=item.period))
        sign = Decimal(1) if item.direction == CashDirection.INFLOW else Decimal(-1)
        prefix = item.activity.value
        if item.activity != CashActivity.UNCLASSIFIED:
            key = f"{prefix}_{item.direction.value}"
            setattr(row, key, getattr(row, key) + item.amount)
        row.net_cash_flow += sign * item.amount
    for row in rows.values():
        row.net_operating_cash_flow = row.operating_inflow - row.operating_outflow
        row.net_investing_cash_flow = row.investing_inflow - row.investing_outflow
        row.net_financing_cash_flow = row.financing_inflow - row.financing_outflow
    return [rows[key] for key in sorted(rows)]


def calculate_burn_metrics(periods: list[CashFlowPeriodSummary], available_cash: Decimal) -> dict[str, Any]:
    if not periods:
        return {
            "base_runway_months": None,
            "net_burn": None,
            "cash_generating": False,
            "cash_flow_state": "insufficient_data",
        }
    count = Decimal(len(periods))
    inflow = sum((x.operating_inflow for x in periods), Decimal(0)) / count
    outflow = sum((x.operating_outflow for x in periods), Decimal(0)) / count
    average_net = inflow - outflow
    net = max(-average_net, Decimal(0))
    runway = available_cash / net if net else None
    nets = [x.net_operating_cash_flow for x in periods]
    cash_flow_state = "generating" if average_net > 0 else "burning" if average_net < 0 else "break_even"
    return {
        "average_operating_inflow": inflow,
        "average_operating_outflow": outflow,
        "average_net_operating_cash_flow": average_net,
        "gross_burn": outflow,
        "net_burn": net,
        "median_net_burn": max(-Decimal(str(median(nets))), Decimal(0)),
        "latest_period_burn": max(-nets[-1], Decimal(0)),
        "three_period_average_burn": net,
        "burn_trend": "improving"
        if len(nets) > 1 and nets[-1] > nets[0]
        else "deteriorating"
        if len(nets) > 1 and nets[-1] < nets[0]
        else "stable",
        "base_runway_months": runway,
        "latest_runway_months": available_cash / max(-nets[-1], Decimal(0)) if nets[-1] < 0 else None,
        "cash_generating": average_net > 0,
        "cash_flow_state": cash_flow_state,
    }


def calculate_cash_metrics(periods: list[dict[str, Any]], current_cash: float) -> dict[str, Any]:
    if current_cash < 0:
        raise ValueError("Current cash must be non-negative")
    normalized: list[dict[str, float | str]] = []
    for index, period in enumerate(periods):
        inflow = float(period.get("inflow", 0))
        outflow = float(period.get("outflow", 0))
        if inflow < 0 or outflow < 0:
            raise ValueError("Cash inflow/outflow must be non-negative")
        normalized.append(
            {
                "period": str(period.get("period", index + 1)),
                "inflow": inflow,
                "outflow": outflow,
                "net_cash_flow": inflow - outflow,
            }
        )
    count = len(normalized)
    avg_inflow = sum(float(p["inflow"]) for p in normalized) / count if count else 0
    avg_outflow = sum(float(p["outflow"]) for p in normalized) / count if count else 0
    net_burn = max(avg_outflow - avg_inflow, 0)
    runway = current_cash / net_burn if net_burn > 0 else None
    return {
        "periods": normalized,
        "average_inflow": round(avg_inflow, 2),
        "average_outflow": round(avg_outflow, 2),
        "net_burn": round(net_burn, 2),
        "runway_periods": round(runway, 2) if runway is not None else None,
    }


def simulate_cash_scenario(
    *, current_cash: float, monthly_inflow: float, monthly_outflow: float, months: int
) -> dict[str, Any]:
    if months < 1 or months > 120:
        raise ValueError("Months must be between 1 and 120")
    balance = float(current_cash)
    projection = []
    for month in range(1, months + 1):
        balance += monthly_inflow - monthly_outflow
        projection.append({"month": month, "ending_cash": round(balance, 2)})
    return {"projection": projection, "ending_cash": round(balance, 2)}
