"use client";

import "leaflet/dist/leaflet.css";

import type { LayerGroup, Map as LeafletMap } from "leaflet";
import { FormEvent, useEffect, useMemo, useRef, useState } from "react";

import { api } from "@/lib/api";
import type {
  Analysis,
  ClaimVerdict,
  GeocodeCandidate,
  MapPoi,
  PlacesEnrichmentItem,
  SatelliteContext,
  SurroundingMapData,
} from "@/types";

type Props = {
  startupId: string;
  industry: string | null;
  initialAddress?: string;
  facts?: Record<string, unknown>;
  initialAnalysis?: Analysis;
  onAnalysisComplete?: (analysis: Analysis) => void;
};

type DependencyChoice = "auto" | "primary" | "supporting" | "independent";

const dependencyOptions: Array<{ value: DependencyChoice; label: string }> = [
  { value: "auto", label: "Tự suy luận" },
  { value: "primary", label: "Phụ thuộc vị trí" },
  { value: "supporting", label: "Vị trí hỗ trợ" },
  { value: "independent", label: "Không áp dụng" },
];

const claimTemplates = [
  "Chưa có đối thủ trực tiếp trong bán kính 500m",
  "Khu dân cư đông đúc",
  "Gần văn phòng nên lưu lượng khách ổn định",
  "Giá thuê mặt bằng khu này rẻ",
];

