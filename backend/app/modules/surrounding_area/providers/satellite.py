"""Satellite scene lookup for the surrounding-area module.

This provider uses the public Copernicus Data Space STAC API to discover recent
Sentinel-2 L2A scenes around a confirmed coordinate. It fetches metadata and
quicklook links only; it does not scrape Google/Esri map tiles or bulk-download
imagery.
"""

from __future__ import annotations

import json
import threading
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from app.modules.surrounding_area.tools.geo import bounding_box

SATELLITE_CONTEXT_VERSION = "1.0.0"
STAC_SEARCH_URL = "https://stac.dataspace.copernicus.eu/v1/search"
STAC_COLLECTION = "sentinel-2-l2a"
STAC_COLLECTION_URL = "https://browser.stac.dataspace.copernicus.eu/collections/sentinel-2-l2a"

Fetcher = Callable[[str, dict[str, Any], float], dict[str, Any]]

_CACHE_TTL_S = 60 * 60 * 12
_CACHE: dict[tuple[float, float, int, int, int], tuple[float, dict[str, Any]]] = {}
_CACHE_LOCK = threading.Lock()


@dataclass(frozen=True)
class SatelliteScene:
    scene_id: str
    collection: str
    datetime: str | None
    cloud_cover: float | None
    gsd_m: float | None
    thumbnail_url: str | None
    visual_url: str | None
    product_url: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.scene_id,
            "collection": self.collection,
            "datetime": self.datetime,
            "cloud_cover": self.cloud_cover,
            "gsd_m": self.gsd_m,
            "thumbnail_url": self.thumbnail_url,
            "visual_url": self.visual_url,
            "product_url": self.product_url,
        }


def _default_fetch(url: str, body: dict[str, Any], timeout_s: float) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/geo+json, application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout_s) as response:
        return json.loads(response.read().decode("utf-8"))


def _asset_href(assets: dict[str, Any], *, role_names: tuple[str, ...], key_names: tuple[str, ...]) -> str | None:
    for key in key_names:
        href = assets.get(key, {}).get("href") if isinstance(assets.get(key), dict) else None
        if href:
            return href

    for asset in assets.values():
        if not isinstance(asset, dict):
            continue
        roles = {str(role).lower() for role in asset.get("roles", [])}
        title = str(asset.get("title") or "").lower()
        media_type = str(asset.get("type") or "").lower()
        if any(role in roles for role in role_names) or any(role in title for role in role_names):
            href = asset.get("href")
            if href:
                return href
        if "image/jpeg" in media_type and "thumbnail" in role_names:
            href = asset.get("href")
            if href:
                return href
    return None


def _product_url(feature: dict[str, Any]) -> str | None:
    for link in feature.get("links", []):
        if not isinstance(link, dict):
            continue
        if link.get("rel") in {"self", "canonical", "alternate"} and link.get("href"):
            return link["href"]
    scene_id = feature.get("id")
    if scene_id:
        return f"{STAC_COLLECTION_URL}/items/{scene_id}"
    return None


def _scene_from_feature(feature: dict[str, Any]) -> SatelliteScene:
    props = feature.get("properties") if isinstance(feature.get("properties"), dict) else {}
    assets = feature.get("assets") if isinstance(feature.get("assets"), dict) else {}
    cloud = props.get("eo:cloud_cover")
    gsd = props.get("gsd")
    return SatelliteScene(
        scene_id=str(feature.get("id") or ""),
        collection=str(feature.get("collection") or STAC_COLLECTION),
        datetime=props.get("datetime"),
        cloud_cover=float(cloud) if isinstance(cloud, int | float) else None,
        gsd_m=float(gsd) if isinstance(gsd, int | float) else 10.0,
        thumbnail_url=_asset_href(
            assets,
            role_names=("thumbnail", "overview"),
            key_names=("thumbnail", "overview", "quicklook", "rendered_preview"),
        ),
        visual_url=_asset_href(
            assets,
            role_names=("visual",),
            key_names=("visual", "TCI", "TCI_10m", "TCI_20m", "TCI_60m"),
        ),
        product_url=_product_url(feature),
    )


def _status(scenes: list[SatelliteScene]) -> str:
    if not scenes:
        return "unavailable"
    best = scenes[0]
    if best.cloud_cover is not None and best.cloud_cover <= 35:
        return "clear_recent_scene"
    if best.cloud_cover is not None and best.cloud_cover <= 70:
        return "usable_cloudy_scene"
    return "cloudy_or_unrated_scene"


def _cache_key(lat: float, lon: float, radius_m: int, days: int, limit: int) -> tuple[float, float, int, int, int]:
    # Round to roughly street-block precision so nearby repeated scans reuse the
    # same STAC lookup without hiding meaningful changes in location.
    return (round(lat, 4), round(lon, 4), int(radius_m), int(days), int(limit))


def fetch_satellite_context(
    lat: float,
    lon: float,
    *,
    radius_m: int = 1000,
    days: int = 180,
    limit: int = 5,
    timeout_s: float = 8.0,
    fetch: Fetcher | None = None,
) -> dict[str, Any]:
    """Return recent Sentinel-2 scene metadata around a coordinate.

    The function never raises for normal network/provider failures; callers get
    an empty scene list plus warnings so the UI can still render the local map.
    """
    radius_m = min(3000, max(100, int(radius_m or 1000)))
    days = min(730, max(7, int(days or 180)))
    limit = min(10, max(1, int(limit or 5)))
    now = datetime.now(tz=UTC)
    key = _cache_key(lat, lon, radius_m, days, limit)

    with _CACHE_LOCK:
        cached = _CACHE.get(key)
        if cached and now.timestamp() - cached[0] < _CACHE_TTL_S:
            return cached[1]

    radius_km = radius_m / 1000.0
    min_lat, max_lat, min_lon, max_lon = bounding_box(lat, lon, radius_km)
    started = (now - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    ended = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    body: dict[str, Any] = {
        "collections": [STAC_COLLECTION],
        "bbox": [min_lon, min_lat, max_lon, max_lat],
        "datetime": f"{started}/{ended}",
        "limit": limit,
        "query": {"eo:cloud_cover": {"lt": 90}},
        "sortby": [{"field": "properties.datetime", "direction": "desc"}],
    }

    warnings: list[str] = []
    scenes: list[SatelliteScene] = []
    try:
        data = (fetch or _default_fetch)(STAC_SEARCH_URL, body, timeout_s)
        features = data.get("features") if isinstance(data, dict) else []
        if isinstance(features, list):
            scenes = [_scene_from_feature(feature) for feature in features if isinstance(feature, dict)]
            scenes.sort(
                key=lambda item: (
                    item.cloud_cover is None,
                    item.cloud_cover if item.cloud_cover is not None else 999.0,
                    item.datetime or "",
                )
            )
    except Exception as exc:  # noqa: BLE001 - external source should degrade, not break analysis
        warnings.append(f"Không lấy được metadata ảnh vệ tinh Copernicus: {exc}")

    result = {
        "provider": "Copernicus Data Space STAC",
        "collection": STAC_COLLECTION,
        "source_url": STAC_COLLECTION_URL,
        "radius_m": radius_m,
        "days": days,
        "status": _status(scenes),
        "best_scene": scenes[0].to_dict() if scenes else None,
        "scenes": [scene.to_dict() for scene in scenes],
        "warnings": warnings,
    }
    with _CACHE_LOCK:
        _CACHE[key] = (now.timestamp(), result)
    return result

