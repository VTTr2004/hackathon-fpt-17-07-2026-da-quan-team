"""Build the POI payload the frontend map renders.

Shared by the analyzer (embeds it in ModuleReport.details.map) and the
`GET /surrounding/map` endpoint so both stay in sync. Pure read over poi.db;
every returned POI carries a Google Maps deep-link so the analyst can click a
place to survey its price/menu/photos (OSM has no price — plan section 4.3).
"""

from __future__ import annotations

from typing import Any

from app.modules.surrounding_area.data_store.poi_store import PoiStore
from app.modules.surrounding_area.tools.industry_taxonomy import resolve_competitor_filter

EATERY_TAGS = (
    ("amenity", "cafe"),
    ("amenity", "restaurant"),
    ("amenity", "fast_food"),
    ("amenity", "bar"),
    ("amenity", "food_court"),
)


def _poi_dict(p: Any) -> dict[str, Any]:
    return {
        "name": p.name,
        "category": p.category_value,
        "category_key": p.category_key,
        "lat": p.lat,
        "lon": p.lon,
        "distance_m": p.distance_m,
        "is_chain": p.is_chain,
        "source": "openstreetmap",
        "source_id": f"{p.osm_type}{p.osm_id}",
        "position_quality": "point" if p.osm_type == "n" else "polygon_centroid",
        "maps_match_status": "unverified_google_maps",
        "google_maps_url": p.google_maps_url(),
    }


def build_map_payload(
    store: PoiStore,
    lat: float,
    lon: float,
    *,
    industry: str | None = None,
    radius_m: int = 1000,
    limit: int = 60,
) -> dict[str, Any]:
    """Return {center, eateries, residential, competitors} for the map.

    `competitors` is industry-specific (empty if the industry has no competitor
    tags); `eateries` is always included as general context (what the user asked
    to see — "có quán ăn hàng ăn nào"). Failures degrade to empty lists, never an
    exception, so the map still renders the pin.
    """
    try:
        eateries = store.query_radius(lat, lon, radius_m, tags=EATERY_TAGS, limit=limit)
        residential = store.query_radius(lat, lon, radius_m, tags=(("landuse", "residential"),), limit=40)
        competitor_tags = resolve_competitor_filter(industry).competitor_tags
        competitors = (
            store.query_radius(lat, lon, radius_m, tags=competitor_tags, limit=limit) if competitor_tags else []
        )
    except Exception:  # noqa: BLE001 - a map that cannot load is empty, not a 500
        return {"center": {"lat": lat, "lon": lon}, "eateries": [], "residential": [], "competitors": []}

    return {
        "center": {"lat": lat, "lon": lon},
        "eateries": [_poi_dict(p) for p in eateries],
        "residential": [{"name": p.name, "lat": p.lat, "lon": p.lon, "distance_m": p.distance_m} for p in residential],
        "competitors": [_poi_dict(p) for p in competitors],
    }
