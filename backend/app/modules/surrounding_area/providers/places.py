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
from dataclasses import dataclass, field
from typing import Any

from app.core.config import get_settings

PLACES_VERSION = "1.0.0"
TEXT_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"

Fetcher = Callable[[str, dict[str, str]], Any]

# Google price_level 0-4 -> human label.
_PRICE_LABELS = {0: "Miễn phí", 1: "₫ (rẻ)", 2: "₫₫ (trung bình)", 3: "₫₫₫ (cao)", 4: "₫₫₫₫ (rất cao)"}


@dataclass(frozen=True)
class PlaceEnrichment:
    place_id: str | None
    name: str
    rating: float | None
    user_ratings_total: int | None
    price_level: int | None
    lat: float
    lon: float
    reviews: list[dict[str, Any]] = field(default_factory=list)

    @property
    def price_label(self) -> str | None:
        return _PRICE_LABELS.get(self.price_level) if self.price_level is not None else None

    def to_dict(self) -> dict[str, Any]:
        return {
            "place_id": self.place_id,
            "name": self.name,
            "rating": self.rating,
            "user_ratings_total": self.user_ratings_total,
            "price_level": self.price_level,
            "price_label": self.price_label,
            "lat": self.lat,
            "lon": self.lon,
            "reviews": self.reviews,
        }


@dataclass(frozen=True)
class PlaceLookupResult:
    enrichment: PlaceEnrichment | None
    warning: str | None = None


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
    return lookup_place(name, lat, lon, api_key=api_key, fetch=fetch).enrichment


def lookup_place(
    name: str,
    lat: float,
    lon: float,
    *,
    api_key: str | None = None,
    fetch: Fetcher | None = None,
) -> PlaceLookupResult:
    """Look up one place and expose provider diagnostics for API users.

    ``enrich_place`` intentionally keeps the old simple API for tests/callers
    that only need data. The analyzer uses this diagnostic wrapper so a bad key
    or disabled Places API is visible in the report instead of looking like a
    place simply has no rating.
    """
    key = (
        api_key
        if api_key is not None
        else get_settings().google_places_api_key or os.environ.get("GOOGLE_PLACES_API_KEY", "")
    )
    if not key:
        return PlaceLookupResult(enrichment=None)
    fetch = fetch or _default_fetch
    params = {
        "input": name,
        "inputtype": "textquery",
        "locationbias": f"circle:200@{lat},{lon}",
        "fields": "place_id,name,rating,user_ratings_total,price_level,geometry",
        "key": key,
    }
    try:
        data = fetch(TEXT_SEARCH_URL, params)
    except Exception as exc:  # noqa: BLE001 - a failed enrichment is not an error
        return PlaceLookupResult(
            enrichment=None,
            warning=f"Google Places lookup failed for '{name}': {type(exc).__name__}.",
        )
    if isinstance(data, dict):
        provider_status = data.get("status")
        if provider_status not in {None, "OK", "ZERO_RESULTS"}:
            message = data.get("error_message")
            detail = f": {message}" if message else ""
            return PlaceLookupResult(
                enrichment=None,
                warning=f"Google Places status {provider_status}{detail}.",
            )
    candidates = (data or {}).get("candidates") if isinstance(data, dict) else None
    if not candidates:
        return PlaceLookupResult(enrichment=None)
    c = candidates[0]
    place_id = c.get("place_id")
    detail_warning = None
    detail = c
    reviews: list[dict[str, Any]] = []
    if place_id:
        detail_result = _fetch_place_details(place_id, key, fetch)
        detail_warning = detail_result.warning
        if detail_result.enrichment:
            detail = detail_result.enrichment
            reviews = _normalise_reviews(detail.get("reviews", []))
    loc = c.get("geometry", {}).get("location", {})
    if isinstance(detail.get("geometry"), dict):
        loc = detail.get("geometry", {}).get("location", loc)
    return PlaceLookupResult(
        enrichment=PlaceEnrichment(
            place_id=place_id,
            name=detail.get("name", c.get("name", name)),
            rating=detail.get("rating", c.get("rating")),
            user_ratings_total=detail.get("user_ratings_total", c.get("user_ratings_total")),
            price_level=detail.get("price_level", c.get("price_level")),
            lat=loc.get("lat", lat),
            lon=loc.get("lng", lon),
            reviews=reviews,
        ),
        warning=detail_warning,
    )


def _fetch_place_details(place_id: str, api_key: str, fetch: Fetcher) -> PlaceLookupResult:
    params = {
        "place_id": place_id,
        "fields": "name,rating,user_ratings_total,price_level,reviews,geometry,url",
        "key": api_key,
    }
    try:
        data = fetch(DETAILS_URL, params)
    except Exception as exc:  # noqa: BLE001
        return PlaceLookupResult(
            enrichment=None,
            warning=f"Google Place Details lookup failed for '{place_id}': {type(exc).__name__}.",
        )
    if not isinstance(data, dict):
        return PlaceLookupResult(enrichment=None, warning="Unexpected Google Place Details response shape.")
    provider_status = data.get("status")
    if provider_status not in {None, "OK", "ZERO_RESULTS"}:
        message = data.get("error_message")
        detail = f": {message}" if message else ""
        return PlaceLookupResult(enrichment=None, warning=f"Google Place Details status {provider_status}{detail}.")
    result = data.get("result")
    return PlaceLookupResult(enrichment=result if isinstance(result, dict) else None)


def _normalise_reviews(raw_reviews: Any, limit: int = 3) -> list[dict[str, Any]]:
    if not isinstance(raw_reviews, list):
        return []
    reviews = []
    for item in raw_reviews[:limit]:
        if not isinstance(item, dict):
            continue
        reviews.append(
            {
                "author_name": item.get("author_name"),
                "rating": item.get("rating"),
                "relative_time_description": item.get("relative_time_description"),
                "text": item.get("text"),
                "time": item.get("time"),
            }
        )
    return reviews
