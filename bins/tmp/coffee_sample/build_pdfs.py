from __future__ import annotations

import json
import os
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = Path(os.environ.get("SAMPLE_OUTPUT_DIR", ROOT / "bins" / "outputs" / "sample_data_2026_07_19" / "goc-ho-coffee"))
OUT_DIR = Path(os.environ.get("SAMPLE_PDF_OUTPUT_DIR", DATA_DIR / "pdf"))
DISCLAIMER = "DỮ LIỆU MÔ PHỎNG - KHÔNG CÓ GIÁ TRỊ PHÁP LÝ"

GREEN = colors.HexColor("#174D3B")
GREEN_2 = colors.HexColor("#2E7259")
CREAM = colors.HexColor("#F5EFE3")
GOLD = colors.HexColor("#D7A84B")
INK = colors.HexColor("#24332E")
MUTED = colors.HexColor("#65736E")
RED = colors.HexColor("#B42318")
LIGHT = colors.HexColor("#F7F9F8")


pdfmetrics.registerFont(TTFont("Arial", r"C:\Windows\Fonts\arial.ttf"))
pdfmetrics.registerFont(TTFont("Arial-Bold", r"C:\Windows\Fonts\arialbd.ttf"))

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="VN", fontName="Arial", fontSize=9.2, leading=13, textColor=INK))
styles.add(ParagraphStyle(name="VN-Small", fontName="Arial", fontSize=7.8, leading=10.5, textColor=MUTED))
styles.add(ParagraphStyle(name="VN-Bold", fontName="Arial-Bold", fontSize=9.2, leading=13, textColor=INK))
styles.add(ParagraphStyle(name="DocTitle", fontName="Arial-Bold", fontSize=17, leading=21, alignment=TA_CENTER, textColor=GREEN))
styles.add(ParagraphStyle(name="DocSub", fontName="Arial", fontSize=9.5, leading=13, alignment=TA_CENTER, textColor=MUTED))
styles.add(ParagraphStyle(name="Section", fontName="Arial-Bold", fontSize=11, leading=14, textColor=GREEN, spaceBefore=4, spaceAfter=5))
styles.add(ParagraphStyle(name="Right", fontName="Arial", fontSize=8.5, leading=11, alignment=TA_RIGHT, textColor=INK))
styles.add(ParagraphStyle(name="Center", fontName="Arial", fontSize=8.5, leading=11, alignment=TA_CENTER, textColor=INK))
styles.add(ParagraphStyle(name="Disclaimer", fontName="Arial-Bold", fontSize=8.2, leading=10, alignment=TA_CENTER, textColor=RED))
styles.add(ParagraphStyle(name="HeaderWhite", fontName="Arial-Bold", fontSize=8, leading=10, textColor=colors.white))


def money(value: int | float) -> str:
    return f"{int(round(value)):,}".replace(",", ".") + " đ"


def vn_date(value: str) -> str:
    y, m, d = value.split("-")
    return f"{d}/{m}/{y}"


def p(text: object, style: str = "VN") -> Paragraph:
    safe = str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return Paragraph(safe, styles[style])


def page_frame(canvas, doc):
    canvas.saveState()
    width, height = A4
    canvas.setFillColor(GREEN)
    canvas.rect(0, height - 12 * mm, width, 12 * mm, stroke=0, fill=1)
    canvas.setFillColor(GOLD)
    canvas.rect(0, height - 13 * mm, width, 1 * mm, stroke=0, fill=1)
    canvas.setFont("Arial-Bold", 8)
    canvas.setFillColor(colors.white)
    canvas.drawString(16 * mm, height - 7.8 * mm, "GÓC HỒ COFFEE - HỒ SƠ DEMO")
    canvas.setFont("Arial", 7.5)
    canvas.drawRightString(width - 16 * mm, height - 7.8 * mm, f"Trang {doc.page}")
    canvas.setStrokeColor(colors.HexColor("#D8DEDB"))
    canvas.line(16 * mm, 16 * mm, width - 16 * mm, 16 * mm)
    canvas.setFont("Arial-Bold", 7.4)
    canvas.setFillColor(RED)
    canvas.drawCentredString(width / 2, 10.5 * mm, DISCLAIMER)
    canvas.restoreState()


