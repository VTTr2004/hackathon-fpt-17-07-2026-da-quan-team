from __future__ import annotations

from app.modules.surrounding_area.data_store.poi_store import Poi
from app.modules.surrounding_area.tools.poi_metrics import (
    build_area_metrics,
    chain_ratio,
    competitor_density,
    demand_breakdown,
    nearest_competitor,
    supply_demand_ratio,
)


def make_poi(distance_m: float, *, name: str | None = None, brand: str | None = None, value: str = "cafe") -> Poi:
    return Poi(
        osm_type="n",
        osm_id=int(distance_m),
        lat=10.0,
        lon=106.0,
        name=name,
        brand=brand,
        operator=None,
        category_key="amenity",
        category_value=value,
        distance_m=distance_m,
    )


class TestCompetitorDensity:
    def test_rings_are_cumulative(self) -> None:
        pois = [make_poi(100), make_poi(300), make_poi(700), make_poi(900)]
        density = {r.radius_m: r.count for r in competitor_density(pois)}
        assert density == {250: 1, 500: 2, 1000: 4}

    def test_empty_gives_zero_counts(self) -> None:
        density = {r.radius_m: r.count for r in competitor_density([])}
        assert density == {250: 0, 500: 0, 1000: 0}


class TestNearestCompetitor:
    def test_finds_closest(self) -> None:
        result = nearest_competitor([make_poi(300), make_poi(71, name="Cà Phê Tutti Frutti"), make_poi(500)])
        assert result is not None
        assert result.distance_m == 71
        assert result.name == "Cà Phê Tutti Frutti"

    def test_none_when_empty(self) -> None:
        assert nearest_competitor([]) is None


class TestChainRatioIsLowerBound:
    def test_brand_tag_counts_as_chain(self) -> None:
        pois = [make_poi(100, brand="Highlands Coffee"), make_poi(200)]
        result = chain_ratio(pois)
        assert result.chain_count == 1
        assert result.ratio == 0.5

    def test_name_match_catches_untagged_chain(self) -> None:
        # No brand tag, but the name is a known chain — the 7.1 workaround.
        pois = [make_poi(100, name="Highlands Coffee Nguyễn Huệ"), make_poi(200, name="Quán cóc")]
        result = chain_ratio(pois)
        assert result.chain_count == 1

    def test_ratio_is_flagged_lower_bound(self) -> None:
        assert chain_ratio([make_poi(100)]).is_lower_bound is True

    def test_ratio_undefined_when_no_competitors(self) -> None:
        result = chain_ratio([])
        assert result.ratio is None  # not 0.0 — undefined
        assert result.total == 0


class TestDemandMissingIsNotZero:
    def test_missing_component_recorded_not_zeroed(self) -> None:
        demand = demand_breakdown({"residential": 5, "office": None, "school": 2, "transport": 3})
        assert demand.office is None
        assert "office" in demand.missing
        # present_score sums only measured components, does not treat office as 0
        assert demand.present_score() == 10

    def test_all_missing_gives_none_score(self) -> None:
        demand = demand_breakdown({"residential": None, "office": None, "school": None, "transport": None})
        assert demand.present_score() is None
        assert len(demand.missing) == 4

    def test_measured_zero_is_real(self) -> None:
        demand = demand_breakdown({"residential": 0, "office": 0, "school": 0, "transport": 0})
        assert demand.present_score() == 0
        assert demand.missing == []


class TestSupplyDemandRatio:
    def test_normal_ratio(self) -> None:
        demand = demand_breakdown({"residential": 8, "office": 2, "school": 0, "transport": 0})
        result = supply_demand_ratio(20, demand)
        assert result["ratio"] == 2.0  # 20 competitors / 10 demand

    def test_undefined_when_demand_missing(self) -> None:
        demand = demand_breakdown({"residential": None, "office": None, "school": None, "transport": None})
        result = supply_demand_ratio(20, demand)
        assert result["ratio"] is None

    def test_undefined_when_demand_zero_not_infinity(self) -> None:
        """Measured-zero demand must not divide — no infinity, no fake number."""
        demand = demand_breakdown({"residential": 0, "office": 0, "school": 0, "transport": 0})
        result = supply_demand_ratio(20, demand)
        assert result["ratio"] is None
        assert "cung/cầu" in result["note"]


class TestBuildAreaMetrics:
    def test_full_bundle(self) -> None:
        competitors = [
            make_poi(71, name="Cà Phê Tutti Frutti"),
            make_poi(120, brand="Highlands Coffee"),
            make_poi(400, value="restaurant"),
            make_poi(900),
        ]
        metrics = build_area_metrics(
            industry_profile="food_beverage",
            competitors=competitors,
            demand_counts={"residential": 6, "office": 3, "school": 1, "transport": 2},
        )
        assert metrics.nearest_competitor.distance_m == 71
        assert {r.radius_m: r.count for r in metrics.competitor_density} == {250: 2, 500: 3, 1000: 4}
        assert metrics.chain_ratio.chain_count == 1
        assert metrics.competitor_category_mix["cafe"] == 3
        assert metrics.to_dict()["industry_profile"] == "food_beverage"

    def test_missing_demand_produces_warning(self) -> None:
        metrics = build_area_metrics(
            industry_profile="food_beverage",
            competitors=[make_poi(100)],
            demand_counts={"residential": 5, "office": None, "school": None, "transport": None},
        )
        assert any("office" in w for w in metrics.warnings)

    def test_serialisation_roundtrip(self) -> None:
        metrics = build_area_metrics(
            industry_profile="retail",
            competitors=[make_poi(100)],
            demand_counts={"residential": 1, "office": 1, "school": 1, "transport": 1},
        )
        data = metrics.to_dict()
        assert isinstance(data["competitor_density"], list)
        assert isinstance(data["chain_ratio"], dict)
