@echo off
title StreamApp - Scrapy catalog service
echo ========================================================
echo   Running Python Scrapy spiders...
echo ========================================================
cd /d "%~dp0scraper"
powershell -ExecutionPolicy Bypass -File run_spiders.ps1
if %errorlevel% neq 0 (
    echo Spider run failed. Backend will still work without scraped_catalog.json.
)
pause
