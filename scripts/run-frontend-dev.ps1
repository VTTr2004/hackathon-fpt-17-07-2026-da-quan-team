$env:NEXT_PUBLIC_API_URL = "http://127.0.0.1:8000/api/v1"
Set-Location (Join-Path $PSScriptRoot "..\frontend")
npm.cmd run dev -- -p 3000
