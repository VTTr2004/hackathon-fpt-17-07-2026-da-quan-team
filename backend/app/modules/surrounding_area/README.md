# Surrounding Area Analysis

Kiểm chứng **tuyên bố của startup về khu vực** bằng dữ liệu bản đồ thật (OpenStreetMap),
trả về verdict có bằng chứng thay vì bảng điểm chủ quan.

## Mục tiêu & phạm vi

- **Trong phạm vi**: mật độ đối thủ theo vành đai, đối thủ gần nhất, tỷ lệ chuỗi, proxy cầu
  (dân cư/văn phòng/trường/giao thông), tỷ lệ cung/cầu, phát hiện vùng bản đồ mỏng, bản đồ
  tương tác + deep-link giá.
- **Ngoài phạm vi** (luôn `CHƯA ĐỦ THÔNG TIN`, không đoán): giá thuê mặt bằng thị trường,
  popular times, nhận diện nhượng quyền.
- **Không áp dụng**: ngành không phụ thuộc vị trí (SaaS...) → `NOT_APPLICABLE`.

## Đầu vào

`analyze(startup_facts, documents, options) -> ModuleReport`

```jsonc
startup_facts = {
  "industry": "chuỗi cà phê",
  "location": {
    "lat": 10.7725, "lon": 106.6980,      // bắt buộc (đã xác nhận qua gate geocode)
    "claims": ["Chưa có đối thủ trong 500m"],  // tuyên bố cần kiểm chứng
    "depends_on_surrounding_customers": true,  // (tùy chọn) override bước 0
    "type": "cửa hàng", "tenure": "thuê", "rent_cost": 30000000,  // dữ kiện, không benchmark
    "target_radius_m": 1000, "known_competitors": ["Highlands kế bên"]
  }
}
options = { "use_gemini": true }   // false để chạy thuần deterministic
```

## Đầu ra — `ModuleReport`

- `status`: `completed` | `partial` | `insufficient_data` | `not_applicable`.
- `score`: 0–100 (chỉ khi coverage `good` + đủ dữ liệu) hoặc `null` (không bao giờ 0 cho
  dữ liệu thiếu).
- `findings`: verdict từng tuyên bố (`[XÁC NHẬN]` / `[BÁC BỎ]` / `[CHƯA ĐỦ THÔNG TIN]`) +
  finding độ phủ bản đồ.
- `details.map`: quán ăn + khu dân cư quanh vị trí, mỗi điểm có `google_maps_url` (khảo sát giá).
- `details.coverage`, `details.metrics`, `details.verdicts`, `evidence` (nguồn OSM +
  `accessed_at`), `tool_calls`.

## Chạy — setup dữ liệu (1 lệnh, cho đồng đội vừa pull về)

```bash
cd backend
pip install -e ".[dev]"                                        # đã gồm osmium
python -m app.modules.surrounding_area.scripts.setup_data      # tải OSM + build poi.db (~310MB tải, ~15s)
```

`setup_data` idempotent (đã có `poi.db` thì bỏ qua; `--force` để build lại). Hoặc chạy tách:
`scripts.download_osm` rồi `scripts.extract_poi`.

**Quan trọng cho teammate:** `poi.db` (44MB) và file `.pbf` (310MB) **KHÔNG commit** (xem
`.gitignore`) — mỗi người tự chạy `setup_data` một lần. App vẫn **import và chạy test bình
thường KHÔNG cần osmium/poi.db**; thiếu `poi.db` chỉ khiến phân tích trả `INSUFFICIENT_DATA`
(không crash). `osmium` chỉ cần lúc build `poi.db`, không cần lúc chạy app.

## Test

```bash
pytest tests/surrounding_area/            # ~197 test; test cần poi.db sẽ skip nếu chưa build
ruff check app/modules/surrounding_area/
```

## API key (tùy chọn — hệ thống chạy đầy đủ mà KHÔNG cần key)

| Env var | Tác dụng khi có key |
|---|---|
| `GOONG_API_KEY` | Geocoding ưu tiên Goong cho địa chỉ số nhà VN (mặc định Nominatim keyless) |
| `GOOGLE_PLACES_API_KEY` | Bật rating + price_level cho top đối thủ (mặc định tắt) |

Không key → geocode bằng Nominatim, giá khảo sát bằng deep-link Google Maps. **Không scrape.**

## Tài liệu

`docs/methodology.md` · `docs/tools.md` · `docs/sources.md` ·
`docs/assumptions-and-limitations.md` · `docs/glossary.md` · `docs/test-cases.md`
