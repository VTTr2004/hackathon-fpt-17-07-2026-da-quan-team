# Bảo mật & giới hạn

> **Tài liệu kỹ thuật:** [⌂ Tổng quan](../README.md) · [Kiến trúc](ARCHITECTURE.md) · [Module & AI](MODULES.md) · [API](API.md) · [Cài đặt & Kiểm thử](DEVELOPMENT.md) · [Dữ liệu mẫu](SAMPLE_DATA.md) · [Bảo mật](SECURITY.md) · [Triển khai](../DEPLOYMENT.md)

## Cơ chế bảo mật

- Mật khẩu được hash bằng PBKDF2-HMAC-SHA256.
- Token là HMAC signed token có thời hạn, cấu hình bởi `AUTH_TOKEN_TTL_HOURS`.
- Backend trả `404` cho tài nguyên không có quyền để tránh lộ sự tồn tại hồ sơ.
- Investor chỉ đọc latest submitted snapshot và tài liệu `shared`.
- Analysis của investor được scope theo `startup_version_id` và `created_by_id`.
- Chat history được scope theo startup, user và version/draft.
- RAG prompt coi `USER_QUESTION`, `CHAT_HISTORY` và `SOURCES` là dữ liệu không đáng tin cậy, không phải instruction.
- Tài liệu đã nằm trong snapshot đã nộp không được đổi visibility; muốn cập nhật phải upload bản mới trong draft.

## Giới hạn đã biết

- Rate limit cho geocode/map/satellite hiện là in-process, theo user ID; multi-instance production nên chuyển sang Redis.
- Surrounding Area phụ thuộc chất lượng dữ liệu bản đồ và giới hạn provider; thiếu dữ liệu trả `insufficient_data`, không được biến thành điểm 0.
- Kết quả phân tích không phải tư vấn đầu tư, tư vấn pháp lý, kế toán hoặc thuế chính thức.

## Báo cáo audit

Chi tiết đánh giá lỗ hổng bảo mật và logic nghiệp vụ (SEC-01/02/03 và trạng thái khắc phục): [`security_audit_report.md`](../security_audit_report.md).