const verdictStyle: Record<string, { className: string; label: string }> = {
  xac_nhan: { className: "confirmed", label: "Xác nhận" },
  bac_bo: { className: "refuted", label: "Bác bỏ" },
  chua_du_thong_tin: { className: "insufficient", label: "Chưa đủ thông tin" },
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function toNumber(value: unknown) {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function parseRadius(value: string) {
  const radius = Number(value.replace(/[,. ]/g, ""));
  if (!Number.isFinite(radius) || radius <= 0) return null;
  return Math.min(3000, Math.max(100, Math.round(radius)));
}

function splitList(value: string) {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function metricList(value: unknown): Array<{ radius_m: number; count: number }> {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => {
      if (!isRecord(item)) return null;
      const radius = toNumber(item.radius_m);
      const count = toNumber(item.count);
      return radius !== null && count !== null ? { radius_m: radius, count } : null;
    })
    .filter((item): item is { radius_m: number; count: number } => item !== null);
}

function centerFromAnalysis(analysis?: Analysis) {
  const details = analysis?.report.details;
  const location = isRecord(details?.location) ? details.location : null;
  const lat = toNumber(location?.lat);
  const lon = toNumber(location?.lon);
  return lat !== null && lon !== null ? { lat, lon } : null;
}

function mapFromAnalysis(analysis?: Analysis) {
  return analysis?.report.details?.map ?? null;
}

function radiusFromAnalysis(analysis?: Analysis) {
  const details = analysis?.report.details;
  const profiles = [details?.location_profile, details?.location].filter(isRecord);
  for (const profile of profiles) {
    const radius = toNumber(profile.target_radius_m);
    if (radius !== null && radius > 0) return Math.min(3000, Math.max(100, Math.round(radius)));
  }
  return null;
}

function factString(facts: Record<string, unknown> | undefined, key: string) {
  const value = facts?.[key];
  if (typeof value === "string") return value.trim();
  if (typeof value === "number") return String(value);
  return "";
}

function factListString(facts: Record<string, unknown> | undefined, key: string) {
  const value = facts?.[key];
  if (Array.isArray(value)) return value.map(String).join(", ");
  return typeof value === "string" ? value : "";
}

function radiusFromFacts(facts: Record<string, unknown> | undefined) {
  return parseRadius(factString(facts, "target_customer_radius_m") || factString(facts, "target_radius_m"));
}

function dependencyFromFact(value: unknown): DependencyChoice {
  const text = String(value ?? "").toLowerCase();
  if (text.includes("primary") || text.includes("phụ thuộc")) return "primary";
  if (text.includes("supporting") || text.includes("hỗ trợ") || text.includes("vận hành")) return "supporting";
  if (text.includes("independent") || text.includes("không phụ thuộc") || text.includes("không áp dụng")) return "independent";
  return "auto";
}

function claimsFromFacts(facts: Record<string, unknown> | undefined) {
  const value = facts?.area_claims ?? facts?.location_claims;
  if (Array.isArray(value)) return value.map(String).join("\n");
  return typeof value === "string" ? value : "";
}

function satelliteStatusLabel(status?: string) {
  if (status === "clear_recent_scene") return "Ảnh rõ";
  if (status === "usable_cloudy_scene") return "Dùng được";
  if (status === "cloudy_or_unrated_scene") return "Nhiều mây";
  return "Chưa có cảnh";
}

function sceneDate(value?: string | null) {
  if (!value) return "Chưa rõ ngày";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString("vi-VN", { day: "2-digit", month: "2-digit", year: "numeric" });
}

function PoiPreviewList({ title, items, empty }: { title: string; items: MapPoi[]; empty: string }) {
  return (
    <div className="poiPreview">
      <div className="poiPreviewHeader">
        <strong>{title}</strong>
        <span>{items.length}</span>
      </div>
      {items.length === 0 ? (
        <p className="muted smallText">{empty}</p>
      ) : (
        <div className="poiPreviewList">
          {items.slice(0, 6).map((item, index) => {
            const content = (
              <>
                <span>{item.name ?? "(không tên)"}</span>
                <small>
                  {Math.round(item.distance_m)}m{item.category ? ` · ${item.category}` : ""}
                </small>
                <small>{poiSourceLabel(item)}</small>
              </>
            );
            return item.google_maps_url ? (
              <a href={item.google_maps_url} key={`${title}-${item.lat}-${item.lon}-${index}`} target="_blank" rel="noreferrer">
                {content}
              </a>
            ) : (
              <div key={`${title}-${item.lat}-${item.lon}-${index}`}>{content}</div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function ScanMetric({ label, value, hint }: { label: string; value: string | number; hint?: string }) {
  return (
    <div className="scanMetric">
      <span>{label}</span>
      <strong>{value}</strong>
      {hint && <small>{hint}</small>}
    </div>
  );
}

function nearestName(items: MapPoi[]) {
  const first = items[0];
  if (!first) return "Không có";
  return `${first.name ?? "Không tên"} · ${Math.round(first.distance_m)}m`;
}

function poiSourceLabel(item: MapPoi) {
  const quality = item.position_quality === "polygon_centroid" ? "OSM centroid" : "OSM point";
  return item.maps_match_status === "verified_google_maps" ? `${quality} · verified Maps` : `${quality} · chưa verify Maps`;
}

function PlacesSurveyList({ items }: { items: PlacesEnrichmentItem[] }) {
  if (!items.length) return null;

  return (
    <div className="placesSurvey">
      <div className="sectionHeader compact">
        <div>
          <p className="eyebrow">PRICE/RATING SURVEY</p>
          <h4>Top đối thủ cần khảo sát</h4>
        </div>
      </div>
      <div className="placesSurveyList">
        {items.slice(0, 8).map((item, index) => (
          <a href={item.google_maps_url} key={`${item.name}-${item.distance_m}-${index}`} target="_blank" rel="noreferrer">
            <span>
              <strong>{item.name ?? "Không tên"}</strong>
              <small>{Math.round(item.distance_m)}m · {item.category}</small>
            </span>
            <em>
              {item.rating ? `${item.rating}/5` : "Chưa có rating"}
              {" · "}
              {item.price_label ?? "Khảo sát giá"}
            </em>
          </a>
        ))}
      </div>
    </div>
  );
}

function SatellitePanel({ context, error }: { context: SatelliteContext | null; error?: string }) {
  const scene = context?.best_scene ?? null;

  return (
    <div className="satellitePanel">
      <div className="satelliteFrame">
        {scene?.thumbnail_url ? (
          <span
            aria-label="Sentinel-2 quicklook"
            className="satelliteImage"
            role="img"
            style={{ backgroundImage: `url(${scene.thumbnail_url})` }}
          />
        ) : (
          <div className="satelliteFallback">
            <span>Sentinel-2</span>
            <strong>{satelliteStatusLabel(context?.status)}</strong>
          </div>
        )}
        <span className={`satelliteStatus ${context?.status ?? "unavailable"}`}>
          {satelliteStatusLabel(context?.status)}
        </span>
      </div>
      <div className="satelliteMeta">
        <div>
          <span>Ngày chụp</span>
          <strong>{sceneDate(scene?.datetime)}</strong>
        </div>
        <div>
          <span>Mây</span>
          <strong>{scene?.cloud_cover !== null && scene?.cloud_cover !== undefined ? `${Math.round(scene.cloud_cover)}%` : "N/A"}</strong>
        </div>
        <div>
          <span>GSD</span>
          <strong>{scene?.gsd_m ? `${scene.gsd_m}m` : "10m"}</strong>
        </div>
        <div>
          <span>Cảnh</span>
          <strong>{context?.scenes.length ?? 0}</strong>
        </div>
      </div>
      {scene?.product_url && (
        <a className="textLink" href={scene.product_url} target="_blank" rel="noreferrer">
          Mở cảnh vệ tinh
        </a>
      )}
      {error && <p className="muted smallText">{error}</p>}
      {context?.warnings?.map((warning) => (
        <p className="muted smallText" key={warning}>
          {warning}
        </p>
      ))}
    </div>
  );
}

export default function SurroundingArea({
  startupId,
  industry,
  initialAddress = "",
  facts,
  initialAnalysis,
  onAnalysisComplete,
}: Props) {
  const defaultAddress = initialAddress || factString(facts, "exact_location") || factString(facts, "headquarters_address");
  const initialRadius = radiusFromAnalysis(initialAnalysis) ?? radiusFromFacts(facts) ?? 1000;
  const [address, setAddress] = useState(defaultAddress);
  const initialCenter = centerFromAnalysis(initialAnalysis);
  const [manualLat, setManualLat] = useState(initialCenter ? String(initialCenter.lat) : "");
  const [manualLon, setManualLon] = useState(initialCenter ? String(initialCenter.lon) : "");
  const [dependency, setDependency] = useState<DependencyChoice>(() => dependencyFromFact(facts?.location_dependency));
  const [candidates, setCandidates] = useState<GeocodeCandidate[]>([]);
  const [geocodeWarnings, setGeocodeWarnings] = useState<string[]>([]);
  const [center, setCenter] = useState<{ lat: number; lon: number } | null>(initialCenter);
  const [confirmed, setConfirmed] = useState(Boolean(initialCenter));
  const [claims, setClaims] = useState(claimsFromFacts(facts) || claimTemplates.slice(0, 2).join("\n"));
  const [scanRadiusM, setScanRadiusM] = useState(initialRadius);
  const [scanRadiusText, setScanRadiusText] = useState(String(initialRadius));
  const [mapData, setMapData] = useState<SurroundingMapData | null>(mapFromAnalysis(initialAnalysis));
  const [satelliteContext, setSatelliteContext] = useState<SatelliteContext | null>(
    initialAnalysis?.report.details?.satellite_context ?? null,
  );
  const [mapError, setMapError] = useState("");
  const [satelliteError, setSatelliteError] = useState("");
  const [analysis, setAnalysis] = useState<Analysis | null>(initialAnalysis ?? null);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [scanNonce, setScanNonce] = useState(0);
  const [copyStatus, setCopyStatus] = useState("");

  const profileFormRef = useRef<HTMLFormElement | null>(null);
  const mapEl = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<LeafletMap | null>(null);
  const layerRef = useRef<LayerGroup | null>(null);

  const verdicts: ClaimVerdict[] = (analysis?.report.details?.verdicts?.claims as ClaimVerdict[]) ?? [];
  const coverage = analysis?.report.details?.coverage;
  const metrics = analysis?.report.details?.metrics;
  const competitorDensity = useMemo(
    () => (isRecord(metrics) ? metricList(metrics.competitor_density) : []),
    [metrics],
  );
  const demand = isRecord(metrics) && isRecord(metrics.demand) ? metrics.demand : null;
  const nearest = isRecord(metrics) && isRecord(metrics.nearest_competitor) ? metrics.nearest_competitor : null;
  const chainRatio = isRecord(metrics) && isRecord(metrics.chain_ratio) ? metrics.chain_ratio : null;
  const supplyDemand = isRecord(metrics) && isRecord(metrics.supply_demand) ? metrics.supply_demand : null;
  const placesEnrichment = analysis?.report.details?.places_enrichment;
  const locationDefaults = {
    type: factString(facts, "location_type") || factString(facts, "type"),
    tenure: factString(facts, "tenure"),
    area_m2: factString(facts, "area_m2"),
    rent_cost: factString(facts, "rent_cost"),
    operating_hours: factString(facts, "operating_hours"),
    logistics_requirements: factString(facts, "logistics_requirements"),
    known_competitors: factListString(facts, "known_nearby_competitors") || factListString(facts, "known_competitors"),
  };

  async function geocode(event: FormEvent) {
    event.preventDefault();
    if (!address.trim()) return;
    setBusy("geocode");
    setError("");
    setMapError("");
    setConfirmed(false);
    setGeocodeWarnings([]);
    try {
      const result = await api.geocode(address);
      setCandidates(result.candidates);
      setGeocodeWarnings(result.warnings ?? []);
      if (result.candidates[0]) {
        const first = result.candidates[0];
        setCenter({ lat: first.lat, lon: first.lon });
        setManualLat(String(first.lat));
        setManualLon(String(first.lon));
      } else {
        setError(result.warnings.join(" ") || "Không tìm thấy vị trí.");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Geocode thất bại");
    } finally {
      setBusy(null);
    }
  }

  function confirmManualLocation() {
    const lat = Number(manualLat);
    const lon = Number(manualLon);
    if (!Number.isFinite(lat) || !Number.isFinite(lon) || lat < -90 || lat > 90 || lon < -180 || lon > 180) {
      setError("Tọa độ không hợp lệ.");
      return;
    }
    setCenter({ lat, lon });
    setCandidates([]);
    setConfirmed(true);
    setError("");
  }

  function refreshScan() {
    setMapError("");
    setSatelliteError("");
    setScanNonce((current) => current + 1);
  }

  async function copyCoordinates() {
    if (!center) return;
    const text = `${center.lat.toFixed(6)}, ${center.lon.toFixed(6)}`;
    try {
      await navigator.clipboard.writeText(text);
      setCopyStatus("Đã copy tọa độ");
    } catch {
      setCopyStatus(text);
    }
    window.setTimeout(() => setCopyStatus(""), 1800);
  }

  function openCurrentLocation() {
    if (!center) return;
    window.open(`https://www.google.com/maps/search/?api=1&query=${center.lat},${center.lon}`, "_blank", "noopener");
  }

  function appendClaim(template: string) {
    setClaims((current) => {
      const lines = current
        .split("\n")
        .map((line) => line.trim())
        .filter(Boolean);
      if (lines.includes(template)) return current;
      return [...lines, template].join("\n");
    });
  }

  function updateScanRadius(value: string) {
    setScanRadiusText(value);
    const radius = parseRadius(value);
    if (radius !== null) setScanRadiusM(radius);
  }

  useEffect(() => {
    if (!center) return;
    let ignore = false;
    api
      .surroundingMap(center.lat, center.lon, industry ?? undefined, scanRadiusM)
      .then((data) => {
        if (!ignore) {
          setMapData(data);
          setMapError("");
        }
      })
      .catch((err: unknown) => {
        if (!ignore) {
          setMapData(null);
          setMapError(err instanceof Error ? err.message : "Không thể tải dữ liệu POI.");
        }
      });
    return () => {
      ignore = true;
    };
  }, [center, industry, scanRadiusM, scanNonce]);

  useEffect(() => {
    if (!center) return;
    let ignore = false;
    api
      .satelliteContext(center.lat, center.lon, scanRadiusM)
      .then((data) => {
        if (!ignore) {
          setSatelliteContext(data);
          setSatelliteError("");
        }
      })
      .catch((err: unknown) => {
        if (!ignore) {
          setSatelliteContext(null);
          setSatelliteError(err instanceof Error ? err.message : "Không thể tải dữ liệu vệ tinh.");
        }
      });
    return () => {
      ignore = true;
    };
  }, [center, scanRadiusM, scanNonce]);

  useEffect(() => {
    if (!center || !mapEl.current) return;
    let disposed = false;

    (async () => {
      const L = (await import("leaflet")).default;
      if (disposed) return;
      const element = mapEl.current;
      if (!element) return;

      if (!mapRef.current) {
        const map = L.map(element).setView([center.lat, center.lon], 15);
        const street = L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
          attribution: "© OpenStreetMap",
          maxZoom: 19,
        });
        const satellite = L.tileLayer(
          "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
          { attribution: "Tiles © Esri", maxZoom: 19 },
        );
        satellite.addTo(map);
        L.control.layers({ "Vệ tinh": satellite, "Đường phố": street }, {}, { collapsed: true }).addTo(map);
        layerRef.current = L.layerGroup().addTo(map);
        mapRef.current = map;
      } else {
        mapRef.current.setView([center.lat, center.lon], 15);
      }

      window.setTimeout(() => mapRef.current?.invalidateSize(), 40);
      const group = layerRef.current;
      if (!group) return;
      group.clearLayers();

      L.circle([center.lat, center.lon], {
        radius: scanRadiusM,
        color: "#1f6b4f",
        fillColor: "#8fd0d1",
        fillOpacity: 0.12,
        opacity: 0.75,
        weight: 2,
      })
        .bindPopup(`Bán kính quét ${scanRadiusM}m`)
        .addTo(group);

      L.circleMarker([center.lat, center.lon], {
        radius: 10,
        color: "#0f3d2e",
        fillColor: "#1f6b4f",
        fillOpacity: 0.95,
        weight: 2,
      })
        .bindPopup("<b>Địa điểm kinh doanh</b>")
        .addTo(group);

      const popup = (p: { name: string | null; distance_m: number; google_maps_url?: string; category?: string }) =>
        `<b>${p.name ?? "(không tên)"}</b><br/>${p.category ?? ""} · ${Math.round(p.distance_m)}m` +
        (p.google_maps_url
          ? `<br/><a href="${p.google_maps_url}" target="_blank" rel="noopener">Khảo sát trên Google Maps</a>`
          : "");

      mapData?.residential.forEach((zone) =>
        L.circleMarker([zone.lat, zone.lon], {
          radius: 5,
          color: "#2f6f73",
          fillColor: "#8fd0d1",
          fillOpacity: 0.6,
          weight: 1,
        })
          .bindPopup(`<b>Khu dân cư</b><br/>${zone.name ?? ""}`)
          .addTo(group),
      );
      mapData?.competitors.forEach((competitor) =>
        L.circleMarker([competitor.lat, competitor.lon], {
          radius: 6,
          color: "#8a3217",
          fillColor: "#ce6a3a",
          fillOpacity: 0.9,
          weight: 1,
        })
          .bindPopup(popup(competitor))
          .addTo(group),
      );
      mapData?.eateries.forEach((eatery) =>
        L.circleMarker([eatery.lat, eatery.lon], {
          radius: 5,
          color: "#836319",
          fillColor: "#e7c45b",
          fillOpacity: 0.85,
          weight: 1,
        })
          .bindPopup(popup(eatery))
          .addTo(group),
      );
    })();

    return () => {
      disposed = true;
    };
  }, [center, mapData, scanRadiusM]);

  useEffect(() => {
    return () => {
      mapRef.current?.remove();
      mapRef.current = null;
    };
  }, []);

  async function analyze() {
    if (dependency !== "independent" && !confirmed) {
      setError("Cần xác nhận tọa độ trước khi phân tích khu vực.");
      return;
    }

    const claimList = claims
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean);
    const profileForm = profileFormRef.current ? new FormData(profileFormRef.current) : new FormData();
    const locationProfile: Record<string, unknown> = {};
    const areaM2 = Number(String(profileForm.get("area_m2") ?? "").replace(/[,. ]/g, ""));
    const rentCost = Number(String(profileForm.get("rent_cost") ?? "").replace(/[,. ]/g, ""));
    const targetRadiusValues = profileForm
      .getAll("target_radius_m")
      .map((value) => String(value).trim())
      .filter(Boolean);
    const targetRadius = parseRadius(targetRadiusValues.at(-1) ?? "");
    const knownCompetitors = splitList(String(profileForm.get("known_competitors") ?? ""));
    const logisticsRequirements = String(profileForm.get("logistics_requirements") ?? "").trim();

    for (const key of ["type", "tenure", "operating_hours"]) {
      const value = String(profileForm.get(key) ?? "").trim();
      if (value) locationProfile[key] = value;
    }
    if (Number.isFinite(areaM2) && areaM2 > 0) locationProfile.area_m2 = areaM2;
    if (Number.isFinite(rentCost) && rentCost > 0) locationProfile.rent_cost = rentCost;
    if (targetRadius !== null) locationProfile.target_radius_m = targetRadius;
    if (knownCompetitors.length) locationProfile.known_competitors = knownCompetitors;
    if (logisticsRequirements) locationProfile.logistics_requirements = logisticsRequirements;

    const options: Record<string, unknown> = { use_gemini: true, include_satellite: true };
    if (dependency !== "auto") options.location_dependency = dependency;
    if (dependency !== "independent" && center) {
      options.location = {
        lat: center.lat,
        lon: center.lon,
        claims: claimList,
        ...(dependency === "primary" ? { depends_on_surrounding_customers: true } : {}),
        ...locationProfile,
      };
    }

    setBusy("analyze");
    setError("");
    try {
      const result = await api.analyzeSurrounding(startupId, options);
      setAnalysis(result);
      setSatelliteContext(result.report.details?.satellite_context ?? satelliteContext);
      onAnalysisComplete?.(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Phân tích thất bại");
    } finally {
      setBusy(null);
    }
  }

  return (
    <section className="surface surroundingSurface" id="surrounding-area">
      <div className="sectionHeader">
        <div>
          <p className="eyebrow">SURROUNDING AREA</p>
          <h2>Khu vực xung quanh</h2>
        </div>
        <span className="muted">OpenStreetMap local · geocode có xác nhận</span>
      </div>

      <div className="stepGrid">
        <div className="stepCard">
          <span className="stepIndex">1</span>
          <h3>Phạm vi áp dụng</h3>
          <div className="segmentedControl">
            {dependencyOptions.map((option) => (
              <button
                className={dependency === option.value ? "active" : ""}
                key={option.value}
                onClick={() => setDependency(option.value)}
                type="button"
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>

        <div className="stepCard wide">
          <span className="stepIndex">2</span>
          <h3>Tọa độ</h3>
          <form className="inlineForm" onSubmit={geocode}>
            <input
              value={address}
              onChange={(event) => setAddress(event.target.value)}
              placeholder="Chợ Bến Thành, Vinhomes Ocean Park..."
            />
            <button className="secondaryButton" disabled={busy === "geocode"}>
              {busy === "geocode" ? "Đang tìm..." : "Tìm"}
            </button>
          </form>
          <div className="coordinateRow">
            <input
              value={manualLat}
              onChange={(event) => setManualLat(event.target.value)}
              inputMode="decimal"
              placeholder="Lat"
            />
            <input
              value={manualLon}
              onChange={(event) => setManualLon(event.target.value)}
              inputMode="decimal"
              placeholder="Lon"
            />
            <button className="secondaryButton" type="button" onClick={confirmManualLocation}>
              Xác nhận tọa độ
            </button>
          </div>
        </div>
      </div>

      {geocodeWarnings.length > 0 && (
        <div className="notice warning">
          {geocodeWarnings.map((warning) => (
            <p key={warning}>{warning}</p>
          ))}
        </div>
      )}

      {candidates.length > 0 && !confirmed && (
        <div className="candidateList">
          {candidates.map((candidate) => (
            <button
              className={
                center?.lat === candidate.lat && center?.lon === candidate.lon ? "candidateRow active" : "candidateRow"
              }
              key={`${candidate.provider}-${candidate.lat}-${candidate.lon}`}
              onClick={() => {
                setCenter({ lat: candidate.lat, lon: candidate.lon });
                setManualLat(String(candidate.lat));
                setManualLon(String(candidate.lon));
              }}
              type="button"
            >
              <span>{candidate.display_name}</span>
              <small>
                {candidate.lat.toFixed(5)}, {candidate.lon.toFixed(5)} · {candidate.confidence}
              </small>
            </button>
          ))}
          <button className="primaryButton fitButton" type="button" onClick={() => setConfirmed(Boolean(center))}>
            Xác nhận vị trí đã chọn
          </button>
        </div>
      )}

      {center && (
        <div className="mapBlock">
          <div className="mapActionBar">
            <div>
              <strong>Điều khiển quét</strong>
              <span>{copyStatus || `${center.lat.toFixed(5)}, ${center.lon.toFixed(5)} · ${scanRadiusM}m`}</span>
            </div>
            <div className="mapActionButtons">
              <button className="secondaryButton compactButton" type="button" onClick={refreshScan}>
                Làm mới
              </button>
              <button className="secondaryButton compactButton" type="button" onClick={copyCoordinates}>
                Copy tọa độ
              </button>
              <button className="secondaryButton compactButton" type="button" onClick={openCurrentLocation}>
                Mở Maps
              </button>
            </div>
          </div>
          {mapData && (
            <div className="scanMetricGrid">
              <ScanMetric label="Quán ăn" value={mapData.eateries.length} hint={nearestName(mapData.eateries)} />
              <ScanMetric label="Đối thủ" value={mapData.competitors.length} hint={nearestName(mapData.competitors)} />
              <ScanMetric label="Khu dân cư" value={mapData.residential.length} hint={nearestName(mapData.residential)} />
              <ScanMetric
                label="Tọa độ"
                value={confirmed ? "Đã xác nhận" : "Chưa xác nhận"}
                hint={`${center.lat.toFixed(5)}, ${center.lon.toFixed(5)}`}
              />
              <ScanMetric label="Bán kính quét" value={`${scanRadiusM}m`} hint="Vòng tròn trên bản đồ" />
              <ScanMetric
                label="Ảnh vệ tinh"
                value={satelliteStatusLabel(satelliteContext?.status)}
                hint={sceneDate(satelliteContext?.best_scene?.datetime)}
              />
            </div>
          )}
          <div className="mapLayout">
            <div className="mapCanvas" ref={mapEl} />
            <div className="mapSide">
              <SatellitePanel context={satelliteContext} error={satelliteError} />
              <div className="mapLegend">
                <span>
                  <i className="legendDot site" /> Địa điểm
                </span>
                <span>
                  <i className="legendDot competitor" /> Đối thủ ({mapData?.competitors.length ?? 0})
                </span>
                <span>
                  <i className="legendDot eatery" /> Ăn uống ({mapData?.eateries.length ?? 0})
                </span>
                <span>
                  <i className="legendDot residential" /> Dân cư ({mapData?.residential.length ?? 0})
                </span>
              </div>
              <div className="sourceNote">
                POI lấy từ OpenStreetMap local. Tên và vị trí đối thủ được gắn link khảo sát để kiểm chứng lại trên Google Maps khi cần ra quyết định.
              </div>
              <div className={confirmed ? "confirmState confirmed" : "confirmState"}>
                <strong>{confirmed ? "Đã xác nhận tọa độ" : "Chưa xác nhận tọa độ"}</strong>
                <span>
                  {center.lat.toFixed(6)}, {center.lon.toFixed(6)}
                </span>
              </div>
              {mapError && <div className="notice warning">{mapError}</div>}
              {mapData && (
                <div className="poiPreviewGrid">
                  <PoiPreviewList title="Quán ăn gần nhất" items={mapData.eateries} empty="Chưa thấy quán ăn trong bán kính." />
                  <PoiPreviewList title="Đối thủ gần nhất" items={mapData.competitors} empty="Chưa thấy đối thủ theo ngành." />
                  <PoiPreviewList title="Khu dân cư" items={mapData.residential} empty="Chưa thấy zone dân cư." />
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      <div className="analysisComposer">
        <form className="locationProfile" ref={profileFormRef}>
          <div className="sectionHeader compact">
            <div>
              <p className="eyebrow">LOCATION PROFILE</p>
              <h3>Thông tin địa điểm</h3>
            </div>
          </div>
          <div className="formRow three">
            <label>
              Loại mặt bằng
              <input name="type" defaultValue={locationDefaults.type} placeholder="Cửa hàng, văn phòng, kho..." />
            </label>
            <label>
              Thuê / sở hữu
              <input name="tenure" defaultValue={locationDefaults.tenure} placeholder="Thuê, sở hữu..." />
            </label>
            <label>
              Diện tích sử dụng
              <input name="area_m2" defaultValue={locationDefaults.area_m2} inputMode="numeric" placeholder="m2" />
            </label>
          </div>
          <div className="formRow">
            <label>
              Chi phí thuê
              <input name="rent_cost" defaultValue={locationDefaults.rent_cost} inputMode="numeric" placeholder="VNĐ/tháng" />
            </label>
            <label>
              Giờ hoạt động
              <input name="operating_hours" defaultValue={locationDefaults.operating_hours} placeholder="08:00-22:00" />
            </label>
          </div>
          <label>
            Bán kính khách hàng mục tiêu
            <input
              className="scanRadiusInput"
              name="target_radius_m"
              value={scanRadiusText}
              inputMode="numeric"
              onChange={(event) => updateScanRadius(event.target.value)}
              placeholder="500 hoặc 1000"
            />
          </label>
          <label>
            Đối thủ đã biết
            <input
              name="known_competitors"
              defaultValue={locationDefaults.known_competitors}
              placeholder="Highlands, Katinat, quán cạnh bên..."
            />
          </label>
          <label className="wideField">
            Yêu cầu giao thông, logistics hoặc nguồn cung
            <textarea
              name="logistics_requirements"
              defaultValue={locationDefaults.logistics_requirements}
              rows={3}
              placeholder="Mặt tiền, giao hàng, kho, nguồn cung, bãi đỗ xe..."
            />
          </label>
        </form>

        <div className="claimBox">
          <div className="sectionHeader compact">
            <div>
              <p className="eyebrow">CLAIMS</p>
              <h3>Tuyên bố cần kiểm chứng</h3>
            </div>
          </div>
          <div className="templateChips">
            {claimTemplates.map((template) => (
              <button key={template} type="button" onClick={() => appendClaim(template)}>
                + {template}
              </button>
            ))}
          </div>
          <textarea value={claims} onChange={(event) => setClaims(event.target.value)} rows={5} />
          <button className="primaryButton" disabled={busy === "analyze"} onClick={analyze} type="button">
            {busy === "analyze" ? "Đang phân tích..." : "Phân tích khu vực"}
          </button>
        </div>
      </div>

      {error && <div className="alert">{error}</div>}

      {analysis && (
        <div className="surroundingResult">
          <div className="resultHeader">
            <div>
              <p className="eyebrow">RESULT</p>
              <h3>{analysis.status === "not_applicable" ? "Không áp dụng" : "Kết quả kiểm chứng"}</h3>
            </div>
            <div className="scoreBadge">
              <strong>{analysis.score ?? "—"}</strong>
              <span>/100</span>
            </div>
          </div>

          <p className="resultSummary">{analysis.summary}</p>

          <div className="metricStrip">
            <div>
              <span>Coverage</span>
              <strong>{coverage?.tier ?? "—"}</strong>
            </div>
            <div>
              <span>POI/km2</span>
              <strong>{coverage?.density_1km ?? "—"}</strong>
            </div>
            <div>
              <span>Đối thủ 250m</span>
              <strong>{competitorDensity.find((ring) => ring.radius_m === 250)?.count ?? "—"}</strong>
            </div>
            <div>
              <span>Đối thủ 500m</span>
              <strong>{competitorDensity.find((ring) => ring.radius_m === 500)?.count ?? "—"}</strong>
            </div>
            <div>
              <span>Đối thủ 1km</span>
              <strong>{competitorDensity.find((ring) => ring.radius_m === 1000)?.count ?? "—"}</strong>
            </div>
            <div>
              <span>Gần nhất</span>
              <strong>{toNumber(nearest?.distance_m) !== null ? `${Math.round(toNumber(nearest?.distance_m) ?? 0)}m` : "—"}</strong>
            </div>
            <div>
              <span>Tỷ lệ chuỗi</span>
              <strong>
                {toNumber(chainRatio?.ratio) !== null ? `${Math.round((toNumber(chainRatio?.ratio) ?? 0) * 100)}%` : "—"}
              </strong>
            </div>
            <div>
              <span>Cung/cầu</span>
              <strong>{toNumber(supplyDemand?.ratio) !== null ? toNumber(supplyDemand?.ratio) : "—"}</strong>
            </div>
          </div>

          {demand && (
            <div className="demandGrid">
              {["residential", "office", "school", "transport"].map((key) => (
                <div key={key}>
                  <span>{key}</span>
                  <strong>{toNumber(demand[key]) ?? "—"}</strong>
                </div>
              ))}
            </div>
          )}

          {placesEnrichment?.warnings?.length ? (
            <div className="notice subtle">
              {placesEnrichment.warnings.map((warning) => (
                <p key={warning}>{warning}</p>
              ))}
            </div>
          ) : null}

          <PlacesSurveyList items={placesEnrichment?.items ?? []} />

          {verdicts.length > 0 && (
            <div className="verdictList">
              {verdicts.map((verdict, index) => {
                const style = verdictStyle[verdict.verdict] ?? verdictStyle.chua_du_thong_tin;
                return (
                  <article className={`verdictItem ${style.className}`} key={`${verdict.claim}-${index}`}>
                    <div className="verdictTop">
                      <span>{style.label}</span>
                      <small>Độ tin cậy: {verdict.confidence}</small>
                    </div>
                    <h4>{verdict.claim}</h4>
                    <p>{verdict.explanation ?? verdict.reason}</p>
                    {verdict.evidence.length > 0 && (
                      <div className="evidenceList">
                        {verdict.evidence.map((item) => (
                          <span key={item}>{item}</span>
                        ))}
                      </div>
                    )}
                  </article>
                );
              })}
            </div>
          )}

          {(analysis.report.risks?.length || analysis.report.missing_data?.length) && (
            <div className="tagWrap resultTags">
              {analysis.report.missing_data?.map((item) => (
                <span className="tag warn" key={`missing-${item}`}>
                  Thiếu: {item}
                </span>
              ))}
              {analysis.report.risks?.map((item) => (
                <span className="tag risk" key={`risk-${item}`}>
                  {item}
                </span>
              ))}
            </div>
          )}
        </div>
      )}
    </section>
  );
}
