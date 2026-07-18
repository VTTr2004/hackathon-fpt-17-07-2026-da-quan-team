# Deploy: Supabase + Render + Vercel

Production architecture:

```text
Vercel (Next.js) -> Render (FastAPI) -> Supabase (PostgreSQL)
```

Render and Vercel deploy automatically from `main`. GitHub Actions runs the test suite first; the Render Blueprint uses `autoDeployTrigger: checksPass`.

## 1. Supabase database

1. Create a Supabase project in the Singapore or Southeast Asia region.
2. Open **Connect** in the project dashboard.
3. Select the **Session pooler** connection (port `5432`), which supports IPv4 and prepared statements.
4. Convert the URI scheme from `postgresql://` to `postgresql+asyncpg://` for SQLAlchemy.
5. If required by the connection panel, use `?ssl=require` rather than `?sslmode=require` with the asyncpg driver.

Example shape (do not commit the real value):

```text
postgresql+asyncpg://postgres.PROJECT_REF:URL_ENCODED_PASSWORD@aws-0-REGION.pooler.supabase.com:5432/postgres?ssl=require
```

Percent-encode reserved URL characters in the password. The application creates its tables on first startup because `AUTO_CREATE_TABLES=true`.

## 2. Render backend

1. Open the Render Dashboard and choose **New -> Blueprint**.
2. Connect this GitHub repository and select `render.yaml`.
3. During Blueprint creation, enter the secret variables marked `sync: false`:

| Variable | Value |
| --- | --- |
| `DATABASE_URL` | Supabase Session pooler URI from step 1 |
| `AUTH_SECRET` | Unique random secret with at least 32 characters; never reuse the development value |
| `SAMPLE_DATA_PASSWORD` | Mật khẩu riêng (tối thiểu 8 ký tự) cho hai tài khoản demo |
| `CORS_ORIGINS` | Temporary Vercel URL or final frontend domain, e.g. `https://your-app.vercel.app` |
| `GEMINI_API_KEY` | Một Gemini key hoặc danh sách key phân tách bằng dấu phẩy; để trống nếu chỉ cần fallback deterministic |
| `GOONG_API_KEY` | Optional |
| `GOOGLE_PLACES_API_KEY` | Optional |

Blueprint bật `SEED_SAMPLE_DATA=true`. Mỗi lần backend khởi động, seed idempotent sẽ bảo đảm có hồ sơ mẫu
`Lotus Fresh Kitchen` và quyền truy cập tương ứng; dữ liệu không bị nhân đôi khi redeploy.

- Startup demo: `startup.demo@startuplens.vn`
- Investor demo: `investor.demo@startuplens.vn`
- Cả hai dùng mật khẩu cấu hình trong `SAMPLE_DATA_PASSWORD`.

The backend health endpoint is `/api/v1/health`. Copy the resulting Render URL, for example:

```text
https://startup-lens-api.onrender.com
```

The free Render service has an ephemeral filesystem. Uploaded files in `/tmp/uploads` do not survive every restart or redeploy. PostgreSQL records remain in Supabase. Use a paid Render persistent disk or migrate uploaded documents to Supabase Storage before relying on file persistence in production.

## 3. Vercel frontend

1. Import the same GitHub repository into Vercel.
2. Set **Root Directory** to `frontend`.
3. Keep the detected framework as **Next.js**.
4. Add this environment variable for Production and Preview:

```dotenv
NEXT_PUBLIC_API_URL=https://YOUR-RENDER-SERVICE.onrender.com/api/v1
```

5. Deploy, then copy the production Vercel domain.
6. Return to Render and set `CORS_ORIGINS` to that exact origin. Multiple origins can be comma-separated.

Because `NEXT_PUBLIC_API_URL` is embedded during the Next.js build, redeploy Vercel after changing it.

## 4. Automatic deployment

After the GitHub integrations are connected:

- Pull requests run CI and receive a Vercel preview.
- Commits merged or pushed to `main` run CI.
- Render deploys the backend after the GitHub checks pass.
- Vercel deploys the frontend from the same commit.

No VPS, SSH key, GHCR token, or production Docker Compose file is required for this architecture.
