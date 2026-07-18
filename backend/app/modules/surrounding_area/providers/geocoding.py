"""Address -> coordinates, with a mandatory human confirmation step.

Default provider is **Nominatim** (OpenStreetMap), which needs no API key. It was
measured to resolve named landmarks well ("Chợ Bến Thành" to ~30 m, "Vinhomes
Ocean Park" found) but to fail on house-number street addresses. That is
acceptable here only because the module never analyses a geocode result blindly:
every result carries ``needs_confirmation=True`` and plan section 4.2 requires
the analyst to confirm the pin on a map before analysis. A 1.7 km miss that no
one sees would make every downstream verdict meaningless.

Nominatim's administrative labels are unreliable after the 2025 provincial
mergers (it placed Bến Thành in "Thủ Đức"), so only the COORDINATES are used;
the display label is shown to the human but never parsed for logic.

If ``GOOGLE_GEOCODING_API_KEY`` is set, Google Geocoding is tried first. If not,
``GOONG_API_KEY`` can provide Vietnam-tuned geocoding. Nominatim remains the
keyless fallback so the module still works without paid keys.

Runtime uses stdlib ``urllib`` (not httpx, which is a dev-only dependency) run in
a worker thread so the async event loop is never blocked. The low-level fetch is
injectable so tests never touch the network.
"""

from __future__ import annotations

import asyncio
import json
import os
import time
import urllib.parse
import urllib.request
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass, field
from threading import Lock
from typing import Any

from app.core.config import get_settings

GEOCODING_VERSION = "1.0.0"

# In-process cache of geocode results. The single biggest mitigation against
# getting the shared IP blocked by Nominatim: real workloads geocode the same
# handful of addresses repeatedly (re-runs, multiple analysts, retries), and a
# cache hit makes zero upstream calls. TTL keeps results fresh enough for a
# module that also forces human confirmation of every pin.
_CACHE_TTL_S = 24 * 3600
_CACHE_MAX = 512
_cache: OrderedDict[str, tuple[float, GeocodeResult]] = OrderedDict()
_cache_lock = Lock()


def _cache_get(key: str) -> GeocodeResult | None:
    with _cache_lock:
        entry = _cache.get(key)
        if entry is None:
            return None
        ts, result = entry
        if time.time() - ts > _CACHE_TTL_S:
            _cache.pop(key, None)
            return None
        _cache.move_to_end(key)
        return result


def _cache_put(key: str, result: GeocodeResult) -> None:
    with _cache_lock:
        _cache[key] = (time.time(), result)
        _cache.move_to_end(key)
        while len(_cache) > _CACHE_MAX:
            _cache.popitem(last=False)


def clear_geocode_cache() -> None:
    with _cache_lock:
        _cache.clear()


NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
GOOGLE_GEOCODING_URL = "https://maps.googleapis.com/maps/api/geocode/json"
GOONG_URL = "https://rsapi.goong.io/geocode"
# Nominatim usage policy requires an identifying User-Agent and <= 1 req/s.
USER_AGENT = "startup-lens-diligence/0.1 (hackathon; contact: thanhdat3108k67@gmail.com)"
NOMINATIM_MIN_INTERVAL_S = 1.1

Fetcher = Callable[[str, dict[str, str]], Any]


class GeocodingError(RuntimeError):
    pass


@dataclass(frozen=True)
class GeocodeCandidate:
    lat: float
    lon: float
    display_name: str
    provider: str
    # "high" for a specific place (marketplace, building, POI), "low" for an
    # administrative area — the analyst should scrutinise low-confidence pins.
    confidence: str
    osm_class: str | None = None
    osm_type: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class GeocodeResult:
    query: str
    candidates: list[GeocodeCandidate]
    provider: str
    # Always True: section 4.2 mandates human confirmation before analysis.
    needs_confirmation: bool = True
    warnings: list[str] = field(default_factory=list)

    @property
    def best(self) -> GeocodeCandidate | None:
        return self.candidates[0] if self.candidates else None

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "provider": self.provider,
            "needs_confirmation": self.needs_confirmation,
            "candidates": [
                {
                    "lat": c.lat,
                    "lon": c.lon,
                    "display_name": c.display_name,
                    "provider": c.provider,
                    "confidence": c.confidence,
                }
                for c in self.candidates
            ],
            "warnings": self.warnings,
        }


