from dataclasses import dataclass
from typing import Any, Literal

Priority = Literal["required", "major", "optional"]


@dataclass(frozen=True)
class InterviewField:
    key: str
    label: str
    description: str
    priority: Priority = "optional"
    value_type: str = "text"
    target: str = "facts"
    options: tuple[str, ...] = ()


def _field(
    key: str,
    label: str,
    description: str,
    *,
    priority: Priority = "optional",
    value_type: str = "text",
    target: str = "facts",
    options: tuple[str, ...] = (),
) -> InterviewField:
    return InterviewField(key, label, description, priority, value_type, target, options)


INTERVIEW_FIELDS: dict[str, InterviewField] = {
    item.key: item
    for item in (
        _field("name", "Tên startup", "Tên chính thức hoặc tên thương mại.", priority="required", target="startup"),
        _field("industry", "Lĩnh vực", "Ngành kinh doanh chính.", priority="required", target="startup"),
        _field(
            "stage",
            "Giai đoạn",
            "Giai đoạn phát triển hoặc gọi vốn.",
            priority="required",
            target="startup",
            value_type="select",
            options=("Pre-seed", "Seed", "Series A", "Growth"),
        ),
        _field(
            "primary_location", "Địa điểm chính xác", "Địa chỉ hoạt động chính.", priority="required", target="startup"
        ),
        _field("problem", "Bài toán kinh doanh", "Vấn đề hoặc nhu cầu khách hàng.", priority="required"),
        _field("solution", "Giải pháp", "Sản phẩm, dịch vụ hoặc cách giải quyết.", priority="required"),
        _field(
            "target_customers",
            "Khách hàng mục tiêu",
            "Các nhóm khách hàng mục tiêu.",
            priority="required",
            value_type="list",
        ),
        _field(
            "core_products",
            "Sản phẩm/dịch vụ chính",
            "Các sản phẩm hoặc dịch vụ chính.",
            priority="required",
            value_type="list",
        ),
        _field(
            "revenue_model",
            "Nguồn doanh thu",
            "Cách doanh nghiệp tạo doanh thu.",
            priority="required",
            value_type="list",
        ),
        _field(
            "currency",
            "Đơn vị tiền tệ",
            "Đơn vị dùng cho các số liệu tài chính.",
            priority="required",
            value_type="select",
            options=("VND", "USD"),
        ),
        _field(
            "cash_as_of", "Ngày chốt số dư", "Ngày áp dụng của số dư tiền mặt.", priority="required", value_type="date"
        ),
        _field(
            "current_cash",
            "Tiền mặt hiện có",
            "Số tiền mặt hiện có tại ngày chốt.",
            priority="required",
            value_type="number",
        ),
        _field(
            "monthly_revenue",
            "Doanh thu trung bình tháng",
            "Doanh thu trung bình mỗi tháng.",
            priority="required",
            value_type="number",
        ),
        _field(
            "fixed_monthly_costs",
            "Chi phí cố định",
            "Tổng chi phí cố định mỗi tháng.",
            priority="required",
            value_type="number",
        ),
        _field(
            "variable_costs",
            "Chi phí biến đổi",
            "Tổng chi phí biến đổi mỗi tháng.",
            priority="required",
            value_type="number",
        ),
        _field("differentiation", "Giá trị khác biệt", "Điểm khác biệt so với lựa chọn thay thế.", priority="major"),
        _field("pricing_model", "Cách định giá", "Cách đặt giá sản phẩm hoặc dịch vụ.", priority="major"),
        _field("sales_channels", "Kênh bán hàng", "Các kênh bán hàng hiện tại.", priority="major", value_type="list"),
        _field(
            "acquisition_channels",
            "Kênh tiếp cận khách hàng",
            "Các kênh thu hút khách hàng.",
            priority="major",
            value_type="list",
        ),
        _field("traction", "Traction", "Kết quả tăng trưởng hoặc vận hành đã đạt.", priority="major"),
        _field(
            "minimum_cash_buffer",
            "Mức đệm tiền mặt tối thiểu",
            "Mức tiền tối thiểu cần duy trì.",
            priority="major",
            value_type="number",
        ),
        _field(
            "accounts_receivable",
            "Khoản phải thu",
            "Tổng khoản phải thu hiện tại.",
            priority="major",
            value_type="number",
        ),
        _field(
            "accounts_payable", "Khoản phải trả", "Tổng khoản phải trả hiện tại.", priority="major", value_type="number"
        ),
        _field("debt_obligations", "Khoản vay và nghĩa vụ trả nợ", "Các khoản vay và lịch trả nợ.", priority="major"),
        _field("development_objectives", "Mục tiêu phát triển", "Các mục tiêu phát triển chính.", priority="major"),
        _field("development_milestones", "Milestone phát triển", "Milestone và tiêu chí hoàn thành.", priority="major"),
        _field("founded_date", "Ngày bắt đầu hoạt động", "Ngày thành lập hoặc bắt đầu hoạt động.", value_type="date"),
        _field("business_type", "Loại hình doanh nghiệp", "Loại hình pháp lý hoặc vận hành."),
        _field("employee_count", "Số lượng nhân sự", "Tổng số nhân sự hiện tại.", value_type="integer"),
        _field("operating_scope", "Phạm vi hoạt động", "Phạm vi địa lý hoặc vận hành."),
        _field("problem_owner", "Đối tượng gặp vấn đề", "Người trực tiếp gặp vấn đề."),
        _field("market_size", "Quy mô thị trường", "Ước lượng thị trường nếu người dùng nêu rõ."),
        _field("customer_purchase_occasions", "Dịp và lý do mua hàng", "Bối cảnh khách hàng mua hoặc sử dụng."),
        _field("users_and_payers", "Người sử dụng và người trả tiền", "Phân biệt người dùng và người thanh toán."),
        _field("average_order_value", "Giá trị đơn trung bình", "Giá trị trung bình mỗi đơn.", value_type="number"),
        _field("competitors", "Đối thủ", "Các đối thủ hoặc lựa chọn thay thế.", value_type="list"),
        _field(
            "key_suppliers_partners",
            "Nhà cung cấp và đối tác",
            "Các nhà cung cấp hoặc đối tác chính.",
            value_type="list",
        ),
        _field("fundraising_need", "Nhu cầu gọi vốn", "Số vốn cần gọi và mục đích sử dụng."),
        _field("monthly_rent", "Tiền thuê hàng tháng", "Chi phí thuê hàng tháng.", value_type="number"),
        _field("lease_deposit", "Tiền đặt cọc", "Tiền đặt cọc mặt bằng.", value_type="number"),
        _field("inventory", "Tồn kho", "Giá trị tồn kho hiện tại.", value_type="number"),
        _field("unit_cost", "Chi phí đơn vị", "Chi phí tạo một sản phẩm hoặc dịch vụ.", value_type="number"),
        _field("cac", "CAC", "Chi phí thu hút một khách hàng.", value_type="number"),
        _field("churn_retention", "Churn hoặc retention", "Tỷ lệ rời bỏ hoặc giữ chân."),
        _field("forecast_6_12_months", "Dự báo 6–12 tháng", "Dự kiến doanh thu và chi phí."),
        _field("forecast_assumptions", "Giả định dự báo", "Các giả định dùng cho dự báo."),
        _field("planning_horizon_months", "Thời hạn kế hoạch", "Số tháng của kế hoạch.", value_type="integer"),
        _field("product_plan", "Kế hoạch sản phẩm", "Kế hoạch phát triển sản phẩm."),
        _field("customer_growth_plan", "Kế hoạch khách hàng", "Kế hoạch phát triển khách hàng."),
        _field("channel_expansion_plan", "Kế hoạch mở rộng kênh", "Kế hoạch mở rộng kênh bán."),
        _field("outlet_expansion_plan", "Kế hoạch mở rộng điểm bán", "Kế hoạch mở rộng địa điểm."),
        _field("operating_capability_plan", "Kế hoạch năng lực vận hành", "Năng lực cần xây dựng."),
        _field("development_dependencies", "Phụ thuộc và rủi ro", "Các phụ thuộc và rủi ro chính."),
    )
}

REQUIRED_INTERVIEW_KEYS = tuple(key for key, field in INTERVIEW_FIELDS.items() if field.priority == "required")


def has_value(value: Any) -> bool:
    if isinstance(value, (list, dict)):
        return bool(value)
    return value is not None and str(value).strip() != ""
