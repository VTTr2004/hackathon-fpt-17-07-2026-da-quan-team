# Glossary — Surrounding Area Analysis

- **POI (Point of Interest)**: điểm quan tâm trên bản đồ — quán, cửa hàng, trường, văn
  phòng, khu dân cư... Nguồn: OpenStreetMap.

- **Verdict**: kết luận kiểm chứng một tuyên bố, chỉ gồm 3 giá trị:
  - **XÁC NHẬN** (`xac_nhan`): dữ liệu ủng hộ tuyên bố.
  - **BÁC BỎ** (`bac_bo`): dữ liệu mâu thuẫn tuyên bố.
  - **CHƯA ĐỦ THÔNG TIN** (`chua_du_thong_tin`): dữ liệu không đủ để kết luận.

- **Location dependency (phụ thuộc vị trí)** — bước 0:
  - **primary**: vị trí quyết định (F&B, bán lẻ, gym, giáo dục, y tế) → chạy đầy đủ.
  - **supporting**: vị trí phụ trợ (logistics, sản xuất, coworking) → chỉ giao thông/nhân lực.
  - **independent**: không phụ thuộc (SaaS, fintech) → `NOT_APPLICABLE`.

- **Coverage tier (độ phủ bản đồ)**: mức độ tin cậy của bản đồ tại một vị trí, tính bằng
  **mật độ tương đối** (POI/1km so với baseline): `good` / `thin` / `very_thin` / `rural`.

- **Vùng bản đồ mỏng (thin map)**: khu vực có mật độ POI thấp bất thường so với dân số →
  nhiều khả năng là lỗ hổng dữ liệu OSM, KHÔNG phải thị trường trống. Không được kết luận
  "chưa bão hòa".

- **Coverage ratio**: `mật độ đo được / baseline` (baseline 1000 POI/km²).

- **Confidence factor**: hệ số nhân độ tin cậy theo coverage (1.0 good … 0.3 rural).

- **can_assess_saturation**: chỉ `True` khi coverage `good` — mới khẳng định được "không có
  đối thủ" là thật thay vì thiếu dữ liệu.

- **Competitor density (mật độ đối thủ)**: số đối thủ trực tiếp theo vành đai 250/500/1000m.

- **Nearest competitor**: đối thủ trực tiếp gần nhất (khoảng cách + tên + có phải chuỗi).

- **Chain ratio (tỷ lệ chuỗi)**: phần trăm đối thủ là chuỗi (tag `brand` + khớp tên). Luôn
  là **giới hạn dưới** do tag brand của OSM thiếu.

- **Demand proxy (proxy cầu)**: tín hiệu khách hàng quanh vị trí — dân cư (`landuse=
  residential`), văn phòng, trường học, giao thông công cộng.

- **Supply/demand ratio (tỷ lệ cung/cầu)**: đối thủ trên mỗi điểm cầu; cao = bão hòa.
  **Không xác định** (None) khi cầu = 0 hoặc không đo được (không chia cho 0).

- **Thiếu vs bằng 0**: chỉ số **không đo được** (`None`) khác hoàn toàn **đo được và bằng 0**.
  Thiếu → ghi `missing`, cảnh báo, loại khỏi công thức — không bao giờ thay bằng 0.

- **Geocoding**: chuyển địa chỉ → tọa độ. **Needs confirmation**: tọa độ geocode luôn phải
  được chuyên viên xác nhận trên bản đồ trước khi phân tích.

- **Haversine**: công thức khoảng cách cung lớn giữa hai tọa độ trên mặt cầu Trái Đất.

- **R\*Tree**: chỉ mục không gian của SQLite, lọc nhanh POI theo bounding box trước khi tính
  haversine chính xác.

- **Deep-link giá**: nút mở đúng địa điểm trên Google Maps (theo tên + tọa độ) để chuyên
  viên tự khảo sát giá/menu/ảnh — vì OSM không có giá và module không bịa.
