# Trợ lý Đánh giá Startup và Hỏi đáp Tài liệu

## 1. Mục tiêu sản phẩm

Xây dựng một trợ lý AI giúp chuyên viên đọc hồ sơ startup, thực hiện các phân tích chuyên sâu và hỏi đáp trực tiếp trên tài liệu do startup cung cấp.

Sản phẩm trong phạm vi hackathon chỉ tập trung vào hai năng lực:

1. **Đánh giá startup** qua ba module độc lập:
   - Phân tích chuyên sâu mô hình kinh doanh.
   - Phân tích chuyên sâu dòng tiền.
   - Phân tích chuyên sâu khu vực xung quanh.
2. **Chatbot hỏi đáp tài liệu startup** có trích dẫn chính xác về tài liệu nguồn.

AI là công cụ hỗ trợ nghiên cứu và ra quyết định. AI không tự đưa ra quyết định đầu tư cuối cùng và không được tạo dữ kiện khi không có bằng chứng.

## 2. Người dùng và bài toán

### Người dùng chính

- Chuyên viên đánh giá startup.
- Nhà đầu tư hoặc quỹ đầu tư.
- Bộ phận đổi mới sáng tạo của doanh nghiệp.

### Bài toán cần giải quyết

- Hồ sơ startup nằm rải rác trong pitch deck, kế hoạch kinh doanh, báo cáo tài chính và tài liệu phụ trợ.
- Chuyên viên phải đọc thủ công, tìm nguồn nghiên cứu và tổng hợp nhận định.
- Mỗi chuyên viên có thể sử dụng thuật ngữ, phương pháp và tiêu chí khác nhau.
- Các nhận định do AI tạo ra khó kiểm chứng nếu không có trích dẫn và phương pháp rõ ràng.
- Người dùng mất thời gian tìm lại thông tin cụ thể trong bộ tài liệu của startup.

## 3. Phạm vi MVP

### Bắt buộc

1. Tạo hồ sơ startup và tải lên tài liệu `PDF`, `DOCX`, `PPTX`, `XLSX` hoặc văn bản.
2. Trích xuất, chia đoạn và lập chỉ mục nội dung tài liệu.
3. Chuẩn hóa các dữ kiện chung của startup theo một schema thống nhất.
4. Chạy độc lập một hoặc nhiều module phân tích.
5. Mỗi module trả về báo cáo có cấu trúc, điểm đánh giá, rủi ro, dữ liệu thiếu, giả định và nguồn tham chiếu.
6. Tổng hợp kết quả ba module thành một trang đánh giá chung mà không làm mất báo cáo gốc.
7. Chatbot trả lời dựa trên tài liệu startup và trích dẫn tài liệu, trang hoặc đoạn nguồn.
8. Cho phép chuyên viên kiểm tra và chỉnh sửa phần kết luận trước khi lưu.

### Ngoài phạm vi

- Matching startup với nhà đầu tư hoặc đối tác.
- Soạn và gửi email kết nối.
- Đồng bộ lịch hoặc đặt lịch họp.
- Investment Policy Studio và trình chỉnh sửa rubric kéo thả.
- Tự động thu thập dữ liệu từ website trái điều khoản sử dụng.
- Tự quyết định đầu tư, cam kết lợi nhuận hoặc đưa ra tư vấn tài chính chính thức.
- Mô hình dự báo tài chính đầy đủ cho mọi ngành.

## 4. Nguyên tắc thiết kế

1. **Evidence first:** Mọi nhận định quan trọng phải có nguồn hoặc được đánh dấu rõ là giả định.
2. **Không tự suy diễn:** Khi thiếu dữ liệu, trả về `Chưa đủ thông tin` và câu hỏi cần làm rõ.
3. **Tách dữ kiện và nhận định:** Dữ kiện trích từ hồ sơ không được trộn với kết luận của AI.
4. **Tính toán bằng tool:** Mọi công thức, phép tổng hợp số liệu, thuật toán xếp hạng, mô phỏng và phép tính không gian phải được đóng gói thành tool chạy bằng code; LLM chỉ chọn tool, truyền input hợp lệ và diễn giải output.
5. **Đầu ra có cấu trúc:** Tất cả module phải tuân thủ JSON schema chung trước khi hiển thị.
6. **Có thể tái lập:** Báo cáo lưu phiên bản prompt, thuật toán, nguồn, thời điểm truy cập và dữ liệu đầu vào.
7. **Module độc lập:** Một module lỗi không làm hỏng hai module còn lại hoặc chatbot.
8. **Human in the loop:** Chuyên viên luôn có quyền kiểm tra, ghi chú và điều chỉnh kết luận.

