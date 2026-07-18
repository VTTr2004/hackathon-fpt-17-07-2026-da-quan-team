# One-command RAG demo for the Góc Hồ Coffee sample data.
# Prereq: the stack is up (docker compose up -d --build) and NVIDIA_API_KEY is set in .env.
# Usage:  ./scripts/demo-coffee.ps1
#         ./scripts/demo-coffee.ps1 -Question "Số dư cuối kỳ là bao nhiêu?"
param(
    [string]$Base = "http://localhost:8000/api/v1",
    [string]$Question = "Tổng doanh thu thuần 3 tháng là bao nhiêu?",
    [string]$DataDir = "/app/sample-data/goc-ho-coffee"
)
$ErrorActionPreference = "Stop"

function Invoke-Json($Method, $Uri, $Obj) {
    $json = $Obj | ConvertTo-Json -Compress
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($json)
    return Invoke-RestMethod -Method $Method -Uri $Uri -Body $bytes -ContentType "application/json; charset=utf-8"
}

Write-Host "1) Creating startup..." -ForegroundColor Cyan
$startup = Invoke-Json Post "$Base/startups" @{ name = "Goc Ho Coffee (demo)" }
$id = $startup.id
Write-Host "   startup id: $id"

Write-Host "2) Seeding RAG index inside the backend container..." -ForegroundColor Cyan
docker compose exec -T backend python -m scripts.seed_folder_index --startup-id $id --dir $DataDir
if ($LASTEXITCODE -ne 0) { throw "Seeding failed (is the stack up? is scripts/ in the image?)" }

Write-Host "3) Asking: $Question" -ForegroundColor Cyan
$resp = Invoke-Json Post "$Base/startups/$id/chat" @{ question = $Question }
Write-Host ""
Write-Host "ANSWER:" -ForegroundColor Green
Write-Host $resp.answer
Write-Host ""
Write-Host ("meta: " + ($resp.metadata | ConvertTo-Json -Compress))
foreach ($c in $resp.citations) { Write-Host ("  cite: {0} [{1}]" -f $c.filename, $c.locator) }
Write-Host ""
Write-Host "Reuse this startup id for more questions:" -ForegroundColor DarkGray
Write-Host "  Invoke-RestMethod -Method Post -Uri $Base/startups/$id/chat -ContentType 'application/json' -Body '{\"question\":\"...\"}'"
