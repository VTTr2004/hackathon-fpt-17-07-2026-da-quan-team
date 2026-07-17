# Tools — Surrounding Area Analysis

Mọi tool là **deterministic** (cùng input → cùng output), có version, có unit test, và
KHÔNG giao phép tính cho LLM. Lỗi tool được báo có cấu trúc, không thay bằng số Gemini đoán.

| Tool | File | Version | Mục đích |
|---|---|---|---|
| `haversine_km` | `tools/geo.py` | 1.0.0 | Khoảng cách cung lớn giữa 2 tọa độ (km) |
| `bounding_box` | `tools/geo.py` | 1.0.0 | Hộp bao quanh bán kính, để pre-filter bằng R\*Tree |
| `score_location` | `tools/geo.py` | 2.0.0 | Điểm vị trí có trọng số, **phân biệt thiếu vs 0** |
| `classify_location_dependency` | `tools/industry_taxonomy.py` | 1.0.0 | Ngành → primary/supporting/independent (bước 0) |
| `resolve_competitor_filter` | `tools/industry_taxonomy.py` | 1.0.0 | Ngành → tập tag OSM của đối thủ + cầu |
| `PoiStore.query_radius` | `data_store/poi_store.py` | 1.0.0 | Truy vấn POI theo bán kính (R\*Tree + haversine) |
| `build_area_metrics` | `tools/poi_metrics.py` | 1.0.0 | density/nearest/chain/demand/supply-demand |
| `assess_coverage` | `tools/coverage.py` | 1.0.0 | Phát hiện vùng bản đồ mỏng (mật độ tương đối) |
| `evaluate_claim_deterministic` | `verdict.py` | 1.0.0 | Verdict từng tuyên bố từ số của tool |
| `geocode` | `providers/geocoding.py` | 1.0.0 | Địa chỉ → tọa độ (Nominatim keyless / Goong) |
| `enrich_place` | `providers/places.py` | 1.0.0 | (tùy chọn) rating/giá Google Places, key-gated |

## `score_location` (2.0.0)

- **Input**: `metrics: {tên: 0–100 | None}`, `weights: {tên: float}` (tổng = 1).
- **Output**: `{score, status, contributions, measured_metrics, missing_metrics,
  covered_weight, warnings, assumptions}`.
- **Lỗi**: weights không tổng 1, giá trị ngoài [0,100], kiểu sai → `ValueError`.
- **Khác biệt v1→v2**: chỉ số thiếu/`None` **không bị coi là 0**; bị loại khỏi công thức,
  ghi `missing_metrics`, chuẩn hóa lại trọng số. Thiếu >40% trọng số → `score=None`.

## `PoiStore.query_radius`

- **Input**: `lat, lon, radius_m, tags=((key,value)|(key,"*"))..., limit`.
- **Output**: `list[Poi]` sắp theo khoảng cách; mỗi `Poi` có `distance_m`, `is_chain`,
  `google_maps_url()`.
- Mở `poi.db` **read-only**; way/zone khớp theo khoảng cách tới bounding box.
- **Lỗi**: `poi.db` thiếu → `PoiDatabaseUnavailableError` (analyzer → INSUFFICIENT_DATA).

## `build_area_metrics`

- **Input**: `industry_profile, competitors: list[Poi], demand_counts: {proxy: int|None}`.
- **Output**: `AreaMetrics.to_dict()` gồm competitor_density, nearest_competitor,
  chain_ratio (giới hạn dưới), demand (kèm `missing`), supply_demand (None nếu cầu=0),
  competitor_category_mix, warnings.
- Thành phần cầu `None` → ghi vào `missing`, **không tính 0**.

## `assess_coverage`

- **Input**: `lat, lon, density_1km, baseline_density=1000`.
- **Output**: `tier, coverage_ratio, confidence_factor, can_assess_saturation, warnings`.
- **Lỗi**: density âm, baseline ≤ 0 → `ValueError`.

## `geocode` (async)

- **Input**: `address`, tùy chọn `goong_api_key`, fetch inject cho test.
- **Output**: `GeocodeResult{candidates, provider, needs_confirmation=True, warnings}`.
- Không raise khi rỗng: trả candidates rỗng + cảnh báo → analyzer INSUFFICIENT_DATA.
- Env đọc trực tiếp: `GOONG_API_KEY` (không có → Nominatim keyless).

## `enrich_place` (tùy chọn)

- **Input**: `name, lat, lon`, env `GOOGLE_PLACES_API_KEY`.
- **Output**: `PlaceEnrichment{rating, price_level, price_label}` hoặc `None`.
- Không key → `None` (module vẫn chạy đầy đủ). Không bịa giá: thiếu price_level → None.

## Scripts (setup, chạy 1 lần)

- `scripts/download_osm.py` — tải `vietnam-latest.osm.pbf` + verify MD5 Geofabrik.
- `scripts/extract_poi.py` — PBF → `poi.db` (R\*Tree, bbox, meta nguồn + accessed_at).