## 5. Kiến trúc chức năng

```text
Tài liệu startup
       |
       v
Document Intake & Shared Facts
       |
       +----------------+----------------+----------------+
       |                |                |                |
       v                v                v                v
Business Model     Cash Flow       Surrounding Area   Document Chatbot
Analysis           Analysis        Analysis           (RAG)
       |                |                |
       +----------------+----------------+
                        |
                        v
              Evaluation Aggregator
                        |
                        v
              Báo cáo để chuyên viên duyệt
```

### Thành phần dùng chung

- **Document Intake:** tải lên, kiểm tra định dạng, trích xuất văn bản và metadata.
- **Shared Facts:** lưu dữ kiện đã trích xuất để các module không phải đọc và chuẩn hóa lại theo cách riêng.
- **Evidence Store:** quản lý trích dẫn từ tài liệu startup và nguồn nghiên cứu bên ngoài.
- **Evaluation Aggregator:** ghép các báo cáo module, không tự viết lại hoặc thay đổi kết quả của module.
- **Document Chatbot:** tìm kiếm và trả lời chỉ từ tài liệu startup đã được cấp quyền.

## 6. Hợp đồng dữ liệu chung

Các thành viên chốt schema này trước khi phát triển module. Thay đổi schema phải được cả nhóm duyệt.

### 6.1. `StartupFacts`

```json
{
  "startup_id": "string",
  "name": "string|null",
  "industry": "string|null",
  "stage": "string|null",
  "operating_locations": [],
  "problem": "string|null",
  "solution": "string|null",
  "target_customers": [],
  "revenue_model": [],
  "traction": [],
  "team": [],
  "funding_need": null,
  "financial_periods": [],
  "facts": [],
  "missing_fields": []
}
```

Mỗi phần tử trong `facts` phải chứa giá trị, `document_id`, vị trí trích dẫn, độ tin cậy và trạng thái xác nhận.

### 6.2. `Evidence`

```json
{
  "evidence_id": "string",
  "source_type": "startup_document|external_research|calculation",
  "title": "string",
  "publisher": "string|null",
  "url": "string|null",
  "document_id": "string|null",
  "page": "number|null",
  "quote": "string|null",
  "accessed_at": "datetime|null",
  "published_at": "date|null",
  "reliability": "high|medium|low",
  "notes": "string|null"
}
```

### 6.3. `ModuleReport`

```json
{
  "module": "business_model|cash_flow|surrounding_area",
  "version": "string",
  "status": "completed|partial|insufficient_data|failed",
  "score": "number|null",
  "summary": "string",
  "findings": [],
  "risks": [],
  "missing_data": [],
  "assumptions": [],
  "recommended_questions": [],
  "evidence": [],
  "methodology": [],
  "generated_at": "datetime"
}
```

Không module nào được thêm field riêng trực tiếp vào schema chung. Dữ liệu đặc thù đặt trong `details` của module hoặc schema nội bộ do module sở hữu.

### 6.4. Hợp đồng `AnalysisTool`

Trong ba module phân tích chuyên sâu, bất kỳ bước nào có kết quả xác định được bằng công thức hoặc thuật toán đều phải xây dựng thành tool. Không đặt phép tính trực tiếp trong prompt và không yêu cầu LLM tự tính nhẩm.

Một tool tối thiểu phải có:

```json
{
  "name": "string",
  "version": "string",
  "description": "string",
  "input_schema": {},
  "output_schema": {},
  "methodology_reference": "string",
  "deterministic": true
}
```

Quy trình gọi tool:

