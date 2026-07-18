# Methodology — Surrounding Area Analysis

## Mục tiêu

Module **không mô tả khu vực** — nó **kiểm chứng tuyên bố của startup về khu vực**
("chưa có đối thủ trong 500m", "khu dân cư đông đúc", "giá thuê rẻ") bằng dữ liệu bản
đồ thật, và trả về verdict có bằng chứng: `XÁC NHẬN` / `BÁC BỎ` / `CHƯA ĐỦ THÔNG TIN`.

Nguyên tắc xuyên suốt (README dự án): **mọi phép tính nằm trong tool deterministic**;
Gemini chỉ diễn giải, không tự tính; thiếu dữ liệu → `Chưa đủ thông tin`, không bịa.

## Luồng xử lý (analyzer.py)

```
industry ─► [0] phân loại phụ thuộc địa điểm
                 └─ INDEPENDENT (SaaS...) ──► NOT_APPLICABLE (không chấm 0)
location ─► [1] tọa độ đã xác nhận?
                 └─ thiếu ──► INSUFFICIENT_DATA (KHÔNG phải NOT_APPLICABLE)
poi.db  ─► [2] query đối thủ + cầu (dân cư/văn phòng/trường/giao thông) + tổng POI
         ─► [3] coverage: mật độ tương đối vs baseline → phát hiện vùng bản đồ mỏng
         ─► [4] metrics deterministic (density, nearest, chain, supply/demand)
claims  ─► [5] verdict cho từng tuyên bố (deterministic; Gemini diễn giải)
         ─► [6] ModuleReport (findings + risks + missing_data + evidence + tool_calls)
```

## Nguồn dữ liệu — quyết định dựa trên đo đạc thực tế

### POI: bản trích OSM local (không dùng Overpass API làm nguồn chính)

Đo trực tiếp Overpass API công cộng (17/07/2026, 2 endpoint) trên 5 khu vực:

| Khu vực | overpass-api.de | overpass.kumi.systems |
|---|---|---|
| **Quận 1 (địa điểm demo)** | **504** | **timeout 91s** |
| Ninh Kiều, Cần Thơ | **504** | **timeout 90s** |
| Thủ Đức | ok (22, 1.6s) | timeout 90s |
| Biên Hòa | **504** | ok (8, 73s) |
| Bến Tre | ok (9, 1.3s) | ok (9, 58s) |

Overpass **hỏng đúng ở nơi dữ liệu dày** (Quận 1, Cần Thơ) và chỉ chạy ở vùng thưa →
sẽ đẩy hệ thống về kết luận "chưa bão hòa" sai. Vì vậy dùng **bản trích local**
(`data/poi.db`, sinh từ `vietnam-latest.osm.pbf` của Geofabrik bằng pyosmium):
225.027 POI, 44 MB, trích xuất ~14 giây, truy vấn <100ms qua chỉ mục R\*Tree.

Nơi Overpass chạy được, số đếm **khớp bản trích** (Thủ Đức 22=22, Bến Tre 9=9) → dùng
Overpass làm cross-check độ tươi best-effort, không chặn luồng.

Lọc theo **khóa** (`amenity, shop, office, leisure, tourism, craft, healthcare,
landuse, public_transport`), không liệt kê giá trị → phủ mọi loại hình. Lưu cả **node
và way** (nhiều POI ở VN là polygon toà nhà), và **bounding box** mỗi đối tượng để một
khu dân cư lớn được nhận diện qua cạnh, không chỉ tâm.

### Geocoding: Nominatim keyless + gate xác nhận

Đo trực tiếp: Nominatim trả "Chợ Bến Thành" **chính xác ~30m**, "Vinhomes Ocean Park"
tìm thấy; chỉ fail với địa chỉ **số nhà**. Vì thế dùng Nominatim (miễn phí) làm mặc
định, **bắt buộc chuyên viên xác nhận tọa độ trên bản đồ** trước khi phân tích
(needs_confirmation luôn = true). Nhãn hành chính của Nominatim sai sau sáp nhập 2025
→ **chỉ dùng tọa độ**. Có `GOONG_API_KEY` thì tự dùng Goong làm ưu tiên cho địa chỉ khó.

