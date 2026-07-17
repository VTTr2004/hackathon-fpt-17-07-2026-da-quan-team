# Sources — Surrounding Area Analysis

## Dữ liệu POI — OpenStreetMap qua Geofabrik

- **Nguồn**: `https://download.geofabrik.de/asia/vietnam-latest.osm.pbf`
- **License**: ODbL 1.0 — © OpenStreetMap contributors (bắt buộc ghi công khi hiển thị).
- **Trường dùng**: `amenity, shop, office, leisure, tourism, craft, healthcare, landuse,
  public_transport, place, name, brand, operator, population`.
- **Độ phủ**: dày ở 4 TP lớn (HCM, HN, ĐN, Cần Thơ) + Huế; mỏng dần ra tỉnh. Đây là giới
  hạn cốt lõi, được xử lý bằng `coverage.py`.
- **Quota**: không (dữ liệu tải về, xử lý offline).
- **Cập nhật**: Geofabrik build lại hàng ngày; tải lại theo tháng, ghi `accessed_at` mỗi
  lần truy vấn (lưu trong `meta` của `poi.db`, đưa vào `Evidence.accessed_at`).
- **Ngày truy cập bản đang dùng**: 17/07/2026 (bản `Last-Modified` 16/07/2026).

## Geocoding — Nominatim (OpenStreetMap)

- **Endpoint**: `https://nominatim.openstreetmap.org/search`
- **License**: ODbL; usage policy yêu cầu **User-Agent định danh** và **≤ 1 req/s** (đã
  tuân thủ trong `providers/geocoding.py`).
- **Đo độ chính xác (17/07/2026)**: "Chợ Bến Thành" lệch ~30m; "Vinhomes Ocean Park" tìm
  thấy; địa chỉ số nhà ("123 Lê Lợi...") → rỗng. Nhãn hành chính sai sau sáp nhập 2025 →
  chỉ dùng tọa độ.
- **Quota**: free, rate-limited; không cần key.

## Cross-check độ tươi — Overpass API (tùy chọn, không phải nguồn chính)

- **Endpoint**: `overpass-api.de`, `overpass.kumi.systems`.
- **Đo (17/07/2026)**: 504/timeout ở Quận 1 & Cần Thơ trên cả hai; chỉ chạy ở vùng thưa.
  Vì vậy **không dùng làm nguồn chính**; chỉ đối chiếu độ tươi best-effort.
- **Bẫy đã ghi nhận**: thiếu User-Agent → HTTP 406; mirror `overpass.osm.ch` chỉ có dữ
  liệu Thụy Sĩ (query VN trả rỗng, không báo lỗi).

## Dân số — Tổng cục Thống kê (GSO)

- **Nguồn**: Niên giám Thống kê 2022 + dự báo Tổng điều tra Dân số 2019 (ước lượng).
- **Dùng cho**: `data/population.py` — bảng ~15 đô thị lớn để suy luận "khu vực này lẽ ra
  phải dày POI". **Không đưa vào điểm số**, chỉ dùng để đánh giá độ phủ.
- **Độ tin cậy**: trung bình; con số là ước lượng đô thị, không chính xác tuyệt đối.
- OSM cũng có sẵn 450 `place` kèm dân số 2025, nhưng khớp theo khoảng cách không tin cậy
  (TP Vinh: place có dân số gần nhất cách 118km) → bảng tĩnh là nguồn chính.

## Rating & giá — Google Places API (tùy chọn, mặc định TẮT)

- **Endpoint**: `maps.googleapis.com/maps/api/place/...`
- **License/ToS**: dùng qua API chính thức (KHÔNG scrape). Cần `GOOGLE_PLACES_API_KEY`.
- **Trạng thái**: dormant — không key thì module bỏ qua, vẫn chạy đầy đủ.
- **Free tier**: ~ theo SKU; chỉ gọi top 10–20 đối thủ gần nhất để tiết kiệm quota.

## Nguồn KHÔNG dùng (và lý do)

- **Scraping Google Maps/Batdongsan/Chotot (kể cả Selenium)**: vi phạm ToS và trái nguyên
  tắc dự án (trung-plans §3). Giá thuê mặt bằng, popular times → luôn `INSUFFICIENT_DATA`.