1. LLM hoặc orchestration xác định tool cần dùng.
2. Input được parse về kiểu dữ liệu chuẩn, kiểm tra đơn vị, kỳ thời gian và trường bắt buộc.
3. Tool chạy bằng code và trả output có cấu trúc cùng cảnh báo dữ liệu.
4. Hệ thống lưu tên tool, phiên bản, input, output và thời gian chạy vào báo cáo.
5. LLM chỉ diễn giải output, liên kết với bằng chứng và nêu giới hạn; không được sửa giá trị tool trả về.

Yêu cầu kỹ thuật đối với tool:

- Có JSON schema rõ ràng cho input và output.
- Validate dữ liệu thiếu, sai kiểu, sai đơn vị, chia cho 0 và giá trị ngoài miền hợp lệ.
- Kết quả giống nhau khi dùng cùng input và cùng phiên bản tool.
- Có unit test với kết quả được tính tay hoặc đối chiếu bằng bộ dữ liệu chuẩn.
- Có thông báo lỗi có cấu trúc; lỗi tool không được thay bằng một con số do LLM đoán.
- Có tài liệu công thức, thuật toán, nguồn phương pháp và giới hạn áp dụng.
- Tool gọi API hoặc dữ liệu bên ngoài phải lưu nguồn, tham số truy vấn, thời điểm truy cập và response cần thiết để kiểm tra.

Các bước mang tính tổng hợp định tính như giải thích lợi thế cạnh tranh, nhận diện giả định hoặc tạo câu hỏi bổ sung có thể do LLM thực hiện, nhưng vẫn phải dựa trên evidence.

## 7. Module 1 — Phân tích chuyên sâu mô hình kinh doanh

### Mục tiêu

Đánh giá mức độ hợp lý, khác biệt và khả năng mở rộng của mô hình kinh doanh, dựa trên dữ kiện startup và nghiên cứu ngành.

### Phạm vi sở hữu

- Vấn đề và nhu cầu khách hàng.
- Phân khúc khách hàng và job-to-be-done.
- Giá trị khác biệt và phương án thay thế.
- Kênh tiếp cận, quan hệ khách hàng và đối tác chính.
- Mô hình doanh thu và logic unit economics ở cấp mô hình.
- TAM/SAM/SOM và động lực thị trường.
- Lợi thế cạnh tranh, khả năng phòng thủ và khả năng mở rộng.

### Phương pháp/thuật ngữ nghiên cứu gợi ý

- Business Model Canvas và Lean Canvas.
- Jobs-to-be-Done.
- Value Proposition Canvas.
- TAM/SAM/SOM theo top-down và bottom-up.
- Five Forces, SWOT hoặc PESTEL khi phù hợp.
- CAC, LTV, gross margin, payback period ở mức mô hình; việc tính dòng tiền thuộc Module 2.

### Tool tính toán bắt buộc

- `market_size_calculator`: tính TAM/SAM/SOM từ các tham số và phương pháp được chọn.
- `unit_economics_calculator`: tính CAC, LTV, LTV/CAC, gross margin và payback period khi đủ dữ liệu.
- `business_model_score_calculator`: tính điểm rubric và mức độ đầy đủ của dữ liệu.

Các framework định tính như Business Model Canvas, JTBD, SWOT hoặc Five Forces không bắt buộc biến thành tool tính toán. Tuy nhiên, nếu có chấm điểm, quy đổi trọng số hoặc xếp hạng từ các framework này thì phần tính điểm phải nằm trong tool.

### Không thuộc module này

- Dự báo số dư tiền, burn rate và runway.
- Phân tích bán kính, mật độ dân cư hoặc vị trí vật lý.

### Đầu ra bắt buộc

- Bản đồ mô hình kinh doanh hiện tại.
- Nhận định theo từng tiêu chí, kèm bằng chứng.
- Các giả định mô hình chưa được kiểm chứng.
- Rủi ro cạnh tranh và rủi ro mở rộng.
- Câu hỏi cần startup làm rõ.
- Điểm 0–100 và diễn giải cách tính.

## 8. Module 2 — Phân tích chuyên sâu dòng tiền

### Mục tiêu

Đánh giá sức khỏe dòng tiền, khả năng duy trì hoạt động và độ nhạy trước các kịch bản tài chính.

### Phạm vi sở hữu