def doc(path: Path, title: str, subtitle: str, story: list, pagesize=A4):
    path.parent.mkdir(parents=True, exist_ok=True)
    d = SimpleDocTemplate(
        str(path), pagesize=pagesize, rightMargin=16 * mm, leftMargin=16 * mm,
        topMargin=21 * mm, bottomMargin=22 * mm,
        title=title, author="Góc Hồ Coffee - dữ liệu mô phỏng",
    )
    head = [Spacer(1, 3 * mm), p(title, "DocTitle"), p(subtitle, "DocSub"), Spacer(1, 6 * mm)]
    d.build(head + story, onFirstPage=page_frame, onLaterPages=page_frame)


def kv_table(rows, widths=(55 * mm, 115 * mm)):
    data = [[p(k, "VN-Bold"), p(v)] for k, v in rows]
    t = Table(data, colWidths=list(widths), hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), CREAM),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#CBD5D0")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


def note_box(text):
    t = Table([[p(text, "Disclaimer")]], colWidths=[170 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FDECEC")),
        ("BOX", (0, 0), (-1, -1), 0.8, RED),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    return t


def signature_table(left: str, right: str):
    t = Table([
        [p(left, "Center"), p(right, "Center")],
        [Spacer(1, 25 * mm), Spacer(1, 25 * mm)],
        [p("(Ký, ghi rõ họ tên - mô phỏng)", "Center"), p("(Ký, ghi rõ họ tên - mô phỏng)", "Center")],
    ], colWidths=[85 * mm, 85 * mm])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    return t


def make_legal_docs(b):
    legal = OUT_DIR / "02_phap_ly"
    common_note = note_box("Tài liệu được tạo để kiểm thử hệ thống AI. Mọi mã số, nhân vật và nội dung pháp lý đều là hư cấu.")

    story = [common_note, Spacer(1, 6 * mm), p("THÔNG TIN ĐĂNG KÝ", "Section"), kv_table([
        ("Tên hộ kinh doanh", b["legal_name"]),
        ("Mã đăng ký", b["registration_code"]),
        ("Chủ hộ", b["owner_name"]),
        ("Địa chỉ trụ sở", b["address"]),
        ("Ngành nghề", "Dịch vụ phục vụ đồ uống; bán lẻ cà phê và sản phẩm đóng gói"),
        ("Vốn kinh doanh kê khai", money(500_000_000)),
        ("Số lao động dự kiến", str(b["employees"])),
        ("Ngày bắt đầu hoạt động", vn_date(b["opened_on"])),
    ]), Spacer(1, 8 * mm), p("GHI CHÚ MÔ PHỎNG", "Section"), p("Biểu mẫu này không sao chép mẫu của cơ quan nhà nước và không thể dùng trong bất kỳ thủ tục hành chính nào."), Spacer(1, 12 * mm), signature_table("CHỦ HỘ KINH DOANH", "BỘ PHẬN TIẾP NHẬN DEMO")]
    doc(legal / "giay_chung_nhan_dang_ky_ho_kinh_doanh.pdf", "GIẤY XÁC NHẬN THÔNG TIN HỘ KINH DOANH", "Biểu mẫu nội bộ phục vụ demo dữ liệu", story)

    story = [common_note, Spacer(1, 6 * mm), p("THÔNG TIN CƠ SỞ", "Section"), kv_table([
        ("Tên cơ sở", b["name"]),
        ("Địa chỉ", b["address"]),
        ("Người phụ trách", b["owner_name"]),
        ("Loại hình", "Cơ sở pha chế và phục vụ đồ uống"),
        ("Diện tích khu vực", f'{b["area_m2"]} m²'),
        ("Sức chứa", f'{b["seats"]} chỗ ngồi'),
        ("Mã hồ sơ demo", "ATTP-DEMO-2026-001"),
        ("Thời hạn demo", "01/04/2026 - 31/03/2027"),
    ]), Spacer(1, 7 * mm), p("NỘI DUNG TỰ KHAI", "Section"), p("Cơ sở có khu vực pha chế riêng, nguồn nước sử dụng cho chế biến, tủ bảo quản nguyên liệu, lịch vệ sinh thiết bị và sổ theo dõi nguồn gốc hàng hóa."), Spacer(1, 7 * mm), p("Tài liệu thật cần được cơ quan có thẩm quyền cấp theo quy định hiện hành. Bản demo này không chứng minh cơ sở đủ điều kiện an toàn thực phẩm.", "VN-Bold"), Spacer(1, 12 * mm), signature_table("ĐẠI DIỆN CƠ SỞ", "NGƯỜI KIỂM TRA DEMO")]
    doc(legal / "giay_chung_nhan_an_toan_thuc_pham.pdf", "PHIẾU THÔNG TIN AN TOÀN THỰC PHẨM", "Bản tự khai mô phỏng - không phải giấy chứng nhận", story)

    story = [common_note, Spacer(1, 6 * mm), p("THÔNG TIN NGƯỜI NỘP THUẾ", "Section"), kv_table([
        ("Tên người nộp thuế", b["legal_name"]),
        ("Mã số thuế demo", b["tax_code"]),
        ("Mã đăng ký kinh doanh", b["registration_code"]),
        ("Địa chỉ kinh doanh", b["address"]),
        ("Phương pháp ghi nhận", "Sổ thu - chi và doanh thu bán hàng theo ngày"),
        ("Kỳ dữ liệu mẫu", f'{vn_date(b["data_period"]["start"])} - {vn_date(b["data_period"]["end"])}'),
        ("Tiền tệ", b["currency"]),
        ("Trạng thái", "MÔ PHỎNG - KHÔNG TRA CỨU ĐƯỢC"),
    ]), Spacer(1, 8 * mm), p("MỤC ĐÍCH SỬ DỤNG", "Section"), p("Dữ liệu dùng để thử nghiệm trích xuất trường thông tin, đối chiếu doanh thu - chi phí và chatbot hỏi đáp tài liệu của startup."), Spacer(1, 15 * mm), signature_table("NGƯỜI LẬP DỮ LIỆU", "BỘ PHẬN THUẾ DEMO")]
    doc(legal / "thong_tin_dang_ky_thue.pdf", "PHIẾU THÔNG TIN ĐĂNG KÝ THUẾ", "Mã số và trạng thái hoàn toàn mô phỏng", story)


def item_table(items, purchase=False):
    if purchase:
        header = ["STT", "Hàng hóa", "ĐVT", "SL", "Đơn giá", "Tiền trước thuế"]
        rows = [[str(i), p(x["item"]), x["unit"], f'{x["quantity"]:g}', money(x["unit_price"]), money(x["subtotal"])] for i, x in enumerate(items, 1)]
    else:
        header = ["STT", "Sản phẩm", "Mã", "SL", "Đơn giá", "Thành tiền"]
        rows = [[str(i), p(x["name"]), x["sku"], str(x["quantity"]), money(x["unit_price"]), money(x["amount"])] for i, x in enumerate(items, 1)]
    data = [[p(x, "HeaderWhite") for x in header]] + rows
    t = Table(data, colWidths=[10 * mm, 48 * mm, 20 * mm, 13 * mm, 37 * mm, 42 * mm], repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), GREEN), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Arial-Bold"), ("FONTNAME", (0, 1), (-1, -1), "Arial"),
        ("FONTSIZE", (0, 0), (-1, -1), 8), ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#CBD5D0")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ALIGN", (2, 1), (3, -1), "CENTER"), ("ALIGN", (4, 1), (-1, -1), "RIGHT"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return t


def totals_table(rows):
    data = [[p(label, "VN-Bold" if idx == len(rows) - 1 else "VN"), p(money(value), "VN-Bold" if idx == len(rows) - 1 else "Right")] for idx, (label, value) in enumerate(rows)]
    t = Table(data, colWidths=[43 * mm, 42 * mm], hAlign="RIGHT")
    commands = [("ALIGN", (1, 0), (1, -1), "RIGHT"), ("LINEABOVE", (0, -1), (-1, -1), 1.0, GREEN), ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]
    t.setStyle(TableStyle(commands))
    return t


def make_sales_invoices(data):
    b = data["business"]
    folder = OUT_DIR / "03_hoa_don_ban_hang_mau"
    for inv in data["sales_invoices"]:
        story = [note_box(DISCLAIMER), Spacer(1, 5 * mm), kv_table([
            ("Đơn vị bán", b["name"]), ("Địa chỉ", b["address"]), ("Mã hóa đơn", inv["id"]),
            ("Ngày bán", vn_date(inv["date"])), ("Khách hàng", inv["customer"]), ("Thanh toán", inv["payment_method"]),
        ]), Spacer(1, 7 * mm), item_table(inv["items"]), Spacer(1, 5 * mm), totals_table([
            ("Cộng tiền hàng", inv["subtotal"]), ("Giảm giá", inv["discount"]), ("TỔNG THANH TOÁN", inv["total"]),
        ]), Spacer(1, 8 * mm), signature_table("NGƯỜI MUA HÀNG", "NGƯỜI BÁN HÀNG")]
        doc(folder / f'{inv["id"]}.pdf', "HÓA ĐƠN BÁN HÀNG MẪU", "Chứng từ giao dịch mô phỏng phục vụ kiểm thử", story)


def make_purchase_invoices(data):
    b = data["business"]
    folder = OUT_DIR / "04_hoa_don_mua_hang_mau"
    for row in data["purchases"][:6]:
        story = [note_box(DISCLAIMER), Spacer(1, 5 * mm), kv_table([
            ("Nhà cung cấp", row["supplier"]), ("Bên mua", b["legal_name"]), ("Địa chỉ giao", b["address"]),
            ("Mã hóa đơn", row["invoice_id"]), ("Ngày mua", vn_date(row["date"])), ("Trạng thái", row["payment_status"]),
        ]), Spacer(1, 7 * mm), item_table([row], purchase=True), Spacer(1, 5 * mm), totals_table([
            ("Tiền trước thuế", row["subtotal"]), (f'Thuế GTGT {int(row["vat_rate"] * 100)}%', row["vat_amount"]), ("TỔNG THANH TOÁN", row["total"]),
        ]), Spacer(1, 5 * mm), p(f'Phương thức thanh toán: {row["payment_method"]}', "Right"), Spacer(1, 8 * mm), signature_table("BÊN MUA", "NHÀ CUNG CẤP DEMO")]
        doc(folder / f'{row["invoice_id"]}.pdf', "HÓA ĐƠN MUA HÀNG MẪU", "Nhà cung cấp và chứng từ đều được mô phỏng", story)


def make_lease_and_utility(data):
    b = data["business"]
    folder = OUT_DIR / "06_dia_diem_va_van_hanh"
    story = [note_box(DISCLAIMER), Spacer(1, 5 * mm), p("1. THÔNG TIN CÁC BÊN", "Section"), kv_table([
        ("Bên cho thuê", "Trần Hải Bình (nhân vật mô phỏng)"), ("Mã định danh", "CCCD-DEMO-CHO-THUE-001"),
        ("Bên thuê", b["owner_name"]), ("Đại diện cơ sở", b["legal_name"]),
    ]), Spacer(1, 5 * mm), p("2. MẶT BẰNG THUÊ", "Section"), kv_table([
        ("Địa chỉ", b["address"]), ("Diện tích sử dụng", f'{b["area_m2"]} m²'),
        ("Mục đích", "Kinh doanh cà phê và đồ uống"), ("Hiện trạng", "Mặt bằng tầng 1, khu pha chế, khu khách ngồi và kho nhỏ"),
    ]), Spacer(1, 5 * mm), p("3. GIÁ THUÊ VÀ THỜI HẠN", "Section"), kv_table([
        ("Giá thuê", f'{money(b["monthly_rent"])} / tháng'), ("Tiền đặt cọc", money(b["deposit"])),
        ("Thời hạn", "01/04/2026 - 31/03/2027"), ("Thanh toán", "Chuyển khoản vào ngày 01 hàng tháng"),
    ]), PageBreak(), p("4. THỎA THUẬN VẬN HÀNH", "Section"), p("Bên thuê chịu chi phí điện, nước, internet, vệ sinh và bảo trì thiết bị phục vụ hoạt động. Bên thuê không được dùng địa điểm cho mục đích trái pháp luật hoặc chuyển nhượng hợp đồng khi chưa có thỏa thuận."), Spacer(1, 5 * mm), p("5. BÀN GIAO VÀ CHẤM DỨT", "Section"), p("Mặt bằng được bàn giao ngày 01/04/2026. Khi kết thúc thời hạn, hai bên đối soát công nợ, tình trạng tài sản và hoàn trả tiền cọc theo thỏa thuận mô phỏng."), Spacer(1, 8 * mm), p("6. XÁC NHẬN", "Section"), p("Hợp đồng này chỉ là dữ liệu thử nghiệm. Không tạo ra quyền, nghĩa vụ hay giao dịch thuê thực tế giữa bất kỳ cá nhân, tổ chức nào."), Spacer(1, 15 * mm), signature_table("BÊN CHO THUÊ", "BÊN THUÊ")]
    doc(folder / "hop_dong_thue_mat_bang_mo_phong.pdf", "HỢP ĐỒNG THUÊ MẶT BẰNG MÔ PHỎNG", "Số: HDT-DEMO-2026-001", story)

    u = data["utilities"][-1]
    base = u["electricity"] + u["water"] + u["internet"]
    story = [note_box(DISCLAIMER), Spacer(1, 5 * mm), kv_table([
        ("Đơn vị sử dụng", b["legal_name"]), ("Địa chỉ", b["address"]),
        ("Mã chứng từ", u["invoice_id"]), ("Kỳ sử dụng", u["month"]),
    ]), Spacer(1, 7 * mm), Table([
        [p("Khoản mục", "HeaderWhite"), p("Số tiền", "HeaderWhite")],
        [p("Điện"), p(money(u["electricity"]), "Right")], [p("Nước"), p(money(u["water"]), "Right")],
        [p("Internet"), p(money(u["internet"]), "Right")],
    ], colWidths=[120 * mm, 50 * mm], style=TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), GREEN), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5D0")), ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
        ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ])), Spacer(1, 5 * mm), totals_table([("TỔNG CHI PHÍ GHI NHẬN", base)]), Spacer(1, 7 * mm), p("Các số liệu trên là đầu vào vận hành thông thường, được dùng để đối chiếu với sổ thu - chi. Thuế suất tham chiếu trong dữ liệu: 10%.", "VN-Small"), Spacer(1, 12 * mm), signature_table("NGƯỜI LẬP", "CHỦ CƠ SỞ")]
    doc(folder / "hoa_don_dien_nuoc_mau.pdf", "PHIẾU TỔNG HỢP ĐIỆN - NƯỚC - INTERNET", "Kỳ tháng 06/2026 - dữ liệu mô phỏng", story)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    data = json.loads((DATA_DIR / "central_data.json").read_text(encoding="utf-8"))
    make_legal_docs(data["business"])
    make_sales_invoices(data)
    make_purchase_invoices(data)
    make_lease_and_utility(data)
    pdfs = sorted(str(x.relative_to(DATA_DIR)).replace("\\", "/") for x in OUT_DIR.rglob("*.pdf"))
    manifest = {"business": data["business"]["name"], "disclaimer": DISCLAIMER, "pdf_count": len(pdfs), "files": pdfs}
    (OUT_DIR / "pdf_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
