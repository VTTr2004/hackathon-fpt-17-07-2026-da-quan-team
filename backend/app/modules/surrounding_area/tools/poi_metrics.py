"""Deterministic metrics computed from POIs returned by the store.

These tools answer the diligence questions in plan section 6. Every function is
pure: it takes already-fetched POIs (or lists of them) and returns numbers plus
data-gap warnings. None of them fetch data, none call an LLM, and none of them
invent a value when input is missing — a missing input yields ``None`` and a
warning, never ``0`` (the mistake fixed in plan section 7.2).

The unit that ties these together, ``AreaMetrics``, is what the analyzer feeds to
the verdict layer. The LLM reads these numbers; it never recomputes them.
"""

from __future__ import annotations

import unicodedata
from collections import Counter
from dataclasses import asdict, dataclass, field

from app.modules.surrounding_area.data_store.poi_store import Poi

POI_METRICS_VERSION = "1.0.0"

# The three competition rings the plan measures (metres).
RINGS_M = (250, 500, 1000)

# Known F&B / retail chain names to catch brands OSM did not tag. `brand` is null
# almost everywhere outside the four big cities (plan 7.1), so the chain ratio is
# always a LOWER BOUND — we augment it with name matching but never claim
# completeness.
KNOWN_CHAIN_NAMES = (
    "highlands", "phuc long", "trung nguyen", "the coffee house", "starbucks", "cong caphe",
    "katinat", "phe la", "laika", "aha", "milano", "circle k", "ministop", "family mart",
    "gs25", "winmart", "vinmart", "bach hoa xanh", "co.op", "guardian", "pharmacity",
    "long chau", "an khang", "kfc", "lotteria", "jollibee", "mcdonald", "pizza hut",
    "the pizza company", "gong cha", "tocotoco", "ding tea", "royaltea", "phindeli",
)


def _fold(text: str) -> str:
    text = text.lower().replace("đ", "d")
    return "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")


def _looks_like_chain(poi: Poi) -> bool:
    if poi.brand:
        return True
    haystack = _fold(poi.name or "")
    return any(chain in haystack for chain in KNOWN_CHAIN_NAMES)


@dataclass
class RingDensity:
    radius_m: int
    count: int


@dataclass
class NearestCompetitor:
    distance_m: float
    name: str | None
    category_value: str
    is_chain: bool


@dataclass
class ChainRatio:
    total: int
    chain_count: int
    ratio: float | None  # None when total == 0 (undefined, not zero)
    is_lower_bound: bool = True


@dataclass
class DemandBreakdown:
    """Raw counts of demand proxies. Any component that could not be measured is
    ``None`` (not 0) and listed in ``missing``."""

    residential: int | None
    office: int | None
    school: int | None
    transport: int | None
    missing: list[str] = field(default_factory=list)

    def present_score(self) -> int | None:
        measured = [v for v in (self.residential, self.office, self.school, self.transport) if v is not None]
        return sum(measured) if measured else None


def competitor_density(competitors: list[Poi]) -> list[RingDensity]:
    """Count competitors within each ring. Competitors must already be filtered
    to the industry's tags and sorted/annotated with distance."""
    return [RingDensity(radius_m=r, count=sum(1 for c in competitors if c.distance_m <= r)) for r in RINGS_M]


def nearest_competitor(competitors: list[Poi]) -> NearestCompetitor | None:
    if not competitors:
        return None
    nearest = min(competitors, key=lambda c: c.distance_m)
    return NearestCompetitor(
        distance_m=nearest.distance_m,
        name=nearest.name,
        category_value=nearest.category_value,
        is_chain=_looks_like_chain(nearest),
    )


def chain_ratio(competitors: list[Poi]) -> ChainRatio:
    total = len(competitors)
    if total == 0:
        return ChainRatio(total=0, chain_count=0, ratio=None)
    chain_count = sum(1 for c in competitors if _looks_like_chain(c))
    return ChainRatio(total=total, chain_count=chain_count, ratio=round(chain_count / total, 3))


def demand_breakdown(
    counts: dict[str, int | None],
) -> DemandBreakdown:
    """Assemble the demand proxies, tracking which ones could not be measured.

    `counts` maps 'residential'|'office'|'school'|'transport' to a count or None.
    A key mapped to None (a failed/absent query) is recorded as missing, NOT
    treated as zero.
    """
    missing = [k for k in ("residential", "office", "school", "transport") if counts.get(k) is None]
    return DemandBreakdown(
        residential=counts.get("residential"),
        office=counts.get("office"),
        school=counts.get("school"),
        transport=counts.get("transport"),
        missing=missing,
    )


def supply_demand_ratio(competitor_count: int, demand: DemandBreakdown) -> dict[str, object]:
    """Competitors per unit of demand proxy.

    High ratio → many sellers chasing few customers (saturated). This is a
    self-computed metric (no external source provides it, plan section 6). It is
    undefined — returned as None — when demand could not be measured, rather than
    dividing by an assumed zero.
    """
    demand_score = demand.present_score()
    if demand_score is None:
        return {"ratio": None, "note": "Không đo được cầu; tỷ lệ cung/cầu không xác định."}
    if demand_score == 0:
        return {
            "ratio": None,
            "note": "Cầu đo được bằng 0 (không có dân cư/văn phòng/trường quanh đây); "
            "chưa đủ căn cứ tính tỷ lệ cung/cầu.",
        }
    return {"ratio": round(competitor_count / demand_score, 3), "demand_score": demand_score}


@dataclass
class AreaMetrics:
    """Everything the verdict layer needs, computed by tools only."""

    industry_profile: str | None
    competitor_density: list[RingDensity]
    nearest_competitor: NearestCompetitor | None
    chain_ratio: ChainRatio
    demand: DemandBreakdown
    supply_demand: dict[str, object]
    competitor_category_mix: dict[str, int]
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "industry_profile": self.industry_profile,
            "competitor_density": [asdict(r) for r in self.competitor_density],
            "nearest_competitor": asdict(self.nearest_competitor) if self.nearest_competitor else None,
            "chain_ratio": asdict(self.chain_ratio),
            "demand": asdict(self.demand),
            "supply_demand": self.supply_demand,
            "competitor_category_mix": self.competitor_category_mix,
            "warnings": self.warnings,
        }


def build_area_metrics(
    *,
    industry_profile: str | None,
    competitors: list[Poi],
    demand_counts: dict[str, int | None],
    extra_warnings: list[str] | None = None,
) -> AreaMetrics:
    """Assemble the full metric bundle from fetched POIs. Pure and deterministic."""
    density = competitor_density(competitors)
    nearest = nearest_competitor(competitors)
    chains = chain_ratio(competitors)
    demand = demand_breakdown(demand_counts)
    within_1km = density[-1].count if density else len(competitors)
    supply_demand = supply_demand_ratio(within_1km, demand)
    category_mix = dict(Counter(c.category_value for c in competitors).most_common())

    warnings = list(extra_warnings or [])
    if demand.missing:
        warnings.append(
            f"Không đo được cầu: {', '.join(demand.missing)}. "
            f"Các thành phần này bị loại, KHÔNG tính là 0."
        )
    return AreaMetrics(
        industry_profile=industry_profile,
        competitor_density=density,
        nearest_competitor=nearest,
        chain_ratio=chains,
        demand=demand,
        supply_demand=supply_demand,
        competitor_category_mix=category_mix,
        warnings=warnings,
    )