- Chuẩn hóa dòng tiền vào và dòng tiền ra theo kỳ.
- Operating, investing và financing cash flow khi dữ liệu cho phép.
- Gross burn, net burn và runway.
- Working capital, chu kỳ thu tiền và chu kỳ trả tiền.
- Điểm hòa vốn và khoảng thiếu hụt tiền mặt.
- Base case, best case và stress case.
- Cảnh báo dữ liệu tài chính thiếu, mâu thuẫn hoặc bất thường.

### Công thức tối thiểu

- `Net cash flow = Cash inflow - Cash outflow`.
- `Net burn = Monthly cash outflow - Monthly cash inflow` khi kết quả dương.
- `Runway = Current cash / Net burn` khi net burn lớn hơn 0.
- Các công thức khác phải được mô tả trong tài liệu phương pháp và kiểm thử bằng dữ liệu mẫu.

### Tool tính toán bắt buộc

- `cash_flow_normalizer`: chuẩn hóa kỳ, tiền tệ, nhóm dòng tiền vào/ra và phát hiện dữ liệu không đều.
- `cash_metrics_calculator`: tính net cash flow, gross burn, net burn, runway và các chỉ số vốn lưu động được chọn.
- `break_even_calculator`: tính điểm hòa vốn theo dữ liệu đầu vào đã xác nhận.
- `cash_scenario_simulator`: chạy base case, best case và stress case theo bộ giả định tường minh.
- `cash_flow_score_calculator`: tính điểm rubric tài chính và mức độ đầy đủ của dữ liệu.

LLM không được tự cộng bảng dòng tiền, tự tính phần trăm tăng trưởng hoặc tự dự báo số dư tiền. Nếu không có tool phù hợp, kết quả phải được đánh dấu `Chưa hỗ trợ tính toán`.

### Không thuộc module này

- Đánh giá sức hấp dẫn thị trường hoặc lợi thế cạnh tranh.
- Đánh giá chất lượng vị trí và khu vực xung quanh.

### Đầu ra bắt buộc

- Bảng dòng tiền đã chuẩn hóa theo kỳ.
- Các chỉ số tài chính được tính bằng code.
- Biểu đồ dòng tiền và runway.
- Kịch bản cơ sở và ít nhất một stress scenario.
- Cảnh báo, giả định và dữ liệu còn thiếu.
- Điểm 0–100 và diễn giải cách tính.

## 9. Module 3 — Phân tích chuyên sâu khu vực xung quanh

### Mục tiêu

Đánh giá mức độ phù hợp của vị trí kinh doanh đối với các startup có kết quả phụ thuộc vào địa điểm vật lý.

### Điều kiện chạy

Module chỉ chạy khi có địa chỉ hoặc tọa độ đủ chính xác. Với startup thuần số hoặc không phụ thuộc vị trí, trả về `Không áp dụng` thay vì ép chấm điểm.

### Phạm vi sở hữu

- Chuẩn hóa địa chỉ và tọa độ.
- Phân tích theo bán kính hoặc thời gian di chuyển.
- Mật độ khách hàng mục tiêu hoặc proxy phù hợp.
- Đối thủ, sản phẩm thay thế và điểm hút khách trong khu vực.
- Khả năng tiếp cận giao thông, logistics và tiện ích hỗ trợ.
- Chi phí mặt bằng hoặc chi phí khu vực nếu có nguồn đáng tin cậy.
- Rủi ro quy hoạch, pháp lý, môi trường hoặc phụ thuộc vị trí khi có dữ liệu.

### Phương pháp/thuật toán nghiên cứu gợi ý

- Geocoding và kiểm tra độ chính xác tọa độ.
- Haversine distance hoặc routing distance.
- Phân tích buffer/radius và point-of-interest density.
- Weighted location score.
- So sánh nhiều khu vực trên cùng bộ tiêu chí.

### Tool tính toán bắt buộc

- `geocoder`: chuyển địa chỉ thành tọa độ và trả mức độ chính xác của kết quả.
- `distance_calculator`: tính Haversine distance hoặc khoảng cách theo tuyến đường.
- `area_buffer_analyzer`: lọc và tổng hợp điểm dữ liệu theo bán kính hoặc thời gian di chuyển.
- `poi_density_calculator`: tính mật độ đối thủ, khách hàng proxy và tiện ích theo khu vực.
- `location_score_calculator`: áp dụng trọng số đã công bố để tính điểm vị trí.

