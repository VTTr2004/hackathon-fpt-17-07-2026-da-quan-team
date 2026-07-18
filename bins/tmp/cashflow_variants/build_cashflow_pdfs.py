from __future__ import annotations

from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


ROOT = Path(r"K:\ProfileGitHub\hackathon\hackathon-fpt-17-07-2026-da-quan-team")
OUT = ROOT / "sample-data" / "ai-cashflow-variants"
DISCLAIMER = "DỮ LIỆU MÔ PHỎNG - KHÔNG CÓ GIÁ TRỊ KẾ TOÁN, THUẾ HOẶC PHÁP LÝ"

NAVY = colors.HexColor("#17324D")
TEAL = colors.HexColor("#1F6F78")
CREAM = colors.HexColor("#F6F1E8")
GOLD = colors.HexColor("#D99A2B")
INK = colors.HexColor("#1F2933")
MUTED = colors.HexColor("#66727D")
RED = colors.HexColor("#B42318")
LINE = colors.HexColor("#CCD6DD")

pdfmetrics.registerFont(TTFont("Arial", r"C:\Windows\Fonts\arial.ttf"))
pdfmetrics.registerFont(TTFont("Arial-Bold", r"C:\Windows\Fonts\arialbd.ttf"))

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="VN", fontName="Arial", fontSize=9.2, leading=13, textColor=INK, alignment=TA_LEFT))
styles.add(ParagraphStyle(name="Small", fontName="Arial", fontSize=7.8, leading=10.5, textColor=MUTED))
styles.add(ParagraphStyle(name="Bold", fontName="Arial-Bold", fontSize=9.2, leading=13, textColor=INK))
styles.add(ParagraphStyle(name="TitleVN", fontName="Arial-Bold", fontSize=17, leading=21, alignment=TA_CENTER, textColor=NAVY))
styles.add(ParagraphStyle(name="Sub", fontName="Arial", fontSize=9, leading=12, alignment=TA_CENTER, textColor=MUTED))
styles.add(ParagraphStyle(name="H1VN", fontName="Arial-Bold", fontSize=11, leading=15, textColor=TEAL, spaceBefore=4, spaceAfter=5))
styles.add(ParagraphStyle(name="CenterVN", fontName="Arial", fontSize=8.5, leading=11, alignment=TA_CENTER, textColor=INK))
styles.add(ParagraphStyle(name="RightVN", fontName="Arial", fontSize=8.5, leading=11, alignment=TA_RIGHT, textColor=INK))
styles.add(ParagraphStyle(name="Warn", fontName="Arial-Bold", fontSize=8, leading=10, alignment=TA_CENTER, textColor=RED))
styles.add(ParagraphStyle(name="HeaderWhiteVN", fontName="Arial-Bold", fontSize=8, leading=10, textColor=colors.white, alignment=TA_CENTER))


def p(text: object, style: str = "VN") -> Paragraph:
    safe = str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return Paragraph(safe, styles[style])


def vnd(value: int) -> str:
    return f"{value:,}".replace(",", ".") + " đ"


def frame(canvas, doc):
    canvas.saveState()
    width, height = A4
    canvas.setFillColor(NAVY)
    canvas.rect(0, height - 12 * mm, width, 12 * mm, stroke=0, fill=1)
    canvas.setFillColor(GOLD)
    canvas.rect(0, height - 13 * mm, width, 1 * mm, stroke=0, fill=1)
    canvas.setFont("Arial-Bold", 7.8)
    canvas.setFillColor(colors.white)
    canvas.drawString(16 * mm, height - 7.8 * mm, "AI CASHFLOW TEST FIXTURE")
    canvas.drawRightString(width - 16 * mm, height - 7.8 * mm, f"Trang {doc.page}")
    canvas.setStrokeColor(LINE)
    canvas.line(16 * mm, 16 * mm, width - 16 * mm, 16 * mm)
    canvas.setFont("Arial-Bold", 7.2)
    canvas.setFillColor(RED)
    canvas.drawCentredString(width / 2, 10.5 * mm, DISCLAIMER)
    canvas.restoreState()


def build(path: Path, title: str, subtitle: str, story: list):
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(path), pagesize=A4, leftMargin=16*mm, rightMargin=16*mm,
                            topMargin=21*mm, bottomMargin=22*mm, title=title,
                            author="Synthetic cashflow test data")
    head = [Spacer(1, 3*mm), p(title, "TitleVN"), p(subtitle, "Sub"), Spacer(1, 5*mm)]
    doc.build(head + story, onFirstPage=frame, onLaterPages=frame)


