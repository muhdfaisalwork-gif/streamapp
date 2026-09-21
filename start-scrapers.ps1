Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  StreamApp - Scrapy catalog service" -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Cyan
Set-Location "$PSScriptRoot\scraper"
& "$PSScriptRoot\scraper\run_spiders.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Spider run failed (exit $LASTEXITCODE). Backend still works without scraped_catalog.json." -ForegroundColor Yellow
}