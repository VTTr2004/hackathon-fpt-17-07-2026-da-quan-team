"""Static population/coverage reference for major Vietnamese urban areas.

Why a static table when poi.db already has OSM `place` populations: OSM place
matching proved unreliable for this purpose (measured — TP Vinh's nearest
`place` carrying a population tag is 118 km away, and Bien Hoa's is the whole
Dong Nai province at 4 km). So this curated table is the authority for "is this
location supposed to be a dense urban area?", and OSM place data is only a
secondary hint.

Population figures are approximate urban-area estimates (General Statistics
Office of Vietnam, 2022 Statistical Yearbook and 2019 Census projections). They
are NOT precise and are used only to reason about expected coverage, never fed
into a score. `mapped_well` marks the areas where OpenStreetMap coverage was
measured to be dense enough to trust a saturation assessment.

`baseline_density_1km` values are the POI-within-1km densities measured from the
current extract (see docs/methodology.md, "Coverage calibration"). They document
where the coverage thresholds come from; the live density is what gets classified.
"""

from __future__ import annotations

from dataclasses import dataclass

POPULATION_VERSION = "1.0.0"
POPULATION_SOURCE = "Tổng cục Thống kê (GSO) — Niên giám 2022 & dự báo Tổng điều tra 2019 (ước lượng)"


@dataclass(frozen=True)
class UrbanArea:
    name: str
    lat: float
    lon: float
    population: int
    mapped_well: bool
    # POI/1km measured in this extract at the area's core (documentation of calibration).
    measured_density_1km: int | None = None


# Ordered roughly by population. Coordinates are the urban core.
URBAN_AREAS: tuple[UrbanArea, ...] = (
    UrbanArea("TP. Hồ Chí Minh (Quận 1)", 10.7725, 106.6980, 9_500_000, True, 2797),
    UrbanArea("Hà Nội (Hoàn Kiếm)", 21.0287, 105.8524, 8_400_000, True, 3616),
    UrbanArea("Hải Phòng", 20.8449, 106.6881, 2_000_000, False, None),
    UrbanArea("Đà Nẵng (Hải Châu)", 16.0678, 108.2208, 1_200_000, True, 1014),
    UrbanArea("Biên Hòa", 10.9450, 106.8240, 1_200_000, False, 285),
    UrbanArea("Cần Thơ (Ninh Kiều)", 10.0340, 105.7880, 1_240_000, True, 769),
    UrbanArea("Huế", 16.4637, 107.5909, 650_000, True, 848),
    UrbanArea("Nha Trang", 12.2388, 109.1967, 535_000, False, None),
    UrbanArea("Buôn Ma Thuột", 12.6710, 108.0380, 465_000, False, 92),
    UrbanArea("Vinh", 18.6790, 105.6810, 500_000, False, 112),
    UrbanArea("Quy Nhơn", 13.7829, 109.2196, 490_000, False, None),
    UrbanArea("Đà Lạt", 11.9404, 108.4583, 250_000, False, 255),
    UrbanArea("Thủ Đức", 10.8500, 106.7700, 1_200_000, False, 393),
)

# Representative well-mapped urban baseline density (POI within 1km), the
# denominator for the relative coverage ratio. Conservative: below the median of
# the five well-mapped cores so genuinely dense areas clear it comfortably.
WELL_MAPPED_BASELINE_DENSITY = 1000


def nearest_urban_area(lat: float, lon: float) -> tuple[UrbanArea, float]:
    """Return the closest reference urban area and the distance in km."""
    from app.modules.surrounding_area.tools.geo import haversine_km

    best = min(URBAN_AREAS, key=lambda a: haversine_km(lat, lon, a.lat, a.lon))
    return best, haversine_km(lat, lon, best.lat, best.lon)
