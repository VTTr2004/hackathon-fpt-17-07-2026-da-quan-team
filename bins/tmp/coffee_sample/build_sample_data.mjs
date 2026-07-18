import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(scriptDir, "..", "..", "..");
const outputDir = path.resolve(
  process.env.SAMPLE_OUTPUT_DIR ?? path.join(projectRoot, "bins", "outputs", "sample_data_2026_07_19", "goc-ho-coffee"),
);
const previewDir = path.resolve(
  process.env.SAMPLE_PREVIEW_DIR ?? path.join(projectRoot, "bins", "tmp", "coffee_sample", "previews"),
);
await fs.mkdir(outputDir, { recursive: true });
await fs.mkdir(previewDir, { recursive: true });

const COLORS = {
  dark: "#173B2B",
  green: "#2F6B4F",
  cream: "#F4F0E6",
  pale: "#E8F1EA",
  gold: "#D8A84E",
  white: "#FFFFFF",
  ink: "#1F2923",
  gray: "#68756D",
  line: "#D6DDD8",
  input: "#0000FF",
  formula: "#000000",
  link: "#008000",
  warning: "#FFF4CC",
  danger: "#FDE2E2",
};

const business = {
  business_id: "GOCHO-DEMO-001",
  name: "Góc Hồ Coffee",
  legal_name: "Hộ kinh doanh Góc Hồ Coffee (mô phỏng)",
  owner_name: "Nguyễn Minh An (nhân vật mô phỏng)",
  registration_code: "HKD-DEMO-2026-001",
  tax_code: "MST-MOPHONG-001",
  address: "Số 12 phố Lê Thái Tổ, phường Hoàn Kiếm, thành phố Hà Nội",
  latitude: 21.03023,
  longitude: 105.85092,
  opened_on: "2026-04-01",
  industry: "F&B",
  stage: "Seed",
  primary_location: "Hoàn Kiếm, Hà Nội",
  business_type: "Hộ kinh doanh",
  operating_scope: "Một điểm bán tại khu vực Hồ Hoàn Kiếm và giao hàng bán kính gần",
  problem:
    "Khách đi bộ quanh Hồ Hoàn Kiếm cần một điểm dừng chân có cà phê Việt, chỗ ngồi ngắn hạn và phục vụ nhanh.",
  problem_owner:
    "Khách du lịch, nhân viên văn phòng và người trẻ di chuyển quanh khu vực Hồ Hoàn Kiếm.",
  target_customers: [
    "Khách du lịch trong nước và quốc tế đi bộ quanh Hồ Hoàn Kiếm",
    "Nhân viên văn phòng khu vực Hoàn Kiếm",
    "Người trẻ cần chỗ gặp mặt hoặc làm việc ngắn",
  ],
  solution:
    "Quán cà phê quy mô nhỏ, phục vụ cà phê Việt và đồ uống hiện đại, có mang đi và giao hàng trong bán kính gần.",
  differentiation:
    "Vị trí gần Hồ Hoàn Kiếm, menu cà phê Việt dễ tiếp cận, thời gian phục vụ ngắn và ba hình thức nhận món.",
  customer_purchase_occasions:
    "Dừng nghỉ khi tham quan, mua đồ uống trước giờ làm, gặp mặt ngắn và đặt giao trong giờ hành chính.",
  users_and_payers: "Người mua đồ uống cũng là người sử dụng và thanh toán; đơn giao hàng có thể do nhóm văn phòng chi trả.",
  core_products: ["Cà phê Việt", "Đồ uống espresso và cold brew", "Trà, matcha và bánh ngọt"],
  pricing_model: "Giá niêm yết theo món từ 35.000 đến 65.000 VND; khuyến mại theo giao dịch từ 5% đến 10%.",
  revenue_model: ["Bán đồ uống và bánh theo món"],
  sales_channels: ["Tại quán", "Mang đi", "Giao hàng"],
  acquisition_channels: ["Khách vãng lai quanh Hồ Hoàn Kiếm", "Mạng xã hội", "Ứng dụng giao hàng"],
  competitors: ["Chuỗi cà phê lớn tại khu vực Hoàn Kiếm", "Các quán cà phê nội địa quanh Hồ Hoàn Kiếm"],
  key_suppliers_partners: ["Nhà rang Hương Việt", "Sữa & Nguyên liệu An Bình", "Bao bì Xanh Hà Nội", "Bếp bánh Ban Mai"],
  fundraising_need: "Bổ sung vốn lưu động và thử nghiệm chuẩn hóa mô hình trước khi cân nhắc điểm bán thứ hai.",
  opening_hours: "07:00-22:00",
  area_m2: 85,
  seats: 42,
  monthly_rent: 70000000,
  deposit: 210000000,
  employees: 8,
  currency: "VND",
  data_period: { start: "2026-04-01", end: "2026-06-30" },
  disclaimer: "DỮ LIỆU MÔ PHỎNG - KHÔNG CÓ GIÁ TRỊ PHÁP LÝ",
};

const developmentPlan = {
  business_id: business.business_id,
  planning_horizon_months: 12,
  development_objectives:
    "Tăng doanh thu trung bình tháng 20% và duy trì số dư tiền cuối tháng cao hơn mức đệm tối thiểu trong 12 tháng tới.",
  product_plan:
    "Thử nghiệm hai combo cà phê và bánh vào buổi sáng; chỉ giữ sản phẩm có biên đóng góp dương và tỷ lệ mua lại tốt.",
  customer_growth_plan:
    "Triển khai chương trình khách hàng quay lại và gói đặt theo tuần cho các văn phòng trong bán kính 2 km.",
  channel_expansion_plan:
    "Tối ưu kênh giao hàng hiện có trước khi thêm nền tảng mới; theo dõi doanh thu thuần sau phí theo từng kênh.",
  outlet_expansion_plan:
    "Chỉ đánh giá điểm bán thứ hai sau khi điểm hiện tại có sáu tháng dòng tiền hoạt động dương liên tiếp.",
  operating_capability_plan:
    "Chuẩn hóa định lượng nguyên liệu, lịch ca, quy trình chốt quỹ và đối soát hóa đơn theo tuần.",
  development_milestones:
    "Q3/2026: hoàn thiện dashboard chi phí; Q4/2026: tăng tỷ lệ khách quay lại; Q1/2027: đánh giá điều kiện mở rộng.",
  development_dependencies:
    "Phụ thuộc lưu lượng khách khu vực, năng lực giữ nhân sự, phí nền tảng giao hàng và biến động giá nguyên liệu.",
  disclaimer: business.disclaimer,
};

const menu = [
  { sku: "CF-DEN", name: "Cà phê đen", category: "Cà phê Việt", price: 35000, baseQty: 22 },
  { sku: "CF-SUA", name: "Cà phê sữa", category: "Cà phê Việt", price: 39000, baseQty: 25 },
  { sku: "BAC-XIU", name: "Bạc xỉu", category: "Cà phê Việt", price: 42000, baseQty: 18 },
  { sku: "AMERICANO", name: "Americano", category: "Espresso", price: 45000, baseQty: 13 },
  { sku: "LATTE", name: "Caffè Latte", category: "Espresso", price: 55000, baseQty: 16 },
  { sku: "COLD-BREW", name: "Cold Brew", category: "Cà phê lạnh", price: 59000, baseQty: 10 },
  { sku: "MATCHA", name: "Matcha Latte", category: "Không cà phê", price: 59000, baseQty: 12 },
  { sku: "TRA-DAO", name: "Trà đào cam sả", category: "Trà", price: 49000, baseQty: 11 },
  { sku: "CROISSANT", name: "Croissant bơ", category: "Bánh", price: 42000, baseQty: 8 },
  { sku: "TIRAMISU", name: "Tiramisu", category: "Bánh", price: 65000, baseQty: 5 },
];