## Coverage — phát hiện "bản đồ mỏng ≠ thị trường trống" (chống nói dối)

Rủi ro lớn nhất (plan §7.1): ngoài 4 thành phố lớn, độ phủ OSM sụp; Biên Hòa hơn 1
triệu dân nhưng chỉ ~285 POI/km² — đọc ngây thơ sẽ kết luận "chưa bão hòa, cơ hội tốt".

**Tín hiệu là mật độ TƯƠNG ĐỐI** (đo được / baseline), không phải số tuyệt đối (§7.4 bác
bỏ ngưỡng tuyệt đối vì POI bối cảnh đẩy số đếm café lên). Hiệu chỉnh từ số đo thật:

| Tier | Khu vực (POI/1km đo được) | Xử lý |
|---|---|---|
| `good` (≥50% baseline) | Hoàn Kiếm 3616, Q1 2797, ĐN 1014, Huế 848, Cần Thơ 769, Vinhomes 690 | Đánh giá bão hòa tin cậy |
| `thin` (15–50%) | Thủ Đức 393, **Biên Hòa 285**, Đà Lạt 255 | Tuyên bố bão hòa → INSUFFICIENT, hạ confidence |
| `very_thin` (3–15%) | Vinh 112, Buôn Ma Thuột 92 | Số đếm là giới hạn dưới |
| `rural` (<3%) | Mộc Châu 8 | Có thể thưa thật; không kết luận cạnh tranh |

Baseline = 1000 POI/km² (dưới trung vị 5 lõi đã lập bản đồ tốt). Chỉ khi coverage `good`
mới khẳng định được "không có đối thủ" là thật; các tier khác → `CHƯA ĐỦ THÔNG TIN`.

## Chỉ số (poi_metrics.py) — "thiếu" khác "bằng 0"

- **Mật độ đối thủ** theo vành đai 250/500/1000m.
- **Đối thủ gần nhất**: khoảng cách + tên + có phải chuỗi.
- **Tỷ lệ chuỗi**: tag `brand` + khớp tên (tag brand = 0 ngoài 4 TP lớn nên luôn là
  **giới hạn dưới**).
- **Cầu**: dân cư (`landuse=residential`) + văn phòng + trường + giao thông. Thành phần
  không đo được → `None` + cảnh báo, **không bao giờ thay bằng 0** (sửa bug §7.2).
- **Tỷ lệ cung/cầu**: đối thủ trên mỗi điểm cầu; **không xác định** (None) khi cầu bằng 0
  hoặc không đo được, không chia cho 0.

## Verdict (verdict.py) — Gemini không được overclaim

Verdict được tính **deterministic** từ số của tool (chạy được không cần API key, có thể
test). Gemini chỉ viết diễn giải tiếng Việt; **guardrail** chặn nó nâng một verdict
`CHƯA ĐỦ THÔNG TIN` thành khẳng định — đúng lỗi từng xảy ra khi model "xác nhận khu đông
văn phòng" từ dữ liệu không có văn phòng nào. Giá thuê và vùng bản đồ mỏng bị khóa
`CHƯA ĐỦ THÔNG TIN` trước khi Gemini nhìn thấy.

## Điểm số (0–100)

Chỉ phát khi coverage `good` + đo được cả cạnh tranh lẫn cầu; ngược lại `score=null`
(không bao giờ 0 cho dữ liệu thiếu — trung-plans §14). Điểm = trọng số của (cầu, cân bằng
cạnh tranh) × hệ số tin cậy theo coverage.

## Giới hạn phương pháp

- Haversine là đường chim bay, không phải quãng đường/thời gian di chuyển thực.
- Demo thuyết phục nhất ở 4 TP lớn; ngoài đó hệ thống chủ động trả "không đủ dữ liệu".
- Xem thêm `assumptions-and-limitations.md`.
