# Tính năng

## Tính năng chi tiết

### 1. AI phân tích và đánh giá hồ sơ

#### 1.1. Tiếp nhận và số hóa hồ sơ

- Tạo hồ sơ startup bằng biểu mẫu hoặc tải lên tài liệu.
- Hỗ trợ các định dạng phổ biến: PDF, DOCX, PPTX, XLSX và ảnh scan.
- Trích xuất và chuẩn hóa các trường thông tin chính:
  - Thông tin doanh nghiệp, lĩnh vực, giai đoạn và địa bàn hoạt động.
  - Vấn đề startup giải quyết và giải pháp đề xuất.
  - Khách hàng mục tiêu, quy mô thị trường và đối thủ cạnh tranh.
  - Mô hình doanh thu, traction và kế hoạch tăng trưởng.
  - Đội ngũ sáng lập và năng lực thực thi.
  - Số vốn cần gọi, mục đích sử dụng vốn và nhu cầu hợp tác ngoài vốn.
- Hiển thị đoạn tài liệu nguồn tương ứng với từng dữ liệu đã trích xuất.
- Đánh dấu dữ liệu có độ tin cậy thấp, dữ liệu mâu thuẫn hoặc không tìm thấy.
- Cho phép người dùng sửa và xác nhận thông tin trước khi bắt đầu đánh giá.
- Ghi chú kỹ thuật: financial model dạng bảng tính cần pipeline đọc riêng (parse theo sheet/cell), không dùng chung luồng OCR của PDF.

#### 1.2. Đánh giá theo checklist — Profile Analyst Agent

##### Chấm điểm theo checklist của người dùng

- Đối chiếu hồ sơ với checklist mặc định hoặc checklist riêng của từng tổ chức.
- Chấm điểm theo trọng số và thang điểm do người dùng cấu hình, quy về thang 100.
- Kiểm tra các tiêu chí bắt buộc (`hard gate`) trước khi tính điểm tổng.
- Mỗi điểm số kèm giải thích, bằng chứng và trích dẫn về đúng đoạn tài liệu nguồn.
- Đánh dấu rõ mục `Chưa đủ thông tin` thay vì tự suy diễn khi hồ sơ không có bằng chứng.
- Sinh danh sách câu hỏi làm rõ cho từng mục còn thiếu hoặc mâu thuẫn.
- Cho phép chuyên viên điều chỉnh điểm, nhưng bắt buộc ghi lại lý do thay đổi.

##### Các tài liệu kế hoạch kinh doanh được đọc

- Nhóm cốt lõi:
  - Pitch deck.
  - Business plan hoặc one-pager.
  - Financial model (doanh thu, chi phí và dòng tiền dự phóng).
  - Báo cáo tài chính gần nhất (cân đối kế toán, kết quả kinh doanh, lưu chuyển tiền tệ).
  - Cap table và lịch sử gọi vốn.
- Nhóm pháp lý và vận hành:
  - Giấy đăng ký kinh doanh và điều lệ công ty.
  - Hợp đồng lớn với khách hàng, nhà cung cấp và nhà phân phối.
  - Hợp đồng thuê mặt bằng.
  - Giấy phép con theo ngành (an toàn thực phẩm, PCCC, giấy phép hoạt động).
  - Đăng ký sở hữu trí tuệ (nhãn hiệu, sáng chế, bản quyền).
  - Thỏa thuận đầu tư vòng trước (`SAFE`, `convertible note`, `term sheet`).
- Nhóm bằng chứng traction:
  - Số liệu xuất từ hệ thống bán hàng hoặc analytics.
  - Danh sách khách hàng, hợp đồng lặp lại và tỷ lệ giữ chân.
  - Khảo sát người dùng và thư xác nhận từ khách hàng (`LOI`).
  - Biên bản họp hội đồng quản trị.

#### 1.3. Phân tích tài chính và dòng tiền — Financial Analyst Agent

##### Các tài liệu tài chính được đọc

