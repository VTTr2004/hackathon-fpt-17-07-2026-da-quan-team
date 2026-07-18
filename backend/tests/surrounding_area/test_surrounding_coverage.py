import pytest

from app.modules.surrounding_area.data.population import nearest_urban_area
from app.modules.surrounding_area.tools.coverage import (
    CoverageTier,
    assess_coverage,
)

# Coordinates + the densities measured from the real extract.
Q1 = (10.7725, 106.6980, 2797)
HANOI = (21.0287, 105.8524, 3616)
VINHOMES = (20.9943, 105.9485, 690)
THU_DUC = (10.8500, 106.7700, 393)
BIEN_HOA = (10.9450, 106.8240, 285)
VINH = (18.6790, 105.6810, 112)
MOC_CHAU = (20.8300, 104.6300, 8)


class TestTierClassification:
    def test_district_1_is_good(self) -> None:
        assert assess_coverage(*Q1).tier == CoverageTier.GOOD

    def test_hanoi_core_is_good(self) -> None:
        assert assess_coverage(*HANOI).tier == CoverageTier.GOOD

    def test_vinhomes_new_development_is_good(self) -> None:
        """Well-mapped even though it is not a historic city core."""
        assert assess_coverage(*VINHOMES).tier == CoverageTier.GOOD

    def test_bien_hoa_is_thin(self) -> None:
        """The single most important assertion in this module."""
        assessment = assess_coverage(*BIEN_HOA)
        assert assessment.tier == CoverageTier.THIN
        assert assessment.can_assess_saturation is False
        assert assessment.confidence_factor < 1.0

    def test_thu_duc_is_thin(self) -> None:
        assert assess_coverage(*THU_DUC).tier == CoverageTier.THIN

    def test_vinh_is_very_thin(self) -> None:
        assert assess_coverage(*VINH).tier == CoverageTier.VERY_THIN

    def test_moc_chau_is_rural(self) -> None:
        assert assess_coverage(*MOC_CHAU).tier == CoverageTier.RURAL


class TestSaturationGate:
    def test_only_good_coverage_can_assess_saturation(self) -> None:
        assert assess_coverage(*Q1).can_assess_saturation is True
        assert assess_coverage(*BIEN_HOA).can_assess_saturation is False
        assert assess_coverage(*VINH).can_assess_saturation is False
        assert assess_coverage(*MOC_CHAU).can_assess_saturation is False

    def test_thin_areas_warn_against_not_saturated_conclusion(self) -> None:
        warnings = " ".join(assess_coverage(*BIEN_HOA).warnings)
        assert "bão hòa" in warnings or "LỖ HỔNG" in warnings

    def test_bien_hoa_flags_population_mismatch(self) -> None:
        """A million-person city with a thin map should say so explicitly."""
        warnings = " ".join(assess_coverage(*BIEN_HOA).warnings)
        assert "dân" in warnings


class TestConfidenceGradient:
    def test_confidence_decreases_with_coverage(self) -> None:
        factors = [
            assess_coverage(*Q1).confidence_factor,
            assess_coverage(*BIEN_HOA).confidence_factor,
            assess_coverage(*VINH).confidence_factor,
            assess_coverage(*MOC_CHAU).confidence_factor,
        ]
        assert factors == sorted(factors, reverse=True)
        assert factors[0] == 1.0


class TestValidation:
    def test_rejects_negative_density(self) -> None:
        with pytest.raises(ValueError):
            assess_coverage(10.0, 106.0, -1)

    def test_rejects_zero_baseline(self) -> None:
        with pytest.raises(ValueError):
            assess_coverage(10.0, 106.0, 100, baseline_density=0)

    def test_coverage_ratio_reported(self) -> None:
        assessment = assess_coverage(*BIEN_HOA)
        assert assessment.coverage_ratio == round(285 / 1000, 3)

    def test_determinism(self) -> None:
        assert assess_coverage(*BIEN_HOA).to_dict() == assess_coverage(*BIEN_HOA).to_dict()


class TestNearestUrbanArea:
    def test_bien_hoa_matches_bien_hoa(self) -> None:
        area, distance = nearest_urban_area(*BIEN_HOA[:2])
        assert area.name == "Biên Hòa"
        assert distance < 2

    def test_q1_matches_hcmc(self) -> None:
        area, _ = nearest_urban_area(*Q1[:2])
        assert "Hồ Chí Minh" in area.name
