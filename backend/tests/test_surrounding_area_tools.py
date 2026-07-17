from app.modules.surrounding_area.tools import haversine_km, score_location


def test_haversine_same_location() -> None:
    assert haversine_km(21.0285, 105.8542, 21.0285, 105.8542) == 0


def test_location_score() -> None:
    result = score_location({"access": 80, "demand": 60}, {"access": 0.5, "demand": 0.5})
    assert result["score"] == 70
