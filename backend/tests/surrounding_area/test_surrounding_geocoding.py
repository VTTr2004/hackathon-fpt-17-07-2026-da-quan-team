"""Geocoding tests with an injected fetch — no network access.

The canned payloads mirror the real Nominatim/Goong responses measured during
design (Chợ Bến Thành, Vinhomes Ocean Park, and the empty result for a
house-number street address).
"""

from __future__ import annotations

import pytest

from app.modules.surrounding_area.providers.geocoding import (
    GoogleGeocodingProvider,
    GoongProvider,
    NominatimProvider,
    geocode,
)

# Real Nominatim shapes.
BEN_THANH_RESPONSE = [
    {
        "lat": "10.7725301",
        "lon": "106.6980365",
        "display_name": "Chợ Bến Thành, Phường Bến Thành, Thủ Đức, Thành phố Hồ Chí Minh, Việt Nam",
        "class": "amenity",
        "type": "marketplace",
        "importance": 0.395,
    }
]
ADMIN_ONLY_RESPONSE = [
    {
        "lat": "10.7756",
        "lon": "106.7019",
        "display_name": "Quận 1, Thành phố Hồ Chí Minh, Việt Nam",
        "class": "boundary",
        "type": "administrative",
        "importance": 0.6,
    }
]


def fetch_returning(payload):
    def _fetch(url, params):
        return payload

    return _fetch


class TestNominatimProvider:
    def test_parses_marketplace(self) -> None:
        provider = NominatimProvider(fetch=fetch_returning(BEN_THANH_RESPONSE))
        candidates = provider.geocode_sync("Chợ Bến Thành")
        assert len(candidates) == 1
        c = candidates[0]
        assert abs(c.lat - 10.7725) < 0.001
        assert abs(c.lon - 106.6980) < 0.001
        assert c.confidence == "high"  # marketplace is a specific place

    def test_admin_area_is_low_confidence(self) -> None:
        provider = NominatimProvider(fetch=fetch_returning(ADMIN_ONLY_RESPONSE))
        candidates = provider.geocode_sync("Quận 1")
        assert candidates[0].confidence == "low"

    def test_empty_response(self) -> None:
        provider = NominatimProvider(fetch=fetch_returning([]))
        assert provider.geocode_sync("123 Lê Lợi Bến Nghé") == []

    def test_skips_malformed_items(self) -> None:
        provider = NominatimProvider(fetch=fetch_returning([{"lat": "x", "lon": "y"}, BEN_THANH_RESPONSE[0]]))
        candidates = provider.geocode_sync("something")
        assert len(candidates) == 1


class TestGoongProvider:
    def test_requires_key(self) -> None:
        from app.modules.surrounding_area.providers.geocoding import GeocodingError

        with pytest.raises(GeocodingError):
            GoongProvider("")

    def test_parses_goong_shape(self) -> None:
        payload = {
            "results": [
                {
                    "formatted_address": "15 Nguyễn Huệ, Quận 1, HCM",
                    "geometry": {"location": {"lat": 10.7743, "lng": 106.7038}},
                }
            ]
        }
        provider = GoongProvider("fake-key", fetch=fetch_returning(payload))
        candidates = provider.geocode_sync("15 Nguyễn Huệ")
        assert candidates[0].lat == 10.7743
        assert candidates[0].lon == 106.7038
        assert candidates[0].provider == "goong"


class TestGoogleGeocodingProvider:
    def test_requires_key(self) -> None:
        from app.modules.surrounding_area.providers.geocoding import GeocodingError

        with pytest.raises(GeocodingError):
            GoogleGeocodingProvider("")

    def test_parses_google_shape(self) -> None:
        payload = {
            "status": "OK",
            "results": [
                {
                    "formatted_address": "Vinhomes Ocean Park, Gia Lâm, Hà Nội, Việt Nam",
                    "geometry": {
                        "location": {"lat": 20.9933, "lng": 105.9543},
                        "location_type": "ROOFTOP",
                    },
                }
            ],
        }
        provider = GoogleGeocodingProvider("fake-key", fetch=fetch_returning(payload))
        candidates = provider.geocode_sync("Vinhomes Ocean Park")
        assert candidates[0].lat == 20.9933
        assert candidates[0].lon == 105.9543
        assert candidates[0].provider == "google_geocoding"
        assert candidates[0].confidence == "high"


