"""Map-coverage assessment: the module's defence against the "thin map = empty
market" trap (plan section 7.1).

Outside the four big cities, OSM coverage collapses. Bien Hoa has more than a
million residents but only ~285 mapped POIs per km²; a naive reading counts nine
cafes and concludes "not saturated, good opportunity" — awarding points for a
gap in the map. This tool detects that a location's POI density is abnormally
low relative to a well-mapped urban baseline and tells the analyzer to withhold
saturation judgements and lower confidence, rather than reward the gap.

The signal is RELATIVE density (measured / baseline), never an absolute POI
count — an absolute threshold is exactly what plan section 7.4 rejects, because
context POIs push Bien Hoa's raw count above any fixed café threshold.

Thresholds are calibrated from real measurements (docs/methodology.md):
    well-mapped cores  690–3616 POI/km²
    thin (urban gaps)  150–500   (Thu Duc 393, Bien Hoa 285, Da Lat 255)
    very thin          30–150    (Vinh 112, Buon Ma Thuot 92)
    rural              <30       (Moc Chau 8)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from app.modules.surrounding_area.data.population import (
    WELL_MAPPED_BASELINE_DENSITY,
    nearest_urban_area,
)

COVERAGE_VERSION = "1.0.0"
PLACES_COVERAGE_VERSION = "2.0.0"


class CoverageTier(StrEnum):
    GOOD = "good"  # dense enough to trust a saturation assessment
    THIN = "thin"  # abnormally sparse — likely map gaps, not empty market
    VERY_THIN = "very_thin"  # severe gaps
    RURAL = "rural"  # so few POIs the area is plausibly genuinely sparse


# Relative-density cut points (measured_density / baseline).
_GOOD_RATIO = 0.5  # >= 500 POI/km at baseline 1000
_THIN_RATIO = 0.15  # >= 150
_RURAL_RATIO = 0.03  # < 30 -> rural


@dataclass
class CoverageAssessment:
    tier: CoverageTier
    density_1km: int
    baseline_density: int
    coverage_ratio: float
    # Multiply a finding's nominal confidence by this (1.0 good ... 0.3 rural).
    confidence_factor: float
    # True when absence-of-competitor claims can be trusted (only GOOD coverage).
    can_assess_saturation: bool
    nearest_reference: str
    reference_distance_km: float
    warnings: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "tier": self.tier.value,
            "density_1km": self.density_1km,
            "baseline_density": self.baseline_density,
            "coverage_ratio": self.coverage_ratio,
            "confidence_factor": self.confidence_factor,
            "can_assess_saturation": self.can_assess_saturation,
            "nearest_reference": self.nearest_reference,
            "reference_distance_km": self.reference_distance_km,
            "warnings": self.warnings,
            "notes": self.notes,
        }


def assess_coverage(
    lat: float,
    lon: float,
    density_1km: int,
    *,
    baseline_density: int = WELL_MAPPED_BASELINE_DENSITY,
) -> CoverageAssessment:
    """Classify how trustworthy the map is at this location.

    `density_1km` is the total count of POIs (all categories) within 1 km,
    measured by the caller via the POI store.
    """
    if density_1km < 0:
        raise ValueError("density_1km must be >= 0")
    if baseline_density <= 0:
        raise ValueError("baseline_density must be > 0")

    ratio = round(density_1km / baseline_density, 3)
    area, distance_km = nearest_urban_area(lat, lon)
    distance_km = round(distance_km, 1)

    warnings: list[str] = []
    notes: list[str] = []

    if ratio >= _GOOD_RATIO:
        tier = CoverageTier.GOOD
        confidence = 1.0
        can_assess = True
        notes.append(
            f"Mật độ POI ({density_1km}/km²) đủ dày để đánh giá mức độ bão hòa "
            f"(≥ {int(_GOOD_RATIO * baseline_density)}/km²)."
        )
    elif ratio >= _THIN_RATIO:
        tier = CoverageTier.THIN
        confidence = 0.55
        can_assess = False
        warnings.append(
            f"Mật độ POI thấp bất thường ({density_1km}/km², chỉ {ratio:.0%} baseline "
            f"vùng bản đồ tốt). Đây nhiều khả năng là LỖ HỔNG DỮ LIỆU OSM, không phải "
            f"thị trường trống. KHÔNG kết luận 'chưa bão hòa'."
        )
    elif ratio >= _RURAL_RATIO:
        tier = CoverageTier.VERY_THIN
        confidence = 0.4
        can_assess = False
        warnings.append(
            f"Mật độ POI rất thấp ({density_1km}/km², {ratio:.0%} baseline). Vùng bản đồ "
            f"mỏng nghiêm trọng; mọi số đếm đối thủ là giới hạn dưới, không đáng tin để "
            f"kết luận về cạnh tranh."
        )
    else:
        tier = CoverageTier.RURAL
        confidence = 0.3
        can_assess = False
        notes.append(
            f"Rất ít POI ({density_1km}/km²). Có thể là khu vực thưa dân thật sự HOẶC "
            f"vùng chưa được lập bản đồ. Không đủ căn cứ đánh giá cạnh tranh."
        )

    # Population context: a low-density location that a large city sits on top of
    # is a strong "thin map" signal worth surfacing explicitly.
    if tier != CoverageTier.GOOD and distance_km <= 8 and area.population >= 300_000 and not area.mapped_well:
        warnings.append(
            f"Vị trí gần {area.name} (~{area.population:,} dân) nhưng mật độ bản đồ mỏng — "
            f"dấu hiệu rõ của lỗ hổng dữ liệu, không phải khu vực vắng."
        )

    return CoverageAssessment(
        tier=tier,
        density_1km=density_1km,
        baseline_density=baseline_density,
        coverage_ratio=ratio,
        confidence_factor=confidence,
        can_assess_saturation=can_assess,
        nearest_reference=area.name,
        reference_distance_km=distance_km,
        warnings=warnings,
        notes=notes,
    )


def assess_places_coverage(
    *,
    observed_place_count: int,
    successful_groups: int,
    total_groups: int,
    competitor_capped: bool,
) -> CoverageAssessment:
    """Assess request completeness for bounded Google Places observations.

    Unlike OSM, Places does not expose an extract whose absolute completeness
    can be measured.  We therefore judge only whether the planned API groups
    succeeded and whether the competitor request hit the 20-result cap.
    """
    if observed_place_count < 0 or total_groups <= 0:
        raise ValueError("invalid Google Places coverage inputs")
    ratio = round(successful_groups / total_groups, 3)
    warnings = [
        "Google Places là mẫu POI quan sát được, không phải tổng điều tra; "
        "không dùng số đếm để suy ra dân số tuyệt đối."
    ]
    notes: list[str] = []
    if successful_groups == total_groups and not competitor_capped:
        tier = CoverageTier.GOOD
        confidence = 0.8
        can_assess = True
        notes.append("Tất cả nhóm truy vấn thành công và nhóm đối thủ chưa chạm trần 20 kết quả.")
    elif successful_groups == total_groups:
        tier = CoverageTier.THIN
        confidence = 0.6
        can_assess = False
        warnings.append(
            "Nhóm đối thủ chạm trần 20 kết quả; chỉ được kết luận 'có ít nhất 20', không kết luận mức bão hòa đầy đủ."
        )
    elif successful_groups > 0:
        tier = CoverageTier.VERY_THIN
        confidence = 0.4
        can_assess = False
        warnings.append("Một hoặc nhiều nhóm Places thất bại; dữ liệu thiếu không được coi là 0.")
    else:
        tier = CoverageTier.RURAL
        confidence = 0.0
        can_assess = False
        warnings.append("Không có nhóm Places nào truy vấn thành công.")
    return CoverageAssessment(
        tier=tier,
        density_1km=observed_place_count,
        baseline_density=total_groups,
        coverage_ratio=ratio,
        confidence_factor=confidence,
        can_assess_saturation=can_assess,
        nearest_reference="Google Places request groups",
        reference_distance_km=0.0,
        warnings=warnings,
        notes=notes,
    )