- Báo cáo tài chính và bảng dự phóng dòng tiền.
- Bảng lương và kế hoạch nhân sự.
- Sao kê ngân hàng và sổ quỹ.
- Bảng công nợ phải thu, phải trả.
- Kế hoạch sử dụng vốn sau gọi vốn.
- Cap table, khoản vay và các nghĩa vụ tài chính hiện tại.
- Hồ sơ thuế và các khoản phí pháp lý liên quan.

##### Các nhóm chi phí được phân tích

- Lương, thưởng, bảo hiểm, phúc lợi và chi phí tuyển dụng.
- Thuê văn phòng, cửa hàng, nhà xưởng hoặc kho bãi.
- Điện, nước, internet, vận chuyển và chi phí tiện ích.
- Nguyên vật liệu, hàng tồn kho và giá vốn hàng bán (`COGS`).
- Marketing, quảng cáo, sự kiện, hoa hồng và chi phí bán hàng.
- Phần mềm, cloud, máy chủ, API và bản quyền công nghệ.
- Máy móc, thiết bị, sửa chữa, bảo trì và khấu hao tài sản.
- Nghiên cứu, phát triển sản phẩm và thử nghiệm.
- Pháp lý, kế toán, kiểm toán, thuế và giấy phép.
- Lãi vay, phí thanh toán, chênh lệch tỷ giá và chi phí tài chính.
- Đào tạo, công tác, bảo hiểm rủi ro và chi phí quản lý chung.
- Dự phòng cho hoàn tiền, nợ xấu, hỏng hóc và biến động giá.

##### Các chỉ số AI tính toán và cảnh báo

- Doanh thu, lợi nhuận gộp và biên lợi nhuận.
- Tổng chi phí cố định và chi phí biến đổi.
- Burn rate và thời gian runway còn lại.
- Điểm hòa vốn và thời gian dự kiến đạt hòa vốn.
- Dòng tiền thuần theo từng tháng.
- Chi phí thu hút khách hàng (`CAC`) và giá trị vòng đời khách hàng (`LTV`).
- Tỷ lệ `LTV/CAC`, thời gian hoàn vốn CAC và doanh thu định kỳ nếu có.
- Unit economics theo một sản phẩm, đơn hàng hoặc khách hàng.
- Vòng quay tồn kho, thời gian thu công nợ và thời gian trả nhà cung cấp.
- Chênh lệch giữa kế hoạch và số liệu thực tế.
- Nhu cầu vốn tối thiểu và mức dự phòng dòng tiền.
- Kịch bản cơ sở, tích cực và tiêu cực khi doanh thu hoặc chi phí thay đổi.

Lưu ý: burn rate và runway là hai chỉ số ưu tiên cao nhất cho MVP, bắt buộc kèm trích dẫn về ô dữ liệu nguồn.

#### 1.4. Phân tích thị trường — Market Research Agent

##### Khảo sát khu vực bằng công cụ bản đồ

Xây dựng một công cụ sử dụng Google Maps Platform hoặc nguồn bản đồ phù hợp để khảo sát khu vực xung quanh địa điểm kinh doanh:

- Tìm kiếm các địa điểm trong bán kính do người dùng lựa chọn.
- Phân loại khu vực dân cư, văn phòng, trường học, bệnh viện, trung tâm thương mại và khu công nghiệp.
- Thống kê đối thủ trực tiếp và các mô hình kinh doanh tương tự xung quanh.
- Thu thập thông tin công khai về mức giá, khung giờ hoạt động, đánh giá và số lượng lượt nhận xét của đối thủ.
- Phân tích mật độ địa điểm, khoảng cách và mức độ cạnh tranh theo khu vực.
- Xác định các địa điểm bổ trợ như bãi đỗ xe, trạm giao thông công cộng, kho vận hoặc nhà cung cấp.
- So sánh nhiều địa điểm dự kiến mở cửa hàng hoặc văn phòng.
- Hiển thị kết quả trên bản đồ, bảng so sánh và bản tóm tắt cơ hội/rủi ro.

