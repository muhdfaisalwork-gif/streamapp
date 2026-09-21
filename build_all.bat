@echo off
title StreamApp - Build and Warmup Orchestrator
set PATH=C:\Users\Lucifer\AppData\Local\Python\pythoncore-3.14-64;C:\Users\Lucifer\AppData\Local\Python\pythoncore-3.14-64\Scripts;%PATH%

echo ========================================================
echo   StreamApp Build and Deep Crawl Orchestrator
echo ========================================================

echo [1/4] Installing / verifying Python dependencies...
python -m pip install -r "%~dp0scraper\requirements.txt"
if %errorlevel% neq 0 (
    echo Python package install failed.
    pause
    exit /b 1
)

echo [2/4] Verifying Patchright Chromium binaries...
patchright install chromium

echo [3/4] Checking backend node syntax...
node --check "%~dp0backend\src\index.js"
node --check "%~dp0backend\src\api\routes.js"

echo [4/4] Executing Deep Crawl (Target: 100,000 titles)...
python "%~dp0scraper\deep_crawl.py" --target 100000

echo ========================================================
echo   StreamApp Build & Crawl Completed Successfully!
echo ========================================================
pause
