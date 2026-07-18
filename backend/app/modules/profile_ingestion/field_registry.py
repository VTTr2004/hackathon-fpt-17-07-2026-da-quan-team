from dataclasses import dataclass


@dataclass(frozen=True)
class ProfileFieldDefinition:
    key: str
    label: str
    description: str
    value_type: str = "text"
    target: str = "facts"
    keywords: tuple[str, ...] = ()
    max_length: int = 5000


FIELD_REGISTRY: dict[str, ProfileFieldDefinition] = {
    item.key: item
    for item in (
        ProfileFieldDefinition(
            "name",
            "Tên startup",
            "Tên chính thức hoặc tên thương mại của startup.",
            target="startup",
            keywords=("tên doanh nghiệp", "tên startup", "company name", "thương hiệu"),
            max_length=255,
        ),
        ProfileFieldDefinition(
            "industry",
            "Lĩnh vực",
            "Ngành hoặc lĩnh vực kinh doanh chính.",
            target="startup",
            keywords=("lĩnh vực", "ngành", "industry", "sector"),
            max_length=120,
        ),
        ProfileFieldDefinition(
            "stage",
            "Giai đoạn",
            "Giai đoạn phát triển hoặc gọi vốn: Pre-seed, Seed, Series A hoặc Growth.",
            value_type="stage",
            target="startup",
            keywords=("giai đoạn", "stage", "pre-seed", "seed", "series a", "growth"),
            max_length=80,
        ),
        ProfileFieldDefinition(
            "primary_location",
            "Địa điểm chính",
            "Địa chỉ hoặc địa điểm hoạt động chính được nêu trực tiếp trong tài liệu.",
            target="startup",
            keywords=("địa chỉ", "địa điểm", "trụ sở", "location", "address", "headquarters"),
            max_length=500,
        ),
        ProfileFieldDefinition(
            "business_type",
            "Loại hình kinh doanh",
            "Loại hình hoặc mô hình vận hành của doanh nghiệp.",
            keywords=("loại hình", "mô hình", "business type", "hộ kinh doanh", "công ty"),
        ),
        ProfileFieldDefinition(
            "founded_date",
            "Ngày bắt đầu hoạt động",
            "Ngày doanh nghiệp bắt đầu hoạt động hoặc ngày khai trương.",
            keywords=("ngày bắt đầu", "ngày khai trương", "opened_on", "founded date", "thành lập"),
        ),
        ProfileFieldDefinition(
            "employee_count",
            "Số lượng nhân sự",
            "Tổng số nhân sự hoặc nhân viên đang làm việc.",
            keywords=("nhân sự", "nhân viên", "employees", "employee count"),
        ),
        ProfileFieldDefinition(
            "problem",
            "Vấn đề khách hàng",
            "Vấn đề hoặc nhu cầu cụ thể của khách hàng mà startup giải quyết.",
            keywords=("vấn đề", "nhu cầu", "pain point", "problem", "challenge"),
        ),
        ProfileFieldDefinition(
            "solution",
            "Giải pháp",
            "Sản phẩm, dịch vụ hoặc cách startup giải quyết vấn đề.",
            keywords=("giải pháp", "sản phẩm", "dịch vụ", "solution", "product", "service"),
        ),
        ProfileFieldDefinition(
            "core_products",
            "Sản phẩm/dịch vụ chính",
            "Danh sách sản phẩm hoặc dịch vụ chính được startup cung cấp.",
            value_type="list",
            keywords=("sản phẩm", "dịch vụ", "đồ uống", "product", "service", "menu"),
        ),
        ProfileFieldDefinition(
            "differentiation",
            "Giá trị khác biệt",
            "Điểm khác biệt khiến khách hàng chọn startup thay cho phương án khác.",
            keywords=("khác biệt", "lợi thế", "unique", "differentiation", "advantage"),
        ),
        ProfileFieldDefinition(
            "target_customers",
            "Khách hàng mục tiêu",
            "Các nhóm khách hàng mục tiêu được nêu trong tài liệu.",
            value_type="list",
            keywords=("khách hàng mục tiêu", "phân khúc", "target customer", "customer segment", "persona"),
        ),
        ProfileFieldDefinition(
            "revenue_model",
            "Nguồn doanh thu",
            "Cách doanh nghiệp tạo doanh thu hoặc cơ chế thu tiền.",
            value_type="list",
            keywords=("doanh thu", "nguồn thu", "revenue_channels", "revenue model", "monetization", "pricing"),
        ),
        ProfileFieldDefinition(
            "sales_channels",
            "Kênh bán hàng",
            "Danh sách kênh mà startup sử dụng để bán sản phẩm hoặc dịch vụ.",
            value_type="list",
            keywords=("kênh bán", "tại quán", "mang đi", "giao hàng", "sales channel", "revenue_channels"),
        ),
        ProfileFieldDefinition(
            "traction",
            "Traction",
            "Kết quả, tăng trưởng, khách hàng hoặc chỉ số vận hành đã đạt được.",
            keywords=("traction", "tăng trưởng", "khách hàng", "doanh số", "kết quả", "milestone"),
        ),
    )
}

DEFAULT_FIELD_KEYS = tuple(FIELD_REGISTRY)
SCHEMA_VERSION = "profile-v1"
