$env:DATABASE_URL = "postgresql+asyncpg://app:app@127.0.0.1:5433/startup_due_diligence"
$env:AUTO_CREATE_TABLES = "true"
$env:CORS_ORIGINS = "http://localhost:3000"
Set-Location "D:\GitHub\hackathon-fpt-17-07-2026-da-quan-team\backend"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
