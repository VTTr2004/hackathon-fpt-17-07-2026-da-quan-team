"""End-to-end analyzer tests — the mandatory acceptance scenarios (plan section 9).

Run against the real poi.db. The most important assertion in the whole module is
`test_bien_hoa_does_not_fabricate_opportunity`: the system must say "I don't
know" rather than reward a gap in the map.
"""

from __future__ import annotations

import pytest

from app.modules.surrounding_area.analyzer import SurroundingAreaAnalyzer
from app.modules.surrounding_area.data_store.poi_store import DEFAULT_DB_PATH, get_poi_store
from app.schemas.common import AnalysisModule, AnalysisStatus

pytestmark = [
    pytest.mark.skipif(not DEFAULT_DB_PATH.exists(), reason="poi.db not built"),
    pytest.mark.asyncio,
]

DISTRICT_1 = {"lat": 10.7725, "lon": 106.6980}
BIEN_HOA = {"lat": 10.9450, "lon": 106.8240}
VINHOMES = {"lat": 20.9943, "lon": 105.9485}

NO_GEMINI = {"use_gemini": False}


@pytest.fixture
def analyzer() -> SurroundingAreaAnalyzer:
    return SurroundingAreaAnalyzer()


class TestLocationDependency:
    async def test_saas_is_not_applicable_with_no_score(self, analyzer) -> None:
        report = await analyzer.analyze({"industry": "SaaS B2B fintech platform"}, [], NO_GEMINI)
        assert report.status == AnalysisStatus.NOT_APPLICABLE
        assert report.score is None
        assert report.module == AnalysisModule.SURROUNDING_AREA

    async def test_marketplace_is_not_applicable(self, analyzer) -> None:
        report = await analyzer.analyze({"industry": "AI marketplace"}, [], NO_GEMINI)
        assert report.status == AnalysisStatus.NOT_APPLICABLE


class TestMissingCoordinates:
    async def test_missing_coords_is_insufficient_not_not_applicable(self, analyzer) -> None:
        """Plan section 7.3: no coordinates is a data gap, not 'not applicable'."""
        report = await analyzer.analyze({"industry": "quán cà phê"}, [], NO_GEMINI)
        assert report.status == AnalysisStatus.INSUFFICIENT_DATA
        assert report.status != AnalysisStatus.NOT_APPLICABLE
        assert "location.lat" in report.missing_data


class TestDistrict1RefutesAbsence:
    async def test_no_competitor_claim_is_refuted_with_numbers(self, analyzer) -> None:
        facts = {
            "industry": "chuỗi cà phê",
            "location": {**DISTRICT_1, "claims": ["Chưa có đối thủ trực tiếp trong bán kính 500m"]},
        }
        report = await analyzer.analyze(facts, [], NO_GEMINI)
        assert report.status == AnalysisStatus.COMPLETED
        # The absence claim must be refuted, with a concrete competitor count/distance.
        absence = next(f for f in report.findings if "đối thủ" in f.title.lower() or "BÁC BỎ" in f.title)
        assert "BÁC BỎ" in absence.title
        verdicts = report.details["verdicts"]["claims"]
        assert verdicts[0]["verdict"] == "bac_bo"
        assert verdicts[0]["evidence"]

    async def test_district_1_has_a_numeric_score(self, analyzer) -> None:
        facts = {"industry": "cà phê", "location": DISTRICT_1}
        report = await analyzer.analyze(facts, [], NO_GEMINI)
        assert report.score is not None
        assert 0 <= report.score <= 100


