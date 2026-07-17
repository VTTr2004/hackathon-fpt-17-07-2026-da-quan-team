# Plan: Surrounding Area Analysis

> Số liệu trong tài liệu này là **kết quả đo thật** (thí nghiệm 17/07/2026), không phải ước lượng.
> Tham chiếu code: `backend/app/modules/surrounding_area/`.

---

## 1. Hiện trạng

`SurroundingAreaAnalyzer` hiện là **stub**: nó nhận `location_metrics` do người dùng **nhập tay**
rồi nhân trọng số.

```json
"location_metrics": {
  "customer_density": 80, "accessibility": 75,
  "supporting_amenities": 70, "competition_balance": 60
}
```

Bốn con số này **không đến từ bản đồ**. Chúng do con người tự chấm. Nghĩa là module hiện tại
không phân tích khu vực — nó chỉ tính trung bình có trọng số của bốn ý kiến chủ quan.

Đây là khoảng cách lớn nhất cần lấp: **chưa có nguồn dữ liệu khu vực nào được kết nối.**

### Cái đã có và dùng lại được

| Thành phần | Trạng thái |
|---|---|
| `schemas/common.py` — `AnalysisStatus`, `Evidence`, `ToolCall`, `Finding` | Tốt, dùng nguyên |
| `tools/geo.py::haversine_km` | Tốt, dùng nguyên |
| `tools/geo.py::score_location` | Có bug — xem mục 7.2 |
| `analyzer.py` | Phải viết lại phần lấy dữ liệu |
| Nguyên tắc "Gemini không tự tính lại output tool" (README) | Khớp thiết kế, giữ nguyên |

Schema hiện tại đã hỗ trợ sẵn mọi thứ plan này cần — không phải đổi schema:

- `AnalysisStatus.NOT_APPLICABLE` → ngành không phụ thuộc địa điểm.
- `AnalysisStatus.INSUFFICIENT_DATA` → không đủ dữ liệu để kết luận.
- `AnalysisStatus.PARTIAL` → một phần truy vấn hỏng.
- `ToolCall.warnings` → cảnh báo lỗ hổng dữ liệu.
- `Finding.confidence` → độ tin cậy **theo từng finding**, không phải một cờ chung.
- `Evidence.url` + `accessed_at` + `publisher` → trích dẫn nguồn bản đồ.

---

## 2. Nhiệm vụ

Module **không mô tả khu vực**. Nó **kiểm chứng tuyên bố của startup về khu vực**.

Đầu vào là tuyên bố trích từ hồ sơ: *"khu vực chưa bão hòa"*, *"chưa có đối thủ trong 500m"*,
*"gần văn phòng nên lưu lượng khách ổn định"*.

Đầu ra là verdict có bằng chứng. Ví dụ thật đã chạy được:

> **"Chưa có đối thủ trực tiếp trong bán kính 500m"** → **BÁC BỎ**
> Bằng chứng: 81 đối thủ trong 500m, gần nhất cách 71m (Cà Phê Tutti Frutti).
> Nguồn: OpenStreetMap, truy cập 17/07/2026.

Khác biệt: bảng số liệu bắt chuyên viên tự nghĩ; verdict trả lời thẳng câu hỏi thẩm định.

---

## 3. Phạm vi

### Trong phạm vi
- Đếm mật độ đối thủ theo vành đai, theo ngành.
- Đo khoảng cách tới đối thủ gần nhất.
- Tỷ lệ chuỗi thương hiệu.
- Đếm POI bối cảnh (dân cư, văn phòng, trường học, giao thông).
- Tỷ lệ cung/cầu.
- Phát hiện vùng bản đồ mỏng và hạ độ tin cậy.

### Ngoài phạm vi — có lý do
| Hạng mục | Lý do |
|---|---|
| **Giá thuê mặt bằng** | Không có nguồn. Probe quanh Bến Thành: 37 đối tượng liên quan, **0 có giá thuê**, đúng 1 mặt bằng trống. Google Places cũng không có. Batdongsan/Chotot chặn scrape. |
| **Popular times** | Không có trong Google Places API chính thức. Thư viện scrape vi phạm ToS — mâu thuẫn nguyên tắc dự án. |
| **Nhận diện nhượng quyền** | OSM chỉ biết cửa hàng treo biển gì, không biết ai sở hữu. Chuỗi ≠ nhượng quyền. |

