$env:NEXT_PUBLIC_API_URL = "http://127.0.0.1:8000/api/v1"
$rootEnv = Join-Path $PSScriptRoot "..\.env"
if (Test-Path $rootEnv) {
  Get-Content $rootEnv | ForEach-Object {
    if ($_ -match '^\s*NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=(.*)$') {
      $env:NEXT_PUBLIC_GOOGLE_MAPS_API_KEY = $Matches[1]
    }
  }
}
Set-Location (Join-Path $PSScriptRoot "..\frontend")
npm.cmd run dev -- -p 3000
