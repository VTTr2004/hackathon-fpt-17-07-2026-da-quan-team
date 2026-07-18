"""Read-only access layer over the extracted POI database (`data/poi.db`).

Deterministic and offline: given the same `poi.db` and the same query, results
never change. The database is opened read-only and shared across requests; no
tool here writes to it.

Spatial queries use a two-stage filter:
  1. the SQLite R*Tree returns every object whose bounding box overlaps the
     search box — cheap and index-backed;
  2. exact haversine (via `tools/geo.py`) keeps only objects genuinely within
     the radius. For point POIs this is distance-to-point; for zones (landuse
     polygons) it is distance-to-bounding-box, so a large residential estate is
     matched when its edge reaches the point, not only its centre.
"""

from __future__ import annotations

import sqlite3
import threading
from dataclasses import dataclass
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.modules.surrounding_area.tools.geo import bounding_box, haversine_km

POI_STORE_VERSION = "1.0.0"
DEFAULT_DB_PATH = Path(__file__).resolve().parents[4] / "data" / "poi.db"


class PoiDatabaseUnavailableError(RuntimeError):
    """Raised when poi.db is missing. Callers translate this to INSUFFICIENT_DATA
    rather than crashing — a missing map is missing data, not a bug."""


@dataclass(frozen=True)
class Poi:
    osm_type: str
    osm_id: int
    lat: float
    lon: float
    name: str | None
    brand: str | None
    operator: str | None
    category_key: str
    category_value: str
    distance_m: float

    @property
    def is_chain(self) -> bool:
        return self.brand is not None

    def google_maps_url(self) -> str:
        """Deep-link to survey this exact place (price/menu/photos) on Google Maps.

        OSM has no price data (plan section 4.3), so the honest way to let an
        analyst "click to check the price" is to open the real place externally.
        """
        if self.name:
            query = f"{self.name} {self.lat},{self.lon}"
        else:
            query = f"{self.lat},{self.lon}"
        from urllib.parse import quote_plus

        return f"https://www.google.com/maps/search/?api=1&query={quote_plus(query)}"


def _bbox_distance_m(lat: float, lon: float, row: sqlite3.Row) -> float:
    """Distance in metres from (lat, lon) to a POI's bounding box.

    Zero when the point is inside the box. For point POIs the box is degenerate
    and this reduces to point distance.
    """
    clamped_lat = min(max(lat, row["min_lat"]), row["max_lat"])
    clamped_lon = min(max(lon, row["min_lon"]), row["max_lon"])
    if clamped_lat == lat and clamped_lon == lon:
        return 0.0
    return haversine_km(lat, lon, clamped_lat, clamped_lon) * 1000.0


