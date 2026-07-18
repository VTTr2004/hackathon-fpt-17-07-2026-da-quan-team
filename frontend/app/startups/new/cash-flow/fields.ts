import type { ProfileFieldGroup, ProfileSection } from "@/lib/profileFields";

export const cashFlowSections: ProfileSection[] = [
  {
    id: "cash-ledger",
    eyebrow: "CASH POSITION & LEDGER",
    title: "Số dư và lịch sử dòng tiền",
    description: "Số dư dùng để đối soát; dữ liệu theo kỳ dùng để tính burn, runway và xu hướng dòng tiền.",
    fields: [
      { key: "currency", label: "Đơn vị tiền tệ", type: "select", options: ["VND", "USD"] },
      { key: "cash_as_of", label: "Ngày chốt số dư", type: "date" },
      {
        key: "opening_cash",
        label: "Số dư tiền đầu kỳ (VND)",
        type: "number",
        placeholder: "380000000",
        helper: "Dùng để đối chiếu: đầu kỳ + tổng thu - tổng chi = cuối kỳ.",
      },
      {
        key: "reported_ending_cash",
        label: "Số dư tiền cuối kỳ theo sổ (VND)",
        type: "number",
        placeholder: "439372410",
      },
      {
        key: "current_cash",
        label: "Tiền mặt hiện có (VND)",
        type: "number",
        placeholder: "500000000",
        helper: "Dùng làm số dư hiện tại khi sổ chưa cung cấp số dư cuối kỳ.",
      },
      {
        key: "minimum_cash_buffer",
        label: "Mức đệm tiền mặt tối thiểu (VND)",
        type: "number",
        placeholder: "150000000",
        helper: "Mức tiền tối thiểu doanh nghiệp muốn luôn duy trì.",
      },
      {
        key: "financial_periods",
        label: "Dòng tiền hoạt động theo kỳ",
        type: "textarea",
        rows: 6,
        placeholder: "2026-01, 100000000, 160000000\n2026-02, 120000000, 155000000",
        helper: "Mỗi dòng: YYYY-MM, tiền vào, tiền ra. Nếu có sổ chi tiết, hãy tải Excel ở khu vực phía trên.",
      },
    ],
  },
  {
    id: "cash-costs",
    eyebrow: "COST & BREAK-EVEN",
    title: "Chi phí vận hành và hòa vốn",
    description: "Tool dùng định phí và tỷ lệ biến phí để tính doanh thu hòa vốn; các dữ kiện vận hành hỗ trợ giải thích chi phí.",
    fields: [
      {
        key: "fixed_monthly_costs",
        label: "Tổng chi phí cố định hàng tháng (VND)",
        type: "number",
        placeholder: "80000000",
      },
      {
        key: "variable_cost_ratio",
        label: "Tỷ lệ chi phí biến đổi",
        type: "number",
        placeholder: "0.45",
        helper: "Nhập từ 0 đến 1; ví dụ 0.45 tương đương 45% doanh thu.",
      },
      { key: "monthly_rent", label: "Tiền thuê hàng tháng (VND)", type: "number", placeholder: "70000000" },
      { key: "lease_deposit", label: "Tiền đặt cọc mặt bằng (VND)", type: "number", placeholder: "210000000" },
      { key: "employee_count", label: "Số nhân viên hiện tại", type: "number", placeholder: "8" },
    ],
  },
  {
    id: "cash-working-capital",
    eyebrow: "WORKING CAPITAL",
    title: "Vốn lưu động và chu kỳ tiền",
    description: "Số dư phải thu, phải trả, tồn kho và dữ liệu kỳ giúp tool tính DSO, DPO và cash conversion cycle.",
    fields: [
      { key: "accounts_receivable", label: "Khoản phải thu (VND)", type: "number", placeholder: "0" },
      { key: "accounts_payable", label: "Khoản phải trả (VND)", type: "number", placeholder: "0" },
      { key: "inventory", label: "Giá trị tồn kho (VND)", type: "number", placeholder: "0" },
      {
        key: "working_capital_period_revenue",
        label: "Doanh thu trong kỳ vốn lưu động (VND)",
        type: "number",
        placeholder: "670000000",
      },
      {
        key: "working_capital_period_cogs",
        label: "Giá vốn trong kỳ (VND)",
        type: "number",
        placeholder: "360000000",
      },
      {
        key: "working_capital_period_days",
        label: "Số ngày của kỳ dữ liệu",
        type: "number",
        placeholder: "30",
        helper: "Ví dụ 30 ngày cho một tháng hoặc 90 ngày cho một quý.",
      },
    ],
  },
  {
    id: "cash-scenarios",
    eyebrow: "SCENARIO ASSUMPTIONS",
    title: "Giả định dự báo dòng tiền",
    description: "Các tỷ lệ này đi trực tiếp vào scenario tool; số âm là giảm, số dương là tăng so với kỳ gần nhất.",
    fields: [
      { key: "scenario_months", label: "Số tháng dự báo", type: "number", placeholder: "12" },
      {
        key: "best_inflow_change",
        label: "Best case – thay đổi tiền vào",
        type: "number",
        placeholder: "0.10",
        helper: "Ví dụ 0.10 là tăng 10%.",
      },
      {
        key: "best_outflow_change",
        label: "Best case – thay đổi tiền ra",
        type: "number",
        placeholder: "-0.05",
        helper: "Ví dụ -0.05 là giảm 5%.",
      },
      { key: "downside_inflow_change", label: "Downside – thay đổi tiền vào", type: "number", placeholder: "-0.15" },
      { key: "downside_outflow_change", label: "Downside – thay đổi tiền ra", type: "number", placeholder: "0.05" },
      { key: "severe_inflow_change", label: "Severe – thay đổi tiền vào", type: "number", placeholder: "-0.30" },
      { key: "severe_outflow_change", label: "Severe – thay đổi tiền ra", type: "number", placeholder: "0.15" },
    ],
  },
];

