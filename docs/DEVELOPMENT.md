# Cài đặt, biến môi trường & kiểm thử

> **Tài liệu kỹ thuật:** [⌂ Tổng quan](../README.md) · [Kiến trúc](ARCHITECTURE.md) · [Module & AI](MODULES.md) · [API](API.md) · [Cài đặt & Kiểm thử](DEVELOPMENT.md) · [Dữ liệu mẫu](SAMPLE_DATA.md) · [Bảo mật](SECURITY.md) · [Triển khai](../DEPLOYMENT.md)

## Yêu cầu

- Docker Desktop nếu chạy toàn bộ stack bằng Docker.
- Python 3.12 nếu chạy backend local.
- Node.js 24 nếu chạy frontend local theo CI.
- PostgreSQL 17 hoặc service `postgres` trong `docker-compose.yml`.

## Chạy nhanh bằng Docker

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Sau khi stack chạy:

- Frontend: [http://localhost:3000](http://localhost:3000)
- Swagger: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)
- PostgreSQL trên host: `localhost:5433`

## Chạy backend local

```powershell
docker compose up -d postgres
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Backend cần `DATABASE_URL` hợp lệ. Mặc định `.env.example` trỏ tới PostgreSQL local ở port `5433`.

## Chạy frontend local

```powershell
cd frontend
npm ci
npm.cmd run dev -- -p 3000
```

Hoặc dùng helper script:

```powershell
.\scripts\run-frontend-dev.ps1
.\scripts\run-backend-dev.ps1
```

## Biến môi trường

| Biến | Bắt buộc | Mô tả |
|---|:---:|---|
| `DATABASE_URL` | Có | PostgreSQL async SQLAlchemy URL |
| `AUTO_CREATE_TABLES` | Không | Tự tạo/migrate bảng khi app khởi động |
| `CORS_ORIGINS` | Có khi deploy | Danh sách origin frontend được phép gọi API |
| `UPLOAD_DIR` | Không | Thư mục lưu file upload và RAG index |
| `MAX_UPLOAD_MB` | Không | Giới hạn dung lượng upload, mặc định 25 MB |
| `AUTH_SECRET` | Có khi deploy | Secret HMAC token, production cần chuỗi riêng tối thiểu 32 ký tự |
| `AUTH_TOKEN_TTL_HOURS` | Không | Thời hạn token |
| `LLM_PROVIDER` | Không | `gemini` hoặc `nvidia` cho RAG |
| `GEMINI_API_KEY` | Không | Một key hoặc nhiều key cách nhau bằng dấu phẩy |
| `GEMINI_MODEL` | Không | Model phân tích/narrative, mặc định theo env |
| `GEMINI_EMBED_MODEL` | Không | Model embedding cho RAG |
| `NVIDIA_API_KEY` | Không | Bật provider NVIDIA cho RAG |
| `RAG_TOP_K` | Không | Số nguồn đưa vào answer |
| `RAG_CANDIDATE_K` | Không | Số candidate trước rerank |
| `RAG_USE_RERANK` | Không | Bật/tắt rerank LLM |
| `GOONG_API_KEY` | Không | Geocoding địa chỉ Việt Nam nếu cấu hình |
| `GOOGLE_GEOCODING_API_KEY` | Không | Google Geocoding fallback |
| `GOOGLE_PLACES_API_KEY` | Cần cho Area analyzer v2 | Google Places API New cho phân tích khu vực |
| `NEXT_PUBLIC_API_URL` | Có ở frontend | URL backend API, ví dụ `http://localhost:8000/api/v1` |
| `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY` | Không | Hiển thị Google Maps ở frontend; thiếu key sẽ fallback map khác |

## Kiểm thử

### Backend

```powershell
cd backend
pip install -e ".[dev]"
ruff check app tests --select E9,F63,F7,F82
python -m pytest
```

Chạy riêng các module:

```powershell
python -m pytest app/modules/cash_flow/tests tests/test_cash_flow_tools.py tests/test_cash_flow_extractor.py tests/test_cash_flow_regressions.py -q
python -m pytest tests/surrounding_area -q
python -m pytest tests/test_security.py tests/test_security_boundaries.py tests/test_authorization.py -q
```

> Lưu ý: các test `tests/surrounding_area/test_surrounding_analyzer.py` chỉ chạy khi Google Places API (New) được cấu hình; nếu không có key, chúng tự skip (giống môi trường CI). Một số test geocoding mock chỉ Nominatim, nên nếu `.env` local có `GOOGLE_GEOCODING_API_KEY`/`GOONG_API_KEY` thật thì cần clear các key đó khi chạy để khớp CI.

### Frontend

```powershell
cd frontend
npm ci
npm.cmd run lint
npm.cmd run build
```

Lưu ý: `next build` có thể cần mạng để tải Google Font `Inter` thông qua `next/font`.

### CI

GitHub Actions chạy trên `main` và pull request:

- Python 3.12.
- Backend: install dev deps, ruff critical rules, pytest.
- Node.js 24.
- Frontend: `npm ci`, lint, production build.

## Kịch bản demo gợi ý

1. Mở frontend local hoặc production.
2. Đăng ký một tài khoản Startup và một tài khoản Investor.
3. Startup tạo hồ sơ "Góc Hồ Coffee".
4. Upload các file trong [`sample-data/goc-ho-coffee`](../sample-data/goc-ho-coffee).
5. Kiểm tra completeness, nộp hồ sơ và cấp quyền cho investor.
6. Investor mở hồ sơ được chia sẻ.
7. Chạy Cash Flow để xem doanh thu, dòng tiền, runway và cảnh báo reconciliation.
8. Chạy Surrounding Area sau khi xác nhận tọa độ và cấu hình `GOOGLE_PLACES_API_KEY`.
9. Hỏi chatbot: "Tổng doanh thu thuần 3 tháng là bao nhiêu?" và kiểm tra citation.
10. Hỏi một câu không có trong tài liệu để minh họa cơ chế từ chối suy diễn.

Bộ dữ liệu demo chi tiết: xem [SAMPLE_DATA.md](SAMPLE_DATA.md).
