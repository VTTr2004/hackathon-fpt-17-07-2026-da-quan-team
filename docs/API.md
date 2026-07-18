# API & Luồng nghiệp vụ

> **Tài liệu kỹ thuật:** [⌂ Tổng quan](../README.md) · [Kiến trúc](ARCHITECTURE.md) · [Module & AI](MODULES.md) · [API](API.md) · [Cài đặt & Kiểm thử](DEVELOPMENT.md) · [Dữ liệu mẫu](SAMPLE_DATA.md) · [Bảo mật](SECURITY.md) · [Triển khai](../DEPLOYMENT.md)

Tất cả endpoint backend có prefix `/api/v1`. Một số luồng API chính:

```text
POST /api/v1/auth/register
POST /api/v1/auth/login
GET  /api/v1/auth/me
POST /api/v1/startups
GET  /api/v1/startups/{id}/completeness
POST /api/v1/startups/{id}/extractions
GET  /api/v1/startups/{id}/extractions/{extraction_id}
POST /api/v1/startups/{id}/extractions/{extraction_id}/confirm
POST /api/v1/startups/{id}/submit
POST /api/v1/startups/{id}/draft
GET  /api/v1/startups/{id}/versions
POST /api/v1/startups/{id}/documents
POST /api/v1/startups/{id}/analyses/business_model
POST /api/v1/startups/{id}/analyses/cash_flow
POST /api/v1/startups/{id}/analyses/surrounding_area
POST /api/v1/startups/{id}/chat
POST /api/v1/surrounding/geocode
GET  /api/v1/surrounding/map
```

## Auth

| Method | Endpoint | Mô tả |
|---|---|---|
| `POST` | `/auth/register` | Tạo tài khoản startup/investor |
| `POST` | `/auth/login` | Đăng nhập, trả access token |
| `GET` | `/auth/me` | Lấy user hiện tại |
| `GET` | `/auth/investors` | Startup lấy danh sách investor để cấp quyền |

## Startup và version

| Method | Endpoint | Quyền | Mô tả |
|---|---|---|---|
| `GET` | `/startups` | Đăng nhập | Danh sách hồ sơ theo ownership/access |
| `POST` | `/startups` | Startup | Tạo hồ sơ draft |
| `GET` | `/startups/{id}` | Có quyền | Startup đọc live draft; investor đọc latest snapshot |
| `PATCH` | `/startups/{id}` | Owner + draft | Cập nhật profile/facts |
| `GET` | `/startups/{id}/completeness` | Owner | Kiểm tra dữ liệu và tài liệu trước khi nộp |
| `POST` | `/startups/{id}/submit` | Owner + draft | Tạo snapshot và khóa phiên bản |
| `POST` | `/startups/{id}/draft` | Owner | Tạo draft mới sau khi đã nộp |
| `GET` | `/startups/{id}/versions` | Có quyền | Danh sách version đã nộp |
| `GET` | `/startups/{id}/versions/diff` | Có quyền | So sánh hai version |
| `GET` | `/startups/{id}/access` | Owner | Danh sách quyền investor |
| `POST` | `/startups/{id}/access` | Owner | Cấp quyền investor |
| `DELETE` | `/startups/{id}/access/{investor_id}` | Owner | Thu hồi quyền investor |

## Documents, analyses, chat, surrounding

| Method | Endpoint | Quyền | Mô tả |
|---|---|---|---|
| `GET` | `/startups/{id}/documents` | Có quyền | Startup thấy tất cả; investor thấy shared docs trong latest version |
| `POST` | `/startups/{id}/documents` | Owner + draft | Upload và parse tài liệu |
| `PATCH` | `/startups/{id}/documents/{document_id}` | Owner + draft | Đổi visibility nếu tài liệu chưa bị khóa trong version |
| `POST` | `/startups/{id}/extractions` | Owner + draft | Sinh candidate dữ liệu hồ sơ từ tài liệu đã upload |
| `GET` | `/startups/{id}/extractions/{extraction_id}` | Owner + draft | Xem kết quả trích xuất kèm bằng chứng theo trường |
| `POST` | `/startups/{id}/extractions/{extraction_id}/confirm` | Owner + draft | Xác nhận candidate và ghi vào hồ sơ draft |
| `GET` | `/startups/{id}/analyses` | Có quyền | List analysis theo user và version/draft |
| `POST` | `/startups/{id}/analyses/{module}` | Startup/Investor theo module | Chạy `business_model`, `cash_flow`, `surrounding_area` |
| `GET` | `/startups/{id}/chat/history` | Có quyền | Lịch sử chat theo user và version/draft |
| `POST` | `/startups/{id}/chat` | Có quyền | Hỏi đáp tài liệu có citation |
| `POST` | `/surrounding/geocode` | Đăng nhập | Địa chỉ sang candidates tọa độ, cần xác nhận |
| `GET` | `/surrounding/map` | Investor | POI map từ `poi.db` |
| `GET` | `/surrounding/satellite` | Investor | Sentinel-2 scene metadata/quicklook |

## Investor discovery và matching

| Method | Endpoint | Quyền | Mô tả |
|---|---|---|---|
| `GET` | `/investor/preferences` | Investor | Đọc investment thesis hiện tại |
| `PATCH` | `/investor/preferences` | Investor | Cập nhật investment thesis |
| `GET` | `/investor/candidates` | Investor | Danh sách candidate công khai kèm fit score |
| `GET` | `/investor/candidates/{startup_id}` | Investor | Chi tiết một candidate |
| `POST` | `/investor/matches` | Investor | Chấm lại match theo thesis hiện tại |
| `POST` | `/investor/compare` | Investor | So sánh nhiều candidate cùng lúc |
| `POST` | `/investor/candidates/{startup_id}/shortlist` | Investor | Thêm candidate vào pipeline |
| `GET` | `/investor/pipeline` | Investor | Danh sách pipeline đầu tư |
| `PATCH` | `/investor/pipeline/{item_id}` | Investor | Cập nhật trạng thái item pipeline |

## Investor discovery và access workflow

Hệ thống giữ đúng hai role `startup` và `investor`. Startup nộp snapshot rồi bật
`discoverable`; investor cấu hình investment thesis, nhận candidate card công khai,
shortlist và so sánh mà không cần phê duyệt. Chỉ khi investor yêu cầu mở Data Room
thì startup mới quyết định cấp quyền. `StartupAccess` dùng state machine
`pending -> active/rejected`, và `active -> revoked`; chỉ `active` được mở data room,
chạy analysis và document chat. Pipeline đầu tư được lưu độc lập với quyền dữ liệu.

Các màn hình chính: `/investor/preferences`, `/investor/candidates` và
`/investor/pipeline`. API tương ứng nằm dưới `/api/v1/investor`, còn request và phê
duyệt quyền Data Room nằm dưới `/api/v1/startups/{id}`.

## Completeness trước khi nộp

Backend yêu cầu các nhóm dữ liệu sau trước khi `submit`:

- Tên startup.
- Lĩnh vực.
- Giai đoạn.
- Địa điểm chính xác.
- Nhu cầu hoặc vấn đề khách hàng.
- Giải pháp.
- Khách hàng mục tiêu.
- Nguồn doanh thu.
- Tiền mặt hiện có.
- Dòng tiền theo kỳ.
- Ít nhất một tài liệu nền ở visibility `shared`.

`current_cash` phải là số không âm. Nếu thiếu dữ liệu, API trả danh sách `missing_fields`, `missing_documents`, `format_errors` và `can_submit=false`.