Lưu ý: dữ liệu bản đồ chỉ là tín hiệu tham khảo; hệ thống cần hiển thị nguồn, thời điểm truy cập và không thu thập dữ liệu trái với điều khoản của nhà cung cấp.

##### Phân tích quy mô và xu hướng thị trường

- Ước tính `TAM`, `SAM` và `SOM` kèm công thức, giả định và nguồn dữ liệu.
- Phân tích tốc độ tăng trưởng, xu hướng tiêu dùng, công nghệ và chính sách có liên quan.
- Phân khúc thị trường theo nhóm khách hàng, khu vực, hành vi, nhu cầu và khả năng chi trả.
- Xác định mùa vụ, chu kỳ mua hàng và các yếu tố ảnh hưởng đến nhu cầu.
- Đánh giá rào cản gia nhập, mức độ cạnh tranh và nguy cơ xuất hiện sản phẩm thay thế.

##### Phân tích khách hàng

- Xây dựng chân dung khách hàng mục tiêu (`persona`).
- Xác định nhu cầu, vấn đề, động lực mua và tiêu chí lựa chọn.
- Tổng hợp dữ liệu từ khảo sát, phỏng vấn và phản hồi khách hàng.
- Phân tích mức sẵn sàng chi trả và độ nhạy cảm với giá.
- Đánh giá kênh tiếp cận, hành trình khách hàng và tỷ lệ chuyển đổi dự kiến.

##### Phân tích đối thủ

- Lập danh sách đối thủ trực tiếp, gián tiếp và phương án thay thế hiện tại.
- So sánh sản phẩm, giá, nhóm khách hàng, kênh phân phối và lợi thế cạnh tranh.
- Tổng hợp nhận xét công khai để nhận diện điểm mạnh, điểm yếu và nhu cầu chưa được đáp ứng.
- Xây dựng ma trận cạnh tranh và bản đồ định vị.
- Cảnh báo khi lợi thế của startup chưa đủ khác biệt hoặc dễ bị sao chép.

##### Phân tích địa điểm và chi phí vận hành

- Ước tính mức lương theo vị trí công việc, ngành và khu vực.
- Tham chiếu giá thuê mặt bằng, văn phòng, kho hoặc nhà xưởng.
- Ước tính chi phí logistics, vận chuyển, điện nước và hạ tầng công nghệ.
- Đánh giá khả năng tiếp cận khách hàng, nguồn nhân lực và nhà cung cấp.
- So sánh tổng chi phí và tiềm năng doanh thu giữa các khu vực.

Nguyên tắc: mỗi con số thị trường phải kèm nguồn và thời điểm lấy dữ liệu; số liệu do startup tự khai mà không có nguồn được đánh dấu là giả định chưa kiểm chứng.

#### 1.5. Báo cáo thẩm định

- Tạo báo cáo tự động sau khi hoàn tất phân tích.
- Báo cáo bao gồm:
  - Tóm tắt startup và nhu cầu gọi vốn/hợp tác.
  - Điểm tổng và điểm theo từng nhóm tiêu chí.
  - Điểm mạnh, điểm yếu và thông tin còn thiếu.
  - Phân tích kế hoạch kinh doanh, tài chính và thị trường.
  - Các giả định chưa được kiểm chứng.
  - Danh sách rủi ro, mức độ ảnh hưởng và cách xác minh.
  - Kết luận sơ bộ và đề xuất bước tiếp theo.
- Mỗi nhận định quan trọng có trích dẫn từ tài liệu hoặc nguồn nghiên cứu.
- Cho phép chuyên viên chỉnh sửa, ghi chú và phê duyệt báo cáo.
- Lưu lịch sử phiên bản để so sánh trước và sau khi startup bổ sung dữ liệu.

### 2. Tự động ghép nối quỹ đầu tư và startup — Matching Agent

