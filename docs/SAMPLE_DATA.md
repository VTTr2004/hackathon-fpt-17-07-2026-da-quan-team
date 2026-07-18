# Dữ liệu mẫu

> **Tài liệu kỹ thuật:** [⌂ Tổng quan](../README.md) · [Kiến trúc](ARCHITECTURE.md) · [Module & AI](MODULES.md) · [API](API.md) · [Cài đặt & Kiểm thử](DEVELOPMENT.md) · [Dữ liệu mẫu](SAMPLE_DATA.md) · [Bảo mật](SECURITY.md) · [Triển khai](../DEPLOYMENT.md)

## Góc Hồ Coffee

Thư mục [`sample-data/goc-ho-coffee`](../sample-data/goc-ho-coffee) chứa bộ hồ sơ mô phỏng cho quán cà phê:

- Hồ sơ kinh doanh JSON.
- Hồ sơ pháp lý PDF.
- Workbook bán hàng 910 dòng và hóa đơn mẫu.
- Workbook mua hàng, chi phí và hóa đơn mẫu.
- Sổ thu chi 260 giao dịch.
- Dữ liệu địa điểm, vận hành, hợp đồng thuê, điện nước.

Số liệu kiểm tra nhanh:

| Chỉ số | Giá trị |
|---|---:|
| Tổng doanh thu thuần | 671.303.450 VND |
| Tổng mua hàng và chi phí | 761.931.040 VND |
| Tổng tiền vào | 821.303.450 VND |
| Tổng tiền ra | 761.931.040 VND |
| Số dư đầu kỳ | 380.000.000 VND |
| Số dư cuối kỳ | 439.372.410 VND |

## AI Cash Flow Variants

Thư mục [`sample-data/ai-cashflow-variants`](../sample-data/ai-cashflow-variants) chứa ba case kiểm thử AI tự trích xuất dòng tiền:

- Tiệm bánh Mây Sớm.
- Nhà hàng Bếp Việt 36.
- Cửa hàng tiện lợi Đêm 24.

Các case cố ý thay đổi tên sheet, cách đặt bảng, thời điểm ghi nhận và quan hệ giữa Excel/PDF/CSV để kiểm tra khả năng chọn tool, tránh double-count và loại chuyển nội bộ.

Thư mục [`sample-data/ai-cashflow-packages`](../sample-data/ai-cashflow-packages) đóng gói các case trên thành file `.zip` "input-only" để tải nhanh lên hệ thống khi demo.

## Nhóm field dữ liệu nên có

Danh mục field hồ sơ được định nghĩa trong [`backend/app/modules/profile_ingestion/field_registry.py`](../backend/app/modules/profile_ingestion/field_registry.py). Các nhóm quan trọng:

- Hồ sơ startup: `name`, `legal_name`, `industry`, `stage`, `business_type`, `founded_date`, `website_url`, `primary_location`, `founders`, `employee_count`.
- Business Model: `problem`, `solution`, `target_customers`, `core_products`, `differentiation`, `revenue_model`, `sales_channels`, `pricing_model`, `traction`, `expansion_plan`, `fundraising_need`, `use_of_funds`.
- Cash Flow: `current_cash`, `minimum_cash_buffer`, `monthly_revenue`, `monthly_expense`, `fixed_monthly_costs`, `variable_cost_ratio`, `accounts_receivable`, `accounts_payable`, `inventory`, `financial_periods`, `cash_flow_dataset`.
- Funding: `total_funding_usd`, `funding_rounds_count`, `latest_round_type`, `latest_round_amount`, `investors`, `cap_table_summary`, `valuation_pre_money`, `valuation_post_money`.
- Location: `exact_location`, `lat`, `lon`, `location_type`, `area_m2`, `tenure`, `rent_cost`, `operating_hours`, `location_dependency`, `target_customer_radius_m`, `known_nearby_competitors`, `area_claims`.
- Legal/Evidence: `registration_number`, `tax_code`, `licenses`, `ip_assets`, `material_contracts`, `legal_risks`, `document_checklist_status`, `evidence_refs`.