Ba mục này **phải trả `INSUFFICIENT_DATA`**, không được đoán.

---

## 4. Nguồn dữ liệu

Không nguồn nào làm được cả ba việc. Chia theo việc:

### 4.1. Đếm POI → bản trích OSM local

- Nguồn: `https://download.geofabrik.de/asia/vietnam-latest.osm.pbf` — 310 MB, cập nhật hàng ngày.
- Đã đo: **250.329 POI, 650 loại hình, SQLite 45 MB, trích xuất 27 phút, truy vấn 64–89ms**.
- Lọc theo **khóa** (`amenity`, `shop`, `office`, `leisure`, `tourism`, `craft`, `healthcare`),
  không liệt kê giá trị → phủ mọi loại hình, thêm ngành không cần sửa code.

**Vì sao KHÔNG dùng Overpass API công cộng** — đã đo:

| Khu vực | Overpass công cộng | OSM local |
|---|---|---|
| Quận 1 | 339 ✓ | 334, 89ms |
| Cần Thơ | 89 ✓ | 86, 84ms |
| Thủ Đức | **504 THẤT BẠI** | 8, 79ms |
| Biên Hòa | **429 THẤT BẠI** | 9, 71ms |
| Bến Tre | **429 THẤT BẠI** | 11, 72ms |

Overpass hỏng 3/5 khu vực; retry 2 mirror × 2 lần × delay 15s vẫn timeout sau 6’40.
Local: **14/14 khu vực, không lỗi nào**.

### 4.2. Địa chỉ → tọa độ: **Goong** (cần API key)

Module hiện yêu cầu `location.lat/lon` có sẵn. Hồ sơ thật ghi *"123 Lê Lợi, Bến Nghé, Quận 1"*.

**Không dùng Nominatim** — đã đo:
- `"123 Lê Lợi, Bến Nghé, Quận 1"` → không tìm thấy.
- `"15 Nguyễn Huệ, Q1, HCM"` (viết tắt kiểu Việt) → không tìm thấy.
- `"Chợ Bến Thành"` → lệch **1.669m**, gấp **6,7× bán kính phân tích 250m**.

Goong: tương thích code Google, free tier 600 req/phút, xử lý được địa chỉ VN viết tắt/sai chính tả.

**Bắt buộc**: hiển thị tọa độ đã geocode lên bản đồ cho chuyên viên **xác nhận trước khi phân tích**.
Sai 1,7km mà không ai biết thì mọi verdict sau đó vô nghĩa.

### 4.3. Rating & giá → Google Places, chỉ top 10–20

- OSM không có hai trường này (đã đo). Không có nguồn miễn phí thay thế.
- **Không gọi cho toàn bộ 334 quán** — chỉ top 10–20 gần nhất. Chuyên viên không cần rating của
  quán thứ 200 cách 900m.
- Free tier: 5.000 req/tháng (tier Pro) → ~250 hồ sơ/tháng ở mức 20 req/hồ sơ.
- Dùng `FieldMask`: bị tính giá theo **SKU cao nhất** trong request.
- Credit $200/tháng dùng chung **đã bị Google bỏ từ 03/2025**; free tier nay theo từng SKU, không cộng dồn.

---

## 5. Luồng xử lý

```
startup_facts (ngành, địa chỉ, tuyên bố)
   │
   ├─[0] Phân loại phụ thuộc địa điểm
   │       └─ không phụ thuộc ──► NOT_APPLICABLE (dừng, KHÔNG chấm 0 điểm)
   │
   ├─[1] Geocode (Goong) ──► chuyên viên xác nhận trên bản đồ
   │       └─ không geocode được ──► INSUFFICIENT_DATA
   │
   ├─[2] Truy vấn OSM local: đối thủ theo ngành + POI bối cảnh
   │
   ├─[3] Đánh giá độ phủ dữ liệu ──► vùng bản đồ mỏng ──► hạ confidence
   │
   ├─[4] Tính chỉ số bằng tool deterministic  ← Gemini KHÔNG tham gia
   │
   ├─[5] (tùy chọn) Google Places: rating/giá cho top 10–20
   │
   ├─[6] Gemini sinh verdict — chỉ diễn giải, không tính toán
   │
   └─[7] ModuleReport: findings + risks + missing_data + evidence + tool_calls
```