class TestGeocodeFacade:
    @pytest.mark.asyncio
    async def test_returns_candidates_and_needs_confirmation(self) -> None:
        result = await geocode("Chợ Bến Thành", nominatim_fetch=fetch_returning(BEN_THANH_RESPONSE))
        assert result.best is not None
        assert result.needs_confirmation is True  # section 4.2 — always

    @pytest.mark.asyncio
    async def test_empty_address_no_candidates(self) -> None:
        result = await geocode("   ", nominatim_fetch=fetch_returning([]))
        assert result.best is None
        assert result.warnings

    @pytest.mark.asyncio
    async def test_unresolved_address_warns_not_raises(self) -> None:
        result = await geocode("123 Lê Lợi Bến Nghé Quận 1", nominatim_fetch=fetch_returning([]))
        assert result.candidates == []
        assert any("không" in w.lower() or "geocode" in w.lower() for w in result.warnings)

    @pytest.mark.asyncio
    async def test_low_confidence_adds_warning(self) -> None:
        result = await geocode("Quận 1", nominatim_fetch=fetch_returning(ADMIN_ONLY_RESPONSE))
        assert any("hành chính" in w or "thấp" in w for w in result.warnings)

    @pytest.mark.asyncio
    async def test_goong_preferred_when_key_present(self) -> None:
        goong_payload = {
            "results": [{"formatted_address": "Goong result", "geometry": {"location": {"lat": 10.77, "lng": 106.70}}}]
        }
        result = await geocode(
            "15 Nguyễn Huệ",
            goong_api_key="fake-key",
            goong_fetch=fetch_returning(goong_payload),
            nominatim_fetch=fetch_returning(BEN_THANH_RESPONSE),
        )
        assert result.provider == "goong"

    @pytest.mark.asyncio
    async def test_google_preferred_when_key_present(self) -> None:
        google_payload = {
            "status": "OK",
            "results": [
                {
                    "formatted_address": "Google result",
                    "geometry": {"location": {"lat": 10.78, "lng": 106.71}, "location_type": "ROOFTOP"},
                }
            ],
        }
        goong_payload = {
            "results": [{"formatted_address": "Goong result", "geometry": {"location": {"lat": 10.77, "lng": 106.70}}}]
        }
        result = await geocode(
            "15 Nguyễn Huệ",
            google_geocoding_api_key="fake-google-key",
            google_fetch=fetch_returning(google_payload),
            goong_api_key="fake-goong-key",
            goong_fetch=fetch_returning(goong_payload),
            nominatim_fetch=fetch_returning(BEN_THANH_RESPONSE),
        )
        assert result.provider == "google_geocoding"

    @pytest.mark.asyncio
    async def test_falls_back_to_goong_when_google_fails(self) -> None:
        def failing_google(url, params):
            raise RuntimeError("google down")

        goong_payload = {
            "results": [{"formatted_address": "Goong result", "geometry": {"location": {"lat": 10.77, "lng": 106.70}}}]
        }
        result = await geocode(
            "15 Nguyễn Huệ",
            google_geocoding_api_key="fake-google-key",
            google_fetch=failing_google,
            goong_api_key="fake-goong-key",
            goong_fetch=fetch_returning(goong_payload),
            nominatim_fetch=fetch_returning(BEN_THANH_RESPONSE),
        )
        assert result.provider == "goong"
        assert any("google" in w.lower() for w in result.warnings)

    @pytest.mark.asyncio
    async def test_falls_back_to_nominatim_when_goong_fails(self) -> None:
        def failing(url, params):
            raise RuntimeError("goong down")

        result = await geocode(
            "Chợ Bến Thành",
            goong_api_key="fake-key",
            goong_fetch=failing,
            nominatim_fetch=fetch_returning(BEN_THANH_RESPONSE),
        )
        assert result.provider == "nominatim"
        assert any("goong" in w.lower() for w in result.warnings)

    @pytest.mark.asyncio
    async def test_to_dict_serialises(self) -> None:
        result = await geocode("Chợ Bến Thành", nominatim_fetch=fetch_returning(BEN_THANH_RESPONSE))
        data = result.to_dict()
        assert data["needs_confirmation"] is True
        assert data["candidates"][0]["lat"]
