export type ProfileFieldType = "text" | "textarea" | "number" | "list" | "select" | "date";

export type ProfileField = {
  key: string;
  label: string;
  type?: ProfileFieldType;
  placeholder?: string;
  rows?: number;
  options?: string[];
};

export type ProfileSection = {
  id: string;
  eyebrow: string;
  title: string;
  description: string;
  fields: ProfileField[];
};

export const stageOptions = ["Pre-seed", "Seed", "Series A", "Growth"];

export const operatingScopeOptions = ["Địa phương", "Toàn quốc", "Quốc tế"];

export const businessTypeOptions = [
  "Hộ kinh doanh",
  "Công ty TNHH",
  "Công ty cổ phần",
  "Hợp tác xã",
  "Khác",
];

export const locationTypeOptions = ["Văn phòng", "Cửa hàng", "Nhà máy", "Kho", "Hybrid", "Khác"];

export const tenureOptions = ["Thuê", "Sở hữu", "Đối tác cung cấp", "Chưa cố định"];

export const locationDependencyOptions = [
  "Phụ thuộc lượng khách xung quanh",
  "Vị trí hỗ trợ vận hành",
  "Không phụ thuộc vị trí",
  "Chưa xác định",
];

export const quickCreateFields: ProfileSection[] = [
  {
    id: "quick-business",
    eyebrow: "BUSINESS MODEL",
    title: "Mô hình kinh doanh",
    description: "Những dữ kiện cốt lõi để chạy business model và định hướng phân tích.",
    fields: [
      { key: "problem", label: "Bài toán kinh doanh", type: "textarea", rows: 3 },
      { key: "solution", label: "Giải pháp", type: "textarea", rows: 3 },
      { key: "target_customers", label: "Khách hàng mục tiêu", type: "list" },
      { key: "core_products", label: "Sản phẩm/dịch vụ chính", type: "list" },
      { key: "revenue_model", label: "Nguồn doanh thu", type: "list" },
      { key: "sales_channels", label: "Kênh bán hàng", type: "list" },
    ],
  },
  {
    id: "quick-finance",
    eyebrow: "FINANCE",
    title: "Tài chính ban đầu",
    description: "Các số liệu tối thiểu để cash-flow module có điểm bắt đầu.",
    fields: [
      { key: "current_cash", label: "Tiền mặt hiện có", type: "number" },
      { key: "monthly_revenue", label: "Doanh thu trung bình tháng", type: "number" },
      { key: "monthly_expense", label: "Chi phí trung bình tháng", type: "number" },
    ],
  },
];

