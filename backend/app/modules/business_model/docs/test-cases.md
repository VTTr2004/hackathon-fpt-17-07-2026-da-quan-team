# Test cases

- Boundary chỉ giữ 24 field Business Model và loại Cash Flow/Surrounding Area.
- Empty string/list là missing; numeric zero vẫn là giá trị có mặt.
- Order economics với contribution dương, âm, AOV bằng 0 và input không hợp lệ.
- Textarea market size không kích hoạt TAM/SAM/SOM.
- Bốn domain call chạy trước Auditor và Composer.
- Source ID lạ/sai domain hoặc finding không có startup evidence bị loại.
- Composer không thể thêm finding ngoài danh sách Auditor đã duyệt.
- Gemini chưa cấu hình/lỗi trả deterministic fallback và không làm API thất bại.
- `use_gemini=false` không gọi LLM.
