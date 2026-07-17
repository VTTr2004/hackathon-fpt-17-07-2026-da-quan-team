"""Tests for the POI store, run against the real extracted poi.db.

If poi.db is absent (e.g. a fresh checkout that hasn't run extract_poi.py), the
db-backed tests skip rather than fail — the store correctly raises
PoiDatabaseUnavailableError and the analyzer turns that into INSUFFICIENT_DATA.
"""

from __future__ import annotations

import sqlite3

import pytest

from app.modules.surrounding_area.data_store.poi_store import (
    DEFAULT_DB_PATH,
    PoiDatabaseUnavailableError,
    PoiStore,
    _bbox_distance_m,
    get_poi_store,
)

pytestmark = pytest.mark.skipif(not DEFAULT_DB_PATH.exists(), reason="poi.db not built")

# Reference coordinates.
BEN_THANH = (10.7725, 106.6980)
VINHOMES_OCEAN_PARK = (20.9943, 105.9485)
BEN_TRE = (10.2410, 106.3750)
FOOD_TAGS = (("amenity", "cafe"), ("amenity", "restaurant"), ("amenity", "fast_food"))


@pytest.fixture(scope="module")
def store() -> PoiStore:
    return get_poi_store()


class TestBboxDistanceHelper:
    def test_point_inside_box_is_zero(self) -> None:
        row = {"min_lat": 10.0, "max_lat": 11.0, "min_lon": 106.0, "max_lon": 107.0}
        assert _bbox_distance_m(10.5, 106.5, row) == 0.0

    def test_point_outside_box_is_positive(self) -> None:
        row = {"min_lat": 10.0, "max_lat": 10.0, "min_lon": 106.0, "max_lon": 106.0}
        assert _bbox_distance_m(10.0, 106.1, row) > 0


class TestQueryRadiusBasics:
    def test_radius_is_respected(self, store: PoiStore) -> None:
        pois = store.query_radius(*BEN_THANH, 500, tags=FOOD_TAGS)
        assert pois, "Ben Thanh should have eateries within 500m"
        assert all(p.distance_m <= 500 for p in pois)

    def test_results_sorted_by_distance(self, store: PoiStore) -> None:
        pois = store.query_radius(*BEN_THANH, 1000, tags=FOOD_TAGS)
        distances = [p.distance_m for p in pois]
        assert distances == sorted(distances)

    def test_larger_radius_returns_superset(self, store: PoiStore) -> None:
        near = store.query_radius(*BEN_THANH, 250, tags=FOOD_TAGS)
        far = store.query_radius(*BEN_THANH, 1000, tags=FOOD_TAGS)
        assert len(far) >= len(near)

    def test_limit_returns_nearest(self, store: PoiStore) -> None:
        pois = store.query_radius(*BEN_THANH, 1000, tags=FOOD_TAGS, limit=5)
        assert len(pois) <= 5

    def test_wildcard_value_matches_any(self, store: PoiStore) -> None:
        shops = store.query_radius(*BEN_THANH, 500, tags=(("shop", "*"),))
        values = {p.category_value for p in shops}
        assert len(values) > 1, "wildcard should span multiple shop values"
        assert all(p.category_key == "shop" for p in shops)

    def test_negative_radius_rejected(self, store: PoiStore) -> None:
        with pytest.raises(ValueError):
            store.query_radius(*BEN_THANH, -1)


class TestQueryRadiusMatchesValidatedCounts:
    """Pin the counts cross-checked against the live Overpass API."""

    def test_ben_tre_is_sparse(self, store: PoiStore) -> None:
        # Live Overpass measured 9 cafes; extract agreed. Assert the same order.
        cafes = store.query_radius(*BEN_TRE, 1000, tags=(("amenity", "cafe"),))
        assert 5 <= len(cafes) <= 20

    def test_ben_thanh_is_dense(self, store: PoiStore) -> None:
        cafes = store.query_radius(*BEN_THANH, 1000, tags=(("amenity", "cafe"),))
        assert len(cafes) > 100, "District 1 must be dense — refutes 'no competitors'"

    def test_nearest_competitor_is_close_in_district_1(self, store: PoiStore) -> None:
        pois = store.query_radius(*BEN_THANH, 1000, tags=FOOD_TAGS)
        assert pois[0].distance_m < 200


class TestZoneDetection:
    """Residential landuse zones found by edge (bbox), the user's core ask."""

    def test_vinhomes_has_residential_zones(self, store: PoiStore) -> None:
        zones = store.query_radius(*VINHOMES_OCEAN_PARK, 1000, tags=(("landuse", "residential"),))
        assert zones, "Vinhomes Ocean Park must resolve as a residential area"

    def test_vinhomes_has_eateries(self, store: PoiStore) -> None:
        eateries = store.query_radius(*VINHOMES_OCEAN_PARK, 1000, tags=FOOD_TAGS)
        names = {p.name for p in eateries if p.name}
        assert eateries
        assert any("Coffee" in n or "Phở" in n or "Pho" in n for n in names)


class TestPoiHelpers:
    def test_google_maps_url_is_wellformed(self, store: PoiStore) -> None:
        poi = store.query_radius(*BEN_THANH, 1000, tags=FOOD_TAGS, limit=1)[0]
        url = poi.google_maps_url()
        assert url.startswith("https://www.google.com/maps/search/?api=1&query=")

    def test_chain_flag_reflects_brand(self, store: PoiStore) -> None:
        pois = store.query_radius(*BEN_THANH, 1000, tags=FOOD_TAGS)
        assert any(p.is_chain for p in pois), "District 1 has branded chains"


class TestMetadataAndPopulation:
    def test_metadata_has_source(self, store: PoiStore) -> None:
        meta = store.metadata()
        assert "OpenStreetMap" in meta["source_name"]
        assert meta["schema_version"]

    def test_source_accessed_at_parses(self, store: PoiStore) -> None:
        assert store.source_accessed_at().year >= 2026

    def test_nearest_population_place(self, store: PoiStore) -> None:
        places = store.nearest_places_with_population(*BEN_THANH, limit=3)
        assert places
        assert places[0]["population"] > 0
        assert places[0]["distance_km"] <= places[-1]["distance_km"]


def test_missing_db_raises_unavailable(tmp_path) -> None:
    with pytest.raises(PoiDatabaseUnavailableError):
        PoiStore(tmp_path / "does_not_exist.db")


def test_store_is_readonly(store: PoiStore) -> None:
    with pytest.raises(sqlite3.OperationalError):
        store._con.execute("INSERT INTO meta(key, value) VALUES ('x','y')")
