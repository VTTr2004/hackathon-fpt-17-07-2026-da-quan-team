from math import asin, cos, radians, sin, sqrt
from typing import Any


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    if not (-90 <= lat1 <= 90 and -90 <= lat2 <= 90):
        raise ValueError("Latitude must be between -90 and 90")
    if not (-180 <= lon1 <= 180 and -180 <= lon2 <= 180):
        raise ValueError("Longitude must be between -180 and 180")
    d_lat = radians(lat2 - lat1)
    d_lon = radians(lon2 - lon1)
    a = sin(d_lat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lon / 2) ** 2
    return round(2 * 6371.0088 * asin(sqrt(a)), 3)


def score_location(metrics: dict[str, Any], weights: dict[str, float]) -> dict[str, Any]:
    if not weights or abs(sum(weights.values()) - 1.0) > 1e-6:
        raise ValueError("Location weights must sum to 1")
    contributions: dict[str, float] = {}
    for key, weight in weights.items():
        value = float(metrics.get(key, 0))
        if not 0 <= value <= 100:
            raise ValueError(f"Metric {key} must be between 0 and 100")
        contributions[key] = round(value * weight, 2)
    return {"score": round(sum(contributions.values()), 2), "contributions": contributions}
