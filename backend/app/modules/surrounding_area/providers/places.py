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

from app.modules.surrounding_area.tools.geo import haversine_km

from app.core.config import get_settings

PLACES_VERSION = "1.0.0"
TEXT_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"
TEXT_SEARCH_NEW_URL = "https://places.googleapis.com/v1/places:searchText"
NEARBY_SEARCH_NEW_URL = "https://places.googleapis.com/v1/places:searchNearby"

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


# ---------------------------------------------------------------------------
# Places API (New) is the primary data source for Surrounding Area.  The
# legacy helpers above remain temporarily compatible with older callers, while
# the analyzer and geocoding facade use the implementation below.
# ---------------------------------------------------------------------------

PLACES_NEW_VERSION = "2.0.0"
_NEW_FIELDS = (
    "places.id,places.displayName,places.primaryType,places.types,places.location,"
    "places.formattedAddress,places.rating,places.userRatingCount,places.priceLevel,"
    "places.googleMapsUri,places.businessStatus"
)
_PRICE_LEVEL_NUMBER = {
    "PRICE_LEVEL_FREE": 0,
    "PRICE_LEVEL_INEXPENSIVE": 1,
    "PRICE_LEVEL_MODERATE": 2,
    "PRICE_LEVEL_EXPENSIVE": 3,
    "PRICE_LEVEL_VERY_EXPENSIVE": 4,
}

PostFetcher = Callable[[str, dict[str, Any], dict[str, str]], Any]


def _default_post(url: str, payload: dict[str, Any], headers: dict[str, str]) -> Any:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def _api_key(api_key: str | None = None) -> str:
    if api_key is not None:
        return api_key
    return get_settings().google_places_api_key or os.environ.get("GOOGLE_PLACES_API_KEY", "")


@dataclass(frozen=True)
class PlacesPoi:
    place_id: str
    name: str | None
    lat: float
    lon: float
    category_value: str
    types: tuple[str, ...]
    distance_m: float
    formatted_address: str | None = None
    rating: float | None = None
    user_ratings_total: int | None = None
    price_level: int | None = None
    google_maps_uri: str | None = None
    business_status: str | None = None
    brand: str | None = None
    operator: str | None = None
    category_key: str = "google_primary_type"

    @property
    def is_chain(self) -> bool:
        # poi_metrics augments this with known-chain name matching.
        return bool(self.brand)

    @property
    def price_label(self) -> str | None:
        return _PRICE_LABELS.get(self.price_level) if self.price_level is not None else None

    def google_maps_url(self) -> str:
        if self.google_maps_uri:
            return self.google_maps_uri
        query = urllib.parse.quote_plus(f"{self.name or ''} {self.lat},{self.lon}")
        return f"https://www.google.com/maps/search/?api=1&query={query}&query_place_id={self.place_id}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "place_id": self.place_id,
            "name": self.name,
            "category": self.category_value,
            "category_key": self.category_key,
            "types": list(self.types),
            "lat": self.lat,
            "lon": self.lon,
            "distance_m": round(self.distance_m, 1),
            "is_chain": self.is_chain,
            "formatted_address": self.formatted_address,
            "rating": self.rating,
            "user_ratings_total": self.user_ratings_total,
            "price_level": self.price_level,
            "price_label": self.price_label,
            "source": "google_places",
            "source_id": self.place_id,
            "position_quality": "point",
            "maps_match_status": "verified_google_maps",
            "google_maps_url": self.google_maps_url(),
        }


@dataclass
class NearbyGroupResult:
    name: str
    places: list[PlacesPoi] = field(default_factory=list)
    warning: str | None = None
    capped: bool = False


@dataclass
class AreaSurveyResult:
    competitors: list[PlacesPoi]
    eateries: list[PlacesPoi]
    demand_places: dict[str, list[PlacesPoi] | None]
    all_places: list[PlacesPoi]
    groups: list[NearbyGroupResult]
    warnings: list[str]

    @property
    def competitor_capped(self) -> bool:
        return any(group.name == "competitors" and group.capped for group in self.groups)

    @property
    def successful_groups(self) -> int:
        return sum(1 for group in self.groups if group.warning is None)


def _parse_places(data: Any, center_lat: float, center_lon: float) -> list[PlacesPoi]:
    rows = data.get("places", []) if isinstance(data, dict) else []
    parsed: list[PlacesPoi] = []
    for item in rows:
        if not isinstance(item, dict):
            continue
        location = item.get("location") or {}
        place_id = str(item.get("id") or "").strip()
        if not place_id or "latitude" not in location or "longitude" not in location:
            continue
        lat = float(location["latitude"])
        lon = float(location["longitude"])
        display_name = item.get("displayName") or {}
        types = tuple(str(value) for value in item.get("types", []) if value)
        primary_type = str(item.get("primaryType") or (types[0] if types else "place"))
        raw_price = item.get("priceLevel")
        parsed.append(
            PlacesPoi(
                place_id=place_id,
                name=display_name.get("text") if isinstance(display_name, dict) else str(display_name),
                lat=lat,
                lon=lon,
                category_value=primary_type,
                types=types,
                distance_m=haversine_km(center_lat, center_lon, lat, lon) * 1000,
                formatted_address=item.get("formattedAddress"),
                rating=float(item["rating"]) if item.get("rating") is not None else None,
                user_ratings_total=(
                    int(item["userRatingCount"]) if item.get("userRatingCount") is not None else None
                ),
                price_level=_PRICE_LEVEL_NUMBER.get(str(raw_price)) if raw_price is not None else None,
                google_maps_uri=item.get("googleMapsUri"),
                business_status=item.get("businessStatus"),
            )
        )
    return sorted(parsed, key=lambda place: place.distance_m)


