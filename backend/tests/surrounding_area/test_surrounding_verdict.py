from __future__ import annotations

import pytest

from app.modules.surrounding_area.data_store.poi_store import Poi
from app.modules.surrounding_area.tools.coverage import assess_coverage
from app.modules.surrounding_area.tools.poi_metrics import build_area_metrics
from app.modules.surrounding_area.verdict import (
    ClaimType,
    VerdictLabel,
    classify_claim,
    evaluate_claim_deterministic,
    evaluate_claims,
)

# Coverage fixtures from the calibrated densities.
GOOD_COVERAGE = assess_coverage(10.7725, 106.6980, 2797)  # District 1
THIN_COVERAGE = assess_coverage(10.9450, 106.8240, 285)  # Bien Hoa


def poi(distance_m, *, name=None, brand=None, value="cafe"):
    return Poi("n", int(distance_m), 10.0, 106.0, name, brand, None, "amenity", value, distance_m)


def metrics_with(competitors=(), demand=None):
    demand = demand or {"residential": 5, "office": 3, "school": 1, "transport": 2}
    return build_area_metrics(industry_profile="food_beverage", competitors=list(competitors), demand_counts=demand)


class TestClaimClassification:
    @pytest.mark.parametrize(
        "text,expected",
        [
            ("Chưa có đối thủ trong bán kính 500m", ClaimType.COMPETITOR_ABSENCE),
            ("Khu vực chưa bão hòa", ClaimType.SATURATION),
            ("Gần văn phòng nên lưu lượng khách ổn định", ClaimType.DEMAND),
            ("Giá thuê mặt bằng rẻ", ClaimType.PRICE),
            ("Giao thông thuận tiện, gần đường lớn", ClaimType.ACCESSIBILITY),
            ("Sản phẩm của chúng tôi rất tốt", ClaimType.GENERIC),
        ],
    )
    def test_classifies(self, text, expected) -> None:
        assert classify_claim(text) == expected

    def test_price_wins_over_location_words(self) -> None:
        assert classify_claim("mặt bằng gần khu dân cư, giá thuê rẻ") == ClaimType.PRICE


class TestPriceAlwaysInsufficient:
    """Mandatory test: a rent-price claim is always CHƯA ĐỦ THÔNG TIN."""

    @pytest.mark.parametrize("coverage", [GOOD_COVERAGE, THIN_COVERAGE])
    def test_price_insufficient_regardless_of_coverage(self, coverage) -> None:
        v = evaluate_claim_deterministic("Giá thuê mặt bằng ở đây rất rẻ", metrics_with(), coverage)
        assert v.verdict == VerdictLabel.INSUFFICIENT
        assert v.claim_type == ClaimType.PRICE


class TestCompetitorAbsence:
    def test_refuted_when_competitor_within_radius(self) -> None:
        """Mandatory: District 1 'no competitor within 500m' -> BÁC BỎ with numbers."""
        competitors = [poi(71, name="Cà Phê Tutti Frutti"), poi(200), poi(450)]
        v = evaluate_claim_deterministic(
            "Chưa có đối thủ trực tiếp trong bán kính 500m", metrics_with(competitors), GOOD_COVERAGE
        )
        assert v.verdict == VerdictLabel.REFUTED
        assert any("71" in e for e in v.evidence)
        assert any("Tutti Frutti" in e for e in v.evidence)

    def test_insufficient_when_thin_coverage_and_no_competitor(self) -> None:
        """Bien Hoa: no competitor found but map is thin -> cannot confirm absence."""
        v = evaluate_claim_deterministic("Chưa có đối thủ trong 500m", metrics_with(competitors=[]), THIN_COVERAGE)
        assert v.verdict == VerdictLabel.INSUFFICIENT

    def test_confirmed_when_good_coverage_and_no_competitor(self) -> None:
        v = evaluate_claim_deterministic(
            "Chưa có đối thủ trong 250m", metrics_with(competitors=[poi(800)]), GOOD_COVERAGE
        )
        assert v.verdict == VerdictLabel.CONFIRMED

    def test_radius_parsed_from_claim(self) -> None:
        # Competitor at 700m; claim is about 500m -> outside radius.
        v = evaluate_claim_deterministic(
            "Chưa có đối thủ trong 500m", metrics_with(competitors=[poi(700)]), GOOD_COVERAGE
        )
        assert v.verdict == VerdictLabel.CONFIRMED  # 700 > 500

    def test_1km_radius_parsed(self) -> None:
        v = evaluate_claim_deterministic(
            "Không có đối thủ trong 1km", metrics_with(competitors=[poi(700)]), GOOD_COVERAGE
        )
        assert v.verdict == VerdictLabel.REFUTED  # 700 < 1000


