"""Industry taxonomy: how much a business depends on its physical location, and
which OSM POI types count as its competitors.

Two deterministic tools live here:

- ``classify_location_dependency`` implements plan step 0. A SaaS startup run
  through location analysis would receive "0 competitors within 1km" — a
  meaningless number that *looks like* a positive signal. The aggregator must
  drop such a module from scoring, not add a zero (plan section 5). This decides
  which of the three buckets an industry falls in.

- ``resolve_competitor_filter`` maps an industry to the OSM tag filter that
  identifies its direct competitors, and the demand-proxy filters (residential,
  offices, schools) that indicate customers nearby.

Matching is keyword-based over free-text industry strings because StartupFacts
carries an unconstrained ``industry`` string, often Vietnamese. Everything is
lower-cased and accent-folded first so "Nhà hàng", "nha hang" and "F&B" all land
on the food bucket.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from enum import StrEnum
from functools import lru_cache

TAXONOMY_VERSION = "1.0.0"


class LocationDependency(StrEnum):
    # Location decides the outcome: run the full analysis.
    PRIMARY = "primary"
    # Location matters only for logistics/talent access: run a reduced analysis.
    SUPPORTING = "supporting"
    # Digital / location-independent: the module does not apply at all.
    INDEPENDENT = "independent"


def fold(text: str) -> str:
    """Lower-case and strip Vietnamese diacritics for robust keyword matching."""
    text = text.lower().replace("đ", "d")
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")


@lru_cache(maxsize=512)
def _keyword_pattern(keyword: str) -> re.Pattern[str]:
    """Whole-word/phrase matcher for a folded keyword.

    Raw substring matching produced false positives — "spa" matched inside
    "coworking space", classifying a coworking startup as healthcare. Word
    boundaries stop that while still matching multi-word keywords ("nha hang")
    and ones with punctuation ("f&b").
    """
    return re.compile(rf"(?<!\w){re.escape(keyword)}(?!\w)")


def _matches(keyword: str, folded_text: str) -> bool:
    return _keyword_pattern(keyword).search(folded_text) is not None


@dataclass(frozen=True)
class IndustryProfile:
    """One recognised industry: its keywords, dependency class and OSM filters."""

    key: str
    dependency: LocationDependency
    keywords: tuple[str, ...]
    # OSM (key, value) pairs whose presence marks a direct competitor.
    competitor_tags: tuple[tuple[str, str], ...] = ()
    label_vi: str = ""


# Demand proxies are shared across all location-dependent industries: an area
# has customers if people live, work or study nearby (plan section 6, "demand").
# Every (key, value) here must correspond to something extract_poi.py actually
# stores; "*" means "any value of this key". Validated against Vinhomes Ocean
# Park: residential zones, offices, Vinschool/VinUni and bus platforms all resolve.
DEMAND_TAGS: dict[str, tuple[tuple[str, str], ...]] = {
    "residential": (("landuse", "residential"),),
    "office": (("office", "*"),),
    "school": (("amenity", "school"), ("amenity", "college"), ("amenity", "university"), ("amenity", "kindergarten")),
    "transport": (("public_transport", "*"), ("amenity", "bus_station")),
}

# Order matters: the first profile whose keywords match wins, so put specific
# industries before generic ones.
PROFILES: tuple[IndustryProfile, ...] = (
    IndustryProfile(
        key="food_beverage",
        dependency=LocationDependency.PRIMARY,
        keywords=(
            "f&b",
            "fnb",
            "food",
            "restaurant",
            "nha hang",
            "quan an",
            "cafe",
            "ca phe",
            "coffee",
            "an uong",
            "do uong",
            "tra sua",
            "bakery",
            "banh",
            "beverage",
            "bar",
            "pub",
        ),
        competitor_tags=(
            ("amenity", "cafe"),
            ("amenity", "restaurant"),
            ("amenity", "fast_food"),
            ("amenity", "bar"),
            ("amenity", "pub"),
            ("amenity", "food_court"),
            ("shop", "coffee"),
            ("shop", "bakery"),
            ("shop", "confectionery"),
        ),
        label_vi="Ẩm thực / F&B",
    ),
    IndustryProfile(
        key="retail",
        dependency=LocationDependency.PRIMARY,
        keywords=(
            "retail",
            "ban le",
            "cua hang",
            "shop",
            "store",
            "sieu thi",
            "tap hoa",
            "convenience",
            "minimart",
            "grocery",
            "thoi trang",
            "fashion",
            "boutique",
        ),
        competitor_tags=(
            ("shop", "convenience"),
            ("shop", "supermarket"),
            ("shop", "clothes"),
            ("shop", "general"),
            ("shop", "mall"),
            ("shop", "department_store"),
        ),
        label_vi="Bán lẻ",
    ),
    IndustryProfile(
        key="fitness",
        dependency=LocationDependency.PRIMARY,
        keywords=("gym", "fitness", "the hinh", "yoga", "the thao", "phong tap", "sport"),
        competitor_tags=(("leisure", "fitness_centre"), ("leisure", "sports_centre"), ("shop", "sports")),
        label_vi="Gym / Thể thao",
    ),
    IndustryProfile(
        key="education",
        dependency=LocationDependency.PRIMARY,
        keywords=(
            "education",
            "giao duc",
            "truong",
            "trung tam",
            "day hoc",
            "tutor",
            "language",
            "ngoai ngu",
            "training center",
            "mam non",
            "kindergarten",
        ),
        competitor_tags=(
            ("amenity", "school"),
            ("amenity", "language_school"),
            ("amenity", "college"),
            ("amenity", "kindergarten"),
            ("amenity", "training"),
        ),
        label_vi="Giáo dục",
    ),
    IndustryProfile(
        key="healthcare",
        dependency=LocationDependency.PRIMARY,
        keywords=(
            "clinic",
            "phong kham",
            "pharmacy",
            "nha thuoc",
            "dental",
            "nha khoa",
            "y te",
            "healthcare",
            "benh vien",
            "hospital",
            "spa",
            "tham my",
        ),
        competitor_tags=(
            ("amenity", "clinic"),
            ("amenity", "pharmacy"),
            ("amenity", "doctors"),
            ("amenity", "dentist"),
            ("amenity", "hospital"),
            ("shop", "beauty"),
            ("shop", "chemist"),
            ("leisure", "spa"),
        ),
        label_vi="Y tế / Chăm sóc sức khỏe",
    ),
    IndustryProfile(
        key="hospitality",
        dependency=LocationDependency.PRIMARY,
        keywords=("hotel", "khach san", "homestay", "resort", "hostel", "luu tru", "nha nghi"),
        competitor_tags=(
            ("tourism", "hotel"),
            ("tourism", "hostel"),
            ("tourism", "guest_house"),
            ("tourism", "motel"),
            ("tourism", "apartment"),
        ),
        label_vi="Lưu trú / Khách sạn",
    ),
    IndustryProfile(
        key="logistics",
        dependency=LocationDependency.SUPPORTING,
        keywords=(
            "logistics",
            "van tai",
            "kho",
            "warehouse",
            "manufacturing",
            "san xuat",
            "nha may",
            "factory",
            "coworking",
            "khu cong nghiep",
        ),
        competitor_tags=(),
        label_vi="Logistics / Sản xuất",
    ),
    IndustryProfile(
        key="digital",
        dependency=LocationDependency.INDEPENDENT,
        keywords=(
            "saas",
            "software",
            "phan mem",
            "fintech",
            "cong nghe",
            "app",
            "platform",
            "marketplace",
            "ai",
            "blockchain",
            "e-commerce",
            "thuong mai dien tu",
            "edtech",
            "web",
            "digital",
            "startup cong nghe",
            "api",
        ),
        competitor_tags=(),
        label_vi="Công nghệ số / SaaS",
    ),
)


@dataclass(frozen=True)
class ClassificationResult:
    dependency: LocationDependency
    matched_profile: str | None
    label_vi: str
    reason: str
    matched_keyword: str | None = None


def classify_location_dependency(
    industry: str | None,
    explicit: LocationDependency | str | None = None,
) -> ClassificationResult:
    """Plan step 0: decide whether the surrounding-area module applies.

    Unknown industries default to PRIMARY (analyse and let the human decide)
    rather than INDEPENDENT, because wrongly skipping a location-dependent
    startup is worse than running an analysis a human can discard. The label is
    always analyst-editable upstream (Intake owns the final label).

    ``explicit`` lets the analyst / intake override the inference — e.g. the
    startup answered "does it depend on surrounding foot traffic?" directly.
    A valid explicit value wins over any industry keyword.
    """
    if explicit is not None:
        try:
            dep = LocationDependency(explicit) if not isinstance(explicit, LocationDependency) else explicit
        except ValueError:
            dep = None
        if dep is not None:
            return ClassificationResult(
                dependency=dep,
                matched_profile=classify_location_dependency(industry).matched_profile,
                label_vi={
                    "primary": "Phụ thuộc vị trí (chỉ định)",
                    "supporting": "Vị trí phụ trợ (chỉ định)",
                    "independent": "Không phụ thuộc vị trí (chỉ định)",
                }[dep.value],
                reason="Do người dùng/chuyên viên chỉ định trực tiếp, ưu tiên hơn suy luận theo ngành.",
            )

    if not industry or not industry.strip():
        return ClassificationResult(
            dependency=LocationDependency.PRIMARY,
            matched_profile=None,
            label_vi="Chưa rõ ngành",
            reason="Không có thông tin ngành; mặc định phân tích để chuyên viên tự quyết.",
        )

    folded = fold(industry)
    for profile in PROFILES:
        for keyword in profile.keywords:
            if _matches(keyword, folded):
                return ClassificationResult(
                    dependency=profile.dependency,
                    matched_profile=profile.key,
                    label_vi=profile.label_vi,
                    matched_keyword=keyword,
                    reason=f"Ngành khớp nhóm '{profile.label_vi}' qua từ khóa '{keyword}'.",
                )

    return ClassificationResult(
        dependency=LocationDependency.PRIMARY,
        matched_profile=None,
        label_vi="Ngành chưa phân loại",
        reason="Không khớp nhóm ngành nào; mặc định phân tích để chuyên viên tự quyết.",
    )


@dataclass(frozen=True)
class CompetitorFilter:
    profile_key: str | None
    competitor_tags: tuple[tuple[str, str], ...]
    demand_tags: dict[str, tuple[tuple[str, str], ...]] = field(default_factory=lambda: dict(DEMAND_TAGS))


def resolve_competitor_filter(industry: str | None) -> CompetitorFilter:
    """Return the OSM tag filter identifying competitors for this industry.

    Falls back to the food bucket's tags only when a PRIMARY industry is
    recognised but has no explicit competitor tags; otherwise returns an empty
    competitor set (the caller then treats competitor density as unmeasurable
    rather than zero).
    """
    result = classify_location_dependency(industry)
    if result.matched_profile is None:
        return CompetitorFilter(profile_key=None, competitor_tags=())
    profile = next(p for p in PROFILES if p.key == result.matched_profile)
    return CompetitorFilter(profile_key=profile.key, competitor_tags=profile.competitor_tags)
