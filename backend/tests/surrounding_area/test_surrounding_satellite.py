from __future__ import annotations

from app.modules.surrounding_area.providers.satellite import fetch_satellite_context


def test_satellite_context_parses_stac_scene() -> None:
    def fake_fetch(url, body, timeout_s):
        assert "stac.dataspace.copernicus.eu" in url
        assert body["collections"] == ["sentinel-2-l2a"]
        assert body["bbox"]
        assert timeout_s > 0
        return {
            "features": [
                {
                    "id": "S2A_TEST",
                    "collection": "sentinel-2-l2a",
                    "properties": {"datetime": "2026-07-01T03:30:00Z", "eo:cloud_cover": 12.5, "gsd": 10},
                    "assets": {
                        "thumbnail": {"href": "https://example.test/thumb.jpg", "roles": ["thumbnail"]},
                        "visual": {"href": "https://example.test/visual.jp2", "roles": ["visual"]},
                    },
                    "links": [{"rel": "self", "href": "https://example.test/item"}],
                }
            ]
        }

    context = fetch_satellite_context(20.9943, 105.9485, radius_m=750, fetch=fake_fetch)

    assert context["status"] == "clear_recent_scene"
    assert context["best_scene"]["id"] == "S2A_TEST"
    assert context["best_scene"]["cloud_cover"] == 12.5
    assert context["best_scene"]["thumbnail_url"] == "https://example.test/thumb.jpg"
    assert context["best_scene"]["visual_url"] == "https://example.test/visual.jp2"
    assert context["warnings"] == []


def test_satellite_context_degrades_on_fetch_error() -> None:
    def failing_fetch(url, body, timeout_s):
        raise TimeoutError("catalogue timeout")

    context = fetch_satellite_context(10.7725, 106.6980, fetch=failing_fetch)

    assert context["status"] == "unavailable"
    assert context["scenes"] == []
    assert context["warnings"]