export const cashFlowGroups: Record<string, ProfileFieldGroup[]> = {
  "cash-ledger": [
    {
      id: "reporting-scope",
      title: "Phạm vi báo cáo",
      description: "Đơn vị tiền và ngày chốt số liệu.",
      fieldKeys: ["currency", "cash_as_of"],
    },
    {
      id: "cash-position",
      title: "Số dư và mức an toàn",
      description: "Các số dư phục vụ đối soát và xác định thời điểm cần bổ sung vốn.",
      fieldKeys: ["opening_cash", "reported_ending_cash", "current_cash", "minimum_cash_buffer"],
    },
    {
      id: "period-ledger",
      title: "Dòng tiền theo kỳ",
      description: "Dữ liệu tối thiểu cần hai kỳ để đánh giá xu hướng đáng tin cậy hơn.",
      fieldKeys: ["financial_periods"],
    },
  ],
  "cash-costs": [
    {
      id: "break-even-inputs",
      title: "Đầu vào tính hòa vốn",
      fieldKeys: ["fixed_monthly_costs", "variable_cost_ratio"],
    },
    {
      id: "operating-context",
      title: "Bối cảnh chi phí vận hành",
      fieldKeys: ["monthly_rent", "lease_deposit", "employee_count"],
    },
  ],
  "cash-working-capital": [
    {
      id: "working-capital-balances",
      title: "Số dư vốn lưu động",
      fieldKeys: ["accounts_receivable", "accounts_payable", "inventory"],
    },
    {
      id: "working-capital-period",
      title: "Mẫu số của kỳ tính toán",
      description: "Cần đủ doanh thu, giá vốn và số ngày để tính toàn bộ DSO/DPO/CCC.",
      fieldKeys: ["working_capital_period_revenue", "working_capital_period_cogs", "working_capital_period_days"],
    },
  ],
  "cash-scenarios": [
    {
      id: "forecast-horizon",
      title: "Thời hạn dự báo",
      fieldKeys: ["scenario_months"],
    },
    {
      id: "best-case",
      title: "Best case",
      fieldKeys: ["best_inflow_change", "best_outflow_change"],
    },
    {
      id: "downside-case",
      title: "Downside",
      fieldKeys: ["downside_inflow_change", "downside_outflow_change"],
    },
    {
      id: "severe-case",
      title: "Severe stress",
      fieldKeys: ["severe_inflow_change", "severe_outflow_change"],
    },
  ],
};
