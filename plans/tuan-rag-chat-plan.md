# Kế hoạch Module 4 — RAG Chatbot hỏi đáp tài liệu

> **Trạng thái (2026-07-17):** Đã dựng xong lõi RAG chạy end-to-end với 100 dòng CSV.
> LLM = NVIDIA GPT-OSS-120B, embedding = `nv-embedqa-e5-v5`. Retrieval mặc định = **Hybrid (RRF)**,
> rerank tùy chọn (mặc định tắt). Xem kết quả eval + lý do chọn trong
> `backend/app/modules/document_chatbot/docs/methodology.md`.
>
> **Kết luận eval (split thuộc tính, n=40):** hybrid ≥ dense và ổn định hơn → dùng hybrid.
> Rerank chỉ tăng độ chính xác top-1/top-3 (R@1 0.85→0.90, MRR 0.887→0.928), **không tăng Recall@5**
> → khi đưa top-5 vào generator thì không đáng thêm 1 lượt gọi LLM ⇒ mặc định TẮT, bật khi cần top-1 chặt.
>
> Còn lại (TODO): endpoint `GET /chat/history`, bộ test (cross-startup, injection, không-đủ-bằng-chứng),
> và 6/7 tài liệu docs còn thiếu (mới có `methodology.md` + `README.md`).


Chủ sở hữu: Tuấn. Phạm vi sửa: `backend/app/modules/document_chatbot/`, `backend/app/services/chat_service.py`,
`backend/app/services/document_parser.py`, route `chat.py`, schema `chat.py`. Không sửa schema chung và module khác.

## 0. Hiện trạng (đã có sẵn)

- `retrieve(question, documents, limit)` — baseline lexical, đã có interface để thay bằng vector.
- `answer_question()` — retrieve → Gemini generate → citation, có fallback extractive khi thiếu API key.
- `POST /startups/{id}/chat` — đã lọc tuyệt đối theo `startup_id` (chống rò rỉ chéo).
- `document_parser.extract_text()` — PDF/DOCX/PPTX/XLSX/TXT/CSV/MD, đã gắn marker `[PAGE n]`, `[SLIDE n]`, `[SHEET x]`.

## 1. Mục tiêu bản demo với 100 dòng `investments_VC.csv`

Corpus demo = 100 công ty (100 dòng đầu của CSV). Người dùng hỏi tự nhiên trên bộ dữ liệu này, ví dụ:
- "Công ty #waywire gọi được bao nhiêu vốn và ở giai đoạn nào?"
- "Có startup nào ở thị trường Games không, kể vài cái?"
- "Startup nào tại London trong dữ liệu?"

Mỗi câu trả lời phải có citation trỏ về đúng dòng/công ty nguồn. Câu không có trong dữ liệu → từ chối suy diễn.

### Quyết định kiến trúc: CSV là 1 "document" của 1 startup "VC Dataset"

Tận dụng nguyên schema hiện có, ít thay đổi nhất:
1. Tạo 1 startup tên `VC Dataset (demo)` → lấy `startup_id`.
2. Ingest 100 dòng CSV thành 100 **record-card** (mỗi dòng = 1 chunk), gắn metadata `row_index`, `company_name`.
3. Chat trên `startup_id` đó → hỏi đáp toàn bộ 100 công ty. Không đụng luồng startup thật của các module khác.

## 2. Các bước triển khai

### Bước 1 — Ingest CSV → record-cards (`document_chatbot/ingestion.py` mới)

Chuyển mỗi dòng thành 1 đoạn văn ngắn, tự nhiên (tốt cho embedding hơn là chuỗi CSV thô):

```
{name} là startup thị trường {market} tại {city}, {country_code}. Trạng thái: {status}.
Thành lập năm {founded_year}. Nhóm ngành: {category_list}. Tổng vốn: ${funding_total_usd}
qua {funding_rounds} vòng ({first_funding_at} → {last_funding_at}).
Cơ cấu: seed ${seed}, venture ${venture}, angel ${angel}, round A ${round_A}...
```

Mỗi card lưu kèm metadata: `{"row_index": i, "company": name, "market": market, "country": country_code}`.
Giới hạn 100 dòng đầu (`itertools.islice`), bỏ dòng thiếu `name`.

