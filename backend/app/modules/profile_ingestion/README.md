# Profile ingestion

Module tạo đề xuất hồ sơ từ tài liệu có bằng chứng. Module không tự ghi vào `Startup.facts`.

## Phạm vi MVP

- Nguồn: tài liệu `shared` dạng PDF có text, DOCX (paragraph và table), PPTX (text và table), TXT, Markdown.
- Field: `name`, `industry`, `stage`, `primary_location`, `business_type`, `problem`, `solution`,
  `target_customers`, `revenue_model`, `traction`.
- XLSX tài chính tiếp tục đi qua `cash_flow`; PDF scan/OCR chưa thuộc phạm vi này.

## Luồng

1. Dùng `document_chatbot.ingestion.file_to_chunks` tạo block có page/slide/table.
2. Chọn block liên quan theo field keyword và gửi bounded context cho Gemini structured output.
3. Backend xác minh mọi quote là nội dung thật trong block được tham chiếu.
4. Chuẩn hóa type/stage/list và tính confidence deterministic.
5. Lưu `ExtractionJob` cùng `ExtractionCandidate` để người dùng review.
6. Endpoint confirm khóa draft, kiểm tra `based_on_startup_updated_at`, validate lại rồi patch từng field
   trong cùng transaction và ghi audit log.

Candidate `ambiguous` hoặc `conflicting` không được accept nguyên trạng; người dùng phải edit hoặc reject.