Việc lấy dữ liệu bản đồ hoặc POI có thể dùng API bên ngoài, nhưng phép lọc, đếm, tính khoảng cách và chấm điểm phải do tool xử lý. LLM không được ước lượng khoảng cách hoặc mật độ từ mô tả bằng văn bản.

### Không thuộc module này

- Phân tích mô hình doanh thu tổng thể.
- Tính runway và dự báo dòng tiền của doanh nghiệp.

### Đầu ra bắt buộc

- Bản đồ hoặc danh sách điểm quan trọng quanh vị trí.
- Bảng chỉ số theo bán kính/thời gian di chuyển.
- Các thuận lợi, bất lợi và rủi ro vị trí.
- Nguồn, thời điểm truy cập và độ tin cậy của dữ liệu địa lý.
- Điểm 0–100 hoặc trạng thái `Không áp dụng`.

## 10. Module 4 — Chatbot hỏi đáp tài liệu startup

### Mục tiêu

Cho phép người dùng hỏi trực tiếp trên toàn bộ tài liệu của một startup mà không phải tìm thủ công.

### Quy tắc trả lời

- Chỉ sử dụng tài liệu của startup đang được chọn làm nguồn trả lời mặc định.
- Không sử dụng kiến thức web để lấp khoảng trống trong câu trả lời về hồ sơ.
- Mỗi ý quan trọng phải trích dẫn tên tài liệu và trang hoặc đoạn.
- Nếu không tìm thấy bằng chứng, trả lời rõ `Không tìm thấy thông tin trong tài liệu đã cung cấp`.
- Khi hai tài liệu mâu thuẫn, hiển thị cả hai trích dẫn và cảnh báo mâu thuẫn.
- Câu trả lời phải tách rõ nội dung trích từ tài liệu và phần diễn giải.
- Không để người dùng của startup này truy cập tài liệu của startup khác.

### Luồng RAG tối thiểu

1. Parse tài liệu và giữ metadata trang/slide/sheet.
2. Chia đoạn có overlap và gắn `startup_id`, `document_id`.
3. Tạo embedding và lập chỉ mục.
4. Lọc tuyệt đối theo `startup_id` trước khi retrieval.
5. Lấy các đoạn liên quan, có thể rerank.
6. Sinh câu trả lời từ context và kiểm tra citation.
7. Lưu câu hỏi, câu trả lời, đoạn nguồn và phản hồi người dùng.

### Đầu ra bắt buộc

- Câu trả lời ngắn gọn, có citation có thể mở về đúng nguồn.
- Danh sách đoạn bằng chứng đã dùng.
- Trạng thái đủ/không đủ bằng chứng.
- Câu hỏi gợi ý tiếp theo dựa trên tài liệu.

## 11. Yêu cầu tài liệu nghiên cứu bắt buộc

Mỗi module phải có một thư mục `docs` riêng. Task không được coi là hoàn thành nếu chỉ có code mà thiếu tài liệu.

### Bộ tài liệu tối thiểu của mỗi module

1. **`README.md`**
   - Mục tiêu, phạm vi và phần không thuộc module.
   - Đầu vào, đầu ra và hướng dẫn chạy.
2. **`methodology.md`**
   - Khung phân tích, thuật ngữ, thuật toán và công thức.
   - Lý do chọn phương pháp và giới hạn áp dụng.
3. **`tools.md`**
   - Danh sách tool, mục đích, phiên bản và chủ sở hữu.
   - Input/output schema, đơn vị, lỗi có thể xảy ra và ví dụ gọi.
   - Liên kết từ mỗi công thức hoặc thuật toán sang tool thực thi tương ứng.
4. **`sources.md`**
   - Danh mục bài báo, nghiên cứu, sách, tiêu chuẩn hoặc tài liệu chính thức.
   - Tác giả/tổ chức, tiêu đề, URL, ngày xuất bản, ngày truy cập.
   - Tóm tắt nội dung được sử dụng và mức độ tin cậy.
5. **`assumptions-and-limitations.md`**
   - Giả định, dữ liệu tối thiểu, sai số và trường hợp không áp dụng.
