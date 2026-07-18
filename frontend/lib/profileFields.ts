export type ProfileFieldType = "text" | "textarea" | "number" | "list" | "select" | "date";

export type ProfileField = {
  key: string;
  label: string;
  type?: ProfileFieldType;
  placeholder?: string;
  helper?: string;
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

export type ProfileFieldGroup = {
  id: string;
  title: string;
  description?: string;
  fieldKeys: string[];
};

export const stageOptions = ["Pre-seed", "Seed", "Series A", "Growth"];

export const industryOptions = ["F&B", "Bán lẻ"];

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
    title: "Khách hàng và mô hình kinh doanh",
    description: "Dữ kiện cốt lõi cho F&B và bán lẻ nhỏ. Không nhập số dư tiền hay dữ liệu khu vực tại đây.",
    fields: [
      {
        key: "problem",
        label: "Nhu cầu hoặc vấn đề của khách hàng",
        type: "textarea",
        rows: 3,
        placeholder: "Ví dụ: nhân viên văn phòng cần bữa trưa nhanh, ổn định và vừa túi tiền.",
      },
      {
        key: "solution",
        label: "Giải pháp cửa hàng cung cấp",
        type: "textarea",
        rows: 3,
        placeholder: "Mô tả sản phẩm, trải nghiệm hoặc cách phục vụ giải quyết nhu cầu trên.",
      },
      {
        key: "target_customers",
        label: "Nhóm khách hàng mục tiêu",
        type: "list",
        placeholder: "Nhân viên văn phòng, sinh viên, hộ gia đình",
        helper: "Phân tách các nhóm bằng dấu phẩy.",
      },
      {
        key: "core_products",
        label: "Sản phẩm chủ lực",
        type: "list",
        placeholder: "Cà phê pha máy, trà trái cây, bánh ngọt",
        helper: "Phân tách các sản phẩm bằng dấu phẩy.",
      },
      {
        key: "customer_purchase_occasions",
        label: "Dịp và lý do mua hàng",
        type: "textarea",
        rows: 2,
        placeholder: "Bữa sáng, nghỉ trưa, mua mang đi, mua bổ sung hằng tuần...",
      },
      {
        key: "differentiation",
        label: "Giá trị khác biệt",
        type: "textarea",
        rows: 2,
        placeholder: "Điểm khiến khách hàng chọn cửa hàng thay vì phương án khác.",
      },
      {
        key: "revenue_model",
        label: "Nguồn doanh thu",
        type: "list",
        placeholder: "Bán tại cửa hàng, giao hàng, đơn doanh nghiệp",
        helper: "Chỉ mô tả nguồn thu; dòng tiền theo kỳ nhập ở phần Cash Flow.",
      },
      {
        key: "sales_channels",
        label: "Kênh bán hàng",
        type: "list",
        placeholder: "Tại cửa hàng, GrabFood, ShopeeFood, website",
      },
      {
        key: "pricing_model",
        label: "Cách định giá",
        type: "textarea",
        rows: 2,
        placeholder: "Theo món, combo, theo trọng lượng, giá thành viên...",
      },
      {
        key: "average_order_value",
        label: "Giá trị đơn trung bình (VND)",
        type: "number",
        placeholder: "85000",
        helper: "Dùng cho unit economics cấp đơn hàng, không phải doanh thu tháng.",
      },
      {
        key: "variable_cost_per_order",
        label: "Chi phí biến đổi trung bình/đơn (VND)",
        type: "number",
        placeholder: "42000",
        helper: "Nguyên liệu, bao bì, phí nền tảng và chi phí tăng theo từng đơn.",
      },
      {
        key: "traction",
        label: "Bằng chứng sức hút hiện tại",
        type: "textarea",
        rows: 3,
        placeholder: "Số đơn, số khách quay lại, sản phẩm bán chạy hoặc kết quả thử nghiệm; ghi rõ kỳ dữ liệu.",
      },
      {
        key: "competitors",
        label: "Đối thủ hoặc mô hình tương tự",
        type: "list",
        placeholder: "Tên thương hiệu hoặc loại cửa hàng cạnh tranh",
        helper: "Chỉ nhập đối thủ đã biết; mật độ và khoảng cách do Surrounding Area xử lý.",
      },
      {
        key: "market_size",
        label: "Cơ sở ước tính thị trường",
        type: "textarea",
        rows: 3,
        placeholder: "Số khách hàng mục tiêu, tần suất mua, mức chi tiêu và nguồn số liệu.",
      },
      {
        key: "key_suppliers_partners",
        label: "Nhà cung cấp và đối tác chính",
        type: "list",
        placeholder: "Nhà cung cấp nguyên liệu, nền tảng giao hàng, đơn vị vận chuyển",
      },
    ],
  },
  {
    id: "quick-development",
    eyebrow: "DEVELOPMENT PLAN",
    title: "Kế hoạch phát triển",
    description: "Đánh giá hướng đi, khả năng nhân rộng, milestone và mức sẵn sàng thực thi.",
    fields: [
      {
        key: "planning_horizon_months",
        label: "Thời hạn kế hoạch (tháng)",
        type: "number",
        placeholder: "12",
      },
      {
        key: "development_objectives",
        label: "Mục tiêu phát triển",
        type: "textarea",
        rows: 3,
        placeholder: "Mục tiêu, giá trị hiện tại, giá trị cần đạt và thời hạn.",
      },
      {
        key: "product_plan",
        label: "Kế hoạch sản phẩm/danh mục",
        type: "textarea",
        rows: 3,
        placeholder: "Sản phẩm mới, nhóm khách hàng phục vụ và cách đo kết quả.",
      },
      {
        key: "customer_growth_plan",
        label: "Kế hoạch phát triển khách hàng",
        type: "textarea",
        rows: 3,
        placeholder: "Giữ chân, khách hàng thân thiết, phân khúc mới và chỉ số thành công.",
      },
      {
        key: "channel_expansion_plan",
        label: "Kế hoạch mở rộng kênh bán",
        type: "textarea",
        rows: 3,
        placeholder: "Kênh mới, mục tiêu, giai đoạn thử nghiệm và điều kiện cần.",
      },
      {
        key: "outlet_expansion_plan",
        label: "Kế hoạch mở rộng điểm bán",
        type: "textarea",
        rows: 3,
        placeholder: "Số điểm dự kiến, loại cửa hàng, thời hạn và tiêu chí lựa chọn.",
        helper: "Việc chọn địa điểm cụ thể thuộc Surrounding Area.",
      },
      {
        key: "operating_capability_plan",
        label: "Năng lực vận hành cần chuẩn hóa",
        type: "textarea",
        rows: 3,
        placeholder: "SOP, đào tạo, kiểm soát chất lượng, tồn kho hoặc năng lực cung ứng.",
      },
      {
        key: "development_milestones",
        label: "Milestone và tiêu chí hoàn thành",
        type: "textarea",
        rows: 3,
        placeholder: "Mỗi milestone nên có thời hạn và kết quả đo được.",
      },
      {
        key: "development_dependencies",
        label: "Phụ thuộc và rủi ro chính",
        type: "textarea",
        rows: 3,
        placeholder: "Nhân sự, nhà cung cấp, giấy phép, tài chính hoặc giả định chưa kiểm chứng.",
      },
    ],
  },
  {
    id: "quick-finance",
    eyebrow: "CASH FLOW · MODULE RIÊNG",
    title: "Dòng tiền",
    description: "Chỉ dành cho Cash Flow Analysis; Business Model không sử dụng để tính burn hoặc runway.",
    fields: [
      { key: "current_cash", label: "Tiền mặt hiện có (VND)", type: "number", placeholder: "500000000" },
      { key: "minimum_cash_buffer", label: "Minimum cash buffer (VND)", type: "number", placeholder: "150000000" },
      { key: "fixed_monthly_costs", label: "Fixed monthly costs (VND)", type: "number", placeholder: "80000000" },
      { key: "variable_cost_ratio", label: "Variable-cost ratio", type: "number", placeholder: "0.45" },
      { key: "accounts_receivable", label: "Accounts receivable (VND)", type: "number", placeholder: "0" },
      { key: "accounts_payable", label: "Accounts payable (VND)", type: "number", placeholder: "0" },
      { key: "inventory", label: "Inventory (VND)", type: "number", placeholder: "0" },
      {
        key: "financial_periods",
        label: "Dòng tiền theo kỳ",
        type: "textarea",
        rows: 4,
        placeholder: "2026-01, 100000000, 160000000\n2026-02, 120000000, 155000000",
        helper: "Mỗi dòng: kỳ, tiền vào, tiền ra. Các kỳ phải có cùng độ dài.",
      },
    ],
  },
  {
    id: "quick-location",
    eyebrow: "SURROUNDING AREA · MODULE RIÊNG",
    title: "Địa điểm và khu vực",
    description: "Thông tin đầu vào để geocode và kiểm chứng các tuyên bố về khu vực.",
    fields: [
      {
        key: "exact_location",
        label: "Địa chỉ chính xác",
        type: "textarea",
        rows: 2,
        placeholder: "Số nhà, đường, phường/xã, tỉnh/thành phố",
        helper: "Tọa độ vẫn cần được chuyên viên xác nhận trên bản đồ trước khi phân tích.",
      },
      {
        key: "location_dependency",
        label: "Mức phụ thuộc lượng khách xung quanh",
        type: "select",
        options: locationDependencyOptions,
      },
      {
        key: "target_customer_radius_m",
        label: "Bán kính khách hàng mục tiêu (m)",
        type: "number",
        placeholder: "1000",
      },
      {
        key: "area_claims",
        label: "Tuyên bố cần kiểm chứng",
        type: "list",
        placeholder: "Chưa có đối thủ trong 500m, khu vực đông văn phòng",
        helper: "Phân tách các tuyên bố bằng dấu phẩy.",
      },
      {
        key: "known_nearby_competitors",
        label: "Đối thủ gần đó đã biết",
        type: "list",
        placeholder: "Highlands Coffee, cửa hàng tiện lợi A",
      },
    ],
  },
];