export const profileSections: ProfileSection[] = [
  {
    id: "startup-info",
    eyebrow: "STARTUP",
    title: "Thông tin startup",
    description: "Thông tin định danh, quy mô và phạm vi hoạt động của doanh nghiệp.",
    fields: [
      { key: "founded_date", label: "Ngày bắt đầu hoạt động", type: "date" },
      { key: "business_type", label: "Loại hình doanh nghiệp", type: "select", options: businessTypeOptions },
      { key: "employee_count", label: "Số lượng nhân sự", type: "number" },
      { key: "headquarters_address", label: "Địa chỉ trụ sở", type: "textarea", rows: 2 },
      { key: "facility_address", label: "Địa chỉ cửa hàng/nhà máy/kho", type: "textarea", rows: 2 },
      { key: "operating_scope", label: "Phạm vi hoạt động", type: "select", options: operatingScopeOptions },
    ],
  },
  {
    id: "business-model",
    eyebrow: "BUSINESS MODEL",
    title: "Mô hình kinh doanh",
    description: "Dữ kiện cho module mô hình kinh doanh và phần giải thích của Gemini.",
    fields: [
      { key: "problem", label: "Bài toán kinh doanh", type: "textarea", rows: 3 },
      { key: "problem_owner", label: "Đối tượng gặp vấn đề", type: "textarea", rows: 2 },
      { key: "solution", label: "Giải pháp startup cung cấp", type: "textarea", rows: 3 },
      { key: "differentiation", label: "Giá trị khác biệt", type: "textarea", rows: 2 },
      { key: "market_size", label: "Quy mô thị trường", type: "textarea", rows: 2 },
      { key: "target_customers", label: "Khách hàng mục tiêu", type: "list" },
      { key: "users_and_payers", label: "Người sử dụng và người trả tiền", type: "textarea", rows: 2 },
      { key: "core_products", label: "Sản phẩm/dịch vụ chính", type: "list" },
      { key: "pricing_model", label: "Cách định giá", type: "textarea", rows: 2 },
      { key: "revenue_model", label: "Nguồn doanh thu", type: "list" },
      { key: "sales_channels", label: "Kênh bán hàng", type: "list" },
      { key: "acquisition_channels", label: "Kênh tiếp cận khách hàng", type: "list" },
      { key: "competitors", label: "Đối thủ", type: "list" },
      { key: "alternatives", label: "Phương án thay thế", type: "list" },
      { key: "key_suppliers_partners", label: "Nhà cung cấp và đối tác chính", type: "list" },
      { key: "traction", label: "Traction", type: "textarea", rows: 3 },
      { key: "expansion_plan", label: "Kế hoạch mở rộng", type: "textarea", rows: 3 },
      { key: "fundraising_need", label: "Nhu cầu gọi vốn và mục đích sử dụng", type: "textarea", rows: 3 },
    ],
  },
  {
    id: "finance",
    eyebrow: "FINANCE",
    title: "Tài chính và dòng tiền",
    description: "Dữ liệu đầu vào cho runway, burn rate, biên lợi nhuận và dự báo 6-12 tháng.",
    fields: [
      { key: "current_cash", label: "Tiền mặt hiện có", type: "number" },
      { key: "monthly_revenue", label: "Doanh thu trung bình tháng", type: "number" },
      { key: "monthly_expense", label: "Chi phí trung bình tháng", type: "number" },
      { key: "fixed_costs", label: "Chi phí cố định", type: "number" },
      { key: "variable_costs", label: "Chi phí biến đổi", type: "number" },
      { key: "accounts_receivable", label: "Khoản phải thu", type: "number" },
      { key: "accounts_payable", label: "Khoản phải trả", type: "number" },
      { key: "debt_obligations", label: "Khoản vay và nghĩa vụ trả nợ", type: "textarea", rows: 2 },
      { key: "average_price", label: "Giá bán trung bình", type: "number" },
      { key: "unit_cost", label: "Chi phí tạo ra một sản phẩm/dịch vụ", type: "number" },
      { key: "cac", label: "CAC", type: "number" },
      { key: "churn_retention", label: "Churn hoặc retention", type: "textarea", rows: 2 },
      { key: "forecast_6_12_months", label: "Dự kiến doanh thu/chi phí 6-12 tháng", type: "textarea", rows: 3 },
      { key: "forecast_assumptions", label: "Giả định dùng để dự báo", type: "textarea", rows: 3 },
      {
        key: "financial_periods",
        label: "Dòng tiền theo tháng",
        type: "textarea",
        rows: 4,
        placeholder: "2026-01, 100000000, 160000000",
      },
    ],
  },
  {
    id: "location",
    eyebrow: "LOCATION",
    title: "Địa điểm và vận hành",
    description: "Thông tin phục vụ surrounding area, vận hành, logistics và đánh giá phụ thuộc vị trí.",
    fields: [
      { key: "exact_location", label: "Địa chỉ chính xác hoặc tọa độ", type: "textarea", rows: 2 },
      { key: "location_type", label: "Loại địa điểm", type: "select", options: locationTypeOptions },
      { key: "area_m2", label: "Diện tích sử dụng (m2)", type: "number" },
      { key: "tenure", label: "Thuê hay sở hữu", type: "select", options: tenureOptions },
      { key: "rent_cost", label: "Chi phí thuê", type: "number" },
      { key: "operating_hours", label: "Thời gian hoạt động", type: "text" },
      {
        key: "location_dependency",
        label: "Mức phụ thuộc lượng khách xung quanh",
        type: "select",
        options: locationDependencyOptions,
      },
      { key: "target_customer_radius_m", label: "Bán kính khách hàng mục tiêu (m)", type: "number" },
      { key: "logistics_requirements", label: "Yêu cầu giao thông/logistics/nguồn cung", type: "textarea", rows: 3 },
      { key: "known_nearby_competitors", label: "Địa điểm cạnh tranh đã biết", type: "list" },
    ],
  },
];

