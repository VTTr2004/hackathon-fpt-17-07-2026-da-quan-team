# Bộ dữ liệu mẫu - Góc Hồ Coffee

Toàn bộ nội dung trong bộ dữ liệu này là mô phỏng, phục vụ kiểm thử tính năng đánh giá startup và chatbot hỏi đáp tài liệu. Không sử dụng làm chứng từ kế toán, thuế, pháp lý hoặc giao dịch thực tế.

## Bối cảnh

- Tên cơ sở: Góc Hồ Coffee
- Địa chỉ mô phỏng: Số 12 phố Lê Thái Tổ, phường Hoàn Kiếm, thành phố Hà Nội
- Kỳ dữ liệu: 01/04/2026 - 30/06/2026
- Tiền tệ: VND
- Mô hình: quán cà phê 85 m², 42 chỗ ngồi, 8 nhân sự

## Sáu nhóm đầu vào

1. Hồ sơ kinh doanh trực tiếp: `01_ho_so_quan_ca_phe.json`
2. Hồ sơ pháp lý mô phỏng: 3 PDF trong thư mục `02_phap_ly`
3. Dữ liệu bán hàng: workbook 910 dòng và 6 hóa đơn PDF mẫu
4. Dữ liệu mua hàng, chi phí: workbook 77 dòng và 6 hóa đơn PDF mẫu
5. Sổ thu - chi: workbook 260 giao dịch, có bảng đối soát
6. Địa điểm và vận hành: JSON, workbook nhân sự/ca làm/điện nước, hợp đồng thuê và phiếu điện nước PDF

## Số liệu kiểm tra nhanh

- Tổng doanh thu thuần: 671.303.450 đ
- Tổng mua hàng và chi phí: 761.931.040 đ
- Tổng tiền vào: 821.303.450 đ (gồm 150.000.000 đ vốn góp chủ sở hữu)
- Tổng tiền ra: 761.931.040 đ
- Số dư đầu kỳ: 380.000.000 đ
- Số dư cuối kỳ: 439.372.410 đ

## Lưu ý

`central_data.json` là nguồn dữ liệu chuẩn dùng để sinh các workbook và PDF. Các mã số đăng ký, mã số thuế, nhà cung cấp, nhân vật, hóa đơn và hợp đồng đều là hư cấu.
