"""Optional Google Places enrichment: rating and price level for the nearest
competitors.

OSM carries neither rating nor price (measured — plan section 4.3), and there is
no free substitute, so this is the one place the module can use a paid API. It is
**dormant by default**: with no ``GOOGLE_PLACES_API_KEY`` in the environment the
enricher returns nothing and the analyzer proceeds on OSM data alone. Nothing
here is required for the module to run.

Only the top 10-20 nearest competitors are ever looked up — an analyst does not
need the rating of the 200th café 900 m away — which also keeps usage inside the
free tier. Prices are never invented: a place without a price level stays without
one (INSUFFICIENT_DATA), consistent with the rest of the module.
"""

from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from app.core.config import get_settings

PLACES_VERSION = "1.0.0"
TEXT_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"

Fetcher = Callable[[str, dict[str, str]], Any]

# Google price_level 0-4 -> human label.
_PRICE_LABELS = {0: "Miễn phí", 1: "₫ (rẻ)", 2: "₫₫ (trung bình)", 3: "₫₫₫ (cao)", 4: "₫₫₫₫ (rất cao)"}


@dataclass(frozen=True)
class PlaceEnrichment:
    name: str
    rating: float | None
    user_ratings_total: int | None
    price_level: int | None
    lat: float
    lon: float

    @property
    def price_label(self) -> str | None:
        return _PRICE_LABELS.get(self.price_level) if self.price_level is not None else None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "rating": self.rating,
            "user_ratings_total": self.user_ratings_total,
            "price_level": self.price_level,
            "price_label": self.price_label,
            "lat": self.lat,
            "lon": self.lon,
        }


def is_configured(api_key: str | None = None) -> bool:
    key = (
        api_key
        if api_key is not None
        else get_settings().google_places_api_key or os.environ.get("GOOGLE_PLACES_API_KEY", "")
    )
    return bool(key)


def _default_fetch(url: str, params: dict[str, str]) -> Any:
    query = urllib.parse.urlencode(params)
    with urllib.request.urlopen(f"{url}?{query}", timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def enrich_place(
    name: str,
    lat: float,
    lon: float,
    *,
    api_key: str | None = None,
    fetch: Fetcher | None = None,
) -> PlaceEnrichment | None:
    """Look up one place by name near a point. Returns None if not configured or
    not found. Never raises for a normal miss."""
    key = (
        api_key
        if api_key is not None
        else get_settings().google_places_api_key or os.environ.get("GOOGLE_PLACES_API_KEY", "")
    )
    if not key:
        return None
    fetch = fetch or _default_fetch
    params = {
        "input": name,
        "inputtype": "textquery",
        "locationbias": f"circle:200@{lat},{lon}",
        "fields": "name,rating,user_ratings_total,price_level,geometry",
        "key": key,
    }
    try:
        data = fetch(TEXT_SEARCH_URL, params)
    except Exception:  # noqa: BLE001 - a failed enrichment is not an error
        return None
    candidates = (data or {}).get("candidates") if isinstance(data, dict) else None
    if not candidates:
        return None
    c = candidates[0]
    loc = c.get("geometry", {}).get("location", {})
    return PlaceEnrichment(
        name=c.get("name", name),
        rating=c.get("rating"),
        user_ratings_total=c.get("user_ratings_total"),
        price_level=c.get("price_level"),
        lat=loc.get("lat", lat),
        lon=loc.get("lng", lon),
    )