def warning_box(text=DISCLAIMER):
    t = Table([[p(text, "Warn")]], colWidths=[170*mm])
    t.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#FDECEC")),
                           ("BOX", (0,0), (-1,-1), 0.8, RED),
                           ("TOPPADDING", (0,0), (-1,-1), 6), ("BOTTOMPADDING", (0,0), (-1,-1), 6)]))
    return t


def kv(rows):
    data = [[p(k, "Bold"), p(v)] for k, v in rows]
    t = Table(data, colWidths=[53*mm, 117*mm])
    t.setStyle(TableStyle([("BACKGROUND", (0,0), (0,-1), CREAM), ("GRID", (0,0), (-1,-1), .35, LINE),
                           ("VALIGN", (0,0), (-1,-1), "TOP"), ("LEFTPADDING", (0,0), (-1,-1), 6),
                           ("RIGHTPADDING", (0,0), (-1,-1), 6), ("TOPPADDING", (0,0), (-1,-1), 6),
                           ("BOTTOMPADDING", (0,0), (-1,-1), 6)]))
    return t


def signature(left, right):
    return Table([[p(left, "CenterVN"), p(right, "CenterVN")], [Spacer(1, 24*mm), Spacer(1, 24*mm)],
                  [p("(Ký, ghi rõ họ tên - mô phỏng)", "CenterVN"), p("(Ký, ghi rõ họ tên - mô phỏng)", "CenterVN")]],
                 colWidths=[85*mm, 85*mm], style=TableStyle([("VALIGN", (0,0), (-1,-1), "TOP")]))


def payment_table(rows, headers=("Kỳ", "Hạn thanh toán", "Số tiền", "Trạng thái")):
    data = [[p(x, "HeaderWhiteVN") for x in headers]] + [[p(c, "RightVN" if i == 2 else "VN") for i, c in enumerate(row)] for row in rows]
    t = Table(data, colWidths=[28*mm, 43*mm, 44*mm, 55*mm], repeatRows=1)
    t.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,0), TEAL), ("GRID", (0,0), (-1,-1), .4, LINE),
                           ("VALIGN", (0,0), (-1,-1), "MIDDLE"), ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#F7F9FA")]),
                           ("TOPPADDING", (0,0), (-1,-1), 6), ("BOTTOMPADDING", (0,0), (-1,-1), 6)]))
    return t


def bakery_contract():
    path = OUT / "01-tiem-banh-may-som" / "input" / "04_hop_dong_thue_tiem_banh.pdf"
    story = [warning_box(), Spacer(1, 5*mm), p("TÓM TẮT THƯƠNG MẠI", "H1VN"), kv([
        ("Bên thuê", "Hộ kinh doanh Tiệm bánh Mây Sớm"),
        ("Mặt bằng", "Số 18 phố Hàng Bông, Hoàn Kiếm, Hà Nội - 48 m²"),
        ("Thời hạn", "01/04/2026 - 31/03/2027"),
        ("Giá thuê", f"{vnd(32_000_000)} / tháng, thanh toán ngày 02 hàng tháng"),
        ("Đặt cọc", f"{vnd(64_000_000)}, đã thanh toán trước kỳ dữ liệu ngày 20/03/2026"),
        ("Điện nước", "Bên thuê tự thanh toán theo hóa đơn thực tế"),
    ]), Spacer(1, 5*mm), p("LỊCH THANH TOÁN QUÝ II/2026", "H1VN"), payment_table([
        ("04/2026", "02/04/2026", vnd(32_000_000), "Đã trả - BN-THUE-04"),
        ("05/2026", "02/05/2026", vnd(32_000_000), "Đã trả - BN-THUE-05"),
        ("06/2026", "02/06/2026", vnd(32_000_000), "Đã trả - BN-THUE-06"),
    ]), Spacer(1, 6*mm), p("ĐIỀU KHOẢN GHI NHẬN", "H1VN"),
        p("Tiền đặt cọc không phát sinh trong kỳ 01/04/2026 - 30/06/2026. Tiền thuê được ghi nhận là dòng tiền ra tại ngày thực trả từng tháng. Hợp đồng này chỉ là dữ liệu kiểm thử."),
        Spacer(1, 12*mm), signature("BÊN CHO THUÊ", "BÊN THUÊ")]
    build(path, "HỢP ĐỒNG THUÊ CỬA HÀNG", "Số: MS-HDT-2026-01 | Mẫu bố cục bảng tóm tắt", story)


