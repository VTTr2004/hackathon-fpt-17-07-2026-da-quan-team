$env:NEXT_PUBLIC_API_URL = "http://localhost:8000/api/v1"
$rootEnv = "D:\GitHub\hackathon-fpt-17-07-2026-da-quan-team\.env"
if (Test-Path $rootEnv) {
  Get-Content $rootEnv | ForEach-Object {
    if ($_ -match '^\s*NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=(.*)$') {
      $env:NEXT_PUBLIC_GOOGLE_MAPS_API_KEY = $Matches[1]
    }
  }
}
Set-Location "D:\GitHub\hackathon-fpt-17-07-2026-da-quan-team\frontend"
npm.cmd run dev
