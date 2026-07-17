# Startup Lens

Monorepo cho hệ thống đánh giá startup và chatbot hỏi đáp tài liệu:

- **Backend:** FastAPI, SQLAlchemy async và PostgreSQL.
- **LLM:** Gemini qua SDK chính thức `google-genai`.
- **Frontend:** Next.js App Router, React và TypeScript.
- **Phân tích:** ba module độc lập, mọi phép tính nằm trong tool deterministic.

## Cấu trúc

```text
backend/
  app/
    api/routes/              # REST API
    core/                    # Cấu hình
    db/                      # SQLAlchemy engine/base
    llm/                     # Gemini boundary
    models/                  # PostgreSQL models
    modules/
      business_model/        # Analyzer + tools + docs riêng
      cash_flow/
      surrounding_area/
    schemas/                 # API và contract chung
    services/                # Parsing, orchestration, RAG
frontend/
  app/                       # Next.js routes
  lib/                       # API client
  types/                     # TypeScript contracts
plans/                       # Product/technical plan
```

## Chạy nhanh bằng Docker

1. Sao chép `.env.example` thành `.env`.
2. Điền `GEMINI_API_KEY` lấy từ Google AI Studio.
3. Chạy:

```bash
docker compose up --build
```

- Frontend: <http://localhost:3000>
- Swagger: <http://localhost:8000/docs>
- Health check: <http://localhost:8000/api/v1/health>
- PostgreSQL trên host: `localhost:5433` (có thể đổi bằng `POSTGRES_PORT`).

## Chạy local

### Backend

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

Backend cần PostgreSQL đang chạy và `DATABASE_URL` hợp lệ.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Gemini

Tất cả lệnh gọi LLM đi qua `backend/app/llm/gemini.py`. Không gọi SDK Gemini trực tiếp từ module.

- `GEMINI_API_KEY`: bắt buộc khi cần LLM.
- `GEMINI_MODEL`: mặc định `gemini-2.5-flash`.
- Structured output dùng Pydantic schema.
- Khi chưa có API key, tool tính toán vẫn hoạt động và chatbot dùng extractive fallback.
- Gemini không được tự tính lại output tool; nó chỉ tổng hợp định tính và diễn giải bằng chứng.

## API chính

```text
POST /api/v1/startups
POST /api/v1/startups/{id}/documents
POST /api/v1/startups/{id}/analyses/business_model
POST /api/v1/startups/{id}/analyses/cash_flow
POST /api/v1/startups/{id}/analyses/surrounding_area
POST /api/v1/startups/{id}/chat
POST /api/v1/surrounding/geocode
GET  /api/v1/surrounding/map
```

## Dữ liệu demo trong `facts`

Để tool dòng tiền chạy, cập nhật `facts` của startup với cấu trúc:

```json
{
  "current_cash": 500000000,
  "financial_periods": [
    {"period": "2026-01", "inflow": 100000000, "outflow": 160000000},
    {"period": "2026-02", "inflow": 120000000, "outflow": 170000000}
  ]
}
```

Để tool khu vực chạy, tọa độ phải được chuyên viên xác nhận từ bước geocode/map trước khi phân tích:

```json
{
  "industry": "chuỗi cà phê",
  "location": {
    "lat": 10.7725,
    "lon": 106.698,
    "claims": [
      "Chưa có đối thủ trực tiếp trong bán kính 500m",
      "Khu dân cư đông đúc"
    ],
    "depends_on_surrounding_customers": true
  }
}
```

Module `surrounding_area` dùng `backend/data/poi.db` được build từ OpenStreetMap local. Nếu thiếu file này, báo cáo trả
`insufficient_data` thay vì đoán hoặc chấm 0. Build dữ liệu một lần bằng:

```bash
cd backend
python -m app.modules.surrounding_area.scripts.setup_data
```