class TestBienHoaHonesty:
    async def test_bien_hoa_does_not_fabricate_opportunity(self, analyzer) -> None:
        """THE critical test: a thin-map area must return INSUFFICIENT_DATA and must
        NOT conclude 'not saturated / good opportunity'."""
        facts = {
            "industry": "quán cà phê",
            "location": {**BIEN_HOA, "claims": ["Khu vực chưa bão hòa, cơ hội tốt"]},
        }
        report = await analyzer.analyze(facts, [], NO_GEMINI)
        assert report.status == AnalysisStatus.INSUFFICIENT_DATA
        assert report.score is None
        # The saturation claim must be 'chưa đủ thông tin', never confirmed.
        verdicts = report.details["verdicts"]["claims"]
        assert verdicts[0]["verdict"] == "chua_du_thong_tin"
        # A thin-map risk must be surfaced.
        assert any("mỏng" in r or "LỖ HỔNG" in r or "bão hòa" in r for r in report.risks)


class TestPriceClaim:
    async def test_rent_price_always_insufficient(self, analyzer) -> None:
        facts = {
            "industry": "nhà hàng",
            "location": {**DISTRICT_1, "claims": ["Giá thuê mặt bằng khu này rất rẻ"]},
        }
        report = await analyzer.analyze(facts, [], NO_GEMINI)
        price_verdict = report.details["verdicts"]["claims"][0]
        assert price_verdict["verdict"] == "chua_du_thong_tin"
        assert price_verdict["claim_type"] == "price"


class TestPartialOnQueryFailure:
    async def test_broken_subquery_yields_partial_not_completed(self, analyzer, monkeypatch) -> None:
        """Plan section 7.2: a failed POI query -> PARTIAL + warning, never a silent 0."""
        real = get_poi_store()

        class FaultyStore:
            def __init__(self, inner):
                self._inner = inner

            def query_radius(self, lat, lon, radius, *, tags=None, limit=None):
                # Break exactly the office demand proxy in an otherwise good area.
                if tags and ("office", "*") in tags:
                    raise RuntimeError("simulated OSM query 504")
                return self._inner.query_radius(lat, lon, radius, tags=tags, limit=limit)

            def __getattr__(self, name):
                return getattr(self._inner, name)

        monkeypatch.setattr("app.modules.surrounding_area.analyzer.get_poi_store", lambda: FaultyStore(real))
        facts = {"industry": "cà phê", "location": DISTRICT_1}
        report = await analyzer.analyze(facts, [], NO_GEMINI)
        assert report.status == AnalysisStatus.PARTIAL
        assert "demand:office" in report.missing_data
        # The failure must show up as a tool warning somewhere.
        all_warnings = " ".join(w for tc in report.tool_calls for w in tc.warnings)
        assert "office" in all_warnings or "504" in all_warnings


