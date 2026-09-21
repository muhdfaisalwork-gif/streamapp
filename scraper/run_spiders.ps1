# Run all Scrapy spiders on Windows.
# Prerequisites: Python 3.10+ on PATH. Run install_python.ps1 once.
Set-Location $PSScriptRoot

$spiders = @('yts', 'donkey', 'tmovies', 'uflix')
foreach ($spider in $spiders) {
    Write-Host "=== Crawling $spider ===" -ForegroundColor Cyan
    scrapy crawl $spider
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Spider $spider failed with exit $LASTEXITCODE" -ForegroundColor Red
        exit $LASTEXITCODE
    }
}
Write-Host "Done. Output: $(Resolve-Path ./output/scraped_catalog.json)" -ForegroundColor Green