6. **`glossary.md`**
   - Định nghĩa các thuật ngữ nghiệp vụ và cách tính thống nhất.
7. **`test-cases.md`**
   - Happy path, thiếu dữ liệu, dữ liệu mâu thuẫn và giá trị biên.
   - Kết quả mong đợi cho ít nhất một bộ dữ liệu mẫu.

### Tiêu chuẩn nguồn

- Ưu tiên nghiên cứu học thuật, cơ quan nhà nước, tổ chức quốc tế, báo cáo ngành uy tín và tài liệu kỹ thuật chính thức.
- Bài báo phổ thông chỉ dùng để bổ trợ, không phải bằng chứng duy nhất cho kết luận quan trọng.
- Không dùng nguồn không rõ tác giả hoặc không xác định được thời điểm xuất bản nếu có lựa chọn tốt hơn.
- Không sao chép dài nguyên văn; chỉ trích đoạn cần thiết và ghi nguồn.
- Dữ liệu có tính thời điểm phải lưu ngày truy cập.
- Nguồn phản biện hoặc có kết quả trái chiều phải được ghi nhận, không chỉ chọn nguồn ủng hộ kết luận.

## 12. Phân chia task để tránh xung đột

### Cấu trúc thư mục đề xuất

```text
src/
  shared/                  # Schema và tiện ích chung; chỉ người phụ trách tích hợp sửa
  modules/
    business_model/        # Thành viên A sở hữu
      tools/
      docs/
    cash_flow/             # Thành viên B sở hữu
      tools/
      docs/
    surrounding_area/      # Thành viên C sở hữu
      tools/
      docs/
    document_chatbot/      # Thành viên D sở hữu
      docs/
  aggregator/              # Người phụ trách tích hợp sở hữu
tests/
  contracts/
  fixtures/
```

### Ma trận trách nhiệm

| Task | Chủ sở hữu | Được sửa trực tiếp | Không được tự ý sửa |
|---|---|---|---|
| Shared contract + intake + aggregator | Người tích hợp | `src/shared`, `src/aggregator`, contract tests | Logic nội bộ của các module |
| Business Model Analysis | Thành viên A | `src/modules/business_model` | Module khác và shared schema |
| Cash Flow Analysis | Thành viên B | `src/modules/cash_flow` | Module khác và shared schema |
| Surrounding Area Analysis | Thành viên C | `src/modules/surrounding_area` | Module khác và shared schema |
| Document Chatbot | Thành viên D | `src/modules/document_chatbot` | Module đánh giá và shared schema |

Nếu nhóm chỉ có ba thành viên, người phụ trách tích hợp kiêm chatbot; ba module phân tích vẫn giữ chủ sở hữu tách biệt.

### Quy tắc làm việc song song

1. Chốt và đóng băng bản `v1` của `StartupFacts`, `Evidence`, `ModuleReport` trước khi chia nhánh.
2. Mỗi module expose cùng một interface:

   `analyze(startup_facts, documents, options) -> ModuleReport`

3. Mỗi thành viên chỉ sửa trong thư mục mình sở hữu; thay đổi contract tạo pull request riêng.
4. Dùng fixture chung thay vì module tự tạo định dạng startup khác nhau.
5. Không gọi trực tiếp code nội bộ của module khác.
6. Mọi tích hợp đi qua interface và schema chung.
7. Mỗi module có unit test riêng; người tích hợp sở hữu contract test và end-to-end test.
8. Tên biến môi trường, route API và migration phải được đăng ký trong tài liệu tích hợp trước khi thêm.
9. Tool đặc thù nằm trong `tools` của module sở hữu; chỉ tool dùng chung thực sự mới được đề xuất chuyển vào `src/shared`.
10. Không tạo một tool tổng hợp dùng chung cho cả ba module nếu nó khiến nhiều thành viên phải sửa cùng file.

## 13. API tối thiểu đề xuất

```text
POST   /startups
POST   /startups/{id}/documents
GET    /startups/{id}/documents
POST   /startups/{id}/analyses/{module}
GET    /startups/{id}/analyses
GET    /startups/{id}/analyses/{analysis_id}
POST   /startups/{id}/chat
GET    /startups/{id}/chat/history
```

