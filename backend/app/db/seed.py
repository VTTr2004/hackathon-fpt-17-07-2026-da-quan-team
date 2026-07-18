"""Idempotent sample data used by demo deployments."""

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.startup import Startup
from app.models.startup_access import StartupAccess
from app.models.startup_version import StartupVersion
from app.models.user import User

SAMPLE_STARTUP_EMAIL = "startup.demo@startuplens.vn"
SAMPLE_INVESTOR_EMAIL = "investor.demo@startuplens.vn"
SAMPLE_STARTUP_NAME = "Lotus Fresh Kitchen"

SAMPLE_FACTS = {
    "problem": "Nhân viên văn phòng cần bữa trưa lành mạnh, giao nhanh và có mức giá ổn định.",
    "solution": "Suất ăn theo thực đơn tuần, đặt trước trên web và giao theo khung giờ cố định.",
    "target_customers": ["Nhân viên văn phòng", "Doanh nghiệp 20-200 nhân sự"],
    "core_products": ["Suất ăn trưa cân bằng", "Gói ăn theo tuần", "Catering văn phòng"],
    "customer_purchase_occasions": "Bữa trưa ngày làm việc và sự kiện nội bộ quy mô nhỏ.",
    "differentiation": "Thực đơn công khai dinh dưỡng, giao theo tuyến và đổi món mỗi tuần.",
    "revenue_model": ["Bán lẻ theo suất", "Gói thuê bao tuần", "Hợp đồng doanh nghiệp"],
    "sales_channels": ["Website", "Zalo", "Bán trực tiếp cho doanh nghiệp"],
    "pricing_model": "69.000-89.000 VND mỗi suất; giảm 8% cho gói năm ngày.",
    "average_order_value": 78000,
    "variable_cost_per_order": 39000,
    "traction": "Trung bình 115 đơn/ngày trong quý 2/2026; 42% khách mua lại trong 30 ngày.",
    "competitors": ["Cơm văn phòng địa phương", "Bếp Healthy Box"],
    "market_size": "Thử nghiệm tập trung vào khoảng 18.000 nhân viên tại các tòa nhà trong bán kính 3 km.",
    "key_suppliers_partners": ["Nông trại rau Đà Lạt", "Đơn vị giao hàng nội thành"],
    "planning_horizon_months": 12,
    "development_objectives": "Đạt 220 đơn/ngày và tỷ lệ mua lại 55% trước tháng 6/2027.",
    "product_plan": "Thử nghiệm hai thực đơn chay và đo tỷ lệ đặt lại sau bốn tuần.",
    "customer_growth_plan": "Chương trình giới thiệu và bán gói theo phòng ban tại 10 tòa nhà.",
    "channel_expansion_plan": "Thử nghiệm kênh doanh nghiệp trong ba tháng, dừng nếu CAC vượt 180.000 VND.",
    "outlet_expansion_plan": "Chỉ mở bếp thứ hai khi bếp hiện tại duy trì trên 180 đơn/ngày trong ba tháng.",
    "operating_capability_plan": (
        "Chuẩn hóa định lượng món, kiểm tra nhiệt độ giao nhận và dự báo nguyên liệu hằng ngày."
    ),
    "development_milestones": "Q3/2026: 150 đơn/ngày; Q4/2026: 5 hợp đồng doanh nghiệp; Q2/2027: 220 đơn/ngày.",
    "development_dependencies": "Phụ thuộc năng lực bếp giờ cao điểm, giá nguyên liệu và hai đối tác giao hàng.",
    "current_cash": 920000000,
    "minimum_cash_buffer": 300000000,
    "fixed_monthly_costs": 245000000,
    "variable_cost_ratio": 0.5,
    "accounts_receivable": 85000000,
    "accounts_payable": 62000000,
    "inventory": 48000000,
    "currency": "VND",
    "cash_as_of": "2026-06-30",
    "financial_periods": [
        {"period": "2026-01", "inflow": 560000000, "outflow": 610000000},
        {"period": "2026-02", "inflow": 605000000, "outflow": 625000000},
        {"period": "2026-03", "inflow": 650000000, "outflow": 640000000},
        {"period": "2026-04", "inflow": 710000000, "outflow": 665000000},
        {"period": "2026-05", "inflow": 760000000, "outflow": 690000000},
        {"period": "2026-06", "inflow": 820000000, "outflow": 720000000},
    ],
    "exact_location": "12 Nguyễn Thị Minh Khai, Phường Sài Gòn, Thành phố Hồ Chí Minh",
    "location_dependency": "high",
    "target_customer_radius_m": 3000,
    "area_claims": ["Khu vực tập trung nhiều nhân viên văn phòng", "Có nhu cầu giao bữa trưa cao"],
    "known_nearby_competitors": ["Cơm văn phòng A", "Healthy Box"],
}


async def _find_user(session: AsyncSession, email: str) -> User | None:
    return await session.scalar(select(User).where(User.email == email))


async def seed_sample_data(session: AsyncSession, password: str) -> None:
    """Create the demo graph once; later starts only repair missing relations."""
    # Render currently starts one worker, but this also makes the seed safe if that changes.
    await session.execute(text("SELECT pg_advisory_xact_lock(194728361)"))

    owner = await _find_user(session, SAMPLE_STARTUP_EMAIL)
    if owner is None:
        owner = User(
            email=SAMPLE_STARTUP_EMAIL,
            full_name="Nguyễn Minh Anh (Demo)",
            password_hash=hash_password(password),
            role="startup",
            status="active",
        )
        session.add(owner)

    investor = await _find_user(session, SAMPLE_INVESTOR_EMAIL)
    if investor is None:
        investor = User(
            email=SAMPLE_INVESTOR_EMAIL,
            full_name="Trần Quang Huy (Demo)",
            password_hash=hash_password(password),
            role="investor",
            status="active",
        )
        session.add(investor)

    await session.flush()
    startup = await session.scalar(
        select(Startup).where(Startup.owner_id == owner.id, Startup.name == SAMPLE_STARTUP_NAME)
    )
    if startup is None:
        startup = Startup(
            owner_id=owner.id,
            name=SAMPLE_STARTUP_NAME,
            industry="FoodTech / Healthy Meal Delivery",
            stage="Seed",
            primary_location="Quận 1, Thành phố Hồ Chí Minh",
            facts=SAMPLE_FACTS,
            status="submitted",
            current_version=1,
        )
        session.add(startup)
        await session.flush()

    version = await session.scalar(
        select(StartupVersion).where(
            StartupVersion.startup_id == startup.id,
            StartupVersion.version_number == 1,
        )
    )
    if version is None:
        session.add(
            StartupVersion(
                startup_id=startup.id,
                version_number=1,
                snapshot={
                    "name": startup.name,
                    "industry": startup.industry,
                    "stage": startup.stage,
                    "primary_location": startup.primary_location,
                    "facts": startup.facts,
                },
                document_ids=[],
                created_by_id=owner.id,
            )
        )

    access = await session.scalar(
        select(StartupAccess).where(
            StartupAccess.startup_id == startup.id,
            StartupAccess.investor_id == investor.id,
        )
    )
    if access is None:
        session.add(
            StartupAccess(
                startup_id=startup.id,
                investor_id=investor.id,
                granted_by_id=owner.id,
                status="active",
            )
        )

    await session.commit()