def _default_fetch(url: str, params: dict[str, str]) -> Any:
    query = urllib.parse.urlencode(params)
    req = urllib.request.Request(f"{url}?{query}", headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


# High-confidence OSM classes: a concrete place rather than an administrative area.
_SPECIFIC_CLASSES = {"amenity", "shop", "tourism", "building", "office", "leisure", "highway"}
_SPECIFIC_TYPES = {"marketplace", "mall", "commercial", "retail", "residential", "neighbourhood"}


def _nominatim_confidence(item: dict[str, Any]) -> str:
    osm_class = item.get("class")
    osm_type = item.get("type")
    if osm_class in _SPECIFIC_CLASSES or osm_type in _SPECIFIC_TYPES:
        return "high"
    if osm_class == "boundary" or osm_type in {"administrative", "country", "state", "province"}:
        return "low"
    return "medium"


class NominatimProvider:
    name = "nominatim"

    def __init__(self, fetch: Fetcher | None = None) -> None:
        self._fetch = fetch or _default_fetch
        self._last_call = 0.0
        self._throttle_lock = Lock()

    def _throttle(self) -> None:
        with self._throttle_lock:
            wait = NOMINATIM_MIN_INTERVAL_S - (time.monotonic() - self._last_call)
            if wait > 0:
                time.sleep(wait)
            self._last_call = time.monotonic()

    def geocode_sync(self, address: str, *, limit: int = 5) -> list[GeocodeCandidate]:
        self._throttle()
        params = {
            "q": address,
            "format": "json",
            "limit": str(limit),
            "addressdetails": "0",
            "countrycodes": "vn",
        }
        data = self._fetch(NOMINATIM_URL, params)
        if not isinstance(data, list):
            raise GeocodingError("Unexpected Nominatim response shape")
        candidates: list[GeocodeCandidate] = []
        for item in data:
            try:
                candidates.append(
                    GeocodeCandidate(
                        lat=float(item["lat"]),
                        lon=float(item["lon"]),
                        display_name=item.get("display_name", ""),
                        provider=self.name,
                        confidence=_nominatim_confidence(item),
                        osm_class=item.get("class"),
                        osm_type=item.get("type"),
                        raw=item,
                    )
                )
            except (KeyError, TypeError, ValueError):
                continue
        return candidates


class GoongProvider:
    """Vietnamese-tuned geocoder. Active only when GOONG_API_KEY is set."""

    name = "goong"

    def __init__(self, api_key: str, fetch: Fetcher | None = None) -> None:
        if not api_key:
            raise GeocodingError("GoongProvider requires an API key")
        self._api_key = api_key
        self._fetch = fetch or _default_fetch

    def geocode_sync(self, address: str, *, limit: int = 5) -> list[GeocodeCandidate]:
        data = self._fetch(GOONG_URL, {"address": address, "api_key": self._api_key})
        results = (data or {}).get("results", []) if isinstance(data, dict) else []
        candidates: list[GeocodeCandidate] = []
        for item in results[:limit]:
            loc = item.get("geometry", {}).get("location", {})
            if "lat" not in loc or "lng" not in loc:
                continue
            candidates.append(
                GeocodeCandidate(
                    lat=float(loc["lat"]),
                    lon=float(loc["lng"]),
                    display_name=item.get("formatted_address", ""),
                    provider=self.name,
                    confidence="high",
                    raw=item,
                )
            )
        return candidates


def _google_confidence(item: dict[str, Any]) -> str:
    geometry = item.get("geometry", {}) if isinstance(item.get("geometry"), dict) else {}
    location_type = geometry.get("location_type")
    if location_type in {"ROOFTOP", "RANGE_INTERPOLATED"} and not item.get("partial_match"):
        return "high"
    if location_type == "GEOMETRIC_CENTER":
        return "medium"
    return "low"


class GoogleGeocodingProvider:
    """Official Google geocoder. Active only when GOOGLE_GEOCODING_API_KEY is set."""

    name = "google_geocoding"

    def __init__(self, api_key: str, fetch: Fetcher | None = None) -> None:
        if not api_key:
            raise GeocodingError("GoogleGeocodingProvider requires an API key")
        self._api_key = api_key
        self._fetch = fetch or _default_fetch

    def geocode_sync(self, address: str, *, limit: int = 5) -> list[GeocodeCandidate]:
        data = self._fetch(
            GOOGLE_GEOCODING_URL,
            {
                "address": address,
                "components": "country:VN",
                "region": "vn",
                "key": self._api_key,
            },
        )
        if not isinstance(data, dict):
            raise GeocodingError("Unexpected Google Geocoding response shape")
        status = data.get("status")
        if status not in {"OK", "ZERO_RESULTS"}:
            raise GeocodingError(f"Google Geocoding status {status}")

        candidates: list[GeocodeCandidate] = []
        for item in data.get("results", [])[:limit]:
            loc = item.get("geometry", {}).get("location", {})
            if "lat" not in loc or "lng" not in loc:
                continue
            candidates.append(
                GeocodeCandidate(
                    lat=float(loc["lat"]),
                    lon=float(loc["lng"]),
                    display_name=item.get("formatted_address", ""),
                    provider=self.name,
                    confidence=_google_confidence(item),
                    raw=item,
                )
            )
        return candidates


def _build_providers(
    nominatim_fetch: Fetcher | None = None,
    goong_fetch: Fetcher | None = None,
    google_fetch: Fetcher | None = None,
    goong_api_key: str | None = None,
    google_geocoding_api_key: str | None = None,
) -> list[Any]:
    """Ordered provider list. Google/Goong when configured, Nominatim fallback."""
    providers: list[Any] = []
    google_key = (
        google_geocoding_api_key
        if google_geocoding_api_key is not None
        else get_settings().google_geocoding_api_key or os.environ.get("GOOGLE_GEOCODING_API_KEY", "")
    )
    goong_key = (
        goong_api_key
        if goong_api_key is not None
        else get_settings().goong_api_key or os.environ.get("GOONG_API_KEY", "")
    )
    if google_key:
        providers.append(GoogleGeocodingProvider(google_key, fetch=google_fetch))
    if goong_key:
        providers.append(GoongProvider(goong_key, fetch=goong_fetch))
    providers.append(NominatimProvider(fetch=nominatim_fetch))
    return providers


async def geocode(
    address: str,
    *,
    nominatim_fetch: Fetcher | None = None,
    goong_fetch: Fetcher | None = None,
    google_fetch: Fetcher | None = None,
    goong_api_key: str | None = None,
    google_geocoding_api_key: str | None = None,
) -> GeocodeResult:
    """Geocode an address, returning ranked candidates for human confirmation.

    Never raises on an empty result: an address that cannot be resolved yields a
    result with no candidates and a warning, which the analyzer maps to
    INSUFFICIENT_DATA (missing coordinates is missing data, not "not applicable").
    """
    if not address or not address.strip():
        return GeocodeResult(
            query=address, candidates=[], provider="none", warnings=["Địa chỉ trống, không thể geocode."]
        )

    # Serve a repeat address from cache — no upstream call, no rate-limit pressure.
    # Tests that inject a fetch bypass the cache so they always exercise parsing.
    cacheable = nominatim_fetch is None and goong_fetch is None and google_fetch is None
    cache_key = address.strip().lower()
    if cacheable:
        cached = _cache_get(cache_key)
        if cached is not None:
            return cached

    providers = _build_providers(
        nominatim_fetch,
        goong_fetch,
        google_fetch,
        goong_api_key,
        google_geocoding_api_key,
    )
    warnings: list[str] = []
    for provider in providers:
        try:
            candidates = await asyncio.to_thread(provider.geocode_sync, address)
        except Exception as exc:  # noqa: BLE001 - provider failure falls through to the next one
            warnings.append(f"Provider {provider.name} lỗi: {exc}")
            continue
        if candidates:
            result = GeocodeResult(query=address, candidates=candidates, provider=provider.name, warnings=warnings)
            if candidates[0].confidence == "low":
                result.warnings.append(
                    "Kết quả geocode chỉ ở mức khu vực hành chính (độ chính xác thấp). "
                    "Chuyên viên phải kiểm tra kỹ vị trí trên bản đồ."
                )
            if cacheable:
                _cache_put(cache_key, result)
            return result

    warnings.append(
        f"Không geocode được '{address}'. Nominatim thường không nhận địa chỉ số nhà chi tiết; "
        f"hãy thử tên tòa nhà/địa danh, hoặc nhập tọa độ trực tiếp."
    )
    return GeocodeResult(query=address, candidates=[], provider="none", warnings=warnings)