class TestSaturation:
    def test_bien_hoa_saturation_is_insufficient(self) -> None:
        """The most important test: thin map must not conclude 'not saturated'."""
        v = evaluate_claim_deterministic(
            "Khu vực chưa bão hòa, cơ hội tốt", metrics_with(competitors=[poi(300)]), THIN_COVERAGE
        )
        assert v.verdict == VerdictLabel.INSUFFICIENT

    def test_dense_area_refutes_not_saturated(self) -> None:
        competitors = [poi(i * 10) for i in range(60)]  # 60 competitors within 1km
        v = evaluate_claim_deterministic("Khu vực ít cạnh tranh", metrics_with(competitors), GOOD_COVERAGE)
        assert v.verdict == VerdictLabel.REFUTED


class TestDemand:
    def test_office_claim_refuted_when_no_offices(self) -> None:
        """The 7.2 incident: 'office-dense' must be refuted, not confirmed, when
        there are zero offices."""
        demand = {"residential": 10, "office": 0, "school": 2, "transport": 1}
        v = evaluate_claim_deterministic(
            "Gần nhiều văn phòng nên lưu lượng khách ổn định", metrics_with(demand=demand), GOOD_COVERAGE
        )
        assert v.verdict == VerdictLabel.REFUTED

    def test_demand_insufficient_when_office_not_measured(self) -> None:
        demand = {"residential": 10, "office": None, "school": 2, "transport": 1}
        v = evaluate_claim_deterministic("Gần văn phòng, đông khách", metrics_with(demand=demand), GOOD_COVERAGE)
        assert v.verdict == VerdictLabel.INSUFFICIENT

    def test_residential_claim_confirmed_when_present(self) -> None:
        demand = {"residential": 9, "office": 1, "school": 2, "transport": 3}
        v = evaluate_claim_deterministic("Nằm trong khu dân cư đông đúc", metrics_with(demand=demand), GOOD_COVERAGE)
        assert v.verdict == VerdictLabel.CONFIRMED


class TestEvaluateClaimsReport:
    @pytest.mark.asyncio
    async def test_report_without_gemini(self) -> None:
        report = await evaluate_claims(
            ["Chưa có đối thủ trong 500m", "Giá thuê rẻ"],
            metrics_with(competitors=[poi(100)]),
            GOOD_COVERAGE,
            use_gemini=False,
        )
        assert report.llm_used is False
        assert len(report.claims) == 2
        assert report.claims[0].verdict == VerdictLabel.REFUTED
        assert report.claims[1].verdict == VerdictLabel.INSUFFICIENT
        assert report.overall_summary

    @pytest.mark.asyncio
    async def test_explanation_defaults_to_reason(self) -> None:
        report = await evaluate_claims(["Giá thuê rẻ"], metrics_with(), THIN_COVERAGE, use_gemini=False)
        assert report.claims[0].explanation == report.claims[0].reason

    @pytest.mark.asyncio
    async def test_empty_claims(self) -> None:
        report = await evaluate_claims([], metrics_with(), GOOD_COVERAGE, use_gemini=True)
        assert report.claims == []
        assert report.llm_used is False

    @pytest.mark.asyncio
    async def test_serialisation(self) -> None:
        report = await evaluate_claims(["Giá thuê rẻ"], metrics_with(), GOOD_COVERAGE, use_gemini=False)
        data = report.to_dict()
        assert data["claims"][0]["verdict_vi"] == "CHƯA ĐỦ THÔNG TIN"