- Xây dựng hồ sơ cho quỹ đầu tư gồm:
  - Lĩnh vực và mô hình kinh doanh quan tâm.
  - Giai đoạn đầu tư ưu tiên.
  - Quy mô khoản đầu tư (`ticket size`).
  - Khu vực hoạt động.
  - Khẩu vị rủi ro và yêu cầu về traction.
  - Giá trị hỗ trợ ngoài vốn như công nghệ, cố vấn, phân phối hoặc thị trường.
  - Các điều kiện loại trừ.
- Lọc bỏ các cặp không đáp ứng điều kiện bắt buộc.
- Tính điểm phù hợp giữa startup và quỹ dựa trên nhiều tiêu chí, không chỉ dựa vào từ khóa.
- Xếp hạng các quỹ phù hợp và ưu tiên hiển thị top 3–5 kết quả.
- Giải thích rõ:
  - Vì sao hai bên phù hợp.
  - Điểm nào chưa phù hợp.
  - Dữ liệu nào cần xác minh trước khi kết nối.
- Cho phép chuyên viên thay đổi trọng số matching theo mục tiêu của từng chương trình.
- Có thể mở rộng để ghép nối startup với doanh nghiệp, khách hàng, nhà phân phối, cố vấn hoặc đối tác công nghệ.
- Ghi nhận kết quả sau mỗi lần kết nối để cải thiện gợi ý trong tương lai.

### 3. Tự động hóa email và quy trình giao dịch — Outreach & Deal Agent

#### 3.1. Hỗ trợ email kết nối

- Tạo email giới thiệu được cá nhân hóa theo startup và mối quan tâm của quỹ.
- Gợi ý tiêu đề, nội dung giới thiệu ngắn, luận điểm phù hợp và lời kêu gọi hành động.
- Đính kèm hoặc liên kết pitch deck, hồ sơ tóm tắt và báo cáo đã được phép chia sẻ.
- Tạo email nhắc lại nếu chưa nhận được phản hồi sau thời gian được cấu hình.
- Phân loại phản hồi như quan tâm, cần thêm thông tin, từ chối hoặc đề nghị gặp mặt.
- Chỉ gửi email sau khi người dùng xem và xác nhận nội dung.

#### 3.2. Hỗ trợ quy trình giao dịch

Trong phạm vi sản phẩm, "gửi giao dịch" nên được hiểu là gửi đề xuất và quản lý quy trình deal, không tự động chuyển tiền hoặc ký kết thay người dùng.

- Tạo và gửi đề xuất kết nối hoặc đề xuất đầu tư từ mẫu có sẵn.
- Tạo data room và checklist các tài liệu cần cung cấp cho quỹ.
- Theo dõi trạng thái deal:
  - Mới tiếp nhận.
  - Đang thẩm định.
  - Cần bổ sung thông tin.
  - Đã đề xuất kết nối.
  - Quỹ đang xem xét.
  - Đang đàm phán.
  - Đã thống nhất nguyên tắc.
  - Hoàn tất hoặc từ chối.
- Hỗ trợ chuẩn bị term sheet mẫu, biên bản cuộc họp và danh sách việc cần thực hiện.
- Đồng bộ lịch để đề xuất thời gian gặp giữa các bên.
- Gửi thông báo khi deal thay đổi trạng thái hoặc sắp đến hạn xử lý.
- Lưu lịch sử trao đổi, tài liệu, phiên bản đề xuất và người phê duyệt.
- Mọi hành động gửi đề xuất, chia sẻ tài liệu, đặt lịch, ký kết hoặc thanh toán đều phải được người có thẩm quyền xác nhận.

### 4. Trợ lý hỏi đáp — Investment Copilot

