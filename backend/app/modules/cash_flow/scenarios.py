from decimal import Decimal

from .schemas import CashFlowPeriodSummary

DEFAULTS = {
    "base": (Decimal(0), Decimal(0)),
    "downside": (Decimal("-.15"), Decimal(".05")),
    "severe": (Decimal("-.30"), Decimal(".15")),
}


def run_scenarios(periods: list[CashFlowPeriodSummary], available_cash: Decimal, options: dict, facts: dict) -> dict:
    months = max(1, min(int(options.get("scenario_months", 12)), 120))
    latest = periods[-1]
    buffer = Decimal(
        str(facts.get("minimum_cash_buffer", options.get("minimum_cash_buffer", latest.operating_outflow)))
    )
    output = {}
    for name, default in DEFAULTS.items():
        override = (options.get("scenario_assumptions") or {}).get(name, {})
        income_change = Decimal(str(override.get("operating_inflow_change", default[0])))
        cost_change = Decimal(str(override.get("operating_outflow_change", default[1])))
        cash, projection, minimum, first_negative, funding_by = available_cash, [], available_cash, None, None
        for index in range(months):
            inflow = latest.operating_inflow * (1 + income_change)
            outflow = latest.operating_outflow * (1 + cost_change)
            cash += inflow - outflow
            minimum = min(minimum, cash)
            month = f"M{index + 1}"
            first_negative = first_negative or (month if cash < 0 else None)
            funding_by = funding_by or (month if cash < buffer else None)
            projection.append(
                {
                    "month": month,
                    "starting_cash": cash - inflow + outflow,
                    "operating_inflow": inflow,
                    "operating_outflow": outflow,
                    "net_cash_flow": inflow - outflow,
                    "ending_cash": cash,
                }
            )
        output[name] = {
            "name": name,
            "assumptions": {"operating_inflow_change": income_change, "operating_outflow_change": cost_change},
            "monthly_projection": projection,
            "first_negative_cash_month": first_negative,
            "first_below_buffer_month": funding_by,
            "minimum_cash": minimum,
            "ending_cash": cash,
            "runway_months": next((i + 1 for i, x in enumerate(projection) if x["ending_cash"] < 0), None),
            "funding_gap": max(buffer - minimum, Decimal(0)),
            "funding_needed_by": funding_by,
            "minimum_cash_buffer": buffer,
        }
    return output
