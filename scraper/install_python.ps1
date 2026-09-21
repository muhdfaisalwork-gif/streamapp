# Install Python 3.12 + Scrapy on Windows.
# Run once: powershell -ExecutionPolicy Bypass -File install_python.ps1

$ErrorActionPreference = 'Stop'

# Check existing Python
$py = (Get-Command python -ErrorAction SilentlyContinue)
if ($py) {
    $ver = & python --version 2>&1
    Write-Host "Python already installed: $ver" -ForegroundColor Green
} else {
    Write-Host "Python not found. Installing via winget..." -ForegroundColor Yellow
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        winget install --id Python.Python.3.12 -e --source winget --accept-source-agreements --accept-package-agreements
    } else {
        Write-Host "winget not available. Please install Python 3.10+ manually from https://python.org" -ForegroundColor Red
        exit 1
    }
}

Write-Host "Upgrading pip..." -ForegroundColor Cyan
python -m pip install --upgrade pip

Write-Host "Installing Scrapy + Playwright..." -ForegroundColor Cyan
Set-Location $PSScriptRoot
python -m pip install -r requirements.txt

Write-Host "Installing Playwright browser..." -ForegroundColor Cyan
python -m playwright install chromium

Write-Host "Done. Verify with: python -c 'import scrapy; print(scrapy.__version__)'" -ForegroundColor Green
