import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..", "..");
const OUT = path.join(ROOT, "sample-data", "ai-cashflow-variants");
const PREVIEWS = path.join(ROOT, "bins", "tmp", "cashflow_variants", "previews");
const DISCLAIMER = "DỮ LIỆU MÔ PHỎNG - KHÔNG CÓ GIÁ TRỊ KẾ TOÁN, THUẾ HOẶC PHÁP LÝ";

const C = {
  navy: "#17324D", teal: "#1F6F78", cream: "#F6F1E8", pale: "#E9F3F4",
  gold: "#D99A2B", white: "#FFFFFF", ink: "#1F2933", gray: "#66727D",
  line: "#CCD6DD", input: "#0000FF", formula: "#000000", green: "#2F6B4F",
  red: "#B42318", softRed: "#FDECEC", softGreen: "#EAF4EC",
};

function mulberry32(seed) {
  return function () {
    let t = (seed += 0x6d2b79f5);
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const rnd = mulberry32(17072026);
const date = (s) => new Date(`${s}T00:00:00Z`);
const iso = (d) => d.toISOString().slice(0, 10);
const money = (n) => Math.round(n / 1000) * 1000;
const sum = (rows, fn) => rows.reduce((a, x) => a + fn(x), 0);

function days(start, end) {
  const out = [];
  for (let d = date(start); d <= date(end); d.setUTCDate(d.getUTCDate() + 1)) out.push(new Date(d));
  return out;
}

async function ensureDirs() {
  await fs.mkdir(OUT, { recursive: true });
  await fs.mkdir(PREVIEWS, { recursive: true });
}

function title(sheet, titleText, subtitle, lastCol) {
  sheet.showGridLines = false;
  sheet.getRange(`A1:${lastCol}1`).merge();
  sheet.getRange("A1").values = [[titleText]];
  sheet.getRange(`A1:${lastCol}1`).format = {
    fill: C.navy, font: { bold: true, color: C.white, size: 18 },
    rowHeight: 32, verticalAlignment: "center",
  };
  sheet.getRange(`A2:${lastCol}2`).merge();
  sheet.getRange("A2").values = [[subtitle]];
  sheet.getRange(`A2:${lastCol}2`).format = {
    fill: C.cream, font: { italic: true, color: C.gray, size: 9 }, rowHeight: 22,
  };
}

function header(range) {
  range.format = {
    fill: C.teal, font: { bold: true, color: C.white },
    verticalAlignment: "center", wrapText: true,
    borders: { preset: "inside", style: "thin", color: C.line },
  };
  range.format.rowHeight = 30;
}

function body(range) {
  range.format = {
    font: { color: C.ink, size: 9 }, verticalAlignment: "center",
    borders: { insideHorizontal: { style: "thin", color: "#E6ECEF" } },
  };
}

function setWidths(sheet, widths) {
  widths.forEach(([col, width]) => { sheet.getRange(`${col}:${col}`).format.columnWidth = width; });
}

async function exportBook(workbook, filePath, previewSpecs = []) {
  const specs = workbook.worksheets.items.map(sheet => ({ sheet: sheet.name }));
  for (const spec of specs) {
    const blob = await workbook.render({ sheetName: spec.sheet, autoCrop: "all", scale: 1.2, format: "png" });
    const safeSheet = spec.sheet.replace(/[\\/:*?"<>|]/g, "-");
    const safe = `${path.basename(filePath, ".xlsx")}_${safeSheet}.png`;
    await fs.writeFile(path.join(PREVIEWS, safe), new Uint8Array(await blob.arrayBuffer()));
  }
  const xlsx = await SpreadsheetFile.exportXlsx(workbook);
  await xlsx.save(filePath);
  await fs.rm(`${filePath}.inspect.ndjson`, { force: true });
}

function addReadmeSheet(wb, dataset, notes) {
  const s = wb.worksheets.add("Đọc trước");
  title(s, dataset, DISCLAIMER, "F");
  s.getRange("A4:B4").values = [["Mục", "Nội dung"]]; header(s.getRange("A4:B4"));
  const rows = [
    ["Kỳ dữ liệu", "01/04/2026 - 30/06/2026"],
    ["Tiền tệ", "VND"],
    ["Quy tắc", "Không cộng trùng doanh thu với tiền thu trong sổ quỹ/sao kê."],
    ["Lưu ý", notes],
    ["Cảnh báo", DISCLAIMER],
  ];
  s.getRange("A5:B9").values = rows; body(s.getRange("A5:B9"));
  s.getRange("B5:B9").format.wrapText = true;
  setWidths(s, [["A", 22], ["B", 90]]);
}

function bakeryData() {
  const sales = [];
  let i = 0;
  for (const d of days("2026-04-01", "2026-06-30")) {
    const weekend = [0, 6].includes(d.getUTCDay()) ? 1.28 : 1;
    const trend = 1 + i * 0.0015;
    const cash = money(3_000_000 * weekend * trend * (0.88 + rnd() * 0.25));
    const qr = money(4_400_000 * weekend * trend * (0.88 + rnd() * 0.25));
    const appGross = money(2_300_000 * weekend * trend * (0.86 + rnd() * 0.30));
    const promo = rnd() < 0.30 ? money((cash + qr + appGross) * 0.025) : 0;
    const refund = rnd() < 0.08 ? money(120_000 + rnd() * 280_000) : 0;
    const appReceived = money(appGross * 0.82);
    sales.push({ date: new Date(d), cash, qr, appGross, promo, refund, appReceived });
    i++;
  }
  const invoices = [];
  const cats = [
    ["Bột, bơ, sữa", 8_500_000], ["Bao bì", 2_300_000], ["Nhân công", 38_000_000],
    ["Điện nước", 6_500_000], ["Marketing", 4_000_000], ["Thuê mặt bằng", 32_000_000],
  ];
  let idx = 1;
  for (const month of [4, 5, 6]) {
    for (const [cat, base] of cats) {
      const invDate = date(`2026-${String(month).padStart(2, "0")}-${cat === "Thuê mặt bằng" ? "02" : String(2 + (idx * 3) % 23).padStart(2, "0")}`);
      const randomizedTotal = money(base * (0.92 + rnd() * 0.18));
      const total = cat === "Thuê mặt bằng" ? base : randomizedTotal;
      const unpaid = (month === 6 && ["Bột, bơ, sữa", "Bao bì"].includes(cat));
      const paid = unpaid ? 0 : total;
      invoices.push({ id: `BN-${String(idx).padStart(3, "0")}`, invDate, supplier: cat === "Thuê mặt bằng" ? "Chủ mặt bằng Mây Sớm" : `${cat} An Tâm`, cat, total, paidDate: unpaid ? null : new Date(invDate), paid, status: unpaid ? "Chưa thanh toán" : "Đã thanh toán" });
      idx++;
    }
  }
  const opening = 185_000_000;
  const ledger = [];
  let n = 1;
  for (const month of [4, 5, 6]) {
    const rows = sales.filter(x => x.date.getUTCMonth() + 1 === month);
    ledger.push({ id: `BQ-${n++}`, dt: date(`2026-${String(month).padStart(2, "0")}-28`), account: "Tiền và ngân hàng", type: "Thu bán hàng", category: "Khách hàng", amount: sum(rows, x => x.cash + x.qr + x.appReceived - x.promo - x.refund), countCashflow: true, ref: `BH-T${month}` });
    for (const inv of invoices.filter(x => x.paidDate && x.paidDate.getUTCMonth() + 1 === month)) {
      ledger.push({ id: `BQ-${n++}`, dt: inv.paidDate, account: "Tiền và ngân hàng", type: "Chi hoạt động", category: inv.cat, amount: -inv.paid, countCashflow: true, ref: inv.id });
    }
    ledger.push({ id: `BQ-${n++}`, dt: date(`2026-${String(month).padStart(2, "0")}-15`), account: "Tiền mặt", type: "Chuyển nội bộ - ra", category: "Điều chuyển", amount: -15_000_000, countCashflow: false, ref: `NB-${month}` });
    ledger.push({ id: `BQ-${n++}`, dt: date(`2026-${String(month).padStart(2, "0")}-15`), account: "Ngân hàng", type: "Chuyển nội bộ - vào", category: "Điều chuyển", amount: 15_000_000, countCashflow: false, ref: `NB-${month}` });
  }
  ledger.unshift({ id: `BQ-${n++}`, dt: date("2026-04-01"), account: "Ngân hàng", type: "Vốn góp chủ", category: "Tài chính", amount: 80_000_000, countCashflow: true, ref: "VG-01" });
  return { sales, invoices, ledger, opening };
}

async function buildBakery() {
  const base = path.join(OUT, "01-tiem-banh-may-som");
  const input = path.join(base, "input"); await fs.mkdir(input, { recursive: true });
  const d = bakeryData();

  const salesWb = Workbook.create(); addReadmeSheet(salesWb, "TIỆM BÁNH MÂY SỚM - BÁN HÀNG", "Ba sheet tháng có cấu trúc rộng. Tiền app thực nhận đã trừ phí nền tảng; doanh thu thuần không đồng nhất với dòng tiền vào.");
  for (const month of [4, 5, 6]) {
    const s = salesWb.worksheets.add(`T${String(month).padStart(2, "0")}`);
    title(s, `BÁO CÁO BÁN HÀNG THÁNG ${String(month).padStart(2, "0")}/2026`, DISCLAIMER, "I");
    s.getRange("A4:I4").values = [["Ngày", "Cửa hàng", "Tiền mặt", "QR", "App - giá niêm yết", "KM cửa hàng chịu", "Hoàn tiền", "App thực nhận", "Doanh thu thuần"]]; header(s.getRange("A4:I4"));
    const rows = d.sales.filter(x => x.date.getUTCMonth() + 1 === month);
    s.getRange(`A5:H${4 + rows.length}`).values = rows.map(x => [x.date, "Mây Sớm", x.cash, x.qr, x.appGross, x.promo, x.refund, x.appReceived]);
    s.getRange("I5").formulas = [["=C5+D5+E5-F5-G5"]]; s.getRange(`I5:I${4 + rows.length}`).fillDown();
    body(s.getRange(`A5:I${4 + rows.length}`)); s.getRange(`A5:A${4 + rows.length}`).format.numberFormat = "yyyy-mm-dd";
    s.getRange(`C5:I${4 + rows.length}`).format.numberFormat = "#,##0;[Red](#,##0);-";
    s.getRange(`H5:H${4 + rows.length}`).format.font = { color: C.input };
    s.freezePanes.freezeRows(4); setWidths(s, [["A", 14], ["B", 16], ["C", 16], ["D", 16], ["E", 20], ["F", 20], ["G", 15], ["H", 18], ["I", 18]]);
  }
  await exportBook(salesWb, path.join(input, "01_ban_hang_theo_ngay.xlsx"), [{ sheet: "T04", range: "A1:I15" }]);

  const expWb = Workbook.create(); addReadmeSheet(expWb, "TIỆM BÁNH MÂY SỚM - CÔNG NỢ", "Ngày hóa đơn khác ngày thanh toán. Chỉ cột Đã trả mới là dòng tiền ra trong kỳ.");
  const e = expWb.worksheets.add("HoaDonNCC"); title(e, "HÓA ĐƠN NHÀ CUNG CẤP & CÔNG NỢ", DISCLAIMER, "K");
  e.getRange("A4:K4").values = [["Mã HĐ", "Ngày HĐ", "Nhà cung cấp", "Nhóm chi phí", "Tổng HĐ", "Ngày trả", "Đã trả", "Còn nợ", "Trạng thái", "Phương thức", "Ghi chú"]]; header(e.getRange("A4:K4"));
  e.getRange(`A5:G${4 + d.invoices.length}`).values = d.invoices.map((x) => [x.id, x.invDate, x.supplier, x.cat, x.total, x.paidDate ? iso(x.paidDate) : "", x.paid]);
  e.getRange(`I5:K${4 + d.invoices.length}`).values = d.invoices.map(x => [x.status, x.paid ? "Chuyển khoản" : "", x.paid ? "Đã khớp sổ quỹ" : "Thanh toán tháng 07/2026"]);
  e.getRange("H5").formulas = [["=E5-G5"]]; e.getRange(`H5:H${4 + d.invoices.length}`).fillDown();
  body(e.getRange(`A5:K${4 + d.invoices.length}`)); e.getRange(`B5:B${4 + d.invoices.length}`).format.numberFormat = "yyyy-mm-dd"; e.getRange(`F5:F${4 + d.invoices.length}`).format.numberFormat = "yyyy-mm-dd";
  e.getRange(`E5:H${4 + d.invoices.length}`).format.numberFormat = "#,##0;[Red](#,##0);-"; e.freezePanes.freezeRows(4);
  setWidths(e, [["A", 13], ["B", 13], ["C", 24], ["D", 20], ["E", 16], ["F", 13], ["G", 16], ["H", 16], ["I", 18], ["J", 18], ["K", 28]]);
  await exportBook(expWb, path.join(input, "02_cong_no_chi_phi.xlsx"), [{ sheet: "HoaDonNCC", range: "A1:K18" }]);

  const ledgerWb = Workbook.create(); addReadmeSheet(ledgerWb, "TIỆM BÁNH MÂY SỚM - SỔ QUỸ", "Cột Có tính dòng tiền? là quy tắc loại trừ chuyển nội bộ. Số tiền dương là tiền vào, âm là tiền ra.");
  const l = ledgerWb.worksheets.add("Sổ tổng hợp"); title(l, "SỔ QUỸ & NGÂN HÀNG HỢP NHẤT", `Số dư đầu kỳ: ${d.opening.toLocaleString("vi-VN")} VND | ${DISCLAIMER}`, "J");
  l.getRange("A4:J4").values = [["Mã", "Ngày", "Tài khoản", "Loại", "Nhóm", "Số tiền (+/-)", "Có tính dòng tiền?", "Tham chiếu", "Số dư chạy", "Ghi chú"]]; header(l.getRange("A4:J4"));
  l.getRange(`A5:H${4 + d.ledger.length}`).values = d.ledger.map(x => [x.id, x.dt, x.account, x.type, x.category, x.amount, x.countCashflow ? "Có" : "Không", x.ref]);
  l.getRange(`J5:J${4 + d.ledger.length}`).values = d.ledger.map(x => [x.countCashflow ? "" : "Hai dòng cùng mã NB phải loại trừ"]);
  l.getRange("I5").formulas = [[`=${d.opening}+F5`]]; if (d.ledger.length > 1) { l.getRange("I6").formulas = [["=I5+F6"]]; l.getRange(`I6:I${4 + d.ledger.length}`).fillDown(); }
  body(l.getRange(`A5:J${4 + d.ledger.length}`)); l.getRange(`B5:B${4 + d.ledger.length}`).format.numberFormat = "yyyy-mm-dd"; l.getRange(`F5:F${4 + d.ledger.length}`).format.numberFormat = "#,##0;[Red](#,##0);-"; l.getRange(`I5:I${4 + d.ledger.length}`).format.numberFormat = "#,##0;[Red](#,##0);-";
  l.freezePanes.freezeRows(4); setWidths(l, [["A", 12], ["B", 13], ["C", 19], ["D", 22], ["E", 18], ["F", 17], ["G", 17], ["H", 14], ["I", 18], ["J", 34]]);
  await exportBook(ledgerWb, path.join(input, "03_so_quy_ngan_hang.xlsx"), [{ sheet: "Sổ tổng hợp", range: "A1:J20" }]);
  return { base, ...d };
}

function restaurantData() {
  const orders = [], payouts = [], tips = [];
  let oid = 1;
  for (const d of days("2026-04-01", "2026-06-30")) {
    const weekend = [0, 6].includes(d.getUTCDay()) ? 1.35 : 1;
    for (const shift of ["Trưa", "Tối"]) {
      const gross = money((shift === "Tối" ? 16_000_000 : 10_500_000) * weekend * (0.90 + rnd() * 0.22));
      const discount = rnd() < 0.25 ? money(gross * 0.04) : 0;
      const vat = money((gross - discount) * 0.08);
      const net = gross - discount + vat;
      const channel = rnd() < 0.72 ? "Tại bàn" : "Giao hàng";
      orders.push({ id: `OD-${String(oid++).padStart(4, "0")}`, dt: new Date(d), shift, channel, gross, discount, vat, net, status: "Hoàn tất" });
    }
  }
  for (const month of [4, 5, 6]) {
    const monthOrders = orders.filter(x => x.dt.getUTCMonth() + 1 === month);
    const revenue = sum(monthOrders, x => x.net);
    const cash = money(revenue * 0.31), card = money(revenue * 0.42), appGross = revenue - cash - card;
    const appFee = money(appGross * 0.20), cardFee = money(card * 0.012);
    payouts.push({ month: `2026-${String(month).padStart(2, "0")}`, cash, card, cardFee, appGross, appFee, received: cash + card - cardFee + appGross - appFee });
    tips.push({ month: `2026-${String(month).padStart(2, "0")}`, cashTip: money(7_000_000 * (0.9 + rnd() * 0.25)), qrTip: money(5_000_000 * (0.9 + rnd() * 0.25)), paidToStaff: 0 });
  }
  tips.forEach(x => { x.paidToStaff = x.cashTip + x.qrTip; });
  const ledger = [];
  const add = (dt, desc, type, amount, source, status = "Đã ghi sổ") => ledger.push({ dt: date(dt), desc, type, amount, source, status });
  add("2026-04-01", "Vay ngắn hạn từ chủ sở hữu", "Tài chính vào", 250_000_000, "HĐ-VAY-01");
  for (const p of payouts) {
    const m = Number(p.month.slice(5)); const mm = String(m).padStart(2, "0");
    add(`2026-${mm}-30`, `Thu bán hàng ${p.month}`, "Hoạt động vào", p.received, `PAYOUT-${mm}`);
    const t = tips[m - 4]; add(`2026-${mm}-30`, `Thu hộ tiền tip ${p.month}`, "Thu hộ - vào", t.cashTip + t.qrTip, `TIP-${mm}`);
    add(`2026-${mm}-30`, `Chi trả tiền tip nhân viên ${p.month}`, "Chi hộ - ra", -t.paidToStaff, `TIP-${mm}`);
    add(`2026-${mm}-05`, `Lương và bảo hiểm ${p.month}`, "Hoạt động ra", -money(165_000_000 * (0.98 + rnd() * 0.04)), `PAYROLL-${mm}`);
    add(`2026-${mm}-10`, `Nguyên liệu đã thanh toán ${p.month}`, "Hoạt động ra", -money(285_000_000 * (0.95 + rnd() * 0.08)), `NCC-${mm}`);
    add(`2026-${mm}-15`, `Điện nước và dịch vụ ${p.month}`, "Hoạt động ra", -money(28_000_000 * (0.95 + rnd() * 0.10)), `UTIL-${mm}`);
    add(`2026-${mm}-20`, `Tiền mặt nộp ngân hàng`, "Chuyển nội bộ ra", -45_000_000, `TRF-${mm}`);
    add(`2026-${mm}-20`, `Ngân hàng nhận tiền mặt`, "Chuyển nội bộ vào", 45_000_000, `TRF-${mm}`);
  }
  add("2026-04-01", "Thuê mặt bằng trả trước quý II", "Hoạt động ra", -180_000_000, "HDT-NH-01");
  for (const m of [4, 5, 6]) add(`2026-${String(m).padStart(2, "0")}-03`, `Phí dịch vụ tháng ${m}`, "Hoạt động ra", -12_000_000, "HDT-NH-01");
  add("2026-06-29", "Hóa đơn tiệc doanh nghiệp chưa thu", "Công nợ - không tiền", 48_000_000, "AR-0629", "Chưa thu");
  return { orders, payouts, tips, ledger, opening: 420_000_000 };
}

async function buildRestaurant() {
  const base = path.join(OUT, "02-nha-hang-bep-viet-36"); const input = path.join(base, "input"); await fs.mkdir(input, { recursive: true });
  const d = restaurantData();
  const pos = Workbook.create(); addReadmeSheet(pos, "NHÀ HÀNG BẾP VIỆT 36 - POS", "Orders là doanh thu phát sinh; Payouts là tiền thực nhận sau phí. Tips là khoản thu hộ/chi hộ, không phải doanh thu nhà hàng.");
  const o = pos.worksheets.add("Orders"); title(o, "POS - CHI TIẾT ĐƠN HÀNG", DISCLAIMER, "I"); o.getRange("A4:I4").values = [["Order ID", "Business date", "Ca", "Kênh", "Gross", "Discount", "VAT", "Net bill", "Status"]]; header(o.getRange("A4:I4"));
  o.getRange(`A5:I${4 + d.orders.length}`).values = d.orders.map(x => [x.id, x.dt, x.shift, x.channel, x.gross, x.discount, x.vat, x.net, x.status]); body(o.getRange(`A5:I${4 + d.orders.length}`)); o.getRange(`B5:B${4 + d.orders.length}`).format.numberFormat = "yyyy-mm-dd"; o.getRange(`E5:H${4 + d.orders.length}`).format.numberFormat = "#,##0;[Red](#,##0);-"; o.freezePanes.freezeRows(4); setWidths(o, [["A", 14], ["B", 15], ["C", 12], ["D", 15], ["E", 15], ["F", 15], ["G", 14], ["H", 16], ["I", 14]]);
  const p = pos.worksheets.add("Payouts"); title(p, "ĐỐI SOÁT TIỀN THỰC NHẬN", "Tiền thực nhận = tiền mặt + thẻ - phí thẻ + app gross - phí app", "H"); p.getRange("A4:H4").values = [["Tháng", "Cash", "Card gross", "Card fee", "App gross", "App fee", "Thực nhận", "Đối chiếu"]]; header(p.getRange("A4:H4")); p.getRange("A5:F7").values = d.payouts.map(x => [x.month, x.cash, x.card, x.cardFee, x.appGross, x.appFee]); p.getRange("G5").formulas = [["=B5+C5-D5+E5-F5"]]; p.getRange("G5:G7").fillDown(); p.getRange("H5:H7").values = d.payouts.map(() => ["Đã vào sổ"]); body(p.getRange("A5:H7")); p.getRange("B5:G7").format.numberFormat = "#,##0;[Red](#,##0);-"; setWidths(p, [["A", 14], ["B", 16], ["C", 16], ["D", 14], ["E", 16], ["F", 14], ["G", 18], ["H", 16]]);
  const t = pos.worksheets.add("Tips"); title(t, "TIỀN TIP THU HỘ - CHI HỘ", "Không ghi nhận là doanh thu hoặc chi phí của nhà hàng", "E"); t.getRange("A4:E4").values = [["Tháng", "Tip tiền mặt", "Tip QR", "Đã trả nhân viên", "Chênh lệch"]]; header(t.getRange("A4:E4")); t.getRange("A5:D7").values = d.tips.map(x => [x.month, x.cashTip, x.qrTip, x.paidToStaff]); t.getRange("E5").formulas = [["=B5+C5-D5"]]; t.getRange("E5:E7").fillDown(); body(t.getRange("A5:E7")); t.getRange("B5:E7").format.numberFormat = "#,##0;[Red](#,##0);-"; setWidths(t, [["A", 15], ["B", 18], ["C", 18], ["D", 20], ["E", 16]]);
  await exportBook(pos, path.join(input, "01_pos_va_doi_soat.xlsx"), [{ sheet: "Payouts", range: "A1:H8" }, { sheet: "Tips", range: "A1:E8" }]);

  const cash = Workbook.create(); addReadmeSheet(cash, "NHÀ HÀNG BẾP VIỆT 36 - NHẬT KÝ", "Số tiền dùng dấu: dương là vào, âm là ra. Chuyển nội bộ phải loại; dòng Chưa thu không phải dòng tiền.");
  const s = cash.worksheets.add("Nhật ký 90 ngày"); title(s, "NHẬT KÝ THU - CHI", `Số dư đầu kỳ: ${d.opening.toLocaleString("vi-VN")} VND`, "H");
  s.getRange("A4:H4").values = [["Ngày hạch toán", "Diễn giải", "Phân loại", "Số tiền có dấu", "Nguồn", "Trạng thái", "Tháng", "Gợi ý đối soát"]]; header(s.getRange("A4:H4")); s.getRange(`A5:F${4 + d.ledger.length}`).values = d.ledger.map(x => [x.dt, x.desc, x.type, x.amount, x.source, x.status]); s.getRange(`G5:G${4 + d.ledger.length}`).values = d.ledger.map(x => [`2026-${String(x.dt.getUTCMonth() + 1).padStart(2, "0")}`]); s.getRange(`H5:H${4 + d.ledger.length}`).values = d.ledger.map(x => [x.type.startsWith("Chuyển nội bộ") ? "Loại khỏi cash flow" : x.status === "Chưa thu" ? "Không tính đến khi thu" : "Tính theo dấu"]); body(s.getRange(`A5:H${4 + d.ledger.length}`)); s.getRange(`A5:A${4 + d.ledger.length}`).format.numberFormat = "yyyy-mm-dd"; s.getRange(`D5:D${4 + d.ledger.length}`).format.numberFormat = "#,##0;[Red](#,##0);-"; s.freezePanes.freezeRows(4); setWidths(s, [["A", 16], ["B", 38], ["C", 21], ["D", 19], ["E", 16], ["F", 15], ["G", 13], ["H", 28]]);
  await exportBook(cash, path.join(input, "02_nhat_ky_thu_chi.xlsx"), [{ sheet: "Nhật ký 90 ngày", range: "A1:H22" }]);
  return { base, ...d };
}

function convenienceData() {
  const shifts = [], statements = [];
  let sid = 1;
  for (const d of days("2026-04-01", "2026-06-30")) {
    for (const shift of ["Sáng", "Chiều", "Đêm"]) {
      const base = shift === "Đêm" ? 7_300_000 : shift === "Chiều" ? 9_000_000 : 6_400_000;
      const gross = money(base * (0.86 + rnd() * 0.30));
      const discount = rnd() < 0.35 ? money(gross * 0.02) : 0;
      const returns = rnd() < 0.06 ? money(80_000 + rnd() * 180_000) : 0;
      const cash = money((gross - discount - returns) * 0.38);
      const qr = money((gross - discount - returns) * 0.44);
      const walletGross = gross - discount - returns - cash - qr;
      shifts.push({ id: `CA-${String(sid++).padStart(4, "0")}`, dt: new Date(d), shift, gross, discount, returns, cash, qr, walletGross });
    }
  }
  const opening = 310_000_000;
  let tx = 1;
  const push = (dt, account, desc, credit, debit, kind, ref) => statements.push({ tx: `TX-${String(tx++).padStart(4, "0")}`, dt: date(dt), account, desc, credit, debit, kind, ref });
  for (const month of [4, 5, 6]) {
    const rows = shifts.filter(x => x.dt.getUTCMonth() + 1 === month);
    const cash = sum(rows, x => x.cash), qr = sum(rows, x => x.qr), walletGross = sum(rows, x => x.walletGross);
    const walletFee = money(walletGross * 0.025), walletNet = walletGross - walletFee;
    push(`2026-${String(month).padStart(2, "0")}-28`, "Tiền mặt", `Doanh thu tiền mặt T${month}`, cash, 0, "Bán hàng", `CA-T${month}`);
    push(`2026-${String(month).padStart(2, "0")}-29`, "Ngân hàng", `Doanh thu QR T${month}`, qr, 0, "Bán hàng", `QR-T${month}`);
    push(`2026-${String(month).padStart(2, "0")}-30`, "Ví điện tử", `Ví thanh toán net T${month}`, walletNet, 0, "Bán hàng", `EW-T${month}`);
    push(`2026-${String(month).padStart(2, "0")}-07`, "Ngân hàng", `Thanh toán hàng hóa T${month}`, 0, money(390_000_000 * (0.95 + rnd() * 0.08)), "Mua hàng", `INV-T${month}`);
    push(`2026-${String(month).padStart(2, "0")}-12`, "Ngân hàng", `Lương T${month}`, 0, 82_000_000, "Nhân sự", `SAL-T${month}`);
    push(`2026-${String(month).padStart(2, "0")}-18`, "Ngân hàng", `Thuê và điện nước T${month}`, 0, 42_000_000, "Vận hành", `OPS-T${month}`);
    push(`2026-${String(month).padStart(2, "0")}-21`, "Tiền mặt", `Nộp tiền mặt T${month}`, 0, 60_000_000, "Điều chuyển nội bộ", `MOVE-T${month}`);
    push(`2026-${String(month).padStart(2, "0")}-21`, "Ngân hàng", `Nhận tiền nộp quỹ T${month}`, 60_000_000, 0, "Điều chuyển nội bộ", `MOVE-T${month}`);
  }
  push("2026-05-10", "Ngân hàng", "Phí nhượng quyền tháng 04", 0, money(sum(shifts.filter(x => x.dt.getUTCMonth() === 3), x => x.gross - x.discount - x.returns) * 0.04), "Phí nhượng quyền", "FR-04");
  push("2026-06-10", "Ngân hàng", "Phí nhượng quyền tháng 05", 0, money(sum(shifts.filter(x => x.dt.getUTCMonth() === 4), x => x.gross - x.discount - x.returns) * 0.04), "Phí nhượng quyền", "FR-05");
  return { shifts, statements, opening };
}

async function buildConvenience() {
  const base = path.join(OUT, "03-cua-hang-tien-loi-dem-24"); const input = path.join(base, "input"); await fs.mkdir(input, { recursive: true });
  const d = convenienceData();
  const sales = Workbook.create(); addReadmeSheet(sales, "CỬA HÀNG TIỆN LỢI ĐÊM 24 - BÁO CÁO CA", "Mỗi ngày có 3 ca. Ví điện tử trong báo cáo là gross; sao kê nhận net sau phí. Không cộng cả hai nguồn.");
  for (const month of [4, 5, 6]) {
    const s = sales.worksheets.add(`${month}.2026`); title(s, `BÁO CÁO CA - ${month}.2026`, DISCLAIMER, "J");
    s.getRange("A4:J4").values = [["Mã ca", "Ngày", "Ca", "Gross sales", "Khuyến mại", "Hàng trả", "Tiền mặt", "QR", "Ví gross", "Net sales"]]; header(s.getRange("A4:J4"));
    const rows = d.shifts.filter(x => x.dt.getUTCMonth() + 1 === month); s.getRange(`A5:I${4 + rows.length}`).values = rows.map(x => [x.id, x.dt, x.shift, x.gross, x.discount, x.returns, x.cash, x.qr, x.walletGross]); s.getRange("J5").formulas = [["=D5-E5-F5"]]; s.getRange(`J5:J${4 + rows.length}`).fillDown(); body(s.getRange(`A5:J${4 + rows.length}`)); s.getRange(`B5:B${4 + rows.length}`).format.numberFormat = "dd/mm/yyyy"; s.getRange(`D5:J${4 + rows.length}`).format.numberFormat = "#,##0;[Red](#,##0);-"; s.freezePanes.freezeRows(4); setWidths(s, [["A", 14], ["B", 13], ["C", 11], ["D", 16], ["E", 16], ["F", 14], ["G", 16], ["H", 16], ["I", 16], ["J", 16]]);
  }
  await exportBook(sales, path.join(input, "01_bao_cao_ca_ban_hang.xlsx"), [{ sheet: "4.2026", range: "A1:J18" }]);

  const bank = Workbook.create(); addReadmeSheet(bank, "CỬA HÀNG TIỆN LỢI ĐÊM 24 - SAO KÊ", "Credit là tiền vào, Debit là tiền ra. Hai dòng có loại Điều chuyển nội bộ và cùng mã MOVE phải loại khỏi dòng tiền bên ngoài.");
  const s = bank.worksheets.add("ALL_ACCOUNTS"); title(s, "SAO KÊ HỢP NHẤT: CASH / BANK / E-WALLET", `Opening balance: ${d.opening.toLocaleString("vi-VN")} VND`, "I"); s.getRange("A4:I4").values = [["TXN", "Posting date", "Account", "Narrative", "Credit", "Debit", "Type", "Reference", "Net movement"]]; header(s.getRange("A4:I4")); s.getRange(`A5:H${4 + d.statements.length}`).values = d.statements.map(x => [x.tx, x.dt, x.account, x.desc, x.credit, x.debit, x.kind, x.ref]); s.getRange("I5").formulas = [["=E5-F5"]]; s.getRange(`I5:I${4 + d.statements.length}`).fillDown(); body(s.getRange(`A5:I${4 + d.statements.length}`)); s.getRange(`B5:B${4 + d.statements.length}`).format.numberFormat = "yyyy-mm-dd"; s.getRange(`E5:I${4 + d.statements.length}`).format.numberFormat = "#,##0;[Red](#,##0);-"; s.freezePanes.freezeRows(4); setWidths(s, [["A", 14], ["B", 15], ["C", 16], ["D", 36], ["E", 16], ["F", 16], ["G", 22], ["H", 16], ["I", 18]]);
  await exportBook(bank, path.join(input, "02_sao_ke_hop_nhat.xlsx"), [{ sheet: "ALL_ACCOUNTS", range: "A1:I22" }]);
  const csv = ["transaction_id,posting_date,account,narrative,credit_vnd,debit_vnd,type,reference", ...d.statements.map(x => [x.tx, iso(x.dt), x.account, `"${x.desc}"`, x.credit, x.debit, x.kind, x.ref].join(","))].join("\n");
  await fs.writeFile(path.join(input, "03_sao_ke_du_phong.csv"), csv, "utf8");
  return { base, ...d };
}

function summarizeLedger(ledger, opening, predicate, amountFn) {
  const valid = ledger.filter(predicate);
  const inflow = sum(valid.filter(x => amountFn(x) > 0), amountFn);
  const outflow = -sum(valid.filter(x => amountFn(x) < 0), amountFn);
  return { opening_balance: opening, cash_inflow: inflow, cash_outflow: outflow, net_cashflow: inflow - outflow, closing_balance: opening + inflow - outflow };
}

async function writeGroundTruth(bakery, restaurant, convenience) {
  const bakeryTruth = summarizeLedger(bakery.ledger, bakery.opening, x => x.countCashflow, x => x.amount);
  const restaurantTruth = summarizeLedger(restaurant.ledger, restaurant.opening, x => !x.type.startsWith("Chuyển nội bộ") && x.status !== "Chưa thu", x => x.amount);
  const convenienceTruth = summarizeLedger(convenience.statements, convenience.opening, x => x.kind !== "Điều chuyển nội bộ", x => x.credit - x.debit);
  const cases = [
    { id: "01-tiem-banh-may-som", name: "Tiệm bánh Mây Sớm", expected: bakeryTruth, exclusions: ["chuyển nội bộ", "hóa đơn chưa thanh toán", "doanh thu gross của app"], key_tool_challenges: ["nhiều sheet tháng", "phân biệt doanh thu và tiền thực nhận", "lọc theo trạng thái thanh toán"] },
    { id: "02-nha-hang-bep-viet-36", name: "Nhà hàng Bếp Việt 36", expected: restaurantTruth, exclusions: ["chuyển nội bộ", "công nợ chưa thu", "tip thu hộ và chi hộ triệt tiêu"], key_tool_challenges: ["POS + payout + nhật ký", "tiền thuê trả trước theo quý", "loan financing khác operating cash flow"] },
    { id: "03-cua-hang-tien-loi-dem-24", name: "Cửa hàng tiện lợi Đêm 24", expected: convenienceTruth, exclusions: ["chuyển nội bộ", "phí nhượng quyền tháng 06 chưa trả trong kỳ", "không cộng trùng CSV dự phòng"], key_tool_challenges: ["3 ca mỗi ngày", "ví gross so với net settlement", "Excel và CSV chứa cùng sao kê"] },
  ];
  for (const c of cases) {
    const gtDir = path.join(OUT, c.id, "ground-truth"); await fs.mkdir(gtDir, { recursive: true });
    await fs.writeFile(path.join(gtDir, "expected_cashflow.json"), JSON.stringify(c, null, 2), "utf8");
    const prompt = `# Test prompt - ${c.name}\n\nHãy tự chọn tool phù hợp để đọc toàn bộ file trong thư mục input. Trích xuất dòng tiền từ 01/04/2026 đến 30/06/2026, loại giao dịch nội bộ và tránh cộng trùng dữ liệu. Trả về: tiền vào, tiền ra, dòng tiền thuần, số dư đầu kỳ, số dư cuối kỳ; sau đó phân loại operating / investing / financing và nêu các khoản bị loại.\n`;
    await fs.writeFile(path.join(gtDir, "test_prompt.md"), prompt, "utf8");
  }
  return cases;
}

async function writeReadmes(cases) {
  const lines = [
    "# Bộ dữ liệu kiểm thử AI tự trích xuất dòng tiền",
    "",
    DISCLAIMER,
    "",
    "Bộ này mở rộng từ cấu trúc `goc-ho-coffee`, nhưng cố ý thay đổi tên sheet, cách đặt bảng, dấu số tiền, thời điểm ghi nhận và mối quan hệ giữa Excel/PDF/CSV.",
    "",
    "## Cách test",
    "",
    "1. Chỉ upload thư mục `input` của một case cho AI.",
    "2. Dùng prompt trong `ground-truth/test_prompt.md`.",
    "3. So kết quả với `ground-truth/expected_cashflow.json` sau khi AI trả lời.",
    "4. Kiểm tra AI có tự chọn đúng tool, đọc được nhiều sheet/PDF/CSV, loại chuyển nội bộ và tránh double-count hay không.",
    "",
    "## Các case",
    "",
    ...cases.map(c => `- **${c.name}**: tiền vào ${c.expected.cash_inflow.toLocaleString("vi-VN")} đ; tiền ra ${c.expected.cash_outflow.toLocaleString("vi-VN")} đ; cuối kỳ ${c.expected.closing_balance.toLocaleString("vi-VN")} đ.`),
    "",
    "## Nguyên tắc chấm",
    "",
    "- Sai số số học kỳ vọng: 0 VND.",
    "- Không tính doanh thu/hóa đơn phát sinh nhưng chưa thu/chưa trả vào cash flow.",
    "- Không cộng trùng cùng giao dịch xuất hiện ở báo cáo bán hàng và sổ quỹ/sao kê.",
    "- Loại cả hai vế chuyển nội bộ.",
    "- Dòng tiền tài chính (vốn góp/vay) vẫn nằm trong tổng dòng tiền nhưng phải phân loại riêng.",
  ];
  await fs.writeFile(path.join(OUT, "README.md"), lines.join("\n"), "utf8");
}

async function main() {
  await ensureDirs();
  const bakery = await buildBakery();
  const restaurant = await buildRestaurant();
  const convenience = await buildConvenience();
  const cases = await writeGroundTruth(bakery, restaurant, convenience);
  await writeReadmes(cases);
  const manifest = { generated_at: "2026-07-19", disclaimer: DISCLAIMER, cases };
  await fs.writeFile(path.join(OUT, "manifest.json"), JSON.stringify(manifest, null, 2), "utf8");
  console.log(JSON.stringify(cases, null, 2));
}

await main();