const suppliers = [
  { id: "NCC-01", name: "Nhà rang Hương Việt (mô phỏng)", category: "Cà phê hạt" },
  { id: "NCC-02", name: "Sữa & Nguyên liệu An Bình (mô phỏng)", category: "Sữa và nguyên liệu" },
  { id: "NCC-03", name: "Bao bì Xanh Hà Nội (mô phỏng)", category: "Bao bì" },
  { id: "NCC-04", name: "Bếp bánh Ban Mai (mô phỏng)", category: "Bánh" },
  { id: "NCC-05", name: "Dịch vụ Vận hành Hồ Gươm (mô phỏng)", category: "Vận hành" },
  { id: "NCC-06", name: "Truyền thông Phố Cổ (mô phỏng)", category: "Marketing" },
];

function mulberry32(seed) {
  return function random() {
    let t = (seed += 0x6d2b79f5);
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
const random = mulberry32(20260718);
const round1000 = (value) => Math.round(value / 1000) * 1000;
const iso = (date) => date.toISOString().slice(0, 10);
const dateUtc = (text) => new Date(`${text}T00:00:00Z`);

const sales = [];
const dailySales = new Map();
const start = dateUtc("2026-04-01");
const end = dateUtc("2026-06-30");
let dayIndex = 0;
for (let date = new Date(start); date <= end; date.setUTCDate(date.getUTCDate() + 1)) {
  const dateText = iso(date);
  const weekday = date.getUTCDay();
  const weekendFactor = weekday === 0 || weekday === 6 ? 1.28 : 1;
  const growthFactor = 1 + dayIndex * 0.0017;
  let dailyNet = 0;
  menu.forEach((item, productIndex) => {
    const noise = 0.82 + random() * 0.36;
    const qty = Math.max(1, Math.round(item.baseQty * weekendFactor * growthFactor * noise));
    const discountRate = random() < 0.18 ? 0.1 : random() < 0.12 ? 0.05 : 0;
    const gross = qty * item.price;
    const net = Math.round(gross * (1 - discountRate));
    const channelPick = random();
    const channel = channelPick < 0.6 ? "Tại quán" : channelPick < 0.82 ? "Mang đi" : "Giao hàng";
    const payment = random() < 0.34 ? "Tiền mặt" : "Chuyển khoản/QR";
    const batchId = `BH-${dateText.replaceAll("-", "")}-${String(productIndex + 1).padStart(2, "0")}`;
    sales.push({
      date: dateText,
      batch_id: batchId,
      sku: item.sku,
      product: item.name,
      category: item.category,
      quantity: qty,
      unit_price: item.price,
      discount_rate: discountRate,
      gross,
      net,
      channel,
      payment_method: payment,
      evidence_ref: "",
    });
    dailyNet += net;
  });
  dailySales.set(dateText, dailyNet);
  dayIndex += 1;
}

const salesInvoiceDates = ["2026-04-05", "2026-04-24", "2026-05-10", "2026-05-29", "2026-06-14", "2026-06-27"];
const salesInvoices = salesInvoiceDates.map((date, idx) => {
  const items = [
    menu[(idx * 2) % menu.length],
    menu[(idx * 2 + 1) % menu.length],
    menu[(idx * 2 + 4) % menu.length],
  ].map((item, line) => ({
    sku: item.sku,
    name: item.name,
    quantity: line === 0 ? 2 : 1,
    unit_price: item.price,
    amount: (line === 0 ? 2 : 1) * item.price,
  }));
  const subtotal = items.reduce((sum, item) => sum + item.amount, 0);
  const id = `HDBH-MAU-${String(idx + 1).padStart(3, "0")}`;
  items.forEach((invoiceItem) => {
    const row = sales.find((sale) => sale.date === date && sale.sku === invoiceItem.sku);
    if (row) row.evidence_ref = id;
  });
  return {
    id,
    date,
    customer: "Khách lẻ",
    items,
    subtotal,
    discount: 0,
    total: subtotal,
    payment_method: idx % 2 === 0 ? "Chuyển khoản/QR" : "Tiền mặt",
  };
});

const purchases = [];
let purchaseIndex = 1;
const purchaseTemplates = [
  { supplier: suppliers[0], item: "Cà phê hạt rang", unit: "kg", qty: 24, price: 285000, vat: 0.08 },
  { supplier: suppliers[1], item: "Sữa tươi và sữa đặc", unit: "lô", qty: 1, price: 5600000, vat: 0.08 },
  { supplier: suppliers[2], item: "Cốc, nắp và túi mang đi", unit: "lô", qty: 1, price: 2900000, vat: 0.08 },
  { supplier: suppliers[3], item: "Bánh ngọt giao tuần", unit: "lô", qty: 1, price: 4900000, vat: 0.08 },
  { supplier: suppliers[5], item: "Quảng cáo mạng xã hội", unit: "gói", qty: 1, price: 2200000, vat: 0.1 },
];
for (let date = new Date(start); date <= end; date.setUTCDate(date.getUTCDate() + 7)) {
  purchaseTemplates.forEach((template, templateIndex) => {
    const multiplier = 0.9 + random() * 0.22;
    const qty = template.unit === "kg" ? Math.round(template.qty * multiplier) : template.qty;
    const unitPrice = round1000(template.price * (0.97 + random() * 0.06));
    const subtotal = qty * unitPrice;
    const vatAmount = Math.round(subtotal * template.vat);
    const total = subtotal + vatAmount;
    purchases.push({
      date: iso(date),
      invoice_id: `HDMH-MAU-${String(purchaseIndex).padStart(3, "0")}`,
      supplier_id: template.supplier.id,
      supplier: template.supplier.name,
      category: template.supplier.category,
      item: template.item,
      unit: template.unit,
      quantity: qty,
      unit_price: unitPrice,
      subtotal,
      vat_rate: template.vat,
      vat_amount: vatAmount,
      total,
      payment_method: templateIndex % 2 === 0 ? "Chuyển khoản" : "Tiền mặt",
      payment_status: "Đã thanh toán",
    });
    purchaseIndex += 1;
  });
}

const fixedExpenses = [];
for (const month of [4, 5, 6]) {
  const monthText = String(month).padStart(2, "0");
  fixedExpenses.push(
    {
      date: `2026-${monthText}-02`,
      invoice_id: `CP-THUE-2026${monthText}`,
      supplier_id: "NCC-MATBANG",
      supplier: "Chủ mặt bằng (mô phỏng)",
      category: "Tiền thuê",
      item: `Tiền thuê mặt bằng tháng ${monthText}/2026`,
      unit: "tháng",
      quantity: 1,
      unit_price: business.monthly_rent,
      subtotal: business.monthly_rent,
      vat_rate: 0,
      vat_amount: 0,
      total: business.monthly_rent,
      payment_method: "Chuyển khoản",
      payment_status: "Đã thanh toán",
    },
    {
      date: `2026-${monthText}-10`,
      invoice_id: `CP-LUONG-2026${monthText}`,
      supplier_id: "NV-DEMO",
      supplier: "Nhân sự quán (mô phỏng)",
      category: "Tiền lương",
      item: `Lương và phụ cấp tháng ${monthText}/2026`,
      unit: "tháng",
      quantity: 1,
      unit_price: 62000000,
      subtotal: 62000000,
      vat_rate: 0,
      vat_amount: 0,
      total: 62000000,
      payment_method: "Chuyển khoản",
      payment_status: "Đã thanh toán",
    },
    {
      date: `2026-${monthText}-15`,
      invoice_id: `CP-DIENNUOC-2026${monthText}`,
      supplier_id: suppliers[4].id,
      supplier: suppliers[4].name,
      category: "Điện nước",
      item: `Điện, nước, internet tháng ${monthText}/2026`,
      unit: "tháng",
      quantity: 1,
      unit_price: round1000(11800000 + random() * 1800000),
      subtotal: 0,
      vat_rate: 0.1,
      vat_amount: 0,
      total: 0,
      payment_method: "Chuyển khoản",
      payment_status: "Đã thanh toán",
    },
    {
      date: `2026-${monthText}-20`,
      invoice_id: `CP-PHANMEM-2026${monthText}`,
      supplier_id: "NCC-POS",
      supplier: "Nền tảng POS (mô phỏng)",
      category: "Phần mềm",
      item: `POS và phần mềm tháng ${monthText}/2026`,
      unit: "tháng",
      quantity: 1,
      unit_price: 1800000,
      subtotal: 1800000,
      vat_rate: 0.1,
      vat_amount: 180000,
      total: 1980000,
      payment_method: "Chuyển khoản",
      payment_status: "Đã thanh toán",
    },
  );
}
fixedExpenses.forEach((item) => {
  if (item.category === "Điện nước") {
    item.subtotal = item.unit_price;
    item.vat_amount = Math.round(item.subtotal * item.vat_rate);
    item.total = item.subtotal + item.vat_amount;
  }
});
purchases.push(...fixedExpenses);
purchases.sort((a, b) => a.date.localeCompare(b.date) || a.invoice_id.localeCompare(b.invoice_id));

const cashbook = [];
let cashTxIndex = 1;
cashbook.push({
  date: "2026-04-01",
  transaction_id: `PT-${String(cashTxIndex++).padStart(4, "0")}`,
  type: "Vốn góp",
  category: "Vốn chủ",
  description: "Chủ quán bổ sung vốn lưu động",
  account: "Ngân hàng",
  inflow: 150000000,
  outflow: 0,
  source_ref: "BB-GOPVON-DEMO-001",
});
for (const [date, total] of dailySales.entries()) {
  const cashShare = 0.34 + (random() - 0.5) * 0.08;
  const cashAmount = round1000(total * cashShare);
  const bankAmount = total - cashAmount;
  cashbook.push(
    {
      date,
      transaction_id: `PT-${String(cashTxIndex++).padStart(4, "0")}`,
      type: "Thu",
      category: "Bán hàng",
      description: "Doanh thu bán hàng trong ngày - tiền mặt",
      account: "Tiền mặt",
      inflow: cashAmount,
      outflow: 0,
      source_ref: `BH-${date.replaceAll("-", "")}`,
    },
    {
      date,
      transaction_id: `PT-${String(cashTxIndex++).padStart(4, "0")}`,
      type: "Thu",
      category: "Bán hàng",
      description: "Doanh thu bán hàng trong ngày - QR/chuyển khoản",
      account: "Ngân hàng",
      inflow: bankAmount,
      outflow: 0,
      source_ref: `BH-${date.replaceAll("-", "")}`,
    },
  );
}
purchases.forEach((purchase) => {
  cashbook.push({
    date: purchase.date,
    transaction_id: `PC-${String(cashTxIndex++).padStart(4, "0")}`,
    type: "Chi",
    category: purchase.category,
    description: purchase.item,
    account: purchase.payment_method === "Tiền mặt" ? "Tiền mặt" : "Ngân hàng",
    inflow: 0,
    outflow: purchase.total,
    source_ref: purchase.invoice_id,
  });
});
cashbook.sort((a, b) => a.date.localeCompare(b.date) || a.transaction_id.localeCompare(b.transaction_id));

const openingCash = 380000000;
const totalSales = sales.reduce((sum, row) => sum + row.net, 0);
const totalPurchases = purchases.reduce((sum, row) => sum + row.total, 0);
const totalInflows = cashbook.reduce((sum, row) => sum + row.inflow, 0);
const totalOutflows = cashbook.reduce((sum, row) => sum + row.outflow, 0);
const endingCash = openingCash + totalInflows - totalOutflows;
const fixedCostCategories = new Set(["Tiền thuê", "Tiền lương", "Phần mềm"]);
const fixedMonthlyCosts =
  purchases.filter((row) => fixedCostCategories.has(row.category)).reduce((sum, row) => sum + row.total, 0) / 3;
const variableCosts =
  purchases.filter((row) => !fixedCostCategories.has(row.category)).reduce((sum, row) => sum + row.total, 0) / 3;
const monthlyRevenue = totalSales / 3;
const monthlyExpense = fixedMonthlyCosts + variableCosts;
const variableCostRatio = variableCosts / monthlyRevenue;
const totalUnits = sales.reduce((sum, row) => sum + row.quantity, 0);
const averageItemValue = totalUnits ? totalSales / totalUnits : null;

const profileDocument = {
  schema_version: "startup-profile-v2",
  business_id: business.business_id,
  name: business.name,
  industry: business.industry,
  stage: business.stage,
  primary_location: business.primary_location,
  location: business.primary_location,
  founded_date: business.opened_on,
  business_type: business.business_type,
  employee_count: business.employees,
  operating_scope: business.operating_scope,
  problem: business.problem,
  problem_owner: business.problem_owner,
  solution: business.solution,
  differentiation: business.differentiation,
  target_customers: business.target_customers,
  customer_purchase_occasions: business.customer_purchase_occasions,
  users_and_payers: business.users_and_payers,
  core_products: business.core_products,
  pricing_model: business.pricing_model,
  revenue_model: business.revenue_model,
  sales_channels: business.sales_channels,
  acquisition_channels: business.acquisition_channels,
  average_order_value: Math.round(averageItemValue),
  competitors: business.competitors,
  key_suppliers_partners: business.key_suppliers_partners,
  traction: `Doanh thu thuần quý II/2026 đạt ${totalSales.toLocaleString("vi-VN")} VND từ 91 ngày bán hàng.`,
  fundraising_need: business.fundraising_need,
  disclaimer: business.disclaimer,
};

const cashFlowGroundTruth = {
  schema_version: "cashflow-ground-truth-v2",
  currency: business.currency,
  cash_as_of: business.data_period.end,
  current_cash: endingCash,
  monthly_revenue: monthlyRevenue,
  fixed_monthly_costs: fixedMonthlyCosts,
  variable_costs: variableCosts,
  computed: {
    monthly_expense: monthlyExpense,
    variable_cost_ratio: variableCostRatio,
  },
  classification: {
    fixed_categories: [...fixedCostCategories],
    variable_categories: [...new Set(purchases.filter((row) => !fixedCostCategories.has(row.category)).map((row) => row.category))],
  },
};

const staff = [
  { id: "NV-01", name: "Trần Thu Hà", role: "Quản lý" },
  { id: "NV-02", name: "Lê Hoàng Nam", role: "Barista" },
  { id: "NV-03", name: "Phạm Mai Anh", role: "Barista" },
  { id: "NV-04", name: "Vũ Đức Minh", role: "Barista" },
  { id: "NV-05", name: "Ngô Khánh Linh", role: "Phục vụ" },
  { id: "NV-06", name: "Đỗ Quang Huy", role: "Phục vụ" },
  { id: "NV-07", name: "Bùi Ngọc Lan", role: "Thu ngân" },
  { id: "NV-08", name: "Nguyễn Tuấn Kiệt", role: "Phục vụ" },
];
const schedule = [
  ["Thứ Hai", "NV-01, NV-02, NV-05, NV-07", "NV-03, NV-04, NV-06, NV-08"],
  ["Thứ Ba", "NV-01, NV-03, NV-05, NV-07", "NV-02, NV-04, NV-06, NV-08"],
  ["Thứ Tư", "NV-01, NV-02, NV-06, NV-07", "NV-03, NV-04, NV-05, NV-08"],
  ["Thứ Năm", "NV-01, NV-03, NV-05, NV-07", "NV-02, NV-04, NV-06, NV-08"],
  ["Thứ Sáu", "NV-01, NV-02, NV-05, NV-07", "NV-03, NV-04, NV-06, NV-08"],
  ["Thứ Bảy", "NV-01, NV-02, NV-03, NV-05, NV-07", "NV-04, NV-06, NV-08"],
  ["Chủ Nhật", "NV-01, NV-03, NV-04, NV-06, NV-07", "NV-02, NV-05, NV-08"],
];

const utilityRecords = fixedExpenses
  .filter((item) => item.category === "Điện nước")
  .map((item) => ({
    month: item.date.slice(0, 7),
    electricity: round1000(item.subtotal * 0.72),
    water: round1000(item.subtotal * 0.16),
    internet: item.subtotal - round1000(item.subtotal * 0.72) - round1000(item.subtotal * 0.16),
    vat_rate: item.vat_rate,
    invoice_id: item.invoice_id,
  }));

const centralData = {
  business,
  profile: profileDocument,
  development_plan: developmentPlan,
  cash_flow_ground_truth: cashFlowGroundTruth,
  menu,
  suppliers,
  sales,
  sales_invoices: salesInvoices,
  purchases,
  cashbook,
  staff,
  schedule,
  utilities: utilityRecords,
  reconciliation: {
    opening_cash: openingCash,
    total_sales: totalSales,
    total_purchases_and_expenses: totalPurchases,
    total_inflows: totalInflows,
    total_outflows: totalOutflows,
    ending_cash: endingCash,
  },
};

await fs.writeFile(path.join(outputDir, "01_ho_so_quan_ca_phe.json"), JSON.stringify(profileDocument, null, 2), "utf8");
await fs.writeFile(path.join(outputDir, "02_ke_hoach_phat_trien.json"), JSON.stringify(developmentPlan, null, 2), "utf8");
await fs.writeFile(
  path.join(outputDir, "06_thong_tin_dia_diem.json"),
  JSON.stringify(
    {
      business_id: business.business_id,
      address: business.address,
      latitude: business.latitude,
      longitude: business.longitude,
      area_m2: business.area_m2,
      seats: business.seats,
      monthly_rent: business.monthly_rent,
      deposit: business.deposit,
      opening_hours: business.opening_hours,
      delivery_radius_km: 4,
      parking: "Không có bãi xe riêng; sử dụng điểm gửi xe lân cận (thông tin mô phỏng)",
      operating_model: "Tại quán, mang đi và giao hàng",
      disclaimer: business.disclaimer,
    },
    null,
    2,
  ),
  "utf8",
);
await fs.writeFile(path.join(outputDir, "central_data.json"), JSON.stringify(centralData, null, 2), "utf8");
await fs.writeFile(
  path.join(outputDir, "ground_truth.json"),
  JSON.stringify(
    {
      dataset: "Góc Hồ Coffee - dữ liệu mô phỏng",
      generated_on: "2026-07-19",
      required_profile_fields: [
        "name", "industry", "stage", "location", "problem", "solution", "target_customers", "core_products",
        "revenue_model", "currency", "cash_as_of", "current_cash", "monthly_revenue", "fixed_monthly_costs", "variable_costs",
      ],
      profile: profileDocument,
      development_plan: developmentPlan,
      cash_flow: cashFlowGroundTruth,
      reconciliation: centralData.reconciliation,
    },
    null,
    2,
  ),
  "utf8",
);

function setTitle(sheet, lastCol, title, subtitle) {
  sheet.showGridLines = false;
  sheet.getRange(`A1:${lastCol}1`).merge();
  sheet.getRange("A1").values = [[title]];
  sheet.getRange("A1").format = {
    fill: COLORS.dark,
    font: { bold: true, color: COLORS.white, size: 18 },
    rowHeight: 32,
    verticalAlignment: "center",
  };
  sheet.getRange(`A2:${lastCol}2`).merge();
  sheet.getRange("A2").values = [[subtitle]];
  sheet.getRange("A2").format = {
    fill: COLORS.cream,
    font: { italic: true, color: COLORS.gray, size: 10 },
    rowHeight: 25,
    wrapText: true,
    verticalAlignment: "center",
  };
}

function styleHeader(range) {
  range.format = {
    fill: COLORS.green,
    font: { bold: true, color: COLORS.white },
    rowHeight: 28,
    verticalAlignment: "center",
    wrapText: true,
    borders: { preset: "inside", style: "thin", color: "#8DA89A" },
  };
}

function styleData(range) {
  range.format = {
    font: { color: COLORS.ink, size: 10 },
    borders: { preset: "inside", style: "thin", color: COLORS.line },
    verticalAlignment: "center",
  };
}

async function exportAndPreview(workbook, filename, previews) {
  for (const preview of previews) {
    const blob = await workbook.render({
      sheetName: preview.sheet,
      range: preview.range,
      scale: 1.2,
      format: "png",
    });
    await fs.writeFile(
      path.join(previewDir, `${filename.replace(".xlsx", "")}_${preview.sheet.replaceAll(" ", "_")}.png`),
      new Uint8Array(await blob.arrayBuffer()),
    );
  }
  const output = await SpreadsheetFile.exportXlsx(workbook);
  const outputPath = path.join(outputDir, filename);
  await output.save(outputPath);
  await fs.rm(`${outputPath}.inspect.ndjson`, { force: true });
}

function buildSalesWorkbook() {
  const wb = Workbook.create();
  const summary = wb.worksheets.add("Tóm tắt");
  const tx = wb.worksheets.add("Giao dịch");
  const menuSheet = wb.worksheets.add("Menu");

  setTitle(summary, "F", "DỮ LIỆU BÁN HÀNG - GÓC HỒ COFFEE", `${business.data_period.start} đến ${business.data_period.end} | VND | ${business.disclaimer}`);
  summary.getRange("A4:B9").values = [
    ["Chỉ tiêu", "Giá trị"],
    ["Tổng doanh thu thuần", null],
    ["Tổng số lượng bán", null],
    ["Giá trị bán trung bình/ngày", null],
    ["Số ngày dữ liệu", null],
    ["Số dòng dữ liệu", null],
  ];
  styleHeader(summary.getRange("A4:B4"));
  summary.getRange("B5").formulas = [[`=SUM('Giao dịch'!$J$5:$J$${sales.length + 4})`]];
  summary.getRange("B6").formulas = [[`=SUM('Giao dịch'!$F$5:$F$${sales.length + 4})`]];
  summary.getRange("B7").formulas = [["=B5/B8"]];
  summary.getRange("B8").values = [[91]];
  summary.getRange("B9").values = [[sales.length]];
  summary.getRange("B5:B7").setNumberFormat("#,##0;[Red](#,##0);-");
  summary.getRange("B8:B9").setNumberFormat("#,##0");
  summary.getRange("A4:B9").format.borders = { preset: "inside", style: "thin", color: COLORS.line };
  summary.getRange("A12:F16").values = [
    ["Tháng", "Từ ngày", "Đến ngày", "Doanh thu thuần", "Số lượng", "Ghi chú"],
    ["04/2026", dateUtc("2026-04-01"), dateUtc("2026-04-30"), null, null, "Tháng mở cửa"],
    ["05/2026", dateUtc("2026-05-01"), dateUtc("2026-05-31"), null, null, "Actual mô phỏng"],
    ["06/2026", dateUtc("2026-06-01"), dateUtc("2026-06-30"), null, null, "Actual mô phỏng"],
    ["Tổng", null, null, null, null, ""],
  ];
  styleHeader(summary.getRange("A12:F12"));
  for (let row = 13; row <= 15; row++) {
    summary.getRange(`D${row}`).formulas = [[`=SUMIFS('Giao dịch'!$J$5:$J$${sales.length + 4},'Giao dịch'!$A$5:$A$${sales.length + 4},">="&B${row},'Giao dịch'!$A$5:$A$${sales.length + 4},"<="&C${row})`]];
    summary.getRange(`E${row}`).formulas = [[`=SUMIFS('Giao dịch'!$F$5:$F$${sales.length + 4},'Giao dịch'!$A$5:$A$${sales.length + 4},">="&B${row},'Giao dịch'!$A$5:$A$${sales.length + 4},"<="&C${row})`]];
  }
  summary.getRange("D16").formulas = [["=SUM(D13:D15)"]];
  summary.getRange("E16").formulas = [["=SUM(E13:E15)"]];
  summary.getRange("B13:C15").setNumberFormat("yyyy-mm-dd");
  summary.getRange("D13:D16").setNumberFormat("#,##0;[Red](#,##0);-");
  summary.getRange("E13:E16").setNumberFormat("#,##0");
  summary.getRange("A16:F16").format = { font: { bold: true }, borders: { preset: "doubleBottom", style: "thin", color: COLORS.dark } };
  summary.getRange("A4:F16").format.columnWidth = 18;
  summary.getRange("A:A").format.columnWidth = 24;
  summary.getRange("F:F").format.columnWidth = 22;

  setTitle(tx, "M", "CHI TIẾT BÁN HÀNG THEO NGÀY VÀ SẢN PHẨM", `Dữ liệu đầu vào mô phỏng; cột Doanh thu gộp và Doanh thu thuần là công thức.`);
  const salesHeaders = ["Ngày", "Mã lô", "SKU", "Sản phẩm", "Nhóm", "Số lượng", "Đơn giá", "Giảm giá", "Doanh thu gộp", "Doanh thu thuần", "Kênh", "Thanh toán", "Chứng từ mẫu"];
  tx.getRange("A4:M4").values = [salesHeaders];
  styleHeader(tx.getRange("A4:M4"));
  const salesRows = sales.map((row) => [
    dateUtc(row.date), row.batch_id, row.sku, row.product, row.category, row.quantity, row.unit_price,
    row.discount_rate, null, null, row.channel, row.payment_method, row.evidence_ref,
  ]);
  tx.getRangeByIndexes(4, 0, salesRows.length, salesHeaders.length).values = salesRows;
  for (let index = 0; index < salesRows.length; index++) {
    const row = index + 5;
    tx.getRange(`I${row}`).formulas = [[`=F${row}*G${row}`]];
    tx.getRange(`J${row}`).formulas = [[`=ROUND(I${row}*(1-H${row}),0)`]];
  }
  const salesEnd = salesRows.length + 4;
  styleData(tx.getRange(`A5:M${salesEnd}`));
  tx.getRange(`A5:A${salesEnd}`).setNumberFormat("yyyy-mm-dd");
  tx.getRange(`F5:F${salesEnd}`).setNumberFormat("#,##0");
  tx.getRange(`G5:G${salesEnd}`).setNumberFormat("#,##0");
  tx.getRange(`H5:H${salesEnd}`).setNumberFormat("0.0%");
  tx.getRange(`I5:J${salesEnd}`).setNumberFormat("#,##0;[Red](#,##0);-");
  tx.getRange(`I5:J${salesEnd}`).format.font = { color: COLORS.formula };
  tx.freezePanes.freezeRows(4);
  tx.getRange("A:A").format.columnWidth = 12;
  tx.getRange("B:C").format.columnWidth = 18;
  tx.getRange("D:E").format.columnWidth = 20;
  tx.getRange("F:J").format.columnWidth = 14;
  tx.getRange("K:M").format.columnWidth = 18;

  setTitle(menuSheet, "F", "DANH MỤC SẢN PHẨM VÀ GIÁ BÁN", business.disclaimer);
  menuSheet.getRange("A4:F4").values = [["SKU", "Tên món", "Nhóm", "Giá niêm yết", "Số lượng cơ sở/ngày", "Trạng thái"]];
  styleHeader(menuSheet.getRange("A4:F4"));
  const menuRows = menu.map((item) => [item.sku, item.name, item.category, item.price, item.baseQty, "Đang bán"]);
  menuSheet.getRangeByIndexes(4, 0, menuRows.length, 6).values = menuRows;
  styleData(menuSheet.getRange(`A5:F${menuRows.length + 4}`));
  menuSheet.getRange(`D5:D${menuRows.length + 4}`).setNumberFormat("#,##0");
  menuSheet.getRange("A:F").format.columnWidth = 22;
  menuSheet.getRange("B:B").format.columnWidth = 26;
  return wb;
}

function buildPurchasesWorkbook() {
  const wb = Workbook.create();
  const summary = wb.worksheets.add("Tóm tắt");
  const tx = wb.worksheets.add("Mua hàng chi phí");
  const supplierSheet = wb.worksheets.add("Nhà cung cấp");
  setTitle(summary, "F", "MUA HÀNG VÀ CHI PHÍ - GÓC HỒ COFFEE", `${business.data_period.start} đến ${business.data_period.end} | ${business.disclaimer}`);
  summary.getRange("A4:B8").values = [
    ["Chỉ tiêu", "Giá trị"],
    ["Tổng trước VAT", null],
    ["Tổng VAT", null],
    ["Tổng thanh toán", null],
    ["Số chứng từ", purchases.length],
  ];
  styleHeader(summary.getRange("A4:B4"));
  const purchaseEnd = purchases.length + 4;
  summary.getRange("B5").formulas = [[`=SUM('Mua hàng chi phí'!$J$5:$J$${purchaseEnd})`]];
  summary.getRange("B6").formulas = [[`=SUM('Mua hàng chi phí'!$L$5:$L$${purchaseEnd})`]];
  summary.getRange("B7").formulas = [[`=SUM('Mua hàng chi phí'!$M$5:$M$${purchaseEnd})`]];
  summary.getRange("B5:B7").setNumberFormat("#,##0;[Red](#,##0);-");
  summary.getRange("A11:F15").values = [
    ["Tháng", "Từ ngày", "Đến ngày", "Trước VAT", "VAT", "Tổng thanh toán"],
    ["04/2026", dateUtc("2026-04-01"), dateUtc("2026-04-30"), null, null, null],
    ["05/2026", dateUtc("2026-05-01"), dateUtc("2026-05-31"), null, null, null],
    ["06/2026", dateUtc("2026-06-01"), dateUtc("2026-06-30"), null, null, null],
    ["Tổng", null, null, null, null, null],
  ];
  styleHeader(summary.getRange("A11:F11"));
  for (let row = 12; row <= 14; row++) {
    for (const [col, sourceCol] of [["D", "J"], ["E", "L"], ["F", "M"]]) {
      summary.getRange(`${col}${row}`).formulas = [[`=SUMIFS('Mua hàng chi phí'!$${sourceCol}$5:$${sourceCol}$${purchaseEnd},'Mua hàng chi phí'!$A$5:$A$${purchaseEnd},">="&B${row},'Mua hàng chi phí'!$A$5:$A$${purchaseEnd},"<="&C${row})`]];
    }
  }
  summary.getRange("D15").formulas = [["=SUM(D12:D14)"]];
  summary.getRange("E15").formulas = [["=SUM(E12:E14)"]];
  summary.getRange("F15").formulas = [["=SUM(F12:F14)"]];
  summary.getRange("B12:C14").setNumberFormat("yyyy-mm-dd");
  summary.getRange("D12:F15").setNumberFormat("#,##0;[Red](#,##0);-");
  summary.getRange("A15:F15").format = { font: { bold: true }, borders: { preset: "doubleBottom", style: "thin", color: COLORS.dark } };
  summary.getRange("A:F").format.columnWidth = 19;
  summary.getRange("A:A").format.columnWidth = 24;

  setTitle(tx, "P", "CHI TIẾT CHỨNG TỪ MUA HÀNG VÀ CHI PHÍ", "Đơn giá là dữ liệu đầu vào; Trước VAT, VAT và Tổng thanh toán là công thức trong workbook.");
  const headers = ["Ngày", "Mã chứng từ", "Mã NCC", "Nhà cung cấp", "Nhóm", "Nội dung", "ĐVT", "Số lượng", "Đơn giá", "Trước VAT", "VAT %", "VAT", "Tổng thanh toán", "Thanh toán", "Trạng thái", "Ghi chú"];
  tx.getRange("A4:P4").values = [headers];
  styleHeader(tx.getRange("A4:P4"));
  const rows = purchases.map((row) => [
    dateUtc(row.date), row.invoice_id, row.supplier_id, row.supplier, row.category, row.item, row.unit,
    row.quantity, row.unit_price, null, row.vat_rate, null, null, row.payment_method, row.payment_status,
    row.unit === "lô" || row.unit === "tháng" || row.unit === "gói" ? "Đơn giá áp dụng cho toàn đơn vị" : "",
  ]);
  tx.getRangeByIndexes(4, 0, rows.length, headers.length).values = rows;
  for (let index = 0; index < rows.length; index++) {
    const row = index + 5;
    tx.getRange(`J${row}`).formulas = [[`=H${row}*I${row}`]];
    tx.getRange(`L${row}`).formulas = [[`=J${row}*K${row}`]];
    tx.getRange(`M${row}`).formulas = [[`=J${row}+L${row}`]];
  }
  styleData(tx.getRange(`A5:P${purchaseEnd}`));
  tx.getRange(`A5:A${purchaseEnd}`).setNumberFormat("yyyy-mm-dd");
  tx.getRange(`H5:H${purchaseEnd}`).setNumberFormat("#,##0");
  tx.getRange(`I5:J${purchaseEnd}`).setNumberFormat("#,##0;[Red](#,##0);-");
  tx.getRange(`K5:K${purchaseEnd}`).setNumberFormat("0.0%");
  tx.getRange(`L5:M${purchaseEnd}`).setNumberFormat("#,##0;[Red](#,##0);-");
  tx.freezePanes.freezeRows(4);
  tx.getRange("A:C").format.columnWidth = 17;
  tx.getRange("D:D").format.columnWidth = 34;
  tx.getRange("E:F").format.columnWidth = 25;
  tx.getRange("G:O").format.columnWidth = 14;
  tx.getRange("P:P").format.columnWidth = 28;

  setTitle(supplierSheet, "D", "DANH MỤC NHÀ CUNG CẤP MÔ PHỎNG", business.disclaimer);
  supplierSheet.getRange("A4:D4").values = [["Mã NCC", "Tên", "Nhóm", "Trạng thái"]];
  styleHeader(supplierSheet.getRange("A4:D4"));
  const supplierRows = suppliers.map((item) => [item.id, item.name, item.category, "Đang sử dụng"]);
  supplierSheet.getRangeByIndexes(4, 0, supplierRows.length, 4).values = supplierRows;
  styleData(supplierSheet.getRange(`A5:D${supplierRows.length + 4}`));
  supplierSheet.getRange("A:D").format.columnWidth = 28;
  return wb;
}

function buildCashbookWorkbook() {
  const wb = Workbook.create();
  const summary = wb.worksheets.add("Tóm tắt");
  const tx = wb.worksheets.add("Sổ thu chi");
  const checks = wb.worksheets.add("Kiểm tra");
  setTitle(summary, "F", "SỔ THU CHI - GÓC HỒ COFFEE", `${business.data_period.start} đến ${business.data_period.end} | Actual mô phỏng | VND`);
  summary.getRange("A4:B10").values = [
    ["Chỉ tiêu", "Giá trị"],
    ["Số dư đầu kỳ", openingCash],
    ["Tổng tiền vào", null],
    ["Tổng tiền ra", null],
    ["Dòng tiền thuần", null],
    ["Số dư cuối kỳ", null],
    ["Trạng thái kiểm tra", null],
  ];
  styleHeader(summary.getRange("A4:B4"));
  const cashEnd = cashbook.length + 4;
  summary.getRange("B6").formulas = [[`=SUM('Sổ thu chi'!$G$5:$G$${cashEnd})`]];
  summary.getRange("B7").formulas = [[`=SUM('Sổ thu chi'!$H$5:$H$${cashEnd})`]];
  summary.getRange("B8").formulas = [["=B6-B7"]];
  summary.getRange("B9").formulas = [[`='Sổ thu chi'!$J$${cashEnd}`]];
  summary.getRange("B10").formulas = [[`='Kiểm tra'!$E$8`]];
  summary.getRange("B5:B9").setNumberFormat("#,##0;[Red](#,##0);-");
  summary.getRange("B5").format.font = { color: COLORS.input };
  summary.getRange("B6:B10").format.font = { color: COLORS.formula };
  summary.getRange("A4:B10").format.borders = { preset: "inside", style: "thin", color: COLORS.line };
  summary.getRange("A:A").format.columnWidth = 28;
  summary.getRange("B:B").format.columnWidth = 22;
  summary.getRange("A13:F17").values = [
    ["Tháng", "Từ ngày", "Đến ngày", "Tiền vào", "Tiền ra", "Thuần"],
    ["04/2026", dateUtc("2026-04-01"), dateUtc("2026-04-30"), null, null, null],
    ["05/2026", dateUtc("2026-05-01"), dateUtc("2026-05-31"), null, null, null],
    ["06/2026", dateUtc("2026-06-01"), dateUtc("2026-06-30"), null, null, null],
    ["Tổng", null, null, null, null, null],
  ];
  styleHeader(summary.getRange("A13:F13"));
  for (let row = 14; row <= 16; row++) {
    summary.getRange(`D${row}`).formulas = [[`=SUMIFS('Sổ thu chi'!$G$5:$G$${cashEnd},'Sổ thu chi'!$A$5:$A$${cashEnd},">="&B${row},'Sổ thu chi'!$A$5:$A$${cashEnd},"<="&C${row})`]];
    summary.getRange(`E${row}`).formulas = [[`=SUMIFS('Sổ thu chi'!$H$5:$H$${cashEnd},'Sổ thu chi'!$A$5:$A$${cashEnd},">="&B${row},'Sổ thu chi'!$A$5:$A$${cashEnd},"<="&C${row})`]];
    summary.getRange(`F${row}`).formulas = [[`=D${row}-E${row}`]];
  }
  summary.getRange("D17").formulas = [["=SUM(D14:D16)"]];
  summary.getRange("E17").formulas = [["=SUM(E14:E16)"]];
  summary.getRange("F17").formulas = [["=SUM(F14:F16)"]];
  summary.getRange("B14:C16").setNumberFormat("yyyy-mm-dd");
  summary.getRange("D14:F17").setNumberFormat("#,##0;[Red](#,##0);-");
  summary.getRange("A17:F17").format = { font: { bold: true }, borders: { preset: "doubleBottom", style: "thin", color: COLORS.dark } };
  summary.getRange("A:F").format.columnWidth = 18;
  summary.getRange("A:A").format.columnWidth = 28;

  setTitle(tx, "K", "CHI TIẾT SỔ THU CHI", "Tiền thuần và số dư chạy là công thức. Số dư đầu kỳ được lấy từ sheet Tóm tắt.");
  const headers = ["Ngày", "Mã giao dịch", "Loại", "Nhóm", "Diễn giải", "Tài khoản", "Tiền vào", "Tiền ra", "Thuần", "Số dư chạy", "Chứng từ nguồn"];
  tx.getRange("A4:K4").values = [headers];
  styleHeader(tx.getRange("A4:K4"));
  const rows = cashbook.map((row) => [
    dateUtc(row.date), row.transaction_id, row.type, row.category, row.description, row.account,
    row.inflow, row.outflow, null, null, row.source_ref,
  ]);
  tx.getRangeByIndexes(4, 0, rows.length, headers.length).values = rows;
  for (let index = 0; index < rows.length; index++) {
    const row = index + 5;
    tx.getRange(`I${row}`).formulas = [[`=G${row}-H${row}`]];
    tx.getRange(`J${row}`).formulas = [[index === 0 ? `='Tóm tắt'!$B$5+I${row}` : `=J${row - 1}+I${row}`]];
  }
  styleData(tx.getRange(`A5:K${cashEnd}`));
  tx.getRange(`A5:A${cashEnd}`).setNumberFormat("yyyy-mm-dd");
  tx.getRange(`G5:J${cashEnd}`).setNumberFormat("#,##0;[Red](#,##0);-");
  tx.getRange(`I5:J${cashEnd}`).format.font = { color: COLORS.formula };
  tx.freezePanes.freezeRows(4);
  tx.getRange("A:D").format.columnWidth = 17;
  tx.getRange("E:E").format.columnWidth = 38;
  tx.getRange("F:K").format.columnWidth = 17;

  setTitle(checks, "G", "KIỂM TRA ĐỐI SOÁT", "PASS chỉ có nghĩa dữ liệu mô phỏng tự khớp về số học, không phải xác nhận kiểm toán.");
  checks.getRange("A4:G4").values = [["Kiểm tra", "Thực tế", "Kỳ vọng", "Chênh lệch", "Trạng thái", "Nơi sửa", "Ghi chú"]];
  styleHeader(checks.getRange("A4:G4"));
  checks.getRange("A5:C8").values = [
    ["Tổng doanh thu bán hàng", null, totalSales],
    ["Tổng tiền ra khớp chứng từ chi", null, totalPurchases],
    ["Số dư cuối kỳ", null, endingCash],
    ["MODEL STATUS", null, null],
  ];
  checks.getRange("B5").formulas = [[`=SUMIFS('Sổ thu chi'!$G$5:$G$${cashEnd},'Sổ thu chi'!$D$5:$D$${cashEnd},"Bán hàng")`]];
  checks.getRange("B6").formulas = [[`=SUM('Sổ thu chi'!$H$5:$H$${cashEnd})`]];
  checks.getRange("B7").formulas = [[`='Sổ thu chi'!$J$${cashEnd}`]];
  checks.getRange("D5").formulas = [["=B5-C5"]];
  checks.getRange("D6").formulas = [["=B6-C6"]];
  checks.getRange("D7").formulas = [["=B7-C7"]];
  checks.getRange("E5").formulas = [["=IF(ABS(D5)<=1,\"OK\",\"FAIL\")"]];
  checks.getRange("E6").formulas = [["=IF(ABS(D6)<=1,\"OK\",\"FAIL\")"]];
  checks.getRange("E7").formulas = [["=IF(ABS(D7)<=1,\"OK\",\"FAIL\")"]];
  checks.getRange("E8").formulas = [["=IF(COUNTIF(E5:E7,\"FAIL\")=0,\"PASS\",\"FAIL\")"]];
  checks.getRange("F5:G8").values = [
    ["Sổ thu chi - nhóm Bán hàng", "Khớp dữ liệu bán hàng trung tâm"],
    ["Sổ thu chi - Tiền ra", "Khớp mua hàng và chi phí"],
    ["Sổ thu chi - Số dư chạy", "Đầu kỳ + vào - ra"],
    ["Các dòng phía trên", "Tất cả kiểm tra phải OK"],
  ];
  checks.getRange("B5:D7").setNumberFormat("#,##0;[Red](#,##0);-");
  checks.getRange("A4:G8").format.borders = { preset: "inside", style: "thin", color: COLORS.line };
  checks.getRange("A:G").format.columnWidth = 23;
  checks.getRange("A:A").format.columnWidth = 34;
  checks.getRange("F:G").format.columnWidth = 30;
  return wb;
}

function buildOperationsWorkbook() {
  const wb = Workbook.create();
  const profile = wb.worksheets.add("Địa điểm");
  const staffSheet = wb.worksheets.add("Nhân sự lịch ca");
  const utilitySheet = wb.worksheets.add("Điện nước");
  setTitle(profile, "D", "ĐỊA ĐIỂM VÀ VẬN HÀNH - GÓC HỒ COFFEE", business.disclaimer);
  const profileRows = [
    ["Trường", "Giá trị", "Đơn vị", "Ghi chú"],
    ["Địa chỉ", business.address, "", "Địa chỉ mô phỏng gần Hồ Hoàn Kiếm"],
    ["Vĩ độ", business.latitude, "độ", "Tọa độ xấp xỉ cho dữ liệu demo"],
    ["Kinh độ", business.longitude, "độ", "Tọa độ xấp xỉ cho dữ liệu demo"],
    ["Diện tích", business.area_m2, "m2", "Một tầng"],
    ["Số chỗ ngồi", business.seats, "chỗ", "Trong nhà và mặt tiền"],
    ["Giá thuê/tháng", business.monthly_rent, "VND", "Thanh toán đầu tháng"],
    ["Tiền đặt cọc", business.deposit, "VND", "3 tháng tiền thuê"],
    ["Giờ hoạt động", business.opening_hours, "", "Mỗi ngày"],
    ["Bán kính giao hàng", 4, "km", "Thông tin mô phỏng"],
    ["Nhân sự", business.employees, "người", "Bao gồm quản lý"],
    ["Chỗ để xe", "Không có bãi riêng", "", "Dùng điểm gửi xe lân cận"],
  ];
  profile.getRangeByIndexes(3, 0, profileRows.length, 4).values = profileRows;
  styleHeader(profile.getRange("A4:D4"));
  styleData(profile.getRange(`A5:D${profileRows.length + 3}`));
  profile.getRange("B10:B11").setNumberFormat("#,##0;[Red](#,##0);-");
  profile.getRange("A:A").format.columnWidth = 24;
  profile.getRange("B:B").format.columnWidth = 55;
  profile.getRange("C:C").format.columnWidth = 14;
  profile.getRange("D:D").format.columnWidth = 32;
  profile.getRange(`B5:B${profileRows.length + 3}`).format.font = { color: COLORS.input };

  setTitle(staffSheet, "F", "NHÂN SỰ VÀ LỊCH CA TUẦN MẪU", business.disclaimer);
  staffSheet.getRange("A4:C4").values = [["Mã NV", "Tên mô phỏng", "Vai trò"]];
  styleHeader(staffSheet.getRange("A4:C4"));
  const staffRows = staff.map((item) => [item.id, item.name, item.role]);
  staffSheet.getRangeByIndexes(4, 0, staffRows.length, 3).values = staffRows;
  styleData(staffSheet.getRange(`A5:C${staffRows.length + 4}`));
  staffSheet.getRange("A14:C14").values = [["Ngày", "Ca sáng 07:00-15:00", "Ca chiều 14:00-22:00"]];
  styleHeader(staffSheet.getRange("A14:C14"));
  staffSheet.getRangeByIndexes(14, 0, schedule.length, 3).values = schedule;
  styleData(staffSheet.getRange(`A15:C${schedule.length + 14}`));
  staffSheet.getRange("A:A").format.columnWidth = 18;
  staffSheet.getRange("B:C").format.columnWidth = 42;

  setTitle(utilitySheet, "H", "CHI PHÍ ĐIỆN NƯỚC VÀ INTERNET", "Các thành phần và VAT được tính bằng công thức.");
  utilitySheet.getRange("A4:H4").values = [["Tháng", "Điện", "Nước", "Internet", "Trước VAT", "VAT %", "VAT", "Tổng thanh toán"]];
  styleHeader(utilitySheet.getRange("A4:H4"));
  const utilityRows = utilityRecords.map((item) => [item.month, item.electricity, item.water, item.internet, null, item.vat_rate, null, null]);
  utilitySheet.getRangeByIndexes(4, 0, utilityRows.length, 8).values = utilityRows;
  for (let index = 0; index < utilityRows.length; index++) {
    const row = index + 5;
    utilitySheet.getRange(`E${row}`).formulas = [[`=SUM(B${row}:D${row})`]];
    utilitySheet.getRange(`G${row}`).formulas = [[`=E${row}*F${row}`]];
    utilitySheet.getRange(`H${row}`).formulas = [[`=E${row}+G${row}`]];
  }
  const utilityEnd = utilityRows.length + 4;
  styleData(utilitySheet.getRange(`A5:H${utilityEnd}`));
  utilitySheet.getRange(`B5:E${utilityEnd}`).setNumberFormat("#,##0;[Red](#,##0);-");
  utilitySheet.getRange(`F5:F${utilityEnd}`).setNumberFormat("0.0%");
  utilitySheet.getRange(`G5:H${utilityEnd}`).setNumberFormat("#,##0;[Red](#,##0);-");
  utilitySheet.getRange("A:H").format.columnWidth = 18;
  return wb;
}

const workbooks = [
  {
    filename: "03_du_lieu_ban_hang_3_thang.xlsx",
    workbook: buildSalesWorkbook(),
    previews: [
      { sheet: "Tóm tắt", range: "A1:F16" },
      { sheet: "Giao dịch", range: "A1:M24" },
      { sheet: "Menu", range: "A1:F14" },
    ],
  },
  {
    filename: "04_mua_hang_va_chi_phi_3_thang.xlsx",
    workbook: buildPurchasesWorkbook(),
    previews: [
      { sheet: "Tóm tắt", range: "A1:F15" },
      { sheet: "Mua hàng chi phí", range: "A1:P24" },
      { sheet: "Nhà cung cấp", range: "A1:D12" },
    ],
  },
  {
    filename: "05_so_thu_chi_3_thang.xlsx",
    workbook: buildCashbookWorkbook(),
    previews: [
      { sheet: "Tóm tắt", range: "A1:F17" },
      { sheet: "Sổ thu chi", range: "A1:K24" },
      { sheet: "Kiểm tra", range: "A1:G8" },
    ],
  },
  {
    filename: "06_dia_diem_va_van_hanh.xlsx",
    workbook: buildOperationsWorkbook(),
    previews: [
      { sheet: "Địa điểm", range: "A1:D16" },
      { sheet: "Nhân sự lịch ca", range: "A1:F21" },
      { sheet: "Điện nước", range: "A1:H8" },
    ],
  },
];

for (const item of workbooks) {
  const keyInspect = await item.workbook.inspect({
    kind: "sheet,formula",
    maxChars: 4500,
    tableMaxRows: 8,
    tableMaxCols: 10,
    options: { maxResults: 80 },
  });
  console.log(`INSPECT ${item.filename}\n${keyInspect.ndjson}`);
  const errors = await item.workbook.inspect({
    kind: "match",
    searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
    options: { useRegex: true, maxResults: 100 },
    summary: `formula errors ${item.filename}`,
  });
  console.log(`ERROR_SCAN ${item.filename}\n${errors.ndjson}`);
  await exportAndPreview(item.workbook, item.filename, item.previews);
}

await fs.writeFile(
  path.join(outputDir, "manifest.json"),
  JSON.stringify(
    {
      dataset: "Góc Hồ Coffee - dữ liệu mô phỏng",
      generated_on: "2026-07-19",
      period: business.data_period,
      currency: "VND",
      files: [
        "01_ho_so_quan_ca_phe.json",
        "02_ke_hoach_phat_trien.json",
        "03_du_lieu_ban_hang_3_thang.xlsx",
        "04_mua_hang_va_chi_phi_3_thang.xlsx",
        "05_so_thu_chi_3_thang.xlsx",
        "06_thong_tin_dia_diem.json",
        "06_dia_diem_va_van_hanh.xlsx",
        "ground_truth.json",
        "central_data.json",
      ],
      reconciliation: centralData.reconciliation,
      disclaimer: business.disclaimer,
    },
    null,
    2,
  ),
  "utf8",
);

await fs.writeFile(
  path.join(outputDir, "README.md"),
  `# Góc Hồ Coffee — bộ dữ liệu mô phỏng\n\n` +
    `Bộ dữ liệu bằng chứng cho luồng startup và nhà đầu tư. Toàn bộ tên, mã, giao dịch và chứng từ đều là dữ liệu mô phỏng.\n\n` +
    `## Cách dùng\n\n` +
    `1. Tải các tệp JSON, XLSX và PDF trong thư mục này lên tab **Bằng chứng**.\n` +
    `2. Duyệt đề xuất để điền Hồ sơ, Dòng tiền và Kế hoạch phát triển.\n` +
    `3. Dùng \`ground_truth.json\` để đối chiếu test; không tải \`central_data.json\` hoặc \`ground_truth.json\` như bằng chứng người dùng.\n\n` +
    `## Kết quả đối soát kỳ 01/04/2026–30/06/2026\n\n` +
    `- Doanh thu thuần: ${totalSales.toLocaleString("vi-VN")} VND\n` +
    `- Tổng tiền vào: ${totalInflows.toLocaleString("vi-VN")} VND\n` +
    `- Tổng tiền ra: ${totalOutflows.toLocaleString("vi-VN")} VND\n` +
    `- Tiền cuối kỳ: ${endingCash.toLocaleString("vi-VN")} VND\n` +
    `- Doanh thu trung bình tháng: ${Math.round(monthlyRevenue).toLocaleString("vi-VN")} VND\n` +
    `- Chi phí cố định trung bình tháng: ${Math.round(fixedMonthlyCosts).toLocaleString("vi-VN")} VND\n` +
    `- Chi phí biến đổi trung bình tháng: ${Math.round(variableCosts).toLocaleString("vi-VN")} VND\n\n` +
    `Các chỉ số \`monthly_expense\` và \`variable_cost_ratio\` là dữ liệu được tính, không phải trường nhập trực tiếp.\n`,
  "utf8",
);

console.log(JSON.stringify({ outputDir, previewDir, reconciliation: centralData.reconciliation }, null, 2));
