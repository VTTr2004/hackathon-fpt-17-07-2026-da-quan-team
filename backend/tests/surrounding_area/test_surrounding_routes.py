"""HTTP tests for the surrounding-area helper endpoints, driven through the ASGI
app with an injected geocode fetch — no network, no database."""

from __future__ import annotations

import httpx
import pytest

from app.modules.surrounding_area.data_store.poi_store import DEFAULT_DB_PATH

pytestmark = pytest.mark.asyncio


def _make_client():
    # Build the ASGI app but skip DB table creation by hitting only surrounding routes.
    from fastapi import FastAPI

    from app.api.routes.surrounding import router

    app = FastAPI()
    app.include_router(router)
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")


class TestGeocodeEndpoint:
    async def test_geocode_empty_address_rejected(self) -> None:
        async with _make_client() as client:
            resp = await client.post("/surrounding/geocode", json={"address": ""})
        assert resp.status_code == 422  # min_length=1

    async def test_geocode_returns_needs_confirmation(self, monkeypatch) -> None:
        payload = [
            {
                "lat": "10.7725",
                "lon": "106.6980",
                "display_name": "Chợ Bến Thành",
                "class": "amenity",
                "type": "marketplace",
            }
        ]

        async def fake_geocode(address, **kwargs):
            from app.modules.surrounding_area.providers.geocoding import geocode as real

            return await real(address, nominatim_fetch=lambda u, p: payload)

        monkeypatch.setattr("app.api.routes.surrounding.geocode", fake_geocode)
        async with _make_client() as client:
            resp = await client.post("/surrounding/geocode", json={"address": "Chợ Bến Thành"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["needs_confirmation"] is True
        assert body["candidates"][0]["lat"] == 10.7725

    async def test_geocode_rate_limited(self, monkeypatch) -> None:
        from app.api.routes import surrounding as surrounding_route
        from app.modules.surrounding_area.providers.geocoding import GeocodeResult

        async def fake_geocode(address):
            return GeocodeResult(query=address, candidates=[], provider="fake")

        monkeypatch.setattr(surrounding_route, "_geocode_limiter", surrounding_route._RateLimiter(1, 60))
        monkeypatch.setattr(surrounding_route, "geocode", fake_geocode)

        async with _make_client() as client:
            ok = await client.post("/surrounding/geocode", json={"address": "Vinhomes Ocean Park"})
            limited = await client.post("/surrounding/geocode", json={"address": "Vinhomes Ocean Park"})

        assert ok.status_code == 200
        assert limited.status_code == 429

    async def test_map_rate_limited(self, monkeypatch) -> None:
        from app.api.routes import surrounding as surrounding_route

        monkeypatch.setattr(surrounding_route, "_map_limiter", surrounding_route._RateLimiter(1, 60))
        monkeypatch.setattr(surrounding_route, "get_poi_store", lambda: object())
        monkeypatch.setattr(
            surrounding_route,
            "build_map_payload",
            lambda store, lat, lon, industry=None, radius_m=1000: {
                "center": {"lat": lat, "lon": lon},
                "eateries": [],
                "residential": [],
                "competitors": [],
            },
        )

        async with _make_client() as client:
            ok = await client.get("/surrounding/map", params={"lat": 10.7725, "lon": 106.698})
            limited = await client.get("/surrounding/map", params={"lat": 10.7725, "lon": 106.698})

        assert ok.status_code == 200
        assert limited.status_code == 429

    async def test_satellite_endpoint_returns_context(self, monkeypatch) -> None:
        from app.api.routes import surrounding as surrounding_route

        monkeypatch.setattr(
            surrounding_route,
            "fetch_satellite_context",
            lambda lat, lon, radius_m=1000, days=180: {
                "provider": "fake",
                "radius_m": radius_m,
                "days": days,
                "status": "clear_recent_scene",
                "best_scene": {"id": "S2A_TEST", "cloud_cover": 8},
                "scenes": [{"id": "S2A_TEST", "cloud_cover": 8}],
                "warnings": [],
            },
        )

        async with _make_client() as client:
            resp = await client.get(
                "/surrounding/satellite",
                params={"lat": 20.9943, "lon": 105.9485, "radius_m": 500, "days": 30},
            )

        assert resp.status_code == 200
        body = resp.json()
        assert body["radius_m"] == 500
        assert body["best_scene"]["id"] == "S2A_TEST"


@pytest.mark.skipif(not DEFAULT_DB_PATH.exists(), reason="poi.db not built")
class TestMapEndpoint:
    async def test_map_returns_pois(self) -> None:
        async with _make_client() as client:
            resp = await client.get("/surrounding/map", params={"lat": 10.7725, "lon": 106.6980, "industry": "cà phê"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["center"] == {"lat": 10.7725, "lon": 106.698}
        assert body["eateries"]
        assert all("google_maps_url" in e for e in body["eateries"])
        assert body["competitors"]  # cà phê has competitor tags

    async def test_map_rejects_bad_coords(self) -> None:
        async with _make_client() as client:
            resp = await client.get("/surrounding/map", params={"lat": 200, "lon": 106})
        assert resp.status_code == 422

    async def test_map_vinhomes_has_residential(self) -> None:
        async with _make_client() as client:
            resp = await client.get("/surrounding/map", params={"lat": 20.9943, "lon": 105.9485})
        body = resp.json()
        assert body["residential"]