def search_text_locations(
    query: str,
    *,
    api_key: str | None = None,
    fetch: PostFetcher | None = None,
    limit: int = 5,
) -> list[PlacesPoi]:
    """Resolve an address or named place using Places Text Search (New)."""
    key = _api_key(api_key)
    if not key:
        return []
    payload = {
        "textQuery": query,
        "languageCode": "vi",
        "regionCode": "VN",
        "pageSize": min(20, max(1, limit)),
    }
    data = (fetch or _default_post)(
        TEXT_SEARCH_NEW_URL,
        payload,
        {"X-Goog-Api-Key": key, "X-Goog-FieldMask": _NEW_FIELDS},
    )
    # Text search has no analysis center; retain 0 distance for candidate pins.
    return _parse_places(data, 0.0, 0.0)


def _nearby_group(
    name: str,
    types: tuple[str, ...],
    lat: float,
    lon: float,
    radius_m: int,
    key: str,
    fetch: PostFetcher,
) -> NearbyGroupResult:
    payload = {
        "includedTypes": list(types),
        "maxResultCount": 20,
        "rankPreference": "DISTANCE",
        "languageCode": "vi",
        "regionCode": "VN",
        "locationRestriction": {
            "circle": {"center": {"latitude": lat, "longitude": lon}, "radius": float(radius_m)}
        },
    }
    try:
        data = fetch(
            NEARBY_SEARCH_NEW_URL,
            payload,
            {"X-Goog-Api-Key": key, "X-Goog-FieldMask": _NEW_FIELDS},
        )
        places = _parse_places(data, lat, lon)
        return NearbyGroupResult(name=name, places=places, capped=len(places) >= 20)
    except Exception as exc:  # noqa: BLE001 - one failed group becomes missing data
        return NearbyGroupResult(name=name, warning=f"Google Places nhóm '{name}' lỗi: {exc}")


_FNB_TYPES = ("cafe", "coffee_shop", "restaurant", "fast_food_restaurant", "bakery", "bar", "pub")
_RETAIL_TYPES = ("convenience_store", "supermarket", "clothing_store", "department_store", "shopping_mall")
_OFFICE_TYPES = ("corporate_office", "coworking_space")
_SCHOOL_TYPES = ("school", "university", "preschool", "primary_school", "secondary_school")
_TRANSPORT_TYPES = ("bus_station", "transit_station", "subway_station", "train_station")


def survey_area(
    lat: float,
    lon: float,
    *,
    radius_m: int,
    industry_profile: str | None,
    api_key: str | None = None,
    fetch: PostFetcher | None = None,
) -> AreaSurveyResult:
    """Collect bounded, de-duplicated nearby POIs for F&B or small retail."""
    key = _api_key(api_key)
    if not key:
        raise RuntimeError("GOOGLE_PLACES_API_KEY chưa được cấu hình")
    post = fetch or _default_post
    competitor_types = _RETAIL_TYPES if industry_profile == "retail" else _FNB_TYPES
    specs = (
        ("competitors", competitor_types),
        ("eateries", _FNB_TYPES),
        ("office", _OFFICE_TYPES),
        ("school", _SCHOOL_TYPES),
        ("transport", _TRANSPORT_TYPES),
    )
    groups = [_nearby_group(name, types, lat, lon, radius_m, key, post) for name, types in specs]
    by_name = {group.name: group for group in groups}

    def unique(rows: list[PlacesPoi]) -> list[PlacesPoi]:
        return list({row.place_id: row for row in rows}.values())

    competitors = unique(by_name["competitors"].places)
    eateries = unique(by_name["eateries"].places)
    demand_places: dict[str, list[PlacesPoi] | None] = {
        # Places describes establishments, not residential population/zoning.
        "residential": None,
        "office": None if by_name["office"].warning else unique(by_name["office"].places),
        "school": None if by_name["school"].warning else unique(by_name["school"].places),
        "transport": None if by_name["transport"].warning else unique(by_name["transport"].places),
    }
    all_places = unique([place for group in groups for place in group.places])
    warnings = [group.warning for group in groups if group.warning]
    warnings.append("Google Places không cung cấp mật độ dân cư; residential được đánh dấu thiếu, không tính là 0.")
    capped = [group.name for group in groups if group.capped]
    if capped:
        warnings.append(
            "Các nhóm chạm giới hạn 20 kết quả của Nearby Search: "
            + ", ".join(capped)
            + ". Số đếm là giới hạn dưới, không phải tổng điều tra đầy đủ."
        )
    return AreaSurveyResult(
        competitors=competitors,
        eateries=eateries,
        demand_places=demand_places,
        all_places=all_places,
        groups=groups,
        warnings=list(dict.fromkeys(warnings)),
    )
