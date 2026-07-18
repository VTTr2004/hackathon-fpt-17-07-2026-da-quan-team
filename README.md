# Hải Đăng Khởi Nghiệp - Startup Lens

[![CI](https://github.com/VTTr2004/hackathon-fpt-17-07-2026-da-quan-team/actions/workflows/ci.yml/badge.svg)](https://github.com/VTTr2004/hackathon-fpt-17-07-2026-da-quan-team/actions/workflows/ci.yml)

Hải Đăng Khởi Nghiệp là hệ thống thẩm định startup theo hướng **evidence-first**: startup chuẩn bị hồ sơ và tài liệu, nhà đầu tư đọc snapshot đã nộp, chạy các module phân tích độc lập và hỏi đáp trực tiếp trên tài liệu có trích dẫn nguồn.

AI trong dự án đóng vai trò trợ lý phân tích. Các phép tính, đối soát, chấm điểm và đo lường không gian được thực hiện bằng tool deterministic trong backend; LLM chỉ hỗ trợ diễn giải, tổng hợp và gợi ý câu hỏi tiếp theo dựa trên bằng chứng. Con người vẫn là người kiểm tra, phê duyệt và ra quyết định cuối cùng.

## Link nhanh

| Hạng mục | URL |
|---|---|
| Frontend production | TODO: dán URL Vercel production |
| Backend production | TODO: dán URL Render production |
| Video demo | TODO: dán link YouTube/Google Drive video demo |
| Slide thuyết trình | TODO: dán link Google Slides/Canva/PDF |

> Khi nộp bài, cập nhật bốn dòng production/video/slide ở bảng trên để giám khảo có thể mở trực tiếp.

## Mục lục

- [Bài toán và khó khăn](#bài-toán-và-khó-khăn)
- [Đối tượng người dùng](#đối-tượng-người-dùng)
- [Thông tin cơ bản về dự án](#thông-tin-cơ-bản-về-dự-án)
- [Giá trị mang lại](#giá-trị-mang-lại)
- [Tác động tích cực](#tác-động-tích-cực)
- [Tài liệu kỹ thuật](#tài-liệu-kỹ-thuật)

## Bài toán và khó khăn

Một startup giai đoạn sớm thường không thiếu nỗ lực, nhưng lại thiếu một cách trình bày dữ liệu đủ rõ để nhà đầu tư có thể tin và kiểm chứng nhanh. Pitch deck có thể kể câu chuyện rất tốt, nhưng số liệu bán hàng nằm trong Excel, hợp đồng nằm trong PDF, thông tin địa điểm nằm trong ghi chú vận hành, còn các giả định thị trường lại nằm rải rác trong nhiều file khác nhau.

Ở phía nhà đầu tư, vấn đề ngược lại cũng rất thật: mỗi hồ sơ cần đọc nhiều tài liệu, đối chiếu nhiều con số, hỏi đi hỏi lại các câu cơ bản và vẫn phải cảnh giác với những nhận định không có nguồn. Nếu dùng AI một cách đơn giản, hệ thống có thể tóm tắt nhanh hơn nhưng cũng dễ tạo ra kết luận nghe thuyết phục mà không kiểm chứng được.

Những khó khăn cốt lõi mà dự án nhắm tới:

- **Dữ liệu phân mảnh**: thông tin nằm rải rác trong pitch deck, kế hoạch kinh doanh, báo cáo tài chính, hợp đồng, bảng tính và tài liệu phụ trợ.
- **Khó kiểm chứng**: người đọc phải tự tổng hợp, đối chiếu nguồn, kiểm tra số liệu và tìm rủi ro thủ công.
- **Rủi ro "AI đoán mò"**: AI đơn thuần dễ tự tính sai hoặc tóm tắt thiếu căn cứ.
- **Thiếu minh bạch và truy vết**: khó biết một kết luận dựa trên dữ liệu nào, còn thiếu gì.

Hải Đăng Khởi Nghiệp được xây dựng như một "ngọn đèn" trong quá trình đó: không quyết định thay con người, không hứa hẹn thay nhà đầu tư, mà soi rõ dữ liệu nào đã có, dữ liệu nào còn thiếu, kết luận nào có bằng chứng và phép tính nào đã được tool kiểm tra.

## Đối tượng người dùng

| Đối tượng | Họ là ai | Họ cần gì ở hệ thống |
|---|---|---|
| **Startup / nhà sáng lập** | Đội ngũ giai đoạn sớm đang chuẩn bị gọi vốn | Một lộ trình chuẩn bị hồ sơ rõ ràng, biết còn thiếu dữ liệu gì trước khi gặp nhà đầu tư |
| **Nhà đầu tư (angel/VC)** | Người sàng lọc và thẩm định nhiều hồ sơ | Một bàn thẩm định có cấu trúc, có nguồn, có thể truy vết và so sánh nhanh |
| **Chuyên viên thẩm định** | Người review theo rubric của quỹ/tổ chức | Contract dữ liệu và methodology thống nhất để giảm lệch giữa các người review |
| **Đội vận hành chương trình** | Accelerator/incubator quản lý nhiều startup | Trạng thái completeness, phân quyền và audit log để tổng hợp tình trạng hồ sơ |

## Thông tin cơ bản về dự án

Dự án là một **data room hai phía có phân quyền**, giữ đúng hai vai trò `startup` và `investor`:

- Startup tạo hồ sơ, nhập dữ kiện, tải tài liệu và nộp phiên bản chính thức (snapshot bất biến).
- Nhà đầu tư chỉ xem hồ sơ đã được cấp quyền và đọc từ snapshot đã nộp.
- Các module phân tích chạy độc lập, trả về điểm, rủi ro, dữ liệu thiếu, câu hỏi cần làm rõ và bằng chứng.
- Chatbot RAG trả lời câu hỏi trên tài liệu startup, có citation theo file, trang, sheet hoặc dòng.

Các nhóm tính năng chính (MVP):

| Nhóm | Tóm tắt |
|---|---|
| Xác thực và phân quyền | Role `startup`/`investor`, Bearer token, route guard ở frontend |
| Quản lý hồ sơ & phiên bản | Draft → completeness check → submitted snapshot → draft mới; lịch sử version và diff |
| Tài liệu | Upload `PDF/DOCX/PPTX/XLSX/TXT/MD/CSV/JSON`, trích xuất text, visibility `shared/private/restricted` |
| Trích xuất hồ sơ tự động | Sinh candidate field từ tài liệu kèm evidence, startup xác nhận trước khi ghi |
| Phân tích | Business Model, Cash Flow, Surrounding Area theo contract chung `ModuleReport` |
| Investor discovery & matching | Candidate công khai, fit score 9 chiều, shortlist và so sánh |
| Chat tài liệu | Hybrid RAG có citation, fallback khi LLM lỗi |
| Bản đồ | Geocode, xác nhận tọa độ, POI map, satellite context |

Stack: **Next.js 16 / React 19 / TypeScript** (frontend) và **FastAPI / SQLAlchemy async / PostgreSQL** (backend), triển khai trên Vercel + Render + Supabase. Chi tiết kiến trúc, module, API và cách chạy nằm trong [Tài liệu kỹ thuật](#tài-liệu-kỹ-thuật).

## Giá trị mang lại

| Đối tượng | Trước khi có hệ thống | Khi dùng Hải Đăng Khởi Nghiệp |
|---|---|---|
| Startup | Chuẩn bị hồ sơ theo cảm tính, dễ thiếu dữ liệu quan trọng | Biết rõ trường nào còn thiếu, tài liệu nào cần chia sẻ, phiên bản nào đã nộp |
| Nhà đầu tư | Đọc thủ công nhiều file, khó truy vết nguồn của từng kết luận | Có dashboard theo hồ sơ, phân tích theo module, citation và lịch sử version |
| Chuyên viên thẩm định | Dễ lệch rubric giữa các người review | Có contract dữ liệu, `ModuleReport`, tool calls và methodology thống nhất |
| Đội vận hành chương trình | Khó tổng hợp tình trạng nhiều hồ sơ | Có trạng thái completeness, phân quyền, audit log và dữ liệu có cấu trúc |
| Quy trình dùng AI | AI dễ tóm tắt thiếu căn cứ hoặc tự tính sai | Tool-first analysis, RAG có nguồn, fallback khi LLM lỗi, không biến thiếu dữ liệu thành điểm 0 |

Các hiệu quả được thiết kế để đo bằng những chỉ số thực tế sau:

- Thời gian từ lúc nhận hồ sơ đến lúc có bản review đầu tiên.
- Tỷ lệ nhận định có citation hoặc evidence đi kèm.
- Số lượng trường bắt buộc còn thiếu trước và sau khi startup bổ sung.
- Số lỗi đối soát dòng tiền được phát hiện trong workbook/tài liệu.
- Số câu hỏi làm rõ mà investor cần gửi lại cho startup.
- Mức độ nhất quán của báo cáo khi nhiều chuyên viên cùng xem một hồ sơ.

Điểm quan trọng là hệ thống không chỉ "làm nhanh hơn", mà làm cho quá trình thẩm định minh bạch hơn: người dùng thấy được dữ liệu đầu vào, công cụ đã chạy, cảnh báo thiếu dữ liệu và lý do hệ thống không kết luận khi chưa đủ bằng chứng.

## Tác động tích cực

- Giúp startup hiểu chuẩn dữ liệu cần chuẩn bị trước khi gặp nhà đầu tư.
- Giúp nhà đầu tư giảm thời gian xử lý các câu hỏi lặp lại và tập trung vào rủi ro thật.
- Tăng tính minh bạch vì mỗi nhận định quan trọng đều cần nguồn hoặc phải được đánh dấu là giả định.
- Khuyến khích cách dùng AI có trách nhiệm: AI hỗ trợ phân tích, nhưng con người vẫn là người kiểm tra, phê duyệt và ra quyết định cuối cùng.

## Tài liệu kỹ thuật

Phần triển khai chi tiết được tách thành các tài liệu riêng, liên kết chéo với nhau:

- [Kiến trúc & luồng hệ thống](docs/ARCHITECTURE.md) — sơ đồ kiến trúc, cấu trúc thư mục, luồng người dùng end-to-end.
- [Module phân tích & AI](docs/MODULES.md) — `ModuleReport`, Business Model, Cash Flow, Surrounding Area, investor matching, trích xuất hồ sơ, chatbot RAG.
- [API & luồng nghiệp vụ](docs/API.md) — bảng endpoint đầy đủ, investor workflow, completeness.
- [Cài đặt, biến môi trường & kiểm thử](docs/DEVELOPMENT.md) — chạy Docker/local, env vars, test, kịch bản demo.
- [Dữ liệu mẫu](docs/SAMPLE_DATA.md) — Góc Hồ Coffee, AI Cash Flow Variants, nhóm field dữ liệu.
- [Bảo mật & giới hạn](docs/SECURITY.md) — cơ chế bảo mật, giới hạn đã biết, báo cáo audit.
- [Triển khai (Supabase + Render + Vercel)](DEPLOYMENT.md) — hướng dẫn deploy production.

### Tài liệu tham khảo nội bộ

- [`function.md`](function.md): mô tả tính năng tổng thể và phạm vi MVP.
- [`BAO_CAO_CHUC_NANG_VA_LUONG_FE_BE.md`](BAO_CAO_CHUC_NANG_VA_LUONG_FE_BE.md): review luồng FE/BE.
- [`security_audit_report.md`](security_audit_report.md): audit bảo mật và logic nghiệp vụ.
- [`plans/trung-plans.md`](plans/trung-plans.md): plan sản phẩm, module và tiêu chí nghiệm thu.
- [`plans/tuan-rag-chat-plan.md`](plans/tuan-rag-chat-plan.md): kế hoạch RAG chatbot.
- [`plans/surrounding-area.md`](plans/surrounding-area.md): nghiên cứu và plan module khu vực.
- [`plans/surrounding-area-update.md`](plans/surrounding-area-update.md): roadmap nâng cấp module khu vực.
- [`docs/AI_LOG_AUTOMATION.md`](docs/AI_LOG_AUTOMATION.md): cơ chế thu thập AI log tự động cho minh chứng hackathon.
