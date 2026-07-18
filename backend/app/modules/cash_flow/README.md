# Cash Flow Analysis

Module đánh giá sức khỏe dòng tiền, burn, runway, working capital, break-even và độ nhạy kịch bản. Module không đánh giá sức hấp dẫn thị trường, lợi thế cạnh tranh hoặc chất lượng địa điểm.

## Input

- Facts nhập tay: `current_cash`, `minimum_cash_buffer`, `fixed_monthly_costs`, `variable_cost_ratio`, `accounts_receivable`, `accounts_payable`, `inventory`, `financial_periods` hoặc `cash_flow_dataset`.
- Workbook `.xlsx` đã được Document Intake lưu và truyền `storage_path` vào analyzer.
- Options: `use_cash_flow_ingestion_agent`, `use_cash_flow_mapping_ai`, `scenario_months`, `scenario_assumptions`, `reconciliation_tolerance`.

## Agent–tool ingestion

1. Profiler chỉ gửi tên sheet, kích thước, header và tối đa 50 dòng mẫu/30 cột cho AI.
2. AI trả kế hoạch mapping và lựa chọn tool; AI không tính số.
3. Executor kiểm tra document, sheet, header, column index và tool allowlist.
4. Tool chuẩn hóa cashbook, tổng hợp sales/purchases và trích fact bằng `Decimal`.
5. Module tạo `details.ingestion.autofill_proposals` với `proposal_id`, nguồn, range, confidence và warning.
6. Khi Gemini thiếu/lỗi, header alias fallback vẫn chạy deterministic.

Core module không tự ghi vào `Startup.facts`. Hàm `build_cash_flow_facts_patch` chỉ tạo patch từ proposal người dùng đã chọn; persistence, upload folder và optimistic concurrency thuộc integration layer và cần phê duyệt riêng.

## Output

`ModuleReport` gồm normalized periods, tool-generated metrics, base/best/downside/severe scenarios, score, evidence, warnings và ingestion preview. Mọi phép tính được ghi trong `tool_calls` cùng version/input/output.

Chạy test module:

```powershell
python -m pytest app/modules/cash_flow/tests tests/test_cash_flow_tools.py tests/test_cash_flow_extractor.py tests/test_cash_flow_regressions.py -q
```
