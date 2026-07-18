"""Turn startup claims about the area into evidenced verdicts.

The module's real job (plan section 2) is not to describe an area but to
adjudicate what a startup asserts about it — "no competitor within 500 m", "next
to offices so steady foot traffic", "rent is cheap". Each claim gets one of three
verdicts, and nothing else:

    XÁC NHẬN            (confirmed)          the data supports the claim
    BÁC BỎ              (refuted)            the data contradicts the claim
    CHƯA ĐỦ THÔNG TIN   (insufficient data)  the data cannot decide

Design that keeps the LLM honest (plan sections 7.2, 7.6):

* A deterministic engine computes the verdict from tool numbers. It is fully
  testable, needs no API key, and is the source of truth.
* Gemini, when configured, only writes the Vietnamese explanation. A hard
  guardrail forbids it from turning an INSUFFICIENT verdict into a confident one
  — the exact failure where the model once "confirmed" an office-dense area from
  data containing no offices. Price claims and thin-map areas are locked to
  INSUFFICIENT before the LLM ever sees them.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from enum import StrEnum

from pydantic import BaseModel, Field

from app.modules.surrounding_area.tools.coverage import CoverageAssessment
from app.modules.surrounding_area.tools.industry_taxonomy import fold
from app.modules.surrounding_area.tools.poi_metrics import AreaMetrics

VERDICT_VERSION = "1.0.0"


class VerdictLabel(StrEnum):
    CONFIRMED = "xac_nhan"
    REFUTED = "bac_bo"
    INSUFFICIENT = "chua_du_thong_tin"

    @property
    def vi(self) -> str:
        return {"xac_nhan": "XÁC NHẬN", "bac_bo": "BÁC BỎ", "chua_du_thong_tin": "CHƯA ĐỦ THÔNG TIN"}[self.value]


class ClaimType(StrEnum):
    COMPETITOR_ABSENCE = "competitor_absence"
    SATURATION = "saturation"
    DEMAND = "demand"
    PRICE = "price"
    ACCESSIBILITY = "accessibility"
    GENERIC = "generic"


_CLAIM_KEYWORDS: tuple[tuple[ClaimType, tuple[str, ...]], ...] = (
    # Price first: a claim mentioning rent is a price claim even if it also talks
    # about location, and price is always undecidable here.
    (ClaimType.PRICE, ("gia thue", "gia mat bang", "chi phi thue", "mat bang re", "gia re", "rent", "thue re")),
    (
        ClaimType.COMPETITOR_ABSENCE,
        (
            "chua co doi thu",
            "khong co doi thu",
            "chua ai lam",
            "duy nhat",
            "khong canh tranh",
            "no competitor",
            "chua co ai",
            "khong ai ban",
        ),
    ),
    (
        ClaimType.SATURATION,
        (
            "bao hoa",
            "thi truong trong",
            "it canh tranh",
            "it doi thu",
            "chua khai thac",
            "nhieu doi thu",
            "dong doi thu",
            "saturated",
        ),
    ),
    (
        ClaimType.DEMAND,
        (
            "dong dan",
            "khu dan cu",
            "gan van phong",
            "luu luong khach",
            "dong khach",
            "nhieu khach",
            "gan truong",
            "foot traffic",
            "dong duc",
            "khach on dinh",
        ),
    ),
    (ClaimType.ACCESSIBILITY, ("giao thong", "de tiep can", "gan duong lon", "thuan tien", "de di")),
)


def classify_claim(text: str) -> ClaimType:
    folded = fold(text)
    for claim_type, keywords in _CLAIM_KEYWORDS:
        if any(kw in folded for kw in keywords):
            return claim_type
    return ClaimType.GENERIC


def _extract_radius_m(text: str, default: int = 500) -> int:
    """Pull a radius like '500m' or '1km' out of the claim; default 500 m."""
    folded = fold(text)
    km = re.search(r"(\d+(?:[.,]\d+)?)\s*km", folded)
    if km:
        return int(float(km.group(1).replace(",", ".")) * 1000)
    m = re.search(r"(\d+)\s*m(?:et)?\b", folded)
    if m:
        return int(m.group(1))
    return default


@dataclass
class ClaimVerdict:
    claim: str
    claim_type: ClaimType
    verdict: VerdictLabel
    reason: str
    evidence: list[str] = field(default_factory=list)
    confidence: str = "medium"
    explanation: str | None = None  # filled by Gemini when available

    def to_dict(self) -> dict[str, object]:
        return {
            "claim": self.claim,
            "claim_type": self.claim_type.value,
            "verdict": self.verdict.value,
            "verdict_vi": self.verdict.vi,
            "reason": self.reason,
            "evidence": self.evidence,
            "confidence": self.confidence,
            "explanation": self.explanation,
        }


def _confidence_from_coverage(coverage: CoverageAssessment, base: str = "high") -> str:
    factor = coverage.confidence_factor
    if factor >= 0.9:
        return base
    if factor >= 0.5:
        return "medium"
    return "low"


def evaluate_claim_deterministic(
    claim: str,
    metrics: AreaMetrics,
    coverage: CoverageAssessment,
) -> ClaimVerdict:
    """Compute a verdict for one claim from tool numbers only. No LLM, no network."""
    claim_type = classify_claim(claim)

    if claim_type == ClaimType.PRICE:
        return ClaimVerdict(
            claim=claim,
            claim_type=claim_type,
            verdict=VerdictLabel.INSUFFICIENT,
            reason=(
                "Không có nguồn dữ liệu giá thuê mặt bằng đáng tin (Places price level là mức giá dịch vụ, "
                "không phải tiền thuê; các trang rao vặt chặn thu thập). Không thể kết luận về giá."
            ),
            evidence=[],
            confidence="high",  # high confidence that we CANNOT decide
        )

    if claim_type == ClaimType.COMPETITOR_ABSENCE:
        return _verdict_competitor_absence(claim, metrics, coverage)

    if claim_type == ClaimType.SATURATION:
        return _verdict_saturation(claim, metrics, coverage)

    if claim_type == ClaimType.DEMAND:
        return _verdict_demand(claim, metrics, coverage)

    if claim_type == ClaimType.ACCESSIBILITY:
        return _verdict_accessibility(claim, metrics, coverage)

    return ClaimVerdict(
        claim=claim,
        claim_type=claim_type,
        verdict=VerdictLabel.INSUFFICIENT,
        reason="Tuyên bố chung chung, cần dữ liệu cụ thể hơn để kiểm chứng bằng bản đồ.",
        confidence="low",
    )


def _verdict_competitor_absence(claim, metrics, coverage) -> ClaimVerdict:
    radius = _extract_radius_m(claim)
    # Count competitors within the claimed radius, using the density ring at that
    # radius or the nearest ring at/above it.
    ring_count = next((r.count for r in metrics.competitor_density if r.radius_m == radius), None)
    if ring_count is None:
        ring_count = next((r.count for r in metrics.competitor_density if r.radius_m >= radius), None)

    nearest = metrics.nearest_competitor
    if nearest is not None and nearest.distance_m <= radius:
        evidence = [
            f"{ring_count if ring_count is not None else '≥1'} đối thủ trực tiếp trong bán kính {radius}m.",
            f"Đối thủ gần nhất cách {nearest.distance_m:.0f}m"
            + (f" ({nearest.name})" if nearest.name else "")
            + (" — thương hiệu chuỗi." if nearest.is_chain else "."),
        ]
        return ClaimVerdict(
            claim=claim,
            claim_type=ClaimType.COMPETITOR_ABSENCE,
            verdict=VerdictLabel.REFUTED,
            reason=f"Có đối thủ thực tế trong {radius}m, bác bỏ tuyên bố 'chưa có đối thủ'.",
            evidence=evidence,
            confidence=_confidence_from_coverage(coverage),
        )

    # No competitor found within the radius.
    if not coverage.can_assess_saturation:
        return ClaimVerdict(
            claim=claim,
            claim_type=ClaimType.COMPETITOR_ABSENCE,
            verdict=VerdictLabel.INSUFFICIENT,
            reason="Không thấy đối thủ trong bán kính, NHƯNG truy vấn Places bị giới hạn hoặc thiếu "
            f"({coverage.tier.value}) nên không thể phân biệt 'thị trường trống' với 'lỗ hổng dữ liệu'.",
            evidence=[f"Quan sát {coverage.density_1km} POI; {coverage.coverage_ratio:.0%} nhóm truy vấn thành công."],
            confidence="low",
        )
    return ClaimVerdict(
        claim=claim,
        claim_type=ClaimType.COMPETITOR_ABSENCE,
        verdict=VerdictLabel.CONFIRMED,
        reason=f"Nhóm Places đối thủ hoàn tất, chưa chạm trần và không ghi nhận đối thủ trực tiếp trong {radius}m.",
        evidence=[f"0 đối thủ trong {radius}m trong mẫu Nearby Search đã trả về."],
        confidence=_confidence_from_coverage(coverage),
    )


def _verdict_saturation(claim, metrics, coverage) -> ClaimVerdict:
    if not coverage.can_assess_saturation:
        return ClaimVerdict(
            claim=claim,
            claim_type=ClaimType.SATURATION,
            verdict=VerdictLabel.INSUFFICIENT,
            reason=(
                f"Truy vấn Places bị giới hạn hoặc thiếu ({coverage.tier.value}); "
                "không đủ căn cứ kết luận về mức độ bão hòa."
            ),
            evidence=[f"Quan sát {coverage.density_1km} POI; {coverage.coverage_ratio:.0%} nhóm truy vấn thành công."],
            confidence="low",
        )
    count_1km = next((r.count for r in metrics.competitor_density if r.radius_m == 1000), 0)
    ratio = metrics.supply_demand.get("ratio")
    evidence = [f"{count_1km} đối thủ trực tiếp trong 1km."]
    if ratio is not None:
        evidence.append(f"Tỷ lệ cung/cầu {ratio} (đối thủ trên mỗi điểm cầu).")
    folded = fold(claim)
    claims_open_market = any(k in folded for k in ("chua bao hoa", "it canh tranh", "thi truong trong", "it doi thu"))
    dense = count_1km >= 50
    if claims_open_market and dense:
        return ClaimVerdict(
            claim=claim,
            claim_type=ClaimType.SATURATION,
            verdict=VerdictLabel.REFUTED,
            reason=f"Khu vực có {count_1km} đối thủ trong 1km — không phù hợp với mô tả 'chưa bão hòa/ít cạnh tranh'.",
            evidence=evidence,
            confidence=_confidence_from_coverage(coverage),
        )
    verdict = VerdictLabel.CONFIRMED if not dense else VerdictLabel.INSUFFICIENT
    return ClaimVerdict(
        claim=claim,
        claim_type=ClaimType.SATURATION,
        verdict=verdict,
        reason=f"Ghi nhận {count_1km} đối thủ trong 1km tại khu vực có dữ liệu tốt.",
        evidence=evidence,
        confidence=_confidence_from_coverage(coverage),
    )


def _verdict_demand(claim, metrics, coverage) -> ClaimVerdict:
    demand = metrics.demand
    if demand.missing:
        return ClaimVerdict(
            claim=claim,
            claim_type=ClaimType.DEMAND,
            verdict=VerdictLabel.INSUFFICIENT,
            reason=f"Thiếu dữ liệu cầu ({', '.join(demand.missing)}); không thể xác nhận mức độ đông khách. "
            "Các thành phần thiếu KHÔNG được coi là bằng 0.",
            evidence=[],
            confidence="low",
        )
    folded = fold(claim)
    parts = []
    if demand.residential is not None:
        parts.append(f"{demand.residential} khu/điểm dân cư")
    if demand.office is not None:
        parts.append(f"{demand.office} văn phòng")
    if demand.school is not None:
        parts.append(f"{demand.school} trường học")
    evidence = [", ".join(parts) + " trong bán kính phân tích."] if parts else []

    # Verify the specific proxy the claim leans on.
    wants_office = "van phong" in folded
    wants_resident = "dan cu" in folded or "dong dan" in folded
    if wants_office and (demand.office or 0) == 0:
        return ClaimVerdict(
            claim=claim,
            claim_type=ClaimType.DEMAND,
            verdict=VerdictLabel.REFUTED,
            reason="Tuyên bố dựa vào mật độ văn phòng, nhưng không ghi nhận văn phòng nào quanh vị trí.",
            evidence=evidence,
            confidence=_confidence_from_coverage(coverage),
        )
    if wants_resident and (demand.residential or 0) == 0:
        return ClaimVerdict(
            claim=claim,
            claim_type=ClaimType.DEMAND,
            verdict=VerdictLabel.REFUTED,
            reason="Tuyên bố dựa vào khu dân cư, nhưng không ghi nhận khu dân cư nào quanh vị trí.",
            evidence=evidence,
            confidence=_confidence_from_coverage(coverage),
        )
    demand_score = demand.present_score() or 0
    if demand_score > 0:
        return ClaimVerdict(
            claim=claim,
            claim_type=ClaimType.DEMAND,
            verdict=VerdictLabel.CONFIRMED,
            reason="Ghi nhận nguồn cầu thực tế quanh vị trí (dân cư/văn phòng/trường học).",
            evidence=evidence,
            confidence=_confidence_from_coverage(coverage),
        )
    return ClaimVerdict(
        claim=claim,
        claim_type=ClaimType.DEMAND,
        verdict=VerdictLabel.REFUTED,
        reason="Không ghi nhận nguồn cầu (dân cư/văn phòng/trường) quanh vị trí.",
        evidence=evidence,
        confidence=_confidence_from_coverage(coverage),
    )


def _verdict_accessibility(claim, metrics, coverage) -> ClaimVerdict:
    transport = metrics.demand.transport
    if transport is None:
        return ClaimVerdict(
            claim=claim,
            claim_type=ClaimType.ACCESSIBILITY,
            verdict=VerdictLabel.INSUFFICIENT,
            reason="Không đo được dữ liệu giao thông công cộng quanh vị trí.",
            confidence="low",
        )
    if transport > 0:
        return ClaimVerdict(
            claim=claim,
            claim_type=ClaimType.ACCESSIBILITY,
            verdict=VerdictLabel.CONFIRMED,
            reason=f"Ghi nhận {transport} điểm giao thông công cộng quanh vị trí.",
            evidence=[f"{transport} điểm public_transport/bến xe trong bán kính phân tích."],
            confidence=_confidence_from_coverage(coverage, base="medium"),
        )
    return ClaimVerdict(
        claim=claim,
        claim_type=ClaimType.ACCESSIBILITY,
        verdict=VerdictLabel.INSUFFICIENT,
        reason=(
            "Không ghi nhận điểm giao thông công cộng; Places không bảo đảm trả đầy đủ mọi điểm, "
            "chưa đủ để kết luận."
        ),
        confidence="low",
    )


# --------------------------------------------------------------------------- #
# Gemini enrichment. The deterministic verdicts above are authoritative; Gemini
# only writes the Vietnamese prose that explains them (README: "nó chỉ tổng hợp
# định tính và diễn giải bằng chứng"). Verdict labels are never changed by the
# LLM, so it cannot overclaim on missing data.
# --------------------------------------------------------------------------- #

SYSTEM_INSTRUCTION = (
    "Bạn là trợ lý thẩm định startup, phân tích khu vực xung quanh địa điểm kinh doanh. "
    "Bạn CHỈ được diễn giải các con số và verdict đã được công cụ tính sẵn — TUYỆT ĐỐI "
    "không tự tính lại, không đổi verdict, không bịa số liệu. Nếu dữ liệu thiếu, hãy nói rõ "
    "là thiếu. Viết tiếng Việt có dấu đầy đủ, ngắn gọn, khách quan."
)


class _ClaimExplanation(BaseModel):
    index: int = Field(description="Số thứ tự tuyên bố, bắt đầu từ 0")
    explanation: str = Field(description="Giải thích 1-2 câu, dựa CHỈ trên bằng chứng đã cho")


class _AreaNarrative(BaseModel):
    overall_summary: str = Field(description="Tổng hợp 2-3 câu về khu vực, dựa trên bằng chứng")
    claim_explanations: list[_ClaimExplanation] = Field(default_factory=list)


@dataclass
class AreaVerdictReport:
    claims: list[ClaimVerdict]
    overall_summary: str
    llm_used: bool
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "claims": [c.to_dict() for c in self.claims],
            "overall_summary": self.overall_summary,
            "llm_used": self.llm_used,
            "warnings": self.warnings,
        }


def _build_prompt(claims: list[ClaimVerdict], metrics: AreaMetrics, coverage: CoverageAssessment) -> str:
    lines = [
        "GIỚI HẠN DỮ LIỆU (bắt buộc tôn trọng):",
        "- Nguồn POI là Google Places API (New); KHÔNG có giá thuê mặt bằng, KHÔNG dùng 'popular times'.",
        "- Nearby Search tối đa 20 kết quả mỗi nhóm; số đếm có thể là GIỚI HẠN DƯỚI.",
        f"- Đánh giá độ đầy đủ truy vấn: {coverage.tier.value} "
        f"({coverage.density_1km} POI quan sát, {coverage.coverage_ratio:.0%} nhóm truy vấn thành công).",
    ]
    if coverage.warnings:
        lines.append("- Cảnh báo độ phủ: " + " ".join(coverage.warnings))
    if metrics.demand.missing:
        lines.append(f"- Chỉ số cầu KHÔNG đo được (không phải bằng 0): {', '.join(metrics.demand.missing)}.")

    lines.append("\nSỐ LIỆU CÔNG CỤ (đã tính sẵn, không được đổi):")
    lines.append(json.dumps(metrics.to_dict(), ensure_ascii=False))

    lines.append("\nCÁC TUYÊN BỐ & VERDICT ĐÃ CHỐT (chỉ viết diễn giải, giữ nguyên verdict):")
    for i, c in enumerate(claims):
        lines.append(f"[{i}] Tuyên bố: {c.claim}")
        lines.append(f"    Verdict: {c.verdict.vi} | Căn cứ: {c.reason}")
        if c.evidence:
            lines.append(f"    Bằng chứng: {' '.join(c.evidence)}")

    lines.append(
        "\nNhiệm vụ: với mỗi tuyên bố, viết 1-2 câu diễn giải verdict dựa CHỈ trên bằng chứng trên. "
        "Viết overall_summary 2-3 câu về khu vực. Không thêm số liệu mới."
    )
    return "\n".join(lines)


async def evaluate_claims(
    claim_texts: list[str],
    metrics: AreaMetrics,
    coverage: CoverageAssessment,
    *,
    use_gemini: bool = True,
) -> AreaVerdictReport:
    """Evaluate every claim deterministically, then (optionally) add Gemini prose.

    Never raises on LLM failure: without an API key, or on any Gemini error, the
    deterministic reasons stand in as explanations.
    """
    verdicts = [evaluate_claim_deterministic(text, metrics, coverage) for text in claim_texts]
    for v in verdicts:
        v.explanation = v.reason  # default; upgraded by Gemini below when available

    default_summary = _deterministic_summary(verdicts, coverage)
    if not use_gemini or not claim_texts:
        return AreaVerdictReport(claims=verdicts, overall_summary=default_summary, llm_used=False)

    # Imported lazily so the whole module works with no LLM configured / installed.
    try:
        from app.llm.gemini import GeminiNotConfiguredError, get_llm_client
    except Exception:  # noqa: BLE001
        return AreaVerdictReport(claims=verdicts, overall_summary=default_summary, llm_used=False)

    try:
        narrative = await get_llm_client().generate_structured(
            prompt=_build_prompt(verdicts, metrics, coverage),
            system_instruction=SYSTEM_INSTRUCTION,
            response_model=_AreaNarrative,
        )
    except GeminiNotConfiguredError:
        return AreaVerdictReport(claims=verdicts, overall_summary=default_summary, llm_used=False)
    except Exception as exc:  # noqa: BLE001 - never let LLM failure break the report
        return AreaVerdictReport(
            claims=verdicts,
            overall_summary=default_summary,
            llm_used=False,
            warnings=[f"Gemini lỗi, dùng diễn giải deterministic: {exc}"],
        )

    # Attach explanations by index; the verdict label itself is never touched.
    by_index = {e.index: e.explanation for e in narrative.claim_explanations}
    for i, v in enumerate(verdicts):
        if i in by_index and by_index[i].strip():
            v.explanation = by_index[i].strip()
    return AreaVerdictReport(
        claims=verdicts,
        overall_summary=narrative.overall_summary.strip() or default_summary,
        llm_used=True,
    )


def _deterministic_summary(verdicts: list[ClaimVerdict], coverage: CoverageAssessment) -> str:
    if not verdicts:
        return (
            f"Khu vực có độ đầy đủ truy vấn mức '{coverage.tier.value}' "
            f"({coverage.density_1km} POI quan sát). Chưa có tuyên bố nào để kiểm chứng."
        )
    counts = {label: sum(1 for v in verdicts if v.verdict == label) for label in VerdictLabel}
    return (
        f"Đã kiểm chứng {len(verdicts)} tuyên bố: "
        f"{counts[VerdictLabel.CONFIRMED]} xác nhận, {counts[VerdictLabel.REFUTED]} bác bỏ, "
        f"{counts[VerdictLabel.INSUFFICIENT]} chưa đủ thông tin. "
        f"Độ đầy đủ truy vấn Places: {coverage.tier.value}."
    )
