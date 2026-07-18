# Bộ dữ liệu kiểm thử AI tự trích xuất dòng tiền

DỮ LIỆU MÔ PHỎNG - KHÔNG CÓ GIÁ TRỊ KẾ TOÁN, THUẾ HOẶC PHÁP LÝ

Bộ này mở rộng từ cấu trúc `goc-ho-coffee`, nhưng cố ý thay đổi tên sheet, cách đặt bảng, dấu số tiền, thời điểm ghi nhận và mối quan hệ giữa Excel/PDF/CSV.

## Cách test

1. Chỉ upload thư mục `input` của một case cho AI.
2. Dùng prompt trong `ground-truth/test_prompt.md`.
3. So kết quả với `ground-truth/expected_cashflow.json` sau khi AI trả lời.
4. Kiểm tra AI có tự chọn đúng tool, đọc được nhiều sheet/PDF/CSV, loại chuyển nội bộ và tránh double-count hay không.

## Các case

- **Tiệm bánh Mây Sớm**: tiền vào 1.052.418.000 đ; tiền ra 268.305.000 đ; cuối kỳ 969.113.000 đ.
- **Nhà hàng Bếp Việt 36**: tiền vào 2.996.159.000 đ; tiền ra 1.665.819.000 đ; cuối kỳ 1.750.340.000 đ.
- **Cửa hàng tiện lợi Đêm 24**: tiền vào 2.051.231.000 đ; tiền ra 1.603.818.000 đ; cuối kỳ 757.413.000 đ.

## Nguyên tắc chấm

- Sai số số học kỳ vọng: 0 VND.
- Không tính doanh thu/hóa đơn phát sinh nhưng chưa thu/chưa trả vào cash flow.
- Không cộng trùng cùng giao dịch xuất hiện ở báo cáo bán hàng và sổ quỹ/sao kê.
- Loại cả hai vế chuyển nội bộ.
- Dòng tiền tài chính (vốn góp/vay) vẫn nằm trong tổng dòng tiền nhưng phải phân loại riêng.