Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  StreamApp - Legal Streaming & Download Platform" -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "Launching http://localhost:3000 in your browser..." -ForegroundColor Yellow

Start-Process "http://localhost:3000"
Set-Location "$PSScriptRoot\backend"
node src/index.js