- Trả lời câu hỏi dựa trên hồ sơ, dữ liệu tài chính, nghiên cứu thị trường và báo cáo đã lưu.
- Gợi ý câu hỏi thẩm định tiếp theo dựa trên dữ liệu còn thiếu hoặc rủi ro được phát hiện.
- Giải thích cách tính điểm và lý do đưa ra từng nhận định.
- So sánh nhiều startup theo cùng một rubric.
- Tóm tắt hồ sơ theo nhu cầu của chuyên viên, lãnh đạo hoặc quỹ đầu tư.
- Cảnh báo khi không đủ dữ liệu để trả lời thay vì tạo thông tin không có căn cứ.

### 5. Quản trị và kiểm soát

- Phân quyền theo vai trò: quản trị viên, chuyên viên phân tích, người phê duyệt và người chỉ xem.
- Quản lý checklist, rubric, trọng số và lịch sử phiên bản.
- Lưu nhật ký thay đổi điểm số, báo cáo và trạng thái deal.
- Quản lý quyền truy cập theo tổ chức và theo từng hồ sơ.
- Bảo vệ tài liệu nhạy cảm bằng xác thực, mã hóa và giới hạn dữ liệu đưa vào log.
- Phân biệt rõ nội dung do AI đề xuất và nội dung đã được con người xác nhận.

## Luồng sử dụng chính

1. Chuyên viên tạo hồ sơ và tải tài liệu của startup lên hệ thống.
2. Profile Analyst Agent trích xuất dữ liệu, đối chiếu checklist và yêu cầu bổ sung thông tin còn thiếu.
3. Financial Analyst Agent phân tích doanh thu, chi phí, dòng tiền, runway và nhu cầu vốn.
4. Market Research Agent khảo sát thị trường, đối thủ và khu vực kinh doanh.
5. Hệ thống tổng hợp điểm số, rủi ro và tạo báo cáo thẩm định.
6. Chuyên viên kiểm tra nguồn, chỉnh sửa và phê duyệt báo cáo.
7. Matching Agent xếp hạng các quỹ hoặc đối tác phù hợp.
8. Outreach & Deal Agent soạn email và đề xuất bước kết nối tiếp theo.
9. Người dùng phê duyệt trước khi gửi, chia sẻ tài liệu hoặc thay đổi trạng thái giao dịch.

## Phạm vi MVP cho hackathon

### Tính năng bắt buộc

- Tải lên pitch deck hoặc business plan dạng PDF.
- Trích xuất và chuẩn hóa các trường thông tin chính.
- Đánh giá hồ sơ theo một checklist có thể cấu hình.
- Phân tích một bảng dự báo doanh thu, chi phí và dòng tiền mẫu.
- Khảo sát đối thủ và địa điểm xung quanh một vị trí mẫu.
- Tạo báo cáo thẩm định có điểm số, rủi ro và trích dẫn nguồn.
- Match startup với một tập dữ liệu quỹ đầu tư mẫu.
- Soạn email giới thiệu nhưng yêu cầu người dùng phê duyệt trước khi gửi.

### Tính năng mở rộng

- Nhiều agent chuyên biệt theo ngành.
- Nhiều template checklist và rubric theo khẩu vị đầu tư.
- Tra cứu dữ liệu thị trường, mức lương và chi phí theo thời gian thực.
- Tích hợp email, lịch, bản đồ và data room.
- Theo dõi toàn bộ vòng đời giao dịch.
- Học từ phản hồi của chuyên viên để cải thiện matching.

## Nguyên tắc vận hành

- AI đóng vai trò trợ lý phân tích, không thay con người đưa ra quyết định đầu tư.
- Mọi nhận định quan trọng phải có nguồn hoặc được đánh dấu là giả định.
- Điểm số và điều kiện loại được tính bằng quy tắc xác định, không giao hoàn toàn cho mô hình AI.
- Dữ liệu từ bản đồ và nguồn công khai phải hiển thị nguồn, thời gian truy cập và giới hạn sử dụng.
- Gửi email, chia sẻ tài liệu, đặt lịch, ký kết và thanh toán luôn cần người dùng xác nhận.
- Mọi thay đổi quan trọng đều phải được lưu lịch sử để kiểm tra và truy vết.
