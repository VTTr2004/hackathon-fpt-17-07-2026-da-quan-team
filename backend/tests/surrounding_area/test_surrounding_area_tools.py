import pytest

from app.modules.surrounding_area.tools import bounding_box, haversine_km, score_location


class TestHaversine:
    def test_same_location(self) -> None:
        assert haversine_km(21.0285, 105.8542, 21.0285, 105.8542) == 0

    def test_known_distance_hanoi_to_hcmc(self) -> None:
        # Hoan Kiem Lake -> Ben Thanh Market. Great-circle reference ~1141 km.
        distance = haversine_km(21.0287, 105.8524, 10.7725, 106.6980)
        assert 1135 <= distance <= 1150

    def test_one_degree_latitude_is_about_111km(self) -> None:
        assert 110.5 <= haversine_km(10.0, 106.0, 11.0, 106.0) <= 111.5

    def test_symmetric(self) -> None:
        a = haversine_km(10.7725, 106.6980, 10.7758, 106.7050)
        b = haversine_km(10.7758, 106.7050, 10.7725, 106.6980)
        assert a == b

    def test_short_distance_precision(self) -> None:
        # ~71 m apart: the nearest-competitor case the module must resolve.
        distance_m = haversine_km(10.77250, 106.69800, 10.77300, 106.69850) * 1000
        assert 70 <= distance_m <= 80

    @pytest.mark.parametrize(
        "args",
        [(91.0, 0.0, 0.0, 0.0), (0.0, 181.0, 0.0, 0.0), (0.0, 0.0, -91.0, 0.0), (0.0, 0.0, 0.0, -181.0)],
    )
    def test_rejects_out_of_range(self, args: tuple[float, float, float, float]) -> None:
        with pytest.raises(ValueError):
            haversine_km(*args)


class TestBoundingBox:
    def test_box_encloses_circle(self) -> None:
        lat, lon, radius = 10.7725, 106.6980, 1.0
        min_lat, max_lat, min_lon, max_lon = bounding_box(lat, lon, radius)
        # Every point exactly `radius` away in the 4 cardinal directions must be inside.
        assert min_lat < lat - radius / 111.33
        assert max_lat > lat + radius / 111.33
        assert min_lon < lon
        assert max_lon > lon

    def test_box_never_produces_false_negatives(self) -> None:
        """Any point within the radius must fall inside the box."""
        from math import cos, radians

        lat, lon, radius = 10.7725, 106.6980, 2.0
        min_lat, max_lat, min_lon, max_lon = bounding_box(lat, lon, radius)
        for bearing_lat, bearing_lon in [(1, 0), (-1, 0), (0, 1), (0, -1), (0.7, 0.7), (-0.7, -0.7)]:
            p_lat = lat + bearing_lat * radius / 111.32
            p_lon = lon + bearing_lon * radius / (111.32 * cos(radians(lat)))
            if haversine_km(lat, lon, p_lat, p_lon) <= radius:
                assert min_lat <= p_lat <= max_lat
                assert min_lon <= p_lon <= max_lon

    def test_zero_radius(self) -> None:
        min_lat, max_lat, min_lon, max_lon = bounding_box(10.0, 106.0, 0.0)
        assert min_lat == max_lat == 10.0
        assert min_lon == max_lon == 106.0

    def test_pole_does_not_wrap(self) -> None:
        min_lat, max_lat, min_lon, max_lon = bounding_box(89.9, 100.0, 50.0)
        assert max_lat <= 90.0
        assert (min_lon, max_lon) == (-180.0, 180.0)

    def test_rejects_negative_radius(self) -> None:
        with pytest.raises(ValueError):
            bounding_box(10.0, 106.0, -1.0)


class TestScoreLocationHappyPath:
    def test_all_metrics_present(self) -> None:
        result = score_location({"access": 80, "demand": 60}, {"access": 0.5, "demand": 0.5})
        assert result["score"] == 70
        assert result["status"] == "complete"
        assert result["missing_metrics"] == []
        assert result["covered_weight"] == 1.0
        assert result["warnings"] == []

    def test_hand_calculated_weighted_sum(self) -> None:
        # 90*0.4 + 50*0.3 + 40*0.2 + 20*0.1 = 36 + 15 + 8 + 2 = 61
        result = score_location(
            {"customer_density": 90, "accessibility": 50, "supporting_amenities": 40, "competition_balance": 20},
            {"customer_density": 0.4, "accessibility": 0.3, "supporting_amenities": 0.2, "competition_balance": 0.1},
        )
        assert result["score"] == 61.0
        assert result["status"] == "complete"

    def test_measured_zero_is_a_real_observation(self) -> None:
        result = score_location({"access": 0, "demand": 100}, {"access": 0.5, "demand": 0.5})
        assert result["score"] == 50
        assert result["status"] == "complete"
        assert result["missing_metrics"] == []