def bakery_invoice():
    path = OUT / "01-tiem-banh-may-som" / "input" / "05_hoa_don_bot_bo_thang_06.pdf"
    story = [warning_box(), Spacer(1, 5*mm), kv([
        ("Số hóa đơn", "BN-013"), ("Ngày hóa đơn", "18/06/2026"), ("Nhà cung cấp", "Bột, bơ, sữa An Tâm"),
        ("Bên mua", "Tiệm bánh Mây Sớm"), ("Tổng thanh toán", vnd(8_971_000)),
        ("Hạn thanh toán", "10/07/2026"), ("Trạng thái tại 30/06", "CHƯA THANH TOÁN"),
    ]), Spacer(1, 6*mm), p("Hóa đơn là chi phí/công nợ tháng 06 nhưng chưa tạo dòng tiền ra trong kỳ kiểm thử.", "Bold")]
    build(path, "HÓA ĐƠN NGUYÊN LIỆU MẪU", "Chứng từ công nợ chưa thanh toán", story)


def restaurant_contract():
    path = OUT / "02-nha-hang-bep-viet-36" / "input" / "03_hop_dong_mat_bang_nha_hang.pdf"
    story = [warning_box(), Spacer(1, 5*mm), p("ĐIỀU 1. CÁC BÊN VÀ MẶT BẰNG", "H1VN"),
        p("Bên cho thuê là Công ty Mặt Bằng 36 (mô phỏng). Bên thuê là Nhà hàng Bếp Việt 36. Diện tích sử dụng 220 m² tại quận Ba Đình, Hà Nội, phục vụ ăn uống tại bàn và giao hàng."),
        Spacer(1, 4*mm), p("ĐIỀU 2. GIÁ THUÊ VÀ CÁCH TRẢ", "H1VN"),
        p("Giá thuê cố định là 60.000.000 đồng/tháng. Tiền thuê được trả trước theo quý vào ngày đầu tiên của quý. Khoản 180.000.000 đồng cho quý II/2026 được thanh toán ngày 01/04/2026."),
        p("Ngoài tiền thuê, bên thuê trả phí dịch vụ 12.000.000 đồng/tháng vào ngày 03 từng tháng. Phí dịch vụ không nằm trong số tiền thuê trả trước."),
        Spacer(1, 4*mm), p("ĐIỀU 3. TIỀN ĐẶT CỌC", "H1VN"),
        p("Tiền đặt cọc 120.000.000 đồng đã được thanh toán ngày 15/03/2026, trước kỳ dữ liệu. Khoản này không được cộng vào dòng tiền quý II/2026."),
        PageBreak(), p("PHỤ LỤC A - LỊCH THANH TOÁN", "H1VN"), payment_table([
            ("Thuê Q2", "01/04/2026", vnd(180_000_000), "Đã trả - HDT-NH-01"),
            ("Dịch vụ 04", "03/04/2026", vnd(12_000_000), "Đã trả"),
            ("Dịch vụ 05", "03/05/2026", vnd(12_000_000), "Đã trả"),
            ("Dịch vụ 06", "03/06/2026", vnd(12_000_000), "Đã trả"),
            ("Thuê Q3", "01/07/2026", vnd(180_000_000), "Ngoài kỳ"),
        ]), Spacer(1, 6*mm), p("PHỤ LỤC B - NGUYÊN TẮC ĐỐI SOÁT", "H1VN"),
        p("Khi phân tích dòng tiền theo ngày trả, toàn bộ 180.000.000 đồng tiền thuê quý II phát sinh vào tháng 04; không phân bổ 60.000.000 đồng sang từng tháng trong báo cáo cash flow. Việc phân bổ theo tháng chỉ phù hợp cho chi phí kế toán."),
        Spacer(1, 13*mm), signature("ĐẠI DIỆN BÊN CHO THUÊ", "ĐẠI DIỆN NHÀ HÀNG")]
    build(path, "HỢP ĐỒNG THUÊ MẶT BẰNG NHÀ HÀNG", "Số: BV36-HDT-2026 | Mẫu hợp đồng văn xuôi + phụ lục", story)


