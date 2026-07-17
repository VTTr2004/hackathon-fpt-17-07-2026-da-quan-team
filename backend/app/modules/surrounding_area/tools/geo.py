"""Geometric and scoring primitives for surrounding-area analysis.

Every function here is deterministic: identical input always yields identical
output. No network access, no LLM. See docs/tools.md.
"""

from collections.abc import Mapping
from math import asin, cos, radians, sin, sqrt
from typing import Any

HAVERSINE_VERSION = "1.0.0"
LOCATION_SCORE_VERSION = "2.0.0"

EARTH_RADIUS_KM = 6371.0088

# Below this share of total weight actually measured, a score would say more
# about the gaps than about the location, so we refuse to emit one.
DEFAULT_MIN_COVERED_WEIGHT = 0.6


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    if not (-90 <= lat1 <= 90 and -90 <= lat2 <= 90):
        raise ValueError("Latitude must be between -90 and 90")
    if not (-180 <= lon1 <= 180 and -180 <= lon2 <= 180):
        raise ValueError("Longitude must be between -180 and 180")
    d_lat = radians(lat2 - lat1)
    d_lon = radians(lon2 - lon1)
    a = sin(d_lat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lon / 2) ** 2
    return round(2 * EARTH_RADIUS_KM * asin(sqrt(a)), 3)


def bounding_box(lat: float, lon: float, radius_km: float) -> tuple[float, float, float, float]:
    """Return (min_lat, max_lat, min_lon, max_lon) enclosing the radius circle.

    Used to pre-filter candidates with a spatial index before exact haversine.
    The box is deliberately never smaller than the true circle: at the poles and
    across the antimeridian it widens to the full range rather than wrap, so the
    caller may see extra candidates but never a false negative.
    """
    if radius_km < 0:
        raise ValueError("radius_km must be >= 0")
    if not -90 <= lat <= 90:
        raise ValueError("Latitude must be between -90 and 90")
    if not -180 <= lon <= 180:
        raise ValueError("Longitude must be between -180 and 180")

    d_lat = radius_km / 111.32
    min_lat = max(lat - d_lat, -90.0)
    max_lat = min(lat + d_lat, 90.0)

    # Longitude degrees shrink toward the poles; use the latitude closest to a
    # pole (largest |lat|) reached by the box, which gives the widest span.
    worst_lat = max(abs(min_lat), abs(max_lat))
    cos_lat = cos(radians(worst_lat))
    if cos_lat <= 1e-9:
        return (min_lat, max_lat, -180.0, 180.0)
    d_lon = radius_km / (111.32 * cos_lat)
    if d_lon >= 180:
        return (min_lat, max_lat, -180.0, 180.0)
    return (min_lat, max_lat, lon - d_lon, lon + d_lon)


def score_location(
    metrics: Mapping[str, Any],
    weights: Mapping[str, float],
    *,
    min_covered_weight: float = DEFAULT_MIN_COVERED_WEIGHT,
) -> dict[str, Any]:
    """Weighted location score that refuses to treat "unmeasured" as "zero".

    A metric that is absent or ``None`` is *not observed*. It is never coerced
    to 0 — doing so silently converts a failed query into the strongest possible
    negative evidence. Unobserved metrics are reported in ``missing_metrics``,
    excluded from the weighted sum, and the remaining weights are renormalised.

    An explicit ``0`` is a real observation and scores as zero.

    Returns a dict with:
      score            float | None — None when too little weight was observed
      status           "complete" | "partial" | "insufficient_data"
      contributions    per-metric weighted contribution (observed metrics only)
      measured_metrics / missing_metrics
      covered_weight   share of total weight actually observed
      warnings         human-readable data-gap warnings for ToolCall.warnings
      assumptions      what renormalisation implies, when it was applied
    """
    if not weights:
        raise ValueError("Location weights must not be empty")
    if any(w < 0 for w in weights.values()):
        raise ValueError("Location weights must be non-negative")
    if abs(sum(weights.values()) - 1.0) > 1e-6:
        raise ValueError("Location weights must sum to 1")

    contributions: dict[str, float] = {}
    measured: list[str] = []
    missing: list[str] = []
    warnings: list[str] = []
    covered_weight = 0.0

    for key, weight in weights.items():
        raw = metrics.get(key)
        if raw is None:
            missing.append(key)
            warnings.append(
                f"Chỉ số '{key}' (trọng số {weight:.0%}) không đo được. "
                f"Chỉ số này bị loại khỏi công thức, KHÔNG được thay bằng 0."
            )
            continue
        if isinstance(raw, bool) or not isinstance(raw, int | float):
            raise ValueError(f"Metric {key} must be a number or None, got {type(raw).__name__}")
        value = float(raw)
        if not 0 <= value <= 100:
            raise ValueError(f"Metric {key} must be between 0 and 100")
        contributions[key] = round(value * weight, 2)
        measured.append(key)
        covered_weight += weight

    covered_weight = round(covered_weight, 6)
    assumptions: list[str] = []

    if covered_weight < min_covered_weight:
        warnings.append(
            f"Chỉ đo được {covered_weight:.0%} tổng trọng số (yêu cầu tối thiểu "
            f"{min_covered_weight:.0%}); không đủ căn cứ để chấm điểm vị trí."
        )
        return {
            "score": None,
            "status": "insufficient_data",
            "contributions": contributions,
            "measured_metrics": measured,
            "missing_metrics": missing,
            "covered_weight": covered_weight,
            "warnings": warnings,
            "assumptions": assumptions,
        }

    raw_sum = sum(contributions.values())
    if missing:
        score = round(raw_sum / covered_weight, 2)
        status = "partial"
        assumptions.append(
            f"Điểm được chuẩn hóa trên {covered_weight:.0%} trọng số đo được. "
            f"Ngầm giả định các chỉ số thiếu ({', '.join(missing)}) có mức điểm "
            f"tương đương phần đã đo — giả định này chưa được kiểm chứng."
        )
    else:
        score = round(raw_sum, 2)
        status = "complete"

    return {
        "score": min(score, 100.0),
        "status": status,
        "contributions": contributions,
        "measured_metrics": measured,
        "missing_metrics": missing,
        "covered_weight": covered_weight,
        "warnings": warnings,
        "assumptions": assumptions,
    }
