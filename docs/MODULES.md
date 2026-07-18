# Module phân tích & AI

> **Tài liệu kỹ thuật:** [⌂ Tổng quan](../README.md) · [Kiến trúc](ARCHITECTURE.md) · [Module & AI](MODULES.md) · [API](API.md) · [Cài đặt & Kiểm thử](DEVELOPMENT.md) · [Dữ liệu mẫu](SAMPLE_DATA.md) · [Bảo mật](SECURITY.md) · [Triển khai](../DEPLOYMENT.md)

## Contract chung `ModuleReport`

Tất cả module phân tích trả về cùng contract:

```json
{
  "module": "business_model|cash_flow|surrounding_area",
  "version": "0.1.0",
  "status": "completed|partial|insufficient_data|not_applicable|failed",
  "score": 0,
  "summary": "...",
  "findings": [],
  "risks": [],
  "missing_data": [],
  "assumptions": [],
  "recommended_questions": [],
  "evidence": [],
  "methodology": [],
  "tool_calls": [],
  "details": {}
}
```

## 1. Business Model

Mục tiêu: đánh giá vấn đề, giải pháp, khách hàng, mô hình doanh thu, kênh bán hàng, traction, kế hoạch phát triển và logic mở rộng.

Đặc điểm:

- Chỉ nhận dữ liệu thuộc Business Model/Development Plan; dữ liệu Cash Flow và Location bị loại ở boundary.
- Tính `data_completeness`, contribution/order economics và market sizing khi đủ input.
- Có flow subagent gồm Customer & Value Proposition, Retail Model & Channels, Economics & Market Evidence, Development Plan.
- Auditor loại claim thiếu evidence hoặc vượt phạm vi.
- Gemini chỉ diễn giải các finding đã được kiểm duyệt, không tự tính số.

Tài liệu chi tiết: [`backend/app/modules/business_model/README.md`](../backend/app/modules/business_model/README.md)

## 2. Cash Flow

Mục tiêu: đánh giá sức khỏe dòng tiền, burn, runway, working capital, break-even và độ nhạy kịch bản.

Đặc điểm:

- Nhận facts tài chính và workbook `.xlsx` đã upload.
- Profiler chỉ gửi metadata sheet/header/sample rows cho AI mapping; AI không tính số.
- Tool chuẩn hóa cashbook, tổng hợp sales/purchases, loại giao dịch chuyển nội bộ, reconcile và tính metrics bằng `Decimal`.
- Trả về periods chuẩn hóa, base/adverse/severe scenarios, score, warnings, evidence và autofill proposals.

Tài liệu chi tiết: [`backend/app/modules/cash_flow/README.md`](../backend/app/modules/cash_flow/README.md)

## 3. Surrounding Area

Mục tiêu: kiểm chứng claim của startup về khu vực, đối thủ, cầu địa phương và tính phù hợp vị trí.

Đặc điểm:

- Phân loại ngành phụ thuộc vị trí hay không; SaaS/fintech có thể trả `not_applicable`.
- Thiếu tọa độ đã xác nhận trả `insufficient_data`, không chấm 0.
- Analyzer v2 dùng Google Places API New để lấy quan sát POI theo nhóm, tính coverage, competitor density, demand proxy và verdict claim.
- Endpoint `/surrounding/map` vẫn dùng `poi.db` từ OpenStreetMap để render POI và deep-link Google Maps nếu đã build dữ liệu local.
- Có satellite context tùy chọn qua Copernicus Sentinel-2 STAC.
- Không đoán giá thuê, popular times hoặc thông tin không có nguồn; các mục này được đánh dấu thiếu dữ liệu.

Tài liệu chi tiết: [`backend/app/modules/surrounding_area/README.md`](../backend/app/modules/surrounding_area/README.md) · Roadmap: [`plans/surrounding-area-update.md`](../plans/surrounding-area-update.md)

## Investor matching

Module `matching` chấm mức phù hợp giữa snapshot startup và investment thesis của nhà đầu tư, phục vụ trang `/investor/candidates` và `/investor/compare`. Đây là scoring deterministic, không giao cho LLM tự đoán.

- `fit_score` (0-100) tổng hợp từ 9 chiều có trọng số: industry, stage, ticket, location, traction, unit economics, scalability, funding timing và capability need.
- `confidence_score` phản ánh mức đầy đủ dữ liệu; trường thiếu được liệt kê trong `missing_evidence` thay vì bị coi là điểm 0.
- Trả về `score_breakdown`, `matched_reasons`, `mismatched_reasons` để investor hiểu vì sao một hồ sơ được đề xuất.
- `recommended_action` là `request_access` khi fit và confidence đủ cao, `review` ở mức trung bình, còn lại là `pass`.
- Hard filter loại sớm các candidate không đạt tiêu chí bắt buộc trước khi tính score.

## Trích xuất hồ sơ tự động

Module `profile_ingestion` sinh đề xuất field hồ sơ từ tài liệu đã upload, giúp startup không phải nhập tay toàn bộ. Module không tự ghi vào `Startup.facts`; startup phải xác nhận candidate trước.

- Nguồn: tài liệu `shared` dạng PDF/PNG/JPEG (Gemini OCR khi cần), DOCX, PPTX, TXT, Markdown.
- Field hỗ trợ: `name`, `industry`, `stage`, `primary_location`, `business_type`, `problem`, `solution`, `target_customers`, `revenue_model`, `traction`. XLSX tài chính vẫn đi qua module Cash Flow.
- Mỗi candidate đi kèm evidence theo trường (file, trang/sheet) để người dùng đối chiếu trước khi confirm.
- Luồng API: `POST .../extractions` → `GET .../extractions/{id}` → `POST .../extractions/{id}/confirm`.

Tài liệu chi tiết: [`backend/app/modules/profile_ingestion/README.md`](../backend/app/modules/profile_ingestion/README.md)

## Chatbot tài liệu (RAG)

Document Chatbot là pipeline RAG theo scope startup/version:

1. Tạo synthetic profile document từ dữ kiện hồ sơ.
2. Parse tài liệu `CSV`, `JSON`, `XLSX`, `TXT`, `MD`, `PDF`, `DOCX`, `PPTX`.
3. Chunk có metadata `page`, `slide`, `sheet`, `row`.
4. Build hoặc load hybrid index theo `startup_id:version` hoặc `startup_id:draft`.
5. Retrieve bằng dense embedding + BM25, trộn bằng Reciprocal Rank Fusion.
6. Rerank tùy chọn.
7. Generate câu trả lời chỉ từ nguồn đã retrieve, chuẩn hóa citation `[1]`, `[2]`.
8. Nếu LLM thiếu key hoặc lỗi quota/timeout, fallback extractive thay vì fail request.

Provider:

- Mặc định: Gemini (`gemini-flash-latest`, `gemini-embedding-001`).
- Tùy chọn: NVIDIA NIM (`openai/gpt-oss-120b`, `nvidia/nv-embedqa-e5-v5`).

Tài liệu chi tiết: [`backend/app/modules/document_chatbot/docs/README.md`](../backend/app/modules/document_chatbot/docs/README.md)