### Bước 2 — Chunking có metadata (`document_chatbot/chunking.py` mới)

- CSV: mỗi record-card đã là 1 chunk (không cần cắt thêm).
- Tài liệu dài (PDF/DOCX...): cắt ~800–1000 token, overlap ~15%, **giữ lại marker trang/slide/sheet** từ parser để suy ra `page`.
- Mỗi chunk = `{chunk_id, document_id, text, metadata: {page|row|slide|sheet}}`.

### Bước 3 — Embedding + vector store

- Thêm `embed_texts(texts) -> list[list[float]]` vào boundary `llm/gemini.py` (model `text-embedding-004`,
  `task_type=RETRIEVAL_DOCUMENT` khi index / `RETRIEVAL_QUERY` khi hỏi). Batch để tiết kiệm quota.
- Với 100 chunk: **không cần pgvector**. Lưu embedding vào cột JSON của bảng `document_chunks` (hoặc file `.npy`
  trong `UPLOAD_DIR`), nạp vào RAM và tính **cosine similarity bằng numpy**. Đủ nhanh, đơn giản, tái lập được.
- Có fallback: nếu chưa cấu hình `GEMINI_API_KEY` → tự động dùng lại retrieval lexical hiện tại (không vỡ demo).

### Bước 4 — Retrieval mới (thay ruột `retrieve()`, giữ nguyên chữ ký)

```python
def retrieve(question, documents, limit=5):
    # 1. embed(question, task=QUERY)
    # 2. cosine với embedding các chunk (đã lọc theo startup ở tầng DB)
    # 3. top-k; optional: hybrid = trộn điểm vector + điểm lexical (BM25 nhẹ)
    # 4. trả [{id, filename, excerpt, page/row, score}]
```

Hybrid (vector + lexical) giúp bắt tên riêng/mã số mà embedding hay bỏ sót — nên bật cho dữ liệu VC.

### Bước 5 — Generation + citation chính xác

- `chat_service.answer_question()` giữ nguyên khung, chỉ bổ sung `page`/`row` vào `Citation` (schema đã có field `page`).
- System prompt giữ nguyên nguyên tắc: chỉ trả lời từ SOURCE, coi nội dung tài liệu là **dữ liệu không phải chỉ dẫn**
  (chống prompt injection), thiếu bằng chứng → "Không tìm thấy thông tin trong tài liệu đã cung cấp".
- Bổ sung bước **kiểm tra citation**: mọi `[SOURCE n]` trong câu trả lời phải nằm trong tập nguồn đã đưa vào.

### Bước 6 — API & lịch sử

- Đã có `POST /startups/{id}/chat`. Bổ sung `GET /startups/{id}/chat/history` (đọc `chat_messages`) đúng như API plan.
- Trả thêm `grounded` (đủ/không đủ bằng chứng) và `recommended_questions` (gợi ý câu hỏi tiếp theo, tùy chọn).

### Bước 7 — Tài liệu bắt buộc (7 file trong `document_chatbot/docs/`)

`README.md` (đã có, cần bổ sung), `methodology.md`, `tools.md`, `sources.md`, `assumptions-and-limitations.md`,
`glossary.md`, `test-cases.md`. Task chưa được coi là xong nếu thiếu bộ này (mục 11 plan).

## 3. Cảnh báo quan trọng: RAG trên dữ liệu bảng

