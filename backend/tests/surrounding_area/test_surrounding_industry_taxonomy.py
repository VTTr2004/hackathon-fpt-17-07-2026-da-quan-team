import pytest

from app.modules.surrounding_area.tools.industry_taxonomy import (
    DEMAND_TAGS,
    LocationDependency,
    classify_location_dependency,
    fold,
    resolve_competitor_filter,
)


class TestFold:
    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("Nhà hàng", "nha hang"),
            ("Cà phê", "ca phe"),
            ("F&B", "f&b"),
            ("GIÁO DỤC", "giao duc"),
            ("Đồ uống", "do uong"),
        ],
    )
    def test_folds_vietnamese(self, raw: str, expected: str) -> None:
        assert fold(raw) == expected


class TestLocationDependency:
    """Plan step 0: the three dependency buckets."""

    @pytest.mark.parametrize(
        "industry",
        ["F&B", "Chuỗi cà phê", "nhà hàng Nhật", "quán ăn", "coffee shop", "trà sữa", "bakery"],
    )
    def test_food_is_primary(self, industry: str) -> None:
        result = classify_location_dependency(industry)
        assert result.dependency == LocationDependency.PRIMARY
        assert result.matched_profile == "food_beverage"

    @pytest.mark.parametrize(
        "industry",
        ["SaaS", "phần mềm B2B", "fintech", "AI platform", "marketplace", "thương mại điện tử", "blockchain"],
    )
    def test_digital_is_independent(self, industry: str) -> None:
        """The critical case: SaaS must NOT be analysed for location."""
        result = classify_location_dependency(industry)
        assert result.dependency == LocationDependency.INDEPENDENT
        assert result.matched_profile == "digital"

    @pytest.mark.parametrize("industry", ["logistics", "nhà máy sản xuất", "coworking space", "warehouse"])
    def test_logistics_is_supporting(self, industry: str) -> None:
        result = classify_location_dependency(industry)
        assert result.dependency == LocationDependency.SUPPORTING

    @pytest.mark.parametrize("industry", ["gym", "phòng tập yoga", "trung tâm thể hình"])
    def test_fitness_is_primary(self, industry: str) -> None:
        assert classify_location_dependency(industry).dependency == LocationDependency.PRIMARY

    @pytest.mark.parametrize("industry", ["phòng khám", "nhà thuốc", "nha khoa", "spa thẩm mỹ"])
    def test_healthcare_is_primary(self, industry: str) -> None:
        assert classify_location_dependency(industry).matched_profile == "healthcare"

    def test_unknown_defaults_to_primary_not_independent(self) -> None:
        """Wrongly skipping a location business is worse than an extra analysis."""
        result = classify_location_dependency("nghề gì đó lạ")
        assert result.dependency == LocationDependency.PRIMARY
        assert result.matched_profile is None

    @pytest.mark.parametrize("industry", [None, "", "   "])
    def test_missing_industry_defaults_to_primary(self, industry: str | None) -> None:
        result = classify_location_dependency(industry)
        assert result.dependency == LocationDependency.PRIMARY

    def test_result_carries_human_readable_reason(self) -> None:
        result = classify_location_dependency("F&B")
        assert result.reason
        assert result.matched_keyword in fold("F&B")

    def test_determinism(self) -> None:
        assert classify_location_dependency("cà phê") == classify_location_dependency("cà phê")


class TestExplicitOverride:
    """The analyst / profile can state location-dependency directly (plan §5:
    'chuyên viên sửa được')."""

    def test_explicit_independent_overrides_food_industry(self) -> None:
        # A cloud/delivery-only kitchen: F&B industry but analyst says not location-dependent.
        result = classify_location_dependency("nhà hàng", explicit="independent")
        assert result.dependency == LocationDependency.INDEPENDENT

    def test_explicit_primary_overrides_digital(self) -> None:
        result = classify_location_dependency("SaaS", explicit=LocationDependency.PRIMARY)
        assert result.dependency == LocationDependency.PRIMARY

    def test_invalid_explicit_falls_back_to_industry(self) -> None:
        result = classify_location_dependency("SaaS", explicit="garbage")
        assert result.dependency == LocationDependency.INDEPENDENT  # from industry

    def test_none_explicit_uses_industry(self) -> None:
        result = classify_location_dependency("cà phê", explicit=None)
        assert result.dependency == LocationDependency.PRIMARY


class TestCompetitorFilter:
    def test_food_competitor_tags_include_cafe_and_restaurant(self) -> None:
        cf = resolve_competitor_filter("chuỗi cà phê")
        assert ("amenity", "cafe") in cf.competitor_tags
        assert ("amenity", "restaurant") in cf.competitor_tags
        # shop=coffee too: brand tags collapse outside big cities, so cast wide.
        assert ("shop", "coffee") in cf.competitor_tags

    def test_digital_has_no_competitor_tags(self) -> None:
        cf = resolve_competitor_filter("SaaS")
        assert cf.competitor_tags == ()

    def test_unknown_industry_has_no_competitor_tags(self) -> None:
        cf = resolve_competitor_filter("ngành lạ")
        assert cf.competitor_tags == ()
        assert cf.profile_key is None

    def test_demand_tags_present_for_all(self) -> None:
        cf = resolve_competitor_filter("nhà hàng")
        assert "residential" in cf.demand_tags
        assert "office" in cf.demand_tags
        assert "school" in cf.demand_tags


class TestDemandTagsMatchExtractedKeys:
    """DEMAND_TAGS must only reference keys extract_poi.py actually stores."""

    def test_only_extracted_keys(self) -> None:
        from app.modules.surrounding_area.scripts.extract_poi import POI_KEYS

        for proxy, tags in DEMAND_TAGS.items():
            for key, _value in tags:
                assert key in POI_KEYS, f"{proxy} references un-extracted key '{key}'"

    def test_residential_uses_landuse(self) -> None:
        assert ("landuse", "residential") in DEMAND_TAGS["residential"]
