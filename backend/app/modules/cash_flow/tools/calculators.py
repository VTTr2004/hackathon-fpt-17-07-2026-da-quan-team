from typing import Any


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