Job phân tích nên chạy độc lập theo `module` và trả về trạng thái để frontend có thể hiển thị kết quả từng phần ngay khi hoàn thành.

## 14. Scoring và tổng hợp

- Mỗi module tự định nghĩa rubric trong tài liệu phương pháp nhưng trả điểm chuẩn hóa 0–100.
- Thiếu dữ liệu quan trọng không được mặc định thành điểm 0; dùng `score: null` hoặc giảm mức tin cậy theo quy tắc đã công bố.
- Module khu vực có thể trả `Không áp dụng`.
- Aggregator không tự cộng điểm nếu một module `Không áp dụng` hoặc `Chưa đủ dữ liệu`.
- Nếu cần điểm tổng demo, trọng số mặc định là:
  - Mô hình kinh doanh: 40%.
  - Dòng tiền: 40%.
  - Khu vực xung quanh: 20% khi áp dụng.
- Khi module khu vực không áp dụng, chuẩn hóa hai trọng số còn lại về tổng 100%.
- Báo cáo tổng phải hiển thị điểm, phiên bản và độ tin cậy của từng module; không che giấu sự khác biệt về phương pháp.

## 15. Tiêu chí nghiệm thu

### Chung

- Ba module có thể chạy độc lập và trả đúng `ModuleReport`.
- Lỗi một module không chặn kết quả của module khác.
- 100% nhận định quan trọng có evidence hoặc nhãn giả định.
- Mỗi phép tính hoặc thuật toán xác định đều được ánh xạ tới một tool có schema và phiên bản.
- Tool có unit test, kiểm tra lỗi đầu vào và không giao phép tính cho LLM.
- Báo cáo lưu tool call gồm tên, phiên bản, input, output và cảnh báo.
- Mỗi module có đủ bảy tài liệu nghiên cứu bắt buộc.
- Báo cáo lưu phiên bản module, prompt, nguồn và thời gian chạy.

### Business Model

- Phân tích được tối thiểu vấn đề, khách hàng, giải pháp, doanh thu, thị trường và cạnh tranh.
- Tách rõ dữ kiện startup, dữ liệu nghiên cứu và nhận định.
- Không tính điểm khi dữ liệu tối thiểu chưa đủ mà không cảnh báo.
- TAM/SAM/SOM, unit economics và điểm rubric phải được tạo bởi tool tương ứng.

### Cash Flow

- Các công thức khớp với fixture tài chính đã tính tay.
- Xử lý được kỳ dữ liệu không đều, giá trị thiếu và chia cho 0.
- Có ít nhất base case và một stress scenario.
- Tất cả chỉ số và kịch bản số phải xuất phát từ tool, không lấy số do LLM tự tính.

### Surrounding Area

- Không chạy nếu địa chỉ không đủ chính xác và trả lý do rõ ràng.
- Kết quả khoảng cách/bán kính được kiểm thử bằng tọa độ mẫu.
- Mọi dữ liệu địa điểm bên ngoài có nguồn và ngày truy cập.
- Geocoding, khoảng cách, density và location score phải có tool cùng test tọa độ mẫu.

### Chatbot

- Citation mở đúng tài liệu và đúng trang/đoạn.
- Câu hỏi không có trong tài liệu phải bị từ chối trả lời theo dữ kiện tưởng tượng.
- Không retrieval chéo giữa hai `startup_id`.
- Có test cho tài liệu mâu thuẫn và prompt injection nằm trong tài liệu.

## 16. Kịch bản demo

1. Tạo startup và tải lên pitch deck, kế hoạch kinh doanh cùng bảng dòng tiền mẫu.
2. Hiển thị dữ kiện đã trích xuất và các trường còn thiếu.
3. Chạy song song ba module phân tích.
4. Mở báo cáo mô hình kinh doanh và kiểm tra một nhận định cùng nguồn nghiên cứu.
5. Mở báo cáo dòng tiền, xem burn rate, runway và stress scenario.
6. Mở báo cáo khu vực, xem bản đồ/chỉ số quanh vị trí hoặc trạng thái không áp dụng.
7. Xem trang tổng hợp, trong đó mỗi module giữ điểm và mức tin cậy riêng.
8. Hỏi chatbot một câu có đáp án trong pitch deck và mở citation đúng trang.
9. Hỏi một câu không có trong hồ sơ để minh họa cơ chế từ chối suy diễn.

