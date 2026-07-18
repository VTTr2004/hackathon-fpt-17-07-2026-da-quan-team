# Test cases

- Boundary chỉ giữ 27 field đang hoạt động của Business Model/Development Plan, cộng field legacy tùy chọn để tái lập báo cáo cũ; Cash Flow/Surrounding Area vẫn bị loại.
- Empty string/list là missing; numeric zero vẫn là giá trị có mặt.
- Order economics với contribution dương, âm, AOV bằng 0 và input không hợp lệ.
- Textarea market size không kích hoạt TAM/SAM/SOM.
- Bốn domain call chạy trước Auditor và Composer.
- Source ID lạ/sai domain hoặc finding không có startup evidence bị loại.
- Composer không thể thêm finding ngoài danh sách Auditor đã duyệt.
- Gemini chưa cấu hình/lỗi trả deterministic fallback và không làm API thất bại.
- `use_gemini=false` không gọi LLM.
