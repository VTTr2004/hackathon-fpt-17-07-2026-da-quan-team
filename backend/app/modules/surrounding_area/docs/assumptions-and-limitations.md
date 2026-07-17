# Assumptions & Limitations — Surrounding Area Analysis

## Giả định

1. **Tọa độ đã được chuyên viên xác nhận** trước khi phân tích. Module nhận
   `location.lat/lon`; bước geocode + xác nhận trên bản đồ xảy ra trước đó (§4.2).
2. **Khoảng cách là đường chim bay** (haversine), không phải quãng đường thực tế hay
   thời gian di chuyển.
3. **Baseline độ phủ = 1000 POI/km²** đại diện vùng đô thị được lập bản đồ tốt; hiệu chỉnh
   từ số đo thật của 5 lõi đô thị (Q1, Hoàn Kiếm, ĐN, Huế, Cần Thơ).
4. **Nhãn phụ thuộc vị trí do người dùng chỉ định** (nếu có) được ưu tiên hơn suy luận
   theo ngành (`location.depends_on_surrounding_customers` hoặc `location_dependency`).

## Dữ liệu đầu vào module dùng (từ hồ sơ)

| Trường hồ sơ | Cách dùng |
|---|---|
| `industry` | Phân loại phụ thuộc vị trí + chọn tag đối thủ |
| `location.lat/lon` | Tọa độ phân tích (bắt buộc) |
| `location.depends_on_surrounding_customers` / `location_dependency` | Override bước 0 |
| `location.claims` / `area_claims` | Các tuyên bố cần kiểm chứng |
| `location.known_competitors` | Đối thủ startup đã biết (đối chiếu, ghi vào details) |
| `location.type / tenure / area_m2 / rent_cost / target_radius_m / operating_hours` | Ghi vào `details.location_profile` (dữ kiện, không phải kết quả phân tích) |

**Quan trọng — chi phí thuê**: nếu startup tự khai `rent_cost`, đó là **dữ kiện đã biết**,
module ghi lại nguyên văn. Nhưng module **không benchmark** được nó so với giá thị trường
(không có nguồn giá thuê đáng tin) → mọi tuyên bố "giá thuê rẻ/hợp lý so với khu vực" vẫn
trả `CHƯA ĐỦ THÔNG TIN`.

## Giới hạn

1. **Độ phủ OSM sụp ngoài 4 TP lớn.** Đây là giới hạn cốt lõi; xử lý bằng `coverage.py`:
   vùng mỏng → `INSUFFICIENT_DATA`, hạ confidence, KHÔNG cho điểm cộng.
2. **Tag `brand` thiếu nhiều** (=0 ngoài 4 TP lớn) → tỷ lệ chuỗi luôn là **giới hạn dưới**,
   dù đã bù bằng khớp tên.
3. **Không có giá thuê, popular times, nhận diện nhượng quyền** — không nguồn hợp pháp →
   luôn `INSUFFICIENT_DATA`, không đoán.
4. **Geocoding Nominatim** fail với địa chỉ số nhà; nhãn hành chính sai sau sáp nhập 2025.
   Giảm thiểu bằng gate xác nhận bắt buộc của con người.
5. **Zone lớn dùng centroid + bbox**: khu dân cư rất rộng được nhận qua cạnh (bbox), nhưng
   khoảng cách tới zone là xấp xỉ (tới bbox, không phải polygon chính xác).
6. **Bản trích cũ dần**: build lại theo tháng; `Evidence.accessed_at` ghi thời điểm dữ liệu.

## Trường hợp KHÔNG áp dụng

- Ngành không phụ thuộc vị trí (SaaS, fintech, marketplace) → `NOT_APPLICABLE`, loại khỏi
  công thức điểm, **không chấm 0**.

## Sai số đã biết

- Café trong 1km ở Quận 1: bản trích 256 (`amenity=cafe`) vs plan cũ 334 — khác biệt do
  định nghĩa loại hình/bán kính; đối thủ thực tế cao hơn khi gộp `shop=coffee`,
  `fast_food`... (đã gộp trong bộ lọc ngành F&B).
- Vùng thưa khớp Overpass live gần như tuyệt đối (Thủ Đức 22=22, Bến Tre 9=9).