## 17. Kế hoạch triển khai

### Giai đoạn 0 — Chốt contract và fixture

- Chốt schema chung và interface module.
- Chọn một bộ hồ sơ startup mẫu dùng cho toàn nhóm.
- Tạo contract tests và dữ liệu kết quả mong đợi.
- Chia chủ sở hữu thư mục và nhánh làm việc.

### Giai đoạn 1 — Nghiên cứu và thiết kế module

- Mỗi thành viên hoàn thành `methodology.md`, `sources.md` và glossary trước.
- Chốt dữ liệu đầu vào tối thiểu, rubric, công thức và trường hợp không áp dụng.
- Review chéo phương pháp để phát hiện phần trùng lặp hoặc bỏ sót.

### Giai đoạn 2 — Phát triển song song

- Thành viên A xây dựng Business Model Analysis.
- Thành viên B xây dựng Cash Flow Analysis.
- Thành viên C xây dựng Surrounding Area Analysis.
- Thành viên D hoặc người tích hợp xây dựng Document Chatbot.
- Người tích hợp hoàn thiện intake, evidence store và aggregator.

### Giai đoạn 3 — Tích hợp

- Chạy contract tests trước khi merge từng module.
- Kết nối UI với job phân tích độc lập.
- Kiểm tra citation, trạng thái thiếu dữ liệu và lỗi một phần.
- Chạy end-to-end trên cùng bộ hồ sơ mẫu.

### Giai đoạn 4 — Hoàn thiện demo

- Đo thời gian xử lý và độ chính xác citation.
- Chuẩn bị happy path, thiếu dữ liệu và tài liệu mâu thuẫn.
- Đóng băng phiên bản prompt, thuật toán và bộ nguồn dùng cho demo.

## 18. Rủi ro và biện pháp giảm thiểu

| Rủi ro | Biện pháp |
|---|---|
| Các thành viên sửa cùng file/schema | Đóng băng contract v1, phân quyền thư mục và PR riêng cho contract |
| Ba module chồng lấn phạm vi | Ghi rõ phần sở hữu/không sở hữu và chỉ giao tiếp qua schema chung |
| Nghiên cứu thiếu căn cứ | Bắt buộc `sources.md`, ưu tiên nguồn sơ cấp và review chéo |
| AI tạo nhận định không có bằng chứng | Citation bắt buộc, nhãn giả định và trạng thái chưa đủ thông tin |
| LLM tính sai số liệu | Tất cả công thức chạy bằng code và có fixture kiểm thử |
| Nguồn web lỗi thời | Lưu ngày xuất bản, ngày truy cập và độ tin cậy |
| Dữ liệu địa điểm không phù hợp | Điều kiện chạy rõ ràng và hỗ trợ trạng thái `Không áp dụng` |
| Chatbot trả lời ngoài tài liệu | Retrieval theo startup, grounded prompt và kiểm tra citation |
| Rò rỉ tài liệu giữa startup | Authorization và metadata filter bắt buộc trước retrieval |
| Prompt injection trong tài liệu | Xem nội dung tài liệu là dữ liệu, không phải chỉ dẫn; thêm test tấn công |
| Báo cáo không thể tái lập | Lưu phiên bản prompt, module, nguồn, input hash và thời gian chạy |

## 19. Quyết định cần chốt trước khi lập trình

- Số thành viên và người chịu trách nhiệm tích hợp/chatbot.
- Stack backend, frontend, database và vector store.
- Định dạng tài liệu thực sự hỗ trợ trong demo.
- LLM và embedding model, giới hạn chi phí và thời gian phản hồi.
- Bộ hồ sơ startup mẫu và quyền sử dụng dữ liệu.
- Nguồn dữ liệu được phép dùng cho module khu vực.
- Rubric và dữ liệu tối thiểu của từng module.
- Cơ chế xác thực, phân quyền và thời hạn lưu tài liệu.
- Có cần điểm tổng hay chỉ hiển thị ba đánh giá độc lập.