def restaurant_receivable():
    path = OUT / "02-nha-hang-bep-viet-36" / "input" / "04_hoa_don_tiec_chua_thu.pdf"
    story = [warning_box(), Spacer(1, 5*mm), kv([
        ("Mã hóa đơn", "AR-0629"), ("Ngày phục vụ", "29/06/2026"), ("Khách hàng", "Công ty Sự Kiện Ánh Dương (mô phỏng)"),
        ("Nội dung", "Tiệc doanh nghiệp 60 khách"), ("Tổng phải thu", vnd(48_000_000)),
        ("Hạn thanh toán", "15/07/2026"), ("Trạng thái tại 30/06", "CHƯA THU"),
    ]), Spacer(1, 6*mm), p("Khoản này là doanh thu/công nợ nhưng chưa phải dòng tiền vào trong kỳ.", "Bold")]
    build(path, "HÓA ĐƠN DỊCH VỤ TIỆC", "Mẫu khoản phải thu chưa thu tiền", story)


def convenience_contract():
    path = OUT / "03-cua-hang-tien-loi-dem-24" / "input" / "04_thoa_thuan_nhuong_quyen.pdf"
    story = [warning_box(), Spacer(1, 5*mm), p("THẺ ĐIỀU KHOẢN TÀI CHÍNH", "H1VN"), kv([
        ("Đơn vị nhận quyền", "Cửa hàng tiện lợi Đêm 24"),
        ("Kỳ hiệu lực", "01/04/2026 - 31/03/2027"),
        ("Phí nhượng quyền", "4% doanh thu thuần của từng tháng"),
        ("Cơ sở tính", "Gross sales - khuyến mại cửa hàng chịu - hàng trả"),
        ("Thời điểm trả", "Ngày 10 của tháng kế tiếp"),
        ("Phí tháng 06", "Phải trả ngày 10/07/2026 - ngoài kỳ cash flow Q2"),
    ]), Spacer(1, 6*mm), p("MINH HỌA THỜI ĐIỂM", "H1VN"), payment_table([
        ("Phí 04", "10/05/2026", "4% net sales 04", "Đã thanh toán"),
        ("Phí 05", "10/06/2026", "4% net sales 05", "Đã thanh toán"),
        ("Phí 06", "10/07/2026", "4% net sales 06", "Chưa thanh toán"),
    ]), Spacer(1, 6*mm), p("ĐIỀU KHOẢN TRÁNH NHẦM LẪN", "H1VN"),
        p("Phí được tính theo doanh thu tháng nhưng cash outflow chỉ xuất hiện tại ngày thanh toán. Khi phân tích đến 30/06/2026, không ghi dòng tiền ra cho phí tháng 06."),
        Spacer(1, 13*mm), signature("BÊN NHƯỢNG QUYỀN", "BÊN NHẬN QUYỀN")]
    build(path, "THỎA THUẬN NHƯỢNG QUYỀN MÔ PHỎNG", "Số: D24-FR-2026 | Mẫu term sheet một trang", story)


def convenience_notice():
    path = OUT / "03-cua-hang-tien-loi-dem-24" / "input" / "05_thong_bao_phi_vi_dien_tu.pdf"
    story = [warning_box(), Spacer(1, 5*mm), p("CẤU TRÚC ĐỐI SOÁT", "H1VN"), kv([
        ("Nhà cung cấp", "Ví Nhanh Demo"), ("Merchant", "Cửa hàng tiện lợi Đêm 24"),
        ("Phí xử lý", "2,5% doanh số qua ví"), ("Số tiền chuyển", "Doanh số ví gross trừ phí xử lý"),
        ("Nguồn kiểm tra", "Cột Credit của sao kê ALL_ACCOUNTS"),
    ]), Spacer(1, 6*mm), p("Không cộng doanh số ví gross trong báo cáo ca với số tiền net trong sao kê; đây là hai góc nhìn của cùng giao dịch.", "Bold")]
    build(path, "THÔNG BÁO PHÍ VÍ ĐIỆN TỬ", "Tài liệu giải thích gross settlement và net cash receipt", story)


def main():
    bakery_contract(); bakery_invoice(); restaurant_contract(); restaurant_receivable(); convenience_contract(); convenience_notice()
    print("Generated 6 PDF test documents")


if __name__ == "__main__":
    main()