### Bước 0 — phân loại phụ thuộc địa điểm

| Nhóm | Ví dụ | Xử lý |
|---|---|---|
| Địa điểm quyết định | F&B, bán lẻ, gym, giáo dục, phòng khám | Chạy đầy đủ |
| Địa điểm phụ trợ | Logistics, sản xuất, coworking | Chỉ giao thông, nhân lực |
| Không phụ thuộc | SaaS, fintech, marketplace, AI | `NOT_APPLICABLE` |

Startup SaaS chạy qua module sẽ nhận *"0 đối thủ trong 1km"* — vô nghĩa nhưng **trông giống tín hiệu tốt**.
Aggregator phải **loại module khỏi công thức**, không phải cộng 0 điểm.

Nhãn do Intake gán (dùng chung cho cả 4 module), Gemini đề xuất, **chuyên viên sửa được**.

---

## 6. Chỉ số

| Chỉ số | Trả lời | Nguồn |
|---|---|---|
| Mật độ đối thủ 250/500/1000m | Bão hòa chưa? | OSM local |
| Khoảng cách đối thủ gần nhất | "Chưa có đối thủ gần đây" đúng không? | OSM local |
| Tỷ lệ chuỗi | Đối thủ mạnh cỡ nào? | OSM `brand` + khớp tên |
| Điểm cầu (dân cư + văn phòng + trường học) | Có khách không? | OSM local |
| **Tỷ lệ cung/cầu** | Cạnh tranh thực tế | Tự tính — **không nguồn nào có sẵn** |
| Rating & giá top 10–20 | Giả định giá thực tế không? | Google Places |

**Đặt tên đúng**: gọi là **"tỷ lệ chuỗi"**, không gọi "tỷ lệ nhượng quyền".
OSM không biết ai sở hữu. Starbucks VN là chuỗi nhưng không nhượng quyền cho cá nhân.
Con số này luôn là **giới hạn dưới** vì tag `brand` phủ thiếu.

---

## 7. Các vấn đề phải xử lý TRƯỚC KHI CODE

### 7.1. Rủi ro lớn nhất: thiếu dữ liệu trông y hệt thị trường trống

Độ phủ OSM sụp ngoài 4 thành phố lớn — **đã đo**:

| Khu vực | Quán cà phê/1km | Tag `brand` |
|---|---|---|
| Quận 1, TP.HCM | 334 | 44 |
| Hoàn Kiếm, Hà Nội | 383 | 29 |
| Hải Châu, Đà Nẵng | 186 | 11 |
| TP Huế | 114 | 7 |
| Ninh Kiều, Cần Thơ | 86 | **0** |
| Đà Lạt | 53 | **0** |
| Buôn Ma Thuột | 17 | **0** |
| **TP Vinh** (500k dân) | **12** | **0** |
| **Biên Hòa** (đô thị CN lớn) | **9** | **0** |
| **Thủ Đức** | **8** | **0** |
| Mộc Châu | 1 | **0** |

Thủ Đức 8 quán và Vinh 12 quán **không phải sự thật** — đó là lỗ hổng dữ liệu.
Đưa hồ sơ Biên Hòa vào, hệ thống sẽ đếm 9 quán rồi kết luận *"chưa bão hòa, cơ hội tốt"*
và **cho điểm cộng dựa trên lỗ hổng bản đồ**.

Tag `brand` = 0 ở **mọi nơi ngoài 4 thành phố** → đếm chuỗi qua tag vô dụng toàn quốc,
bắt buộc khớp thêm theo tên.

**Xử lý:**
1. Bảng tra dân số tĩnh (~15 dòng, nguồn Tổng cục Thống kê) → tính POI/đầu người.
   Thấp bất thường so với baseline TP.HCM/Hà Nội → đánh dấu *vùng bản đồ mỏng*.
2. Ngoài 4 thành phố lớn: mặc định `INSUFFICIENT_DATA` cho tuyên bố về mức độ bão hòa.
3. Ghi cảnh báo vào `ToolCall.warnings` và hạ `Finding.confidence`.

### 7.2. Bug đã có trong code hiện tại: `null` âm thầm thành `0`

`tools/geo.py::score_location`:

```python
value = float(metrics.get(key, 0))   # <-- thiếu chỉ số => 0, không cảnh báo
```

Chỉ số thiếu bị coi là **đo được và bằng 0**. Không warning, không hạ confidence.

Bug này **đã thực sự xảy ra** trong thí nghiệm: truy vấn `van_phong` lỗi 504 → `null` thành `0`
→ điểm cầu = 33 + 24 + **0** = 57 → LLM **XÁC NHẬN** tuyên bố *"khu vực đông văn phòng"*
bằng dữ liệu **không chứa văn phòng nào**, và báo *độ tin cậy = cao*.

**Xử lý:** phân biệt rõ *"đo được = 0"* và *"không đo được"*.
- Thiếu chỉ số → thêm vào `missing_data`, ghi `ToolCall.warnings`, **không** thay bằng 0.
- Nếu thiếu chỉ số trọng số lớn → `PARTIAL` hoặc `INSUFFICIENT_DATA`, không `COMPLETED`.
- Trạng thái thiếu phải truyền tới tận prompt Gemini.

### 7.3. `NOT_APPLICABLE` đang dùng sai ngữ nghĩa

`analyzer.py` hiện trả `NOT_APPLICABLE` khi thiếu `lat/lon`. Sai:

- **Thiếu tọa độ** = *chưa có dữ liệu* → `INSUFFICIENT_DATA`.
- **`NOT_APPLICABLE`** phải dành cho *ngành không phụ thuộc địa điểm* (SaaS, fintech).

Khác biệt quan trọng vì Aggregator xử lý hai trạng thái này khác nhau: `NOT_APPLICABLE` loại khỏi
công thức tính điểm; `INSUFFICIENT_DATA` là dữ liệu còn thiếu, cần bổ sung.

### 7.4. Ngưỡng confidence tuyệt đối là sai

Ngưỡng `< 30 POI` từ thí nghiệm không dùng được: Biên Hòa 9 quán vẫn lọt nếu tính cả POI bối cảnh.
Phải dùng **mật độ tương đối** so với dân số, không phải số tuyệt đối.

### 7.5. Bẫy kỹ thuật đã gặp — ghi lại để không mất thời gian lần nữa

| Bẫy | Triệu chứng |
|---|---|
| Overpass thiếu `User-Agent` | HTTP **406**, thông báo lỗi không gợi ý gì |
| Mirror `overpass.osm.ch` | Chỉ có dữ liệu **Thụy Sĩ** → query VN trả rỗng, không báo lỗi |
| `office=company` không giới hạn giá trị | Overpass **504** ở khu trung tâm |
| Python 3.13+ | `cur.lastrowid` = `None` sau `executemany` |
| Console Windows | cp1252 → phải `PYTHONIOENCODING=utf-8` mới in được tiếng Việt |
| Cache kết quả rỗng | Mirror quá tải trả rỗng, cache lại → hỏng demo vĩnh viễn |
| Ranh giới hành chính OSM | Lộn xộn sau sáp nhập 2025 — Nominatim gán chợ Bến Thành vào *"Phường Sài Gòn, Thủ Đức"* |

### 7.6. Ranh giới Gemini

README đã quy định *"Gemini không được tự tính lại output tool"*. Plan này giữ nguyên và bổ sung:

- Prompt phải viết **tiếng Việt có dấu đầy đủ**. Đã đo: model hiểu *"thu do"* thành *"thuế doanh nghiệp"*.
- Dùng **structured output Pydantic** (README đã có sẵn).
- Prompt **phải ghi rõ giới hạn dữ liệu** (*"OSM không có giá thuê"*) — đây là lý do model trả đúng
  `INSUFFICIENT_DATA` cho tuyên bố về giá trong thí nghiệm.
