# Business Model Analysis

Module phân tích Business Model cho F&B và bán lẻ nhỏ. Module chỉ nhận 27 field Business Model/Development Plan đang hoạt động trên UI; dữ liệu Cash Flow, vị trí và Surrounding Area bị loại tại boundary. `variable_cost_per_order` chỉ được đọc như dữ liệu legacy để tái lập báo cáo cũ và không tham gia điểm completeness.

## Flow

1. Whitelist input và đo `data_completeness` bằng code deterministic.
2. Tính contribution cấp đơn khi có AOV và chi phí biến đổi/đơn.
3. Coordinator gửi bộ câu hỏi cố định cho bốn subagent chạy song song:
   - Customer & Value Proposition;
   - Retail Model & Channels;
   - Economics & Market Evidence;
   - Development Plan.
4. Citation & Evidence Auditor loại claim thiếu startup evidence, sai source hoặc vượt phạm vi.
5. Report Composer chỉ diễn đạt các finding đã được Auditor chấp nhận.
6. Adapter trả `ModuleReport` tương thích API hiện tại.

System prompt nằm trong `prompts/` để được đóng gói cùng Docker image. Mỗi prompt chứa research digest đủ dùng; runtime không tải toàn bài báo.

## Options

- `use_business_agents`: bật/tắt flow subagent; mặc định theo `use_gemini`.
- `use_gemini`: khi false, module chỉ trả deterministic fallback.
- `market_size_inputs`: chỉ tính TAM/SAM/SOM nếu có đủ bốn field có cấu trúc: `total_customers`, `annual_revenue_per_customer`, `reachable_share`, `target_share`.

Khi flow agent hoàn tất hoặc đã được thử chạy, analyzer tắt vòng Gemini narrative dùng chung để Composer không bị ghi đè. Đây là workaround nội bộ nhằm không sửa service/module khác.