class TestDirectInputs:
    async def test_explicit_dependency_override_makes_saas_run(self, analyzer) -> None:
        """Analyst says a 'SaaS'-labelled startup actually has a physical store."""
        facts = {
            "industry": "SaaS",
            "location_dependency": "primary",
            "location": DISTRICT_1,
        }
        report = await analyzer.analyze(facts, [], NO_GEMINI)
        assert report.status != AnalysisStatus.NOT_APPLICABLE

    async def test_depends_on_surrounding_customers_flag(self, analyzer) -> None:
        facts = {
            "industry": "dịch vụ lạ",
            "location": {**DISTRICT_1, "depends_on_surrounding_customers": True},
        }
        report = await analyzer.analyze(facts, [], NO_GEMINI)
        assert report.status != AnalysisStatus.NOT_APPLICABLE

    async def test_location_from_analysis_options(self, analyzer) -> None:
        """Frontend can pass confirmed coords in options after the geocode gate."""
        facts = {"industry": "cà phê"}  # no saved location
        options = {"use_gemini": False, "location": {**DISTRICT_1, "claims": ["Chưa có đối thủ 500m"]}}
        report = await analyzer.analyze(facts, [], options)
        assert report.status == AnalysisStatus.COMPLETED
        assert report.details["verdicts"]["claims"][0]["verdict"] == "bac_bo"

    async def test_location_profile_echoed_including_stated_rent(self, analyzer) -> None:
        """The startup's own rent is echoed as a known fact, not treated as a market rate."""
        facts = {
            "industry": "cà phê",
            "location": {
                **DISTRICT_1,
                "type": "cửa hàng",
                "tenure": "thuê",
                "rent_cost": 30_000_000,
                "area_m2": 60,
                "known_competitors": ["Highlands kế bên"],
            },
        }
        report = await analyzer.analyze(facts, [], NO_GEMINI)
        profile = report.details["location_profile"]
        assert profile["stated_rent"] == 30_000_000
        assert profile["type"] == "cửa hàng"
        assert profile["known_competitors"] == ["Highlands kế bên"]

    async def test_profile_aliases_are_normalized(self, analyzer) -> None:
        facts = {
            "industry": "cafe",
            "location": DISTRICT_1,
            "location_type": "cua hang",
            "target_customer_radius_m": 500,
            "known_nearby_competitors": ["Highlands"],
        }
        report = await analyzer.analyze(facts, [], NO_GEMINI)
        profile = report.details["location_profile"]
        assert profile["type"] == "cua hang"
        assert profile["target_radius_m"] == 500
        assert profile["known_competitors"] == ["Highlands"]

    async def test_claims_can_be_extracted_from_documents(self, analyzer) -> None:
        docs = [{"filename": "pitch.txt", "text": "Khu vực chưa có đối thủ trực tiếp trong 500m."}]
        facts = {"industry": "cafe", "location": DISTRICT_1}
        report = await analyzer.analyze(facts, docs, NO_GEMINI)
        verdicts = report.details["verdicts"]["claims"]
        assert verdicts
        assert "đối thủ" in verdicts[0]["claim"].lower()


class TestMapPayload:
    async def test_map_payload_present_for_vinhomes(self, analyzer) -> None:
        """The user's example: the report must carry residential + eateries for the map."""
        facts = {"industry": "quán ăn", "location": VINHOMES}
        report = await analyzer.analyze(facts, [], NO_GEMINI)
        map_data = report.details["map"]
        assert map_data["eateries"], "Vinhomes must have eateries on the map"
        assert map_data["residential"], "Vinhomes must show residential zones"
        assert all("google_maps_url" in e for e in map_data["eateries"])

    async def test_satellite_context_is_included_when_requested(self, analyzer, monkeypatch) -> None:
        def fake_satellite(lat, lon, radius_m=1000):
            return {
                "provider": "fake",
                "source_url": "https://example.test/sentinel",
                "radius_m": radius_m,
                "days": 180,
                "status": "clear_recent_scene",
                "best_scene": {"id": "S2A_TEST", "cloud_cover": 6},
                "scenes": [{"id": "S2A_TEST", "cloud_cover": 6}],
                "warnings": [],
            }

        monkeypatch.setattr("app.modules.surrounding_area.analyzer.fetch_satellite_context", fake_satellite)
        facts = {"industry": "quÃ¡n Äƒn", "location": {**VINHOMES, "target_radius_m": 500}}
        report = await analyzer.analyze(facts, [], {"use_gemini": False, "include_satellite": True})

        assert report.details["satellite_context"]["best_scene"]["id"] == "S2A_TEST"
        assert report.details["satellite_context"]["radius_m"] == 500
        assert any(tool.name == "satellite_scene_context" for tool in report.tool_calls)


class TestReportIntegrity:
    async def test_every_finding_has_evidence_or_is_coverage(self, analyzer) -> None:
        facts = {"industry": "cà phê", "location": {**DISTRICT_1, "claims": ["Chưa có đối thủ 500m"]}}
        report = await analyzer.analyze(facts, [], NO_GEMINI)
        assert report.evidence
        assert report.evidence[0].accessed_at is not None
        assert report.tool_calls
        assert {tc.name for tc in report.tool_calls} >= {"poi_area_metrics", "coverage_assessment"}
