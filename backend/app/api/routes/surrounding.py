"""Surrounding-area helper endpoints: geocoding (with the confirmation gate) and
map POIs.

These are additive and self-contained — they do not touch the shared analysis
flow (that stays in analyses.py). They exist so the frontend can:
  1. geocode an address and let the analyst confirm the pin on a map before
     analysis (plan section 4.2), and
  2. render the surrounding POIs (eateries, residential, competitors) with a
     Google Maps deep-link per place.

Neither endpoint needs the database; the map endpoint reads poi.db directly.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from app.core.auth import get_current_user, require_role
from app.models.user import User
from app.modules.surrounding_area.data_store.poi_store import (
    PoiDatabaseUnavailableError,
    get_poi_store,
)
from app.modules.surrounding_area.map_data import build_map_payload
from app.modules.surrounding_area.providers.geocoding import geocode
from app.modules.surrounding_area.providers.satellite import fetch_satellite_context

router = APIRouter(prefix="/surrounding", tags=["surrounding_area"])
investor_only = require_role("investor")


class _RateLimiter:
    """Fixed-window per-client limiter. In-process only — a real multi-instance
    deploy should move this to Redis, but this alone stops a single client from
    hammering the geocoder and getting the shared upstream IP blocked."""

    def __init__(self, max_calls: int, window_s: float) -> None:
        self.max_calls = max_calls
        self.window_s = window_s
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def check(self, key: str) -> bool:
        now = time.monotonic()
        with self._lock:
            hits = self._hits[key]
            while hits and now - hits[0] > self.window_s:
                hits.popleft()
            if len(hits) >= self.max_calls:
                return False
            hits.append(now)
            return True


# Geocode proxies to Nominatim (≤1 req/s upstream policy) → keep it tight.
_geocode_limiter = _RateLimiter(max_calls=20, window_s=60)
# Map only reads local poi.db → looser.
_map_limiter = _RateLimiter(max_calls=120, window_s=60)
_satellite_limiter = _RateLimiter(max_calls=60, window_s=60)


def _client_key(request: Request, user: User) -> str:
    # These endpoints are authenticated. A user ID avoids grouping every user
    # behind a reverse proxy without trusting spoofable forwarded headers.
    user_id = getattr(user, "id", None)
    if user_id is not None:
        return f"user:{user_id}"
    return f"client:{request.client.host if request.client else 'unknown'}"


def _enforce(limiter: _RateLimiter, request: Request, user: User) -> None:
    if not limiter.check(_client_key(request, user)):
        raise HTTPException(status_code=429, detail="Quá nhiều yêu cầu, thử lại sau ít giây.")


class GeocodeRequest(BaseModel):
    address: str = Field(min_length=1, description="Địa chỉ hoặc tên địa danh cần geocode")


@router.post("/geocode")
async def geocode_address(
    payload: GeocodeRequest, request: Request, user: User = Depends(get_current_user)
) -> dict:
    """Địa chỉ -> danh sách tọa độ ứng viên để chuyên viên xác nhận trên bản đồ.

    Luôn kèm needs_confirmation=true (mục 4.2). Không tìm thấy -> candidates rỗng
    + cảnh báo (không lỗi), để UI hướng dẫn nhập lại hoặc nhập tọa độ tay.
    """
    _enforce(_geocode_limiter, request, user)
    result = await geocode(payload.address)
    return result.to_dict()


@router.get("/map")
def surrounding_map(
    request: Request,
    user: User = Depends(investor_only),
    lat: float = Query(ge=-90, le=90),
    lon: float = Query(ge=-180, le=180),
    industry: str | None = Query(default=None),
    radius_m: int = Query(default=1000, ge=100, le=3000),
) -> dict:
    """POI quanh một tọa độ cho bản đồ: quán ăn, khu dân cư, đối thủ theo ngành.

    Mỗi điểm kèm google_maps_url để click khảo sát giá. poi.db chưa build -> 503.
    """
    _enforce(_map_limiter, request, user)
    try:
        store = get_poi_store()
    except PoiDatabaseUnavailableError as exc:
        raise HTTPException(
            status_code=503,
            detail="Chưa có cơ sở dữ liệu POI (poi.db). Chạy scripts.download_osm + scripts.extract_poi.",
        ) from exc
    return build_map_payload(store, lat, lon, industry=industry, radius_m=radius_m)


@router.get("/satellite")
def surrounding_satellite(
    request: Request,
    user: User = Depends(investor_only),
    lat: float = Query(ge=-90, le=90),
    lon: float = Query(ge=-180, le=180),
    radius_m: int = Query(default=1000, ge=100, le=3000),
    days: int = Query(default=180, ge=7, le=730),
) -> dict:
    """Recent Sentinel-2 scene metadata/quicklooks for the confirmed location."""
    _enforce(_satellite_limiter, request, user)
    return fetch_satellite_context(lat, lon, radius_m=radius_m, days=days)