export const documentChecklist = [
  {
    title: "Pháp lý",
    items: [
      "Giấy đăng ký doanh nghiệp",
      "Giấy phép chuyên ngành",
      "Đăng ký thuế",
      "Điều lệ công ty",
      "Cap table/cổ đông",
      "Góp vốn",
      "Giấy phép địa điểm",
      "Sở hữu trí tuệ",
      "Hợp đồng công nghệ",
      "An toàn thực phẩm/môi trường/PCCC",
      "Xử phạt, tranh chấp hoặc nghĩa vụ pháp lý",
    ],
  },
  {
    title: "Bán hàng và doanh thu",
    items: [
      "Hóa đơn bán hàng",
      "Phiếu thu",
      "Đơn đặt hàng",
      "Hợp đồng khách hàng",
      "Biên bản nghiệm thu",
      "Báo giá/bảng giá",
      "Báo cáo POS",
      "Xuất dữ liệu sàn TMĐT",
      "Doanh thu theo sản phẩm/khách hàng/khu vực",
      "Danh sách khách hàng đã ẩn thông tin",
      "Hoàn hàng, hủy đơn, chiết khấu",
      "LOI, MoU hoặc hợp đồng thử nghiệm",
    ],
  },
  {
    title: "Mua hàng và chi phí",
    items: [
      "Hóa đơn mua hàng",
      "Phiếu chi",
      "Đơn mua hàng",
      "Hợp đồng nhà cung cấp",
      "Báo giá nhà cung cấp",
      "Biên bản giao nhận",
      "Nguyên vật liệu",
      "Vận chuyển/logistics",
      "Điện, nước, internet",
      "Phần mềm/dịch vụ",
      "Marketing",
      "Thuê mặt bằng",
      "Bảo trì máy móc thiết bị",
    ],
  },
  {
    title: "Kế toán và dòng tiền",
    items: [
      "Sao kê ngân hàng",
      "Sổ quỹ tiền mặt",
      "Nhật ký thu-chi",
      "Kết quả kinh doanh",
      "Bảng cân đối kế toán",
      "Lưu chuyển tiền tệ",
      "Sổ cái/tổng hợp tài khoản",
      "Công nợ phải thu",
      "Công nợ phải trả",
      "Tờ khai thuế/VAT",
      "Khoản vay và lịch trả nợ",
      "Bảng lương",
      "Ngân sách và dự báo dòng tiền",
    ],
  },
  {
    title: "Địa điểm và vận hành",
    items: [
      "Hợp đồng thuê địa điểm",
      "Quyền sử dụng/sở hữu địa điểm",
      "Biên lai tiền thuê",
      "Sơ đồ mặt bằng",
      "Hình ảnh địa điểm",
      "Máy móc và tài sản",
      "Kho bãi/vận chuyển",
      "Nhà cung cấp",
      "Tồn kho",
      "Công suất vận hành",
      "Lượng khách theo ngày/giờ",
      "Dữ liệu giao hàng/vùng phục vụ",
      "Quy hoạch, môi trường và an toàn",
    ],
  },
];

export function textValue(form: FormData, key: string) {
  return String(form.get(key) ?? "").trim();
}

export function listValue(form: FormData, key: string) {
  return textValue(form, key)
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

export function parseNumberValue(raw: string) {
  const normalized = raw.replace(/[,. ]/g, "");
  const value = Number(normalized);
  return Number.isFinite(value) ? value : null;
}

export function parsePeriods(raw: string) {
  return raw
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const [period, inflow, outflow] = line.split(",").map((part) => part.trim());
      const inflowValue = parseNumberValue(inflow ?? "");
      const outflowValue = parseNumberValue(outflow ?? "");
      return inflowValue !== null && outflowValue !== null ? { period, inflow: inflowValue, outflow: outflowValue } : null;
    })
    .filter((row): row is { period: string; inflow: number; outflow: number } => Boolean(row?.period));
}

export function readProfileField(form: FormData, field: ProfileField) {
  const raw = textValue(form, field.key);
  if (!raw) return undefined;

  if (field.key === "financial_periods") {
    const periods = parsePeriods(raw);
    return periods.length ? periods : undefined;
  }

  if (field.type === "list") {
    const items = listValue(form, field.key);
    return items.length ? items : undefined;
  }

  if (field.type === "number") {
    return parseNumberValue(raw) ?? undefined;
  }

  return raw;
}

export function formatPeriods(value: unknown) {
  if (!Array.isArray(value)) return "";
  return value
    .map((item) => {
      if (!item || typeof item !== "object") return "";
      const row = item as Record<string, unknown>;
      return [row.period, row.inflow, row.outflow].filter((part) => part !== undefined && part !== null).join(", ");
    })
    .filter(Boolean)
    .join("\n");
}

export function formatProfileValue(field: ProfileField, value: unknown) {
  if (field.key === "financial_periods") return formatPeriods(value);
  if (Array.isArray(value)) return value.map(String).join(", ");
  if (typeof value === "number") return String(value);
  return typeof value === "string" ? value : "";
}
