@echo off
REM Start all three services for StreamApp: Python live-scraper :7800,
REM Node backend :3000, Expo web :8088. Each service runs in a separate
REM window with its own persistent log file. Crash of one does not stop
REM the others.

set BASE=G:\streaming app
set PY=C:\Users\Lucifer\AppData\Local\Python\pythoncore-3.14-64\python.exe

echo [%date% %time%] launching StreamApp stack...

REM 1) Python live scraper with watchdog (respawns on crash)
start "StreamApp-LiveScraper" /min powershell -ExecutionPolicy Bypass -File "%BASE%\start-live-scraper.ps1"

REM Wait up to 25s for :7800 to come up
echo waiting for live-scraper on :7800...
set LIVE_OK=0
for /L %%i in (1,1,25) do (
  timeout /t 1 /nobreak >nul
  powershell -NoProfile -Command "try{(Invoke-WebRequest -Uri 'http://127.0.0.1:7800/health' -UseBasicParsing -TimeoutSec 1).StatusCode}catch{exit 1}" >nul 2>&1
  if not errorlevel 1 (
    echo   live-scraper :7800 UP after %%i s
    set LIVE_OK=1
    goto :backend
  )
)
echo   WARNING live-scraper :7800 did not respond in 25s; continuing

:backend
REM 2) Node backend
start "StreamApp-Backend" /min cmd /c "node src\index.js > %BASE%\backend\backend.log 2>&1"
echo waiting for backend on :3000...
for /L %%i in (1,1,15) do (
  timeout /t 1 /nobreak >nul
  powershell -NoProfile -Command "try{(Invoke-WebRequest -Uri 'http://localhost:3000/api/v1/health' -UseBasicParsing -TimeoutSec 1).StatusCode}catch{exit 1}" >nul 2>&1
  if not errorlevel 1 (
    echo   backend :3000 UP after %%i s
    goto :frontend
  )
)
echo   WARNING backend :3000 did not respond in 15s; continuing

:frontend
REM 3) Expo web
start "StreamApp-Expo" /min cmd /c "cd /d %BASE%\frontend && npx expo start --web --port 8088 > %BASE%\frontend\expo.log 2>&1"
echo waiting for Expo web on :8088...
for /L %%i in (1,1,60) do (
  timeout /t 1 /nobreak >nul
  powershell -NoProfile -Command "try{(Invoke-WebRequest -Uri 'http://localhost:8088/' -UseBasicParsing -TimeoutSec 1).StatusCode}catch{exit 1}" >nul 2>&1
  if not errorlevel 1 (
    echo   expo :8088 UP after %%i s
    goto :done
  )
)
echo   WARNING expo :8088 did not respond in 60s; check %BASE%\frontend\expo.log

:done
echo [%date% %time%] all services launched.
echo Open http://localhost:8088 in your browser.