class PoiStore:
    def __init__(self, db_path: Path = DEFAULT_DB_PATH) -> None:
        self.db_path = db_path
        if not db_path.exists():
            raise PoiDatabaseUnavailableError(f"{db_path} not found. Run download_osm.py then extract_poi.py.")
        # One read-only SQLite connection PER THREAD. A single shared connection is
        # not safe when queries run in a thread pool (via asyncio.to_thread) — even
        # read-only concurrent use can raise or corrupt state. Thread-local
        # connections give each worker its own handle with zero contention.
        self._local = threading.local()
        self._open_connections: list[sqlite3.Connection] = []
        self._lock = threading.Lock()
        # Validate the schema is readable up front (fail fast, on this thread).
        _ = self._con.execute("SELECT 1 FROM meta LIMIT 1").fetchone()

    @property
    def _con(self) -> sqlite3.Connection:
        con = getattr(self._local, "con", None)
        if con is None:
            con = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True, check_same_thread=False)
            con.row_factory = sqlite3.Row
            self._local.con = con
            with self._lock:
                self._open_connections.append(con)
        return con

    def metadata(self) -> dict[str, str]:
        return {row["key"]: row["value"] for row in self._con.execute("SELECT key, value FROM meta")}

    def source_accessed_at(self) -> datetime:
        """When the underlying OSM extract was produced — for Evidence.accessed_at."""
        meta = self.metadata()
        stamp = meta.get("pbf_downloaded_at") or meta.get("extracted_at")
        if stamp:
            try:
                return datetime.fromisoformat(stamp)
            except ValueError:
                pass
        return datetime.now(tz=UTC)

    def query_radius(
        self,
        lat: float,
        lon: float,
        radius_m: float,
        *,
        tags: tuple[tuple[str, str], ...] | None = None,
        limit: int | None = None,
    ) -> list[Poi]:
        """Return POIs within `radius_m` metres of (lat, lon), optionally filtered.

        `tags` is a set of (key, value) pairs; a value of "*" matches any value
        of that key. An empty/None `tags` returns every category.
        """
        if radius_m < 0:
            raise ValueError("radius_m must be >= 0")
        radius_km = radius_m / 1000.0
        min_lat, max_lat, min_lon, max_lon = bounding_box(lat, lon, radius_km)

        where = [
            "r.max_lat >= ? AND r.min_lat <= ? AND r.max_lon >= ? AND r.min_lon <= ?",
        ]
        params: list[Any] = [min_lat, max_lat, min_lon, max_lon]

        tag_clause = self._tag_clause(tags, params)
        if tag_clause:
            where.append(tag_clause)

        sql = f"""
            SELECT p.osm_type, p.osm_id, p.lat, p.lon, p.min_lat, p.max_lat, p.min_lon, p.max_lon,
                   p.name, p.brand, p.operator, p.category_key, p.category_value
            FROM poi p JOIN poi_rtree r ON r.id = p.id
            WHERE {" AND ".join(where)}
        """
        results: list[Poi] = []
        for row in self._con.execute(sql, params):
            distance_m = _bbox_distance_m(lat, lon, row)
            if distance_m <= radius_m:
                results.append(
                    Poi(
                        osm_type=row["osm_type"],
                        osm_id=row["osm_id"],
                        lat=row["lat"],
                        lon=row["lon"],
                        name=row["name"],
                        brand=row["brand"],
                        operator=row["operator"],
                        category_key=row["category_key"],
                        category_value=row["category_value"],
                        distance_m=round(distance_m, 1),
                    )
                )
        results.sort(key=lambda p: p.distance_m)
        return results[:limit] if limit is not None else results

    @staticmethod
    def _tag_clause(tags: tuple[tuple[str, str], ...] | None, params: list[Any]) -> str:
        if not tags:
            return ""
        ors: list[str] = []
        for key, value in tags:
            if value == "*":
                ors.append("p.category_key = ?")
                params.append(key)
            else:
                ors.append("(p.category_key = ? AND p.category_value = ?)")
                params.extend([key, value])
        return "(" + " OR ".join(ors) + ")"

    def nearest_places_with_population(self, lat: float, lon: float, limit: int = 5) -> list[dict[str, Any]]:
        """Nearest settlement `place` rows carrying a population figure.

        Used by the coverage tool to estimate local population density from OSM's
        own data before falling back to the static table.
        """
        rows = self._con.execute(
            "SELECT name, place_type, population, lat, lon FROM place WHERE population IS NOT NULL"
        ).fetchall()
        scored = [
            {
                "name": r["name"],
                "place_type": r["place_type"],
                "population": r["population"],
                "distance_km": haversine_km(lat, lon, r["lat"], r["lon"]),
            }
            for r in rows
        ]
        scored.sort(key=lambda d: d["distance_km"])
        return scored[:limit]

    def close(self) -> None:
        with self._lock:
            for con in self._open_connections:
                try:
                    con.close()
                except sqlite3.Error:
                    pass
            self._open_connections.clear()
        self._local = threading.local()


@lru_cache(maxsize=1)
def get_poi_store(db_path: Path = DEFAULT_DB_PATH) -> PoiStore:
    """Process-wide cached store. Raises PoiDatabaseUnavailableError if no db."""
    return PoiStore(db_path)
