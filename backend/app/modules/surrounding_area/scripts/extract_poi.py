"""Extract points of interest from an OSM PBF extract into a queryable SQLite file.

Usage (from backend/):
    python -m app.modules.surrounding_area.scripts.extract_poi

Design decisions (see docs/methodology.md for the reasoning):

1. Filter by KEY, never by an enumerated list of values. `amenity=*` captures
   cafe, restaurant, pharmacy, school and the ~650 other values present in
   Vietnam. Adding an industry later needs no re-extraction.

2. Nodes AND ways. A large share of Vietnamese POIs are mapped as building
   polygons rather than points; a node-only extract silently undercounts
   competitors, which is the exact failure this module must not commit.

3. One row per (object, category key). An object tagged both `amenity=cafe` and
   `shop=coffee` yields two rows. Count distinct places with
   COUNT(DISTINCT osm_type || osm_id), count a category with a plain filter.

4. Explicit primary keys. `cur.lastrowid` returns None after executemany on
   Python 3.13+ (plan section 7.5), so ids are generated here instead.
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

try:
    import osmium
except ImportError:  # pragma: no cover - optional setup dependency
    osmium = None

DEFAULT_PBF = Path(__file__).resolve().parents[4] / "data" / "vietnam-latest.osm.pbf"
DEFAULT_DB = Path(__file__).resolve().parents[4] / "data" / "poi.db"

SCHEMA_VERSION = "1.0.0"
SOURCE_NAME = "OpenStreetMap via Geofabrik (asia/vietnam-latest.osm.pbf)"
SOURCE_URL = "https://download.geofabrik.de/asia/vietnam-latest.osm.pbf"
SOURCE_LICENSE = "ODbL 1.0 - (c) OpenStreetMap contributors"

# Plan section 4.1: these keys cover every business-like POI type without
# enumerating values. Beyond businesses we also keep:
#   - landuse: residential / commercial / industrial ZONES. Residential zones are
#     the "khu dân cư" demand proxy; without them the module cannot tell a housing
#     estate from an empty field.
#   - public_transport: platforms / stations, for the accessibility signal.
POI_KEYS = ("amenity", "shop", "office", "leisure", "tourism", "craft", "healthcare", "landuse", "public_transport")

# `place` nodes carry settlement names and sometimes a population tag. Kept in a
# separate table: they are context for coverage assessment, not businesses.
PLACE_VALUES = ("city", "town", "borough", "suburb", "quarter", "neighbourhood", "village", "hamlet")

DDL = """
PRAGMA journal_mode = OFF;
PRAGMA synchronous = OFF;

CREATE TABLE poi (
    id             INTEGER PRIMARY KEY,
    osm_type       TEXT    NOT NULL,   -- 'n' node | 'w' way
    osm_id         INTEGER NOT NULL,
    lat            REAL    NOT NULL,   -- representative point (way centroid)
    lon            REAL    NOT NULL,
    min_lat        REAL    NOT NULL,   -- bounding box, so large zones are found
    max_lat        REAL    NOT NULL,   -- by their edge, not just their centre
    min_lon        REAL    NOT NULL,
    max_lon        REAL    NOT NULL,
    name           TEXT,
    brand          TEXT,
    operator       TEXT,
    category_key   TEXT    NOT NULL,
    category_value TEXT    NOT NULL
);

CREATE TABLE place (
    id         INTEGER PRIMARY KEY,
    osm_id     INTEGER NOT NULL,
    lat        REAL    NOT NULL,
    lon        REAL    NOT NULL,
    name       TEXT,
    place_type TEXT    NOT NULL,
    population INTEGER
);

CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
"""

INDEXES = """
CREATE INDEX idx_poi_category   ON poi(category_key, category_value);
CREATE INDEX idx_poi_brand      ON poi(brand) WHERE brand IS NOT NULL;
CREATE INDEX idx_place_type     ON place(place_type);
CREATE VIRTUAL TABLE poi_rtree USING rtree(id, min_lat, max_lat, min_lon, max_lon);
INSERT INTO poi_rtree SELECT id, min_lat, max_lat, min_lon, max_lon FROM poi;
"""


def _way_geometry(way: osmium.osm.Way) -> tuple[float, float, float, float, float, float] | None:
    """Return (centroid_lat, centroid_lon, min_lat, max_lat, min_lon, max_lon).

    Closed ways repeat the first node last; including it would bias the centroid
    toward that vertex, so it is dropped. The bounding box uses every valid
    vertex so a large zone is discoverable by its edge.
    """
    nodes = list(way.nodes)
    if len(nodes) > 1 and nodes[0].ref == nodes[-1].ref:
        nodes = nodes[:-1]
    lats: list[float] = []
    lons: list[float] = []
    for node in nodes:
        if not node.location.valid():
            continue
        lats.append(node.location.lat)
        lons.append(node.location.lon)
    if not lats:
        return None
    return (sum(lats) / len(lats), sum(lons) / len(lons), min(lats), max(lats), min(lons), max(lons))


def _parse_population(raw: str | None) -> int | None:
    if not raw:
        return None
    cleaned = raw.replace(",", "").replace(".", "").replace(" ", "").strip()
    return int(cleaned) if cleaned.isdigit() else None


def _rows_for(
    obj: osmium.osm.OSMObject,
    osm_type: str,
    box: tuple[float, float, float, float, float, float],
    next_id: int,
) -> list[tuple]:
    lat, lon, min_lat, max_lat, min_lon, max_lon = box
    tags = obj.tags
    name = tags.get("name")
    brand = tags.get("brand")
    operator = tags.get("operator")
    rows = []
    for key in POI_KEYS:
        value = tags.get(key)
        if not value or value in ("no", "yes"):
            # `amenity=yes` carries no category information; keeping it would
            # inflate counts with unclassifiable objects.
            continue
        rows.append(
            (
                next_id + len(rows),
                osm_type,
                obj.id,
                lat,
                lon,
                min_lat,
                max_lat,
                min_lon,
                max_lon,
                name,
                brand,
                operator,
                key,
                value,
            )
        )
    return rows


def extract(pbf: Path, db_path: Path) -> dict[str, int]:
    if osmium is None:
        raise RuntimeError(
            "Thiếu thư viện 'osmium'. Cài đặt bằng pip install .[osm] trước khi build poi.db."
        )
    if not pbf.exists():
        raise FileNotFoundError(f"{pbf} not found. Run download_osm.py first.")

    db_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_db = db_path.with_suffix(".db.part")
    tmp_db.unlink(missing_ok=True)

    con = sqlite3.connect(tmp_db)
    con.executescript(DDL)

    started = time.monotonic()
    poi_batch: list[tuple] = []
    place_batch: list[tuple] = []
    next_poi_id = 1
    next_place_id = 1
    stats = {"nodes": 0, "ways": 0, "places": 0, "skipped_ways_no_geom": 0}

    key_filter = osmium.filter.KeyFilter(*POI_KEYS, "place")
    processor = (
        osmium.FileProcessor(str(pbf))
        .with_locations()
        .with_filter(osmium.filter.EntityFilter(osmium.osm.NODE | osmium.osm.WAY))
        .with_filter(key_filter)
    )

    for obj in processor:
        is_node = obj.is_node()
        if is_node:
            place_type = obj.tags.get("place")
            if place_type in PLACE_VALUES:
                place_batch.append(
                    (
                        next_place_id,
                        obj.id,
                        obj.location.lat,
                        obj.location.lon,
                        obj.tags.get("name"),
                        place_type,
                        _parse_population(obj.tags.get("population")),
                    )
                )
                next_place_id += 1
                stats["places"] += 1
            if not obj.location.valid():
                continue
            lat, lon = obj.location.lat, obj.location.lon
            box = (lat, lon, lat, lat, lon, lon)
            osm_type = "n"
        else:
            geom = _way_geometry(obj)
            if geom is None:
                stats["skipped_ways_no_geom"] += 1
                continue
            box = geom
            osm_type = "w"

        rows = _rows_for(obj, osm_type, box, next_poi_id)
        if rows:
            poi_batch.extend(rows)
            next_poi_id += len(rows)
            stats["nodes" if is_node else "ways"] += 1

        if len(poi_batch) >= 50_000:
            con.executemany("INSERT INTO poi VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", poi_batch)
            poi_batch.clear()
        if len(place_batch) >= 10_000:
            con.executemany("INSERT INTO place VALUES (?,?,?,?,?,?,?)", place_batch)
            place_batch.clear()

    if poi_batch:
        con.executemany("INSERT INTO poi VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", poi_batch)
    if place_batch:
        con.executemany("INSERT INTO place VALUES (?,?,?,?,?,?,?)", place_batch)

    elapsed = time.monotonic() - started
    print(f"[..] scan finished in {elapsed:.0f}s; building indexes")
    con.executescript(INDEXES)

    poi_total = con.execute("SELECT COUNT(*) FROM poi").fetchone()[0]
    distinct_objects = con.execute("SELECT COUNT(DISTINCT osm_type || osm_id) FROM poi").fetchone()[0]
    category_values = con.execute("SELECT COUNT(DISTINCT category_key || '=' || category_value) FROM poi").fetchone()[0]

    pbf_mtime = datetime.fromtimestamp(pbf.stat().st_mtime, tz=UTC).isoformat()
    meta = {
        "schema_version": SCHEMA_VERSION,
        "source_name": SOURCE_NAME,
        "source_url": SOURCE_URL,
        "source_license": SOURCE_LICENSE,
        "pbf_file": pbf.name,
        "pbf_size_bytes": str(pbf.stat().st_size),
        "pbf_downloaded_at": pbf_mtime,
        "extracted_at": datetime.now(tz=UTC).isoformat(),
        "extract_seconds": f"{elapsed:.1f}",
        "poi_keys": ",".join(POI_KEYS),
        "poi_rows": str(poi_total),
        "poi_distinct_objects": str(distinct_objects),
        "poi_category_values": str(category_values),
        "place_rows": str(stats["places"]),
    }
    con.executemany("INSERT OR REPLACE INTO meta VALUES (?,?)", list(meta.items()))
    con.commit()
    con.execute("VACUUM")
    con.close()

    tmp_db.replace(db_path)

    print(f"[ok] {db_path} ({db_path.stat().st_size / 1e6:.0f} MB)")
    print(f"     {poi_total:,} rows / {distinct_objects:,} distinct objects / {category_values:,} category values")
    print(f"     nodes={stats['nodes']:,} ways={stats['ways']:,} places={stats['places']:,}")
    if stats["skipped_ways_no_geom"]:
        print(f"     [warn] {stats['skipped_ways_no_geom']:,} ways skipped: no resolvable geometry", file=sys.stderr)
    return {**stats, "poi_rows": poi_total, "distinct_objects": distinct_objects}


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract POIs from an OSM PBF into SQLite")
    parser.add_argument("--pbf", type=Path, default=DEFAULT_PBF)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()
    extract(args.pbf, args.db)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