export const quickCreateFieldGroups: Record<string, ProfileFieldGroup[]> = {
  "quick-business": [
    {
      id: "customer",
      title: "Khách hàng và nhu cầu",
      description: "Xác định ai mua, họ cần gì và mua trong hoàn cảnh nào.",
      fieldKeys: ["problem", "target_customers", "customer_purchase_occasions"],
    },
    {
      id: "offering",
      title: "Sản phẩm và giá trị khác biệt",
      description: "Mô tả sản phẩm chủ lực và lý do khách hàng lựa chọn.",
      fieldKeys: ["solution", "core_products", "differentiation"],
    },
    {
      id: "commercial-model",
      title: "Doanh thu, kênh bán và unit economics",
      description: "Dữ liệu ở cấp mô hình hoặc đơn hàng; không phải dòng tiền theo tháng.",
      fieldKeys: [
        "revenue_model",
        "sales_channels",
        "pricing_model",
        "average_order_value",
        "variable_cost_per_order",
      ],
    },
    {
      id: "market-evidence",
      title: "Thị trường, cạnh tranh và bằng chứng",
      description: "Cơ sở kiểm chứng sức hút, quy mô thị trường và các phụ thuộc chính.",
      fieldKeys: ["traction", "competitors", "market_size", "key_suppliers_partners"],
    },
  ],
  "quick-development": [
    {
      id: "growth-direction",
      title: "Mục tiêu và hướng phát triển",
      description: "Kế hoạch phát triển sản phẩm, khách hàng, kênh bán và điểm bán.",
      fieldKeys: [
        "planning_horizon_months",
        "development_objectives",
        "product_plan",
        "customer_growth_plan",
        "channel_expansion_plan",
        "outlet_expansion_plan",
      ],
    },
    {
      id: "execution-readiness",
      title: "Mức sẵn sàng thực thi",
      description: "Năng lực cần chuẩn hóa, milestone, phụ thuộc và rủi ro.",
      fieldKeys: ["operating_capability_plan", "development_milestones", "development_dependencies"],
    },
  ],
  "quick-finance": [
    {
      id: "cash-position",
      title: "Số dư và dòng tiền theo kỳ",
      description: "Dữ liệu đầu vào riêng cho Cash Flow Analysis.",
      fieldKeys: ["current_cash", "minimum_cash_buffer", "financial_periods"],
    },
    {
      id: "break-even",
      title: "Hòa vốn và chi phí",
      description: "Dùng để tính doanh thu hòa vốn và mức đệm tiền mặt cần duy trì.",
      fieldKeys: ["fixed_monthly_costs", "variable_cost_ratio"],
    },
    {
      id: "working-capital",
      title: "Vốn lưu động",
      description: "Các khoản phải thu, phải trả và tồn kho hỗ trợ đánh giá nhu cầu vốn lưu động.",
      fieldKeys: ["accounts_receivable", "accounts_payable", "inventory"],
    },
  ],
  "quick-location": [
    {
      id: "location-profile",
      title: "Địa điểm kinh doanh",
      description: "Địa chỉ và mức phụ thuộc vào khách hàng xung quanh.",
      fieldKeys: ["exact_location", "location_dependency", "target_customer_radius_m"],
    },
    {
      id: "area-claims",
      title: "Tuyên bố và đối thủ đã biết",
      description: "Những thông tin Surrounding Area cần kiểm chứng bằng dữ liệu bản đồ.",
      fieldKeys: ["area_claims", "known_nearby_competitors"],
    },
  ],
};

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
      { key: "minimum_cash_buffer", label: "Mức đệm tiền mặt tối thiểu", type: "number" },
      { key: "fixed_monthly_costs", label: "Định phí hàng tháng", type: "number" },
      {
        key: "variable_cost_ratio",
        label: "Tỷ lệ biến phí",
        type: "number",
        placeholder: "0.45",
        helper: "Nhập từ 0 đến 1, ví dụ 0.45 tương đương 45%.",
      },
      { key: "monthly_revenue", label: "Doanh thu trung bình tháng", type: "number" },
      { key: "monthly_expense", label: "Chi phí trung bình tháng", type: "number" },
      { key: "fixed_costs", label: "Chi phí cố định", type: "number" },
      { key: "variable_costs", label: "Chi phí biến đổi", type: "number" },
      { key: "accounts_receivable", label: "Khoản phải thu", type: "number" },
      { key: "accounts_payable", label: "Khoản phải trả", type: "number" },
      { key: "inventory", label: "Tồn kho", type: "number" },
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

export function parseRatioValue(raw: string) {
  const normalized = raw.trim().replace(",", ".");
  const value = Number(normalized);
  return Number.isFinite(value) && value >= 0 && value <= 1 ? value : null;
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
    if (field.key === "variable_cost_ratio") return parseRatioValue(raw) ?? undefined;
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