class TestScoreLocationMissingIsNotZero:
    """Section 7.2: a metric that was not measured must never be scored as 0."""

    def test_missing_metric_is_not_silently_zero(self) -> None:
        # The bug: absent 'demand' used to become 0 -> score 40, status complete.
        result = score_location({"access": 80}, {"access": 0.5, "demand": 0.5})
        assert result["score"] != 40, "regression: missing metric was coerced to 0"
        assert result["status"] != "complete"
        assert "demand" in result["missing_metrics"]

    def test_explicit_none_is_missing_not_zero(self) -> None:
        result = score_location({"access": 80, "demand": None}, {"access": 0.5, "demand": 0.5})
        assert "demand" in result["missing_metrics"]
        assert "demand" not in result["contributions"]

    def test_missing_metric_emits_warning(self) -> None:
        result = score_location({"access": 80, "demand": None}, {"access": 0.7, "demand": 0.3})
        assert result["warnings"], "a data gap must produce a warning"
        assert any("demand" in w for w in result["warnings"])

    def test_small_gap_renormalises_and_reports_partial(self) -> None:
        # 80 measured over 70% of weight -> 80, but flagged partial + assumption.
        result = score_location({"access": 80, "demand": None}, {"access": 0.7, "demand": 0.3})
        assert result["status"] == "partial"
        assert result["score"] == 80.0
        assert result["covered_weight"] == 0.7
        assert result["assumptions"], "renormalisation must be declared as an assumption"

    def test_heavy_metric_missing_yields_insufficient_data(self) -> None:
        """Section 7.2: missing a heavy weight must not report COMPLETED."""
        result = score_location({"access": 80, "demand": None}, {"access": 0.3, "demand": 0.7})
        assert result["status"] == "insufficient_data"
        assert result["score"] is None

    def test_all_metrics_missing_yields_no_score(self) -> None:
        result = score_location({}, {"access": 0.5, "demand": 0.5})
        assert result["score"] is None
        assert result["status"] == "insufficient_data"
        assert result["covered_weight"] == 0.0

    def test_the_exact_regression_from_the_experiment(self) -> None:
        """The 504-on-offices incident: score 57 + 'high confidence' from no office data.

        Old: 33 + 24 + 0 = 57, status complete, LLM confirmed "office-dense area".
        New: the office gap must be visible and must not read as a measured zero.
        """
        weights = {"residential": 0.33, "retail": 0.24, "van_phong": 0.43}
        result = score_location({"residential": 100, "retail": 100, "van_phong": None}, weights)
        assert result["status"] == "insufficient_data"
        assert result["score"] is None
        assert "van_phong" in result["missing_metrics"]
        assert any("van_phong" in w for w in result["warnings"])


class TestScoreLocationValidation:
    def test_rejects_weights_not_summing_to_one(self) -> None:
        with pytest.raises(ValueError):
            score_location({"a": 50}, {"a": 0.5})

    def test_rejects_empty_weights(self) -> None:
        with pytest.raises(ValueError):
            score_location({"a": 50}, {})

    def test_rejects_negative_weights(self) -> None:
        with pytest.raises(ValueError):
            score_location({"a": 50, "b": 50}, {"a": 1.5, "b": -0.5})

    @pytest.mark.parametrize("bad_value", [-1, 101, 1000])
    def test_rejects_out_of_range_metric(self, bad_value: float) -> None:
        with pytest.raises(ValueError):
            score_location({"a": bad_value}, {"a": 1.0})

    @pytest.mark.parametrize("bad_value", ["80", True, [], {}])
    def test_rejects_non_numeric_metric(self, bad_value: object) -> None:
        """A string or bool is a caller bug, not a data gap — fail loudly."""
        with pytest.raises(ValueError):
            score_location({"a": bad_value}, {"a": 1.0})

    def test_determinism(self) -> None:
        args = ({"a": 73, "b": 21}, {"a": 0.6, "b": 0.4})
        assert score_location(*args) == score_location(*args)