RAG vector **giỏi truy hồi bản ghi cụ thể**, nhưng **không đáng tin cho câu tổng hợp** ("có tổng cộng bao nhiêu công ty
operating?", "tổng vốn thị trường Games?"). Top-k chỉ lấy vài dòng nên đếm/tính tổng sẽ sai.

- Demo an toàn: tập trung câu hỏi kiểu tra cứu (một/vài công ty, một thuộc tính).
- Stretch (nếu còn thời gian): phát hiện câu tổng hợp → chạy tool truy vấn có cấu trúc (pandas/SQL trên CSV) rồi để LLM
  diễn giải — đúng nguyên tắc "tính toán bằng tool, LLM không tự tính" (mục 4 & 6.4 plan). Không để LLM tự cộng.

## 4. Tiêu chí nghiệm thu (mục 15 — Chatbot)

- [ ] Citation mở đúng công ty/dòng nguồn.
- [ ] Câu ngoài dữ liệu bị từ chối, không bịa.
- [ ] Không retrieval chéo giữa hai `startup_id` (đã có filter DB — thêm test).
- [ ] Có test tài liệu mâu thuẫn và prompt injection trong nội dung.
- [ ] Fallback khi thiếu API key vẫn chạy.

## 5. Thứ tự làm (ước lượng)

1. Ingestion CSV + chunking (nửa buổi) — có thể test ngay bằng script, chưa cần LLM.
2. Embedding boundary + vector retrieve + hybrid (1 buổi).
3. Citation page/row + history endpoint (2–3h).
4. Tests (cross-startup, injection, không-đủ-bằng-chứng) + 7 docs (nửa buổi).

---

## Phụ lục — RAG cho nhiều định dạng tài liệu

Đây là hướng mở rộng khi muốn hỏi đáp trên PDF/DOCX/PPTX/XLSX/ảnh/scan... Nguyên tắc: **một pipeline chung, mỗi định
dạng có extractor riêng trả về "segment có metadata" theo một interface thống nhất.**

```
File → [Format detector] → [Extractor theo định dạng] → segments{text, loc}
     → [Chunker theo loại] → chunks{text, metadata}
     → [Embedding] → [Vector index] → [Retrieval] → [LLM + citation trỏ vị trí gốc]
```

### 1. Extractor theo định dạng (giữ được vị trí gốc để citation)

| Định dạng | Thư viện (đã có/nên thêm) | Đơn vị vị trí (citation) |
|---|---|---|
| PDF (text) | `pypdf` (đã có) | trang |
| PDF scan / ảnh | + OCR (`pytesseract`) hoặc Gemini vision | trang + bbox |
| DOCX | `python-docx` (đã có) | heading/đoạn |
| PPTX | `python-pptx` (đã có) | slide |
| XLSX/CSV | `openpyxl` (đã có) | sheet + dòng/ô |
| HTML/MD/TXT | stdlib / `beautifulsoup4` | heading/vị trí |
| Ảnh (png/jpg) | Gemini vision (multimodal) | mô tả + bbox |

Chuẩn hoá đầu ra thành `Segment{text, metadata:{page|slide|sheet|cell|para}}` — phần còn lại của pipeline không cần
biết định dạng gốc.

### 2. Chunking khác nhau theo loại

- Văn bản dài (PDF/DOCX/HTML): cắt theo **ngữ nghĩa/heading**, overlap ~10–15%.
- Trình chiếu (PPTX): **1 slide = 1 chunk** (giữ ngữ cảnh slide).
- Bảng (XLSX/CSV): **1 dòng = 1 record-card** (như phần CSV ở trên); bảng lớn có thể nhóm theo cụm cột.
- Ảnh/scan: OCR/vision → text + giữ toạ độ vùng để citation.

### 3. Những điểm cần xử lý thêm

- **Scan/PDF ảnh**: phát hiện trang không có text layer → chuyển sang OCR/vision, đừng để chunk rỗng.
- **Bảng trong PDF/DOCX**: text thô dễ mất cấu trúc → cân nhắc trích bảng riêng (vd `camelot`/vision) nếu số liệu quan trọng.
- **Metadata thống nhất**: mọi chunk cùng khoá `document_id`, `startup_id`, `page/loc` → giữ được ràng buộc bảo mật và citation.
- **Định dạng hỗn hợp trong 1 file**: PPTX có text + ảnh → chạy cả text extractor và vision cho ảnh trong slide.
- **Kích thước/quota**: file lớn → ingest bất đồng bộ (job), embed theo batch, cache embedding theo hash nội dung để tái lập.

### 4. Điểm mấu chốt

Pipeline retrieval/generation/citation **không đổi** khi thêm định dạng — chỉ cần viết thêm 1 extractor tuân theo
interface `Segment`. Đây chính là lý do interface `retrieve()` hiện tại được thiết kế tách rời khỏi nguồn tài liệu.
