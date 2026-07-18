# Tools

- `calculate_order_economics`: AOV, biến phí/đơn, contribution/đơn, contribution margin và variable-cost ratio. Đây không phải cash flow hoặc net profit.
- `calculate_market_size`: TAM/SAM/SOM từ bốn input có cấu trúc. Không parse textarea bằng LLM.
- `score_business_model`: tỷ lệ đầy đủ của 24 field thuộc Business Model/Development Plan.
- `calculate_unit_economics`: API cũ được giữ để tương thích test/code hiện có; flow F&B mới không dùng CAC/churn vì UI chưa thu thập hai field này.

LLM không được tự thực hiện phép tính hoặc thay đổi tool output.
