"""Google Places enrichment tests. The provider is dormant without a key; with a
mocked fetch we verify parsing and that prices are never fabricated."""

from __future__ import annotations

from dataclasses import dataclass

from app.modules.surrounding_area.analyzer import SurroundingAreaAnalyzer
from app.modules.surrounding_area.providers.places import enrich_place, is_configured, lookup_place


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

    def test_lookup_exposes_provider_status_warning(self) -> None:
        result = lookup_place(
            "Highlands",
            10.77,
            106.70,
            api_key="k",
            fetch=fetch_returning({"status": "REQUEST_DENIED", "error_message": "API key blocked"}),
        )

        assert result.enrichment is None
        assert result.warning is not None
        assert "REQUEST_DENIED" in result.warning

    def test_lookup_biases_around_supplied_coordinate(self) -> None:
        seen = {}

        def capture_fetch(url, params):
            seen.update(params)
            return {
                "status": "OK",
                "candidates": [
                    {
                        "name": "STG coffee",
                        "rating": 4.1,
                        "geometry": {"location": {"lat": 20.995, "lng": 105.944}},
                    }
                ],
            }

        result = lookup_place("STG coffee", 20.995, 105.944, api_key="k", fetch=capture_fetch)

        assert result.enrichment is not None
        assert seen["locationbias"] == "circle:200@20.995,105.944"

    def test_lookup_fetches_details_reviews_when_place_id_is_available(self) -> None:
        seen_urls = []

        def dispatch_fetch(url, params):
            seen_urls.append(url)
            if "findplacefromtext" in url:
                return {
                    "status": "OK",
                    "candidates": [
                        {
                            "place_id": "place-123",
                            "name": "Highlands Coffee",
                            "rating": 4.0,
                            "geometry": {"location": {"lat": 20.993, "lng": 105.946}},
                        }
                    ],
                }
            return {
                "status": "OK",
                "result": {
                    "name": "Highlands Coffee Ocean Park",
                    "rating": 4.4,
                    "user_ratings_total": 827,
                    "price_level": 2,
                    "geometry": {"location": {"lat": 20.9932, "lng": 105.946}},
                    "reviews": [
                        {
                            "author_name": "Analyst",
                            "rating": 5,
                            "relative_time_description": "a month ago",
                            "text": "Good location and steady traffic.",
                            "time": 1780000000,
                        }
                    ],
                },
            }

        result = lookup_place("Highlands", 20.993, 105.946, api_key="k", fetch=dispatch_fetch)

        assert result.enrichment is not None
        assert result.enrichment.place_id == "place-123"
        assert result.enrichment.name == "Highlands Coffee Ocean Park"
        assert result.enrichment.rating == 4.4
        assert result.enrichment.price_level == 2
        assert result.enrichment.user_ratings_total == 827
        assert result.enrichment.reviews[0]["text"] == "Good location and steady traffic."
        assert len(seen_urls) == 2

    def test_analyzer_enrichment_uses_each_poi_coordinate(self, monkeypatch) -> None:
        seen: list[tuple[str, float, float]] = []

        @dataclass
        class FakeLookup:
            enrichment = None
            warning = None

        class FakePoi:
            name = "STG coffee"
            category_value = "cafe"
            distance_m = 642
            is_chain = False
            lat = 20.995
            lon = 105.944

            def google_maps_url(self):
                return "https://maps.google.com/?q=STG"

        def fake_lookup(name, lat, lon):
            seen.append((name, lat, lon))
            return FakeLookup()

        monkeypatch.setattr("app.modules.surrounding_area.analyzer.places_is_configured", lambda: True)
        monkeypatch.setattr("app.modules.surrounding_area.analyzer.lookup_place", fake_lookup)

        SurroundingAreaAnalyzer._places_enrichment([FakePoi()])

        assert seen == [("STG coffee", 20.995, 105.944)]
