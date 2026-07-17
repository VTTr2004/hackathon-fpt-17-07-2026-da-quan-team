"""Google Places enrichment tests. The provider is dormant without a key; with a
mocked fetch we verify parsing and that prices are never fabricated."""

from __future__ import annotations

from app.modules.surrounding_area.providers.places import enrich_place, is_configured


def fetch_returning(payload):
    def _fetch(url, params):
        return payload

    return _fetch


class TestConfiguration:
    def test_not_configured_without_key(self) -> None:
        assert is_configured(api_key="") is False

    def test_configured_with_key(self) -> None:
        assert is_configured(api_key="something") is True


class TestEnrichment:
    def test_returns_none_without_key(self) -> None:
        assert enrich_place("Highlands", 10.77, 106.70, api_key="") is None

    def test_parses_rating_and_price(self) -> None:
        payload = {
            "candidates": [
                {
                    "name": "Highlands Coffee",
                    "rating": 4.3,
                    "user_ratings_total": 512,
                    "price_level": 2,
                    "geometry": {"location": {"lat": 10.7725, "lng": 106.698}},
                }
            ]
        }
        result = enrich_place("Highlands", 10.77, 106.70, api_key="k", fetch=fetch_returning(payload))
        assert result is not None
        assert result.rating == 4.3
        assert result.price_level == 2
        assert result.price_label is not None

    def test_missing_price_stays_none_not_fabricated(self) -> None:
        payload = {
            "candidates": [{"name": "Quán cóc", "rating": 4.0, "geometry": {"location": {"lat": 10.0, "lng": 106.0}}}]
        }
        result = enrich_place("Quán cóc", 10.0, 106.0, api_key="k", fetch=fetch_returning(payload))
        assert result.price_level is None
        assert result.price_label is None  # never invented

    def test_no_candidates_returns_none(self) -> None:
        result = enrich_place("Nowhere", 10.0, 106.0, api_key="k", fetch=fetch_returning({"candidates": []}))
        assert result is None

    def test_fetch_failure_returns_none(self) -> None:
        def failing(url, params):
            raise RuntimeError("api down")

        assert enrich_place("X", 10.0, 106.0, api_key="k", fetch=failing) is None
