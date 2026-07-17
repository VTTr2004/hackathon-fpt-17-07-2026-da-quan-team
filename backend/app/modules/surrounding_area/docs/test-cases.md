# Test Cases — Surrounding Area Analysis

Chạy: `pytest tests/surrounding_area/` (~197 test, gom trong 1 thư mục). Test gắn với `poi.db`
sẽ **skip** nếu chưa build DB, không fail. Kết quả dưới đây đối chiếu số đo thật.

## Test bắt buộc (plan §9) — `tests/test_surrounding_analyzer.py`

| # | Kịch bản | Kỳ vọng | Kết quả live |
|---|---|---|---|
| 1 | Startup SaaS | `NOT_APPLICABLE`, score None | ✅ không chấm 0 |
| 2 | Thiếu tọa độ (ngành F&B) | `INSUFFICIENT_DATA`, KHÔNG `NOT_APPLICABLE` | ✅ missing_data=[location.lat/lon] |
| 3 | Café Quận 1 "chưa có đối thủ 500m" | **BÁC BỎ** bằng số thật | ✅ "253 đối thủ, gần nhất 52m" |
| 4 | **Café Biên Hòa "chưa bão hòa"** | **`INSUFFICIENT_DATA`**, KHÔNG kết luận cơ hội | ✅ "285 POI/km² = 28% baseline" |
| 5 | Tuyên bố giá thuê rẻ | Luôn `CHƯA ĐỦ THÔNG TIN` | ✅ mọi coverage |
| 6 | 1 truy vấn POI hỏng (office 504) | `PARTIAL` + warnings, KHÔNG `COMPLETED` | ✅ missing_data=[demand:office] |
| 7 | Geocode lệch | Chuyên viên xác nhận trước khi phân tích | ✅ needs_confirmation=True + low-conf warning |

Test #4 (Biên Hòa) là quan trọng nhất: hệ thống phải **dám nói "tôi không biết"**.

## Happy path — `test_surrounding_analyzer.py`, `test_surrounding_poi_store.py`

- Vinhomes Ocean Park (ví dụ của user): "khu dân cư đông đúc" → **XÁC NHẬN** ("10 khu dân
  cư, 3 văn phòng, 5 trường học"); map trả 10 quán ăn + 10 zone dân cư có deep-link giá.
- Quận 1: score 72.5 (coverage good); nearest competitor < 200m.

## Thiếu dữ liệu / biên — `test_surrounding_area_tools.py`, `test_surrounding_poi_metrics.py`

- `score_location`: chỉ số thiếu KHÔNG thành 0; thiếu trọng số lớn → score None.
- Tái hiện sự cố 504-văn-phòng: 33+24+None → INSUFFICIENT, không "xác nhận đông văn phòng".
- Demand thiếu 1 thành phần → ghi `missing`, không tính 0; supply/demand khi cầu=0 → None.
- `haversine`: cùng tọa độ = 0; Q1↔HN ≈ 1140km; tọa độ ngoài miền → ValueError.
- `bounding_box`: không tạo âm tính giả (mọi điểm trong bán kính đều nằm trong hộp).

## Coverage / thin-map — `test_surrounding_coverage.py`

- Q1 2797, Hoàn Kiếm 3616, Vinhomes 690 → `good`.
- Thủ Đức 393, Biên Hòa 285, Đà Lạt 255 → `thin` (không đánh giá bão hòa được).
- Vinh 112 → `very_thin`; Mộc Châu 8 → `rural`.
- Confidence giảm dần theo coverage; Biên Hòa cảnh báo "gần đô thị lớn nhưng bản đồ mỏng".

## Verdict — `test_surrounding_verdict.py`

- Phân loại tuyên bố; giá thắng khi câu vừa nói vị trí vừa nói giá.
- Absence: BÁC BỎ khi có đối thủ trong bán kính; INSUFFICIENT khi coverage mỏng; radius đọc
  từ câu ("500m" vs "1km").
- Office claim + 0 văn phòng → BÁC BỎ (không phải xác nhận — chống bug §7.2).

## Geocoding — `test_surrounding_geocoding.py` (fetch inject, không mạng)

- Parse Nominatim/Goong; marketplace → confidence high; admin area → low + cảnh báo.
- Địa chỉ không giải được → cảnh báo, không raise. Goong ưu tiên khi có key; fallback
  Nominatim khi Goong lỗi. `needs_confirmation` luôn True.

## Places (tùy chọn) — `test_surrounding_places.py`

- Không key → dormant (None). Thiếu price_level → None (không bịa giá).

## Direct inputs — `test_surrounding_analyzer.py::TestDirectInputs`

- `location_dependency=primary` / `depends_on_surrounding_customers=True` override ngành.
- `location_profile` echo `type/tenure/rent_cost/known_competitors` (dữ kiện, không benchmark).