- Prompt phải nêu **trường nào thiếu**.
- Verdict chỉ được thuộc 3 giá trị: `XÁC NHẬN` / `BÁC BỎ` / `CHƯA ĐỦ THÔNG TIN`.

### 7.7. Vận hành

| Vấn đề | Xử lý |
|---|---|
| Bản trích 310MB không nên nằm trong git | Thêm `data/*.pbf`, `data/*.db` vào `.gitignore`; script tải riêng |
| Trích xuất mất 27 phút | Chạy 1 lần khi setup; đóng gói `poi.db` (45MB) cho cả đội dùng chung |
| Docker | `poi.db` phải mount volume hoặc build vào image — 45MB chấp nhận được |
| Dữ liệu cũ dần | Tải lại theo tháng; **ghi `Evidence.accessed_at`** mỗi lần truy vấn |

---

## 8. Lộ trình

**Ưu tiên 1 — chống hệ thống nói dối** (chặn mọi thứ khác)
- Sửa `score_location`: phân biệt *thiếu* và *bằng 0*; điền `missing_data` + `ToolCall.warnings`.
- Sửa ngữ nghĩa `NOT_APPLICABLE` vs `INSUFFICIENT_DATA`.
- Thêm bước 0: phân loại phụ thuộc địa điểm.

**Ưu tiên 2 — kết nối dữ liệu thật** (thay stub)
- Script tải + `extract.py` → `poi.db`.
- Tool truy vấn POI theo bán kính + ngành.
- Thay `location_metrics` nhập tay bằng chỉ số tính từ bản đồ.

**Ưu tiên 3 — chạy được hồ sơ thật**
- Xin key Goong; thêm geocoding + màn xác nhận tọa độ.
- Không có bước này thì **không demo được với hồ sơ do giám khảo đưa**.

**Ưu tiên 4 — phát hiện vùng mỏng**
- Bảng dân số tĩnh; ngưỡng theo mật độ tương đối.

**Ưu tiên 5 — làm giàu**
- Google Places top 10–20 (rating, giá).
- Khớp chuỗi theo tên bù tag `brand` thiếu.

---

## 9. Test bắt buộc

| Test | Kỳ vọng |
|---|---|
| Startup SaaS | `NOT_APPLICABLE`, không có điểm |
| Thiếu tọa độ | `INSUFFICIENT_DATA`, **không** `NOT_APPLICABLE` |
| Quán cà phê Quận 1 | Bác bỏ "chưa có đối thủ trong 500m" bằng số thật |
| **Startup ở Biên Hòa** | **`INSUFFICIENT_DATA` — KHÔNG được kết luận "chưa bão hòa"** |
| Tuyên bố về giá thuê | Luôn `INSUFFICIENT_DATA` |
| Một truy vấn POI hỏng | `PARTIAL` + `warnings`, **không** `COMPLETED` |
| Geocode lệch | Chuyên viên phải thấy và sửa được trước khi phân tích |

Test Biên Hòa là quan trọng nhất: nó kiểm tra hệ thống có **dám nói "tôi không biết"** hay không.

---

## 10. Rủi ro tồn đọng

| Rủi ro | Mức | Trạng thái |
|---|---|---|
| Cho điểm cộng dựa trên lỗ hổng dữ liệu | **Cao** | Mục 7.1, 7.2 — chưa xử lý |
| Chưa có geocoding → không chạy hồ sơ thật | **Cao** | Cần key Goong |
| Demo chỉ thuyết phục ở Q1/Hoàn Kiếm | Trung bình | Chọn địa điểm demo trong 4 TP lớn và **nói thẳng giới hạn** |
| Gemini là API ngoài, module khác đọc tài liệu mật | Trung bình | Riêng module này chỉ gửi số đếm POI công khai — an toàn |
| Bản trích cũ dần | Thấp | Ghi `accessed_at`, tải lại theo tháng |
