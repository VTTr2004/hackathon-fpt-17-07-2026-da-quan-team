"""Surrounding-area analyzer: classify -> locate -> query Google Places -> assess coverage
-> compute metrics -> adjudicate claims -> ModuleReport.

The pipeline follows plan section 5. Two status semantics are fixed here relative
to the old stub (plan section 7.3):

    NOT_APPLICABLE     the industry does not depend on location (SaaS, fintech).
                       The aggregator drops the module; it is NOT scored 0.
    INSUFFICIENT_DATA  location-dependent, but coordinates or map data are
                       missing. This is a data gap to fill, not "not applicable".

All numbers come from deterministic tools; Gemini only writes prose (see
verdict.py). A failed POI sub-query degrades the report to PARTIAL with a
warning — it is never silently treated as zero (plan section 7.2).
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any

from app.modules.surrounding_area.providers.places import PLACES_NEW_VERSION, is_configured, lookup_place, survey_area
from app.modules.surrounding_area.providers.satellite import SATELLITE_CONTEXT_VERSION, fetch_satellite_context
from app.modules.surrounding_area.tools.coverage import PLACES_COVERAGE_VERSION, assess_places_coverage
from app.modules.surrounding_area.tools.geo import score_location
from app.modules.surrounding_area.tools.industry_taxonomy import (
    LocationDependency,
    classify_location_dependency,
    resolve_competitor_filter,
)
from app.modules.surrounding_area.tools.poi_metrics import (
    POI_METRICS_VERSION,
    build_area_metrics,
)
from app.modules.surrounding_area.verdict import VERDICT_VERSION, VerdictLabel, evaluate_claims
from app.schemas.common import (
    AnalysisModule,
    AnalysisStatus,
    Evidence,
    Finding,
    ModuleReport,
    ToolCall,
)

ANALYSIS_RADIUS_M = 1000
MODULE_VERSION = "2.0.0"
# Backward-compatible injection names for the old focused provider test. The
# production path below uses Nearby Search data directly and performs no N+1
# enrichment calls.
places_is_configured = is_configured


class SurroundingAreaAnalyzer:
    async def analyze(
        self,
        startup_facts: dict[str, Any],
        documents: list[dict[str, Any]],
        options: dict[str, Any],
    ) -> ModuleReport:
        industry = startup_facts.get("industry")
        # Coordinates may come from the saved profile OR directly from the analysis
        # request options — the latter lets the frontend run analysis right after
        # the analyst confirms a geocoded pin, without a separate profile-update
        # call. Saved facts win if both are present.
        location = self._resolve_location(startup_facts, options)

        # --- Step 0: does location even matter for this industry? --------------
        # An explicit answer ("does the startup depend on surrounding customers?")
        # from the profile or the analyst overrides the industry-based inference.
        explicit_dep = self._explicit_dependency(startup_facts, location, options)
        classification = classify_location_dependency(industry, explicit=explicit_dep)
        if classification.dependency == LocationDependency.INDEPENDENT:
            return ModuleReport(
                module=AnalysisModule.SURROUNDING_AREA,
                version=MODULE_VERSION,
                status=AnalysisStatus.NOT_APPLICABLE,
                score=None,
                summary=(
                    f"Ngành '{industry}' không phụ thuộc vị trí vật lý "
                    f"({classification.label_vi}); phân tích khu vực không áp dụng. "
                    "Module này cần được loại khỏi công thức tính điểm, KHÔNG chấm 0."
                ),
                methodology=[f"Location-dependency classification v1.0 ({classification.reason})"],
                details={"classification": classification.__dict__},
            )

        # --- Step 1: coordinates (geocoding + confirmation happen upstream) -----
        lat, lon = location.get("lat"), location.get("lon")
        if lat is None or lon is None:
            return ModuleReport(
                module=AnalysisModule.SURROUNDING_AREA,
                version=MODULE_VERSION,
                status=AnalysisStatus.INSUFFICIENT_DATA,  # NOT not_applicable (7.3)
                score=None,
                summary="Ngành phụ thuộc vị trí nhưng chưa có tọa độ đã xác nhận. "
                "Hãy geocode địa chỉ và xác nhận vị trí trên bản đồ trước khi phân tích.",
                missing_data=["location.lat", "location.lon"],
                recommended_questions=["Địa chỉ chính xác của địa điểm kinh doanh là gì?"],
                details={"classification": classification.__dict__},
            )
        lat, lon = float(lat), float(lon)

        # --- Step 2: query Google Places (New) ---------------------------------
        if not is_configured():
            return ModuleReport(
                module=AnalysisModule.SURROUNDING_AREA,
                version=MODULE_VERSION,
                status=AnalysisStatus.INSUFFICIENT_DATA,
                score=None,
                summary="Chưa cấu hình Google Places API (New) cho backend.",
                missing_data=["GOOGLE_PLACES_API_KEY"],
                recommended_questions=[
                    "Đã bật Places API (New), billing và giới hạn API key cho backend chưa?"
                ],
                details={"classification": classification.__dict__},
            )

        if classification.matched_profile not in {"food_beverage", "retail"}:
            return ModuleReport(
                module=AnalysisModule.SURROUNDING_AREA,
                version=MODULE_VERSION,
                status=AnalysisStatus.NOT_APPLICABLE,
                score=None,
                summary=(
                    "Surrounding Area hiện chỉ triển khai Google Places cho F&B và bán lẻ nhỏ. "
                    f"Ngành '{industry}' nằm ngoài phạm vi phiên bản này."
                ),
                details={"classification": classification.__dict__, "supported_profiles": ["food_beverage", "retail"]},
            )
        competitor_filter = resolve_competitor_filter(industry)
        target_radius_m = self._target_radius(location)
        try:
            survey = await asyncio.to_thread(
                survey_area,
                lat,
                lon,
                radius_m=target_radius_m,
                industry_profile=competitor_filter.profile_key,
            )
        except Exception as exc:  # noqa: BLE001 - provider failures become explicit missing data
            return ModuleReport(
                module=AnalysisModule.SURROUNDING_AREA,
                version=MODULE_VERSION,
                status=AnalysisStatus.INSUFFICIENT_DATA,
                score=None,
                summary="Không truy vấn được Google Places API (New).",
                missing_data=["google_places_nearby_search"],
                risks=[str(exc)],
                details={"classification": classification.__dict__, "error": str(exc)},
            )

        query_warnings = list(survey.warnings)
        demand_counts = {
            proxy: None if rows is None else len(rows)
            for proxy, rows in survey.demand_places.items()
        }
        competitors_list = survey.competitors
        competitor_group = next(group for group in survey.groups if group.name == "competitors")
        competitor_measurable = competitor_group.warning is None

        # --- Step 3: bounded-provider coverage guard ---------------------------
        coverage = assess_places_coverage(
            observed_place_count=len(survey.all_places),
            successful_groups=survey.successful_groups,
            total_groups=len(survey.groups),
            competitor_capped=survey.competitor_capped,
        )

        # --- Step 4: metrics (deterministic) -----------------------------------
        metrics = build_area_metrics(
            industry_profile=competitor_filter.profile_key,
            competitors=competitors_list,
            demand_counts=demand_counts,
            extra_warnings=[*coverage.warnings, *query_warnings],
        )

        # --- Step 5: adjudicate claims -----------------------------------------
        claims = self._extract_claims(startup_facts, options, location, documents)
        use_gemini = options.get("use_gemini", True)
        verdict_report = await evaluate_claims(claims, metrics, coverage, use_gemini=use_gemini)

        map_pois = self._places_map_payload(lat, lon, survey)
        places_enrichment = self._places_enrichment(competitors_list)
        satellite_context = None
        if options.get("include_satellite") is True:
            satellite_context = await asyncio.to_thread(
                fetch_satellite_context,
                lat,
                lon,
                radius_m=target_radius_m,
            )

        # --- Step 6: assemble ModuleReport -------------------------------------
        return self._build_report(
            lat=lat,
            lon=lon,
            industry=industry,
            classification=classification,
            coverage=coverage,
            metrics=metrics,
            verdict_report=verdict_report,
            competitors=competitors_list,
            competitor_measurable=competitor_measurable,
            demand_counts=demand_counts,
            query_warnings=query_warnings,
            survey=survey,
            location=location,
            map_pois=map_pois,
            places_enrichment=places_enrichment,
            satellite_context=satellite_context,
        )

    # ---- helpers ----------------------------------------------------------- #

    @staticmethod
    def _resolve_location(startup_facts: dict[str, Any], options: dict[str, Any]) -> dict[str, Any]:
        """Merge canonical location data with flat profile-form aliases."""
        location: dict[str, Any] = {}
        option_location = options.get("location")
        saved_location = startup_facts.get("location")
        if isinstance(option_location, dict):
            location.update(option_location)
        if isinstance(saved_location, dict):
            location.update(saved_location)

        aliases = {
            "exact_location": "address",
            "location_type": "type",
            "target_customer_radius_m": "target_radius_m",
            "known_nearby_competitors": "known_competitors",
        }
        for source_key, target_key in aliases.items():
            if target_key not in location and startup_facts.get(source_key):
                location[target_key] = startup_facts[source_key]

        for key in ("type", "tenure", "area_m2", "rent_cost", "target_radius_m", "operating_hours"):
            if key not in location and startup_facts.get(key) is not None:
                location[key] = startup_facts[key]

        return location

    @staticmethod
    def _target_radius(location: dict[str, Any]) -> int:
        try:
            radius = int(str(location.get("target_radius_m") or ANALYSIS_RADIUS_M).replace(",", "").replace(".", ""))
        except (TypeError, ValueError):
            radius = ANALYSIS_RADIUS_M
        return min(3000, max(100, radius))

    @staticmethod
    def _explicit_dependency(startup_facts: dict[str, Any], location: dict[str, Any], options: dict[str, Any]):
        """Resolve an explicit location-dependency override from the profile.

        Honours (in order): options["location_dependency"],
        facts["location_dependency"], or the direct yes/no answer
        location["depends_on_surrounding_customers"] (True -> primary).
        Anything unrecognised returns None so the industry inference is used.
        """
        aliases = {
            "phụ thuộc lượng khách xung quanh": "primary",
            "phu thuoc luong khach xung quanh": "primary",
            "vị trí hỗ trợ vận hành": "supporting",
            "vi tri ho tro van hanh": "supporting",
            "không phụ thuộc vị trí": "independent",
            "khong phu thuoc vi tri": "independent",
            "chưa xác định": None,
            "chua xac dinh": None,
            "auto": None,
        }
        for source in (options.get("location_dependency"), startup_facts.get("location_dependency")):
            if isinstance(source, str) and source.strip():
                value = source.strip().lower()
                return aliases.get(value, value)
        depends = location.get("depends_on_surrounding_customers")
        if depends is True:
            return "primary"
        return None

    @staticmethod
    def _extract_claims(
        startup_facts: dict[str, Any],
        options: dict[str, Any],
        location: dict[str, Any],
        documents: list[dict[str, Any]],
    ) -> list[str]:
        """Collect area claims to verify.

        Accepts them from options["claims"], facts["area_claims"], or a claims
        list nested under the resolved location (from either facts or options).
        Each must be a non-empty string; duplicates are removed.
        """
        raw: list[Any] = []
        raw += options.get("claims") or []
        raw += startup_facts.get("area_claims") or []
        if isinstance(location, dict):
            raw += location.get("claims") or []
        if not raw:
            raw += SurroundingAreaAnalyzer._claims_from_documents(documents)
        seen: dict[str, None] = {}
        for c in raw:
            text = str(c).strip()
            if text:
                seen.setdefault(text, None)
        return list(seen)

    @staticmethod
    def _claims_from_documents(documents: list[dict[str, Any]]) -> list[str]:
        """Best-effort deterministic extraction of area-related claims.

        This is intentionally conservative: only short sentences containing
        location/competition/rent/demand keywords are kept. Gemini may later
        explain verdicts, but it is not needed to discover these candidate claims.
        """
        keywords = (
            "đối thủ",
            "doi thu",
            "cạnh tranh",
            "canh tranh",
            "bão hòa",
            "bao hoa",
            "dân cư",
            "dan cu",
            "văn phòng",
            "van phong",
            "trường",
            "truong",
            "giao thông",
            "giao thong",
            "giá thuê",
            "gia thue",
            "mặt bằng",
            "mat bang",
            "500m",
            "1km",
            "khu vực",
            "khu vuc",
        )
        claims: list[str] = []
        for doc in documents[:5]:
            text = str(doc.get("text") or "")
            for raw_sentence in text.replace("\r", "\n").split("\n"):
                sentence = raw_sentence.strip(" -•\t")
                if not 12 <= len(sentence) <= 220:
                    continue
                folded = sentence.lower()
                if any(keyword in folded for keyword in keywords):
                    claims.append(sentence)
                if len(claims) >= 5:
                    return claims
        return claims

    @staticmethod
    def _places_enrichment(competitors) -> dict[str, Any]:
        """Expose fields already returned by Nearby Search; no N+1 lookups."""
        rows = []
        for poi in competitors[:20]:
            if hasattr(poi, "to_dict"):
                item = poi.to_dict()
                item["reviews"] = []
            else:  # compatibility for legacy POI-like objects in unit tests
                lookup = lookup_place(poi.name or "", poi.lat, poi.lon) if places_is_configured() else None
                google_data = lookup.enrichment if lookup else None
                item = {
                    "place_id": google_data.place_id if google_data else None,
                    "name": poi.name,
                    "category": poi.category_value,
                    "distance_m": poi.distance_m,
                    "is_chain": poi.is_chain,
                    "google_maps_url": poi.google_maps_url(),
                    "rating": google_data.rating if google_data else None,
                    "user_ratings_total": google_data.user_ratings_total if google_data else None,
                    "price_level": google_data.price_level if google_data else None,
                    "price_label": google_data.price_label if google_data else None,
                    "reviews": google_data.reviews if google_data else [],
                    "source": "google_places" if google_data else "manual_survey_link",
                }
            rows.append(item)
        return {"configured": True, "items": rows, "warnings": []}

    @staticmethod
    def _places_map_payload(lat: float, lon: float, survey) -> dict[str, Any]:
        """Frontend map payload built only from Google Places observations."""
        return {
            "center": {"lat": lat, "lon": lon},
            "eateries": [place.to_dict() for place in survey.eateries],
            # Google Places does not provide residential polygons/zones.
            "residential": [],
            "competitors": [place.to_dict() for place in survey.competitors],
        }

    def _build_report(
        self,
        *,
        lat,
        lon,
        industry,
        classification,
        coverage,
        metrics,
        verdict_report,
        competitors,
        competitor_measurable,
        demand_counts,
        query_warnings,
        survey,
        location,
        map_pois,
        places_enrichment,
        satellite_context,
    ) -> ModuleReport:
        evidence = [
            Evidence(
                evidence_id="google-places-api-new",
                source_type="external_research",
                title="Google Places API (New) - Nearby Search",
                publisher="Google Maps Platform",
                url="https://developers.google.com/maps/documentation/places/web-service/nearby-search",
                accessed_at=datetime.now(UTC).isoformat(),
                reliability="medium",
                notes="POI quan sát theo bán kính; mỗi nhóm tối đa 20 kết quả và không phải tổng điều tra đầy đủ.",
            )
        ]
        if satellite_context:
            evidence.append(
                Evidence(
                    evidence_id="copernicus-sentinel-2",
                    source_type="external_research",
                    title="Sentinel-2 L2A satellite scenes",
                    publisher="Copernicus Data Space Ecosystem",
                    url=satellite_context.get("source_url"),
                    accessed_at=None,
                    reliability="medium",
                    notes="Metadata/quicklook scene lookup from the public STAC catalogue.",
                )
            )

        findings = [
            Finding(
                title=f"[{v.verdict.vi}] {v.claim}",
                detail=v.explanation or v.reason,
                evidence_ids=["google-places-api-new"],
                confidence=v.confidence,
            )
            for v in verdict_report.claims
        ]
        # Always include a coverage finding so a thin map is visible even with no claims.
        findings.append(
            Finding(
                title=f"Độ đầy đủ truy vấn Places: {coverage.tier.value}",
                detail=f"Quan sát {coverage.density_1km} POI; {coverage.coverage_ratio:.0%} nhóm truy vấn thành công. "
                + (" ".join(coverage.warnings) if coverage.warnings else "Các nhóm truy vấn đã hoàn tất."),
                evidence_ids=["google-places-api-new"],
                confidence="high" if coverage.can_assess_saturation else "low",
            )
        )

        risks = list(coverage.warnings)
        if not competitor_measurable:
            risks.append("Không đo được mật độ đối thủ cho ngành này; kết luận cạnh tranh bị hạn chế.")

        missing_data: list[str] = []
        for proxy, count in demand_counts.items():
            if count is None:
                missing_data.append(f"demand:{proxy}")

        # Status semantics:
        #   thin map (can't judge the core saturation question) -> INSUFFICIENT_DATA
        #     (plan section 9: Bien Hoa must not be scored as an opportunity);
        #   good map but a sub-query failed -> PARTIAL;
        #   good map, everything measured -> COMPLETED.
        had_query_failure = bool(query_warnings) or not competitor_measurable
        if not coverage.can_assess_saturation:
            status = AnalysisStatus.INSUFFICIENT_DATA
        elif had_query_failure:
            status = AnalysisStatus.PARTIAL
        else:
            status = AnalysisStatus.COMPLETED

        score = self._compute_score(metrics, coverage, competitor_measurable)

        tool_calls = [
            ToolCall(
                name="poi_area_metrics",
                version=POI_METRICS_VERSION,
                input={"lat": lat, "lon": lon, "radius_m": ANALYSIS_RADIUS_M, "industry": industry},
                output=metrics.to_dict(),
                warnings=metrics.warnings,
            ),
            ToolCall(
                name="google_places_request_coverage",
                version=PLACES_COVERAGE_VERSION,
                input={
                    "successful_groups": survey.successful_groups,
                    "total_groups": len(survey.groups),
                    "competitor_capped": survey.competitor_capped,
                },
                output=coverage.to_dict(),
                warnings=coverage.warnings,
            ),
            ToolCall(
                name="claim_verdicts",
                version=VERDICT_VERSION,
                input={"claims": [c.claim for c in verdict_report.claims]},
                output=verdict_report.to_dict(),
            ),
            ToolCall(
                name="google_places_nearby_search",
                version=PLACES_NEW_VERSION,
                input={"radius_m": self._target_radius(location), "provider": "google_places_new"},
                output=places_enrichment,
                warnings=places_enrichment["warnings"],
            ),
        ]
        if satellite_context:
            tool_calls.append(
                ToolCall(
                    name="satellite_scene_context",
                    version=SATELLITE_CONTEXT_VERSION,
                    input={
                        "lat": lat,
                        "lon": lon,
                        "radius_m": satellite_context.get("radius_m"),
                        "days": satellite_context.get("days"),
                    },
                    output=satellite_context,
                    warnings=satellite_context.get("warnings", []),
                )
            )

        return ModuleReport(
            module=AnalysisModule.SURROUNDING_AREA,
            version=MODULE_VERSION,
            status=status,
            score=score,
            summary=verdict_report.overall_summary,
            findings=findings,
            risks=list(dict.fromkeys(risks)),
            missing_data=missing_data,
            assumptions=[
                "Khoảng cách là đường chim bay (haversine), không phải quãng đường thực tế.",
                "Nearby Search tối đa 20 kết quả mỗi nhóm; số đếm có thể là giới hạn dưới.",
                "Places không cung cấp mật độ dân cư; residential luôn là dữ liệu thiếu.",
            ],
            recommended_questions=self._questions(verdict_report),
            evidence=evidence,
            methodology=[
                f"Location-dependency classification v1.0 ({classification.label_vi})",
                "Google Places API (New) Nearby Search + loại trùng bằng place_id",
                "Haversine ring counts + bounded-provider coverage assessment v2.0",
                f"Deterministic claim verdicts v{VERDICT_VERSION}"
                + (" + Gemini narrative" if verdict_report.llm_used else " (no LLM)"),
            ],
            tool_calls=tool_calls,
            details={
                "location": {"lat": lat, "lon": lon},
                # Profile inputs echoed back for transparency. The startup's own
                # stated rent is a KNOWN fact; the module still cannot benchmark it
                # against a market rate (no source), which stays INSUFFICIENT.
                "location_profile": self._location_profile(location),
                "classification": classification.__dict__,
                "coverage": coverage.to_dict(),
                "metrics": metrics.to_dict(),
                "verdicts": verdict_report.to_dict(),
                "map": map_pois,
                "places_enrichment": places_enrichment,
                "satellite_context": satellite_context,
                "llm_used": verdict_report.llm_used,
            },
        )

    @staticmethod
    def _compute_score(metrics, coverage, competitor_measurable) -> float | None:
        """A 0-100 location score, or None when data is too thin to be honest.

        Only emitted for GOOD coverage with measurable competition and demand —
        otherwise the verdicts carry the finding and score stays null (never 0
        for missing data, per plan section 14).
        """
        if not coverage.can_assess_saturation or not competitor_measurable:
            return None
        demand = metrics.demand
        if demand.present_score() is None:
            return None

        # Normalise three 0-100 sub-metrics, letting score_location handle any that
        # cannot be computed (it renormalises rather than zero-filling).
        sub: dict[str, float] = {}
        # Demand: more proxies present -> higher, capped.
        sub["demand"] = min(100.0, (demand.present_score() or 0) * 5.0)
        # Competition balance: some competition validates the market, too much saturates.
        count_1km = next((r.count for r in metrics.competitor_density if r.radius_m == 1000), 0)
        if count_1km == 0:
            sub["competition"] = 40.0  # unproven market
        elif count_1km <= 30:
            sub["competition"] = 90.0
        elif count_1km <= 80:
            sub["competition"] = 70.0
        else:
            sub["competition"] = 45.0
        weights = {"demand": 0.5, "competition": 0.5}
        result = score_location(sub, weights)
        base = result["score"]
        if base is None:
            return None
        return round(base * coverage.confidence_factor, 2)

    @staticmethod
    def _location_profile(location: dict[str, Any]) -> dict[str, Any]:
        """Echo the analyst-provided location facts (type, tenure, area, own rent,
        target radius, known competitors). These are inputs, not analysis output;
        the startup's own rent is a known fact but is NOT a market benchmark."""
        if not isinstance(location, dict):
            return {}
        return {
            "type": location.get("type"),
            "tenure": location.get("tenure"),  # thuê / sở hữu
            "area_m2": location.get("area_m2"),
            "stated_rent": location.get("rent_cost"),  # startup's own figure, not a market rate
            "target_radius_m": location.get("target_radius_m"),
            "operating_hours": location.get("operating_hours"),
            "known_competitors": location.get("known_competitors") or [],
        }

    @staticmethod
    def _questions(verdict_report) -> list[str]:
        questions = []
        for v in verdict_report.claims:
            if v.verdict == VerdictLabel.INSUFFICIENT:
                questions.append(f"Cần thêm bằng chứng cho tuyên bố: '{v.claim}'.")
        return questions
