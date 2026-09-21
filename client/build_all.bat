@echo off
REM StreamApp — Master build orchestrator (Windows).
REM Builds all artifacts that can be produced on this machine:
REM   - Backend Node bundle (no build step; just verifies)
REM   - Flutter web (single-binary web deployment)
REM   - Flutter Windows .exe + NSIS installer
REM   - Flutter Android APK (per-ABI split)
REM   - Expo web (already running, no build needed)
REM
REM Skips targets that need a different OS (Linux .deb/rpm/AppImage, iOS .ipa, Mac builds).
REM Usage:  build_all.bat                (release builds)
REM         build_all.bat --debug       (debug builds, faster)

setlocal
set DEBUG_FLAG=%1
set FLAGS=
if "%DEBUG_FLAG%"=="--debug" set FLAGS=--debug

echo ========================================================
echo  StreamApp build orchestrator
echo  Flags: %FLAGS%
echo ========================================================

REM 1. Verify backend syntax
echo [1/5] Backend lint...
cd /d "%~dp0backend"
node --check src/index.js || goto :error
node --check src/api/routes.js || goto :error
node --check src/scrapers/MovieBoxScraper.js || goto :error
echo Backend OK.

REM 2. Flutter web
echo [2/5] Flutter web build...
cd /d "%~dp0client"
if not exist web\index.html (
    echo ERROR: client\web\index.html missing. Phase 2 deliverable.
    goto :error
)
flutter build web --release %FLAGS% || goto :error
echo Flutter web built: client\build\web\

REM 3. Flutter Windows .exe + NSIS installer
echo [3/5] Flutter Windows + NSIS...
flutter build windows --release %FLAGS% || goto :error
if exist "C:\Program Files (x86)\NSIS\makensis.exe" (
    set NSIS="C:\Program Files (x86)\NSIS\makensis.exe"
) else if exist "C:\Program Files\NSIS\makensis.exe" (
    set NSIS="C:\Program Files\NSIS\makensis.exe"
) else (
    echo NSIS not found. Skipping installer.
    goto :skip_nsis
)
"%NSIS%" /DAPPNAME=StreamApp "%~dp0packaging\windows\installer.nsi" || goto :error
:skip_nsis
echo Windows build: client\build\windows\x64\runner\Release\streaming_app.exe

REM 4. Flutter Android APK
echo [4/5] Flutter Android APK...
flutter build apk --release --split-per-abi %FLAGS% || goto :error
echo Android APK: client\build\app\outputs\flutter-apk\

REM 5. iOS — skipped (needs Mac)
echo [5/5] iOS — skipped (requires macOS). Run on a Mac with:
echo    cd client ^&^& flutter build ios --release

echo ========================================================
echo  BUILD COMPLETE.
echo ========================================================
echo.
echo Artifacts:
echo   Backend:   ^(running on port 3000 already^)
echo   Flutter web:    client\build\web\
echo   Windows .exe:   client\build\windows\x64\runner\Release\streaming_app.exe
echo   Android APK:    client\build\app\outputs\flutter-apk\app-arm64-v8a-release.apk
echo   ^(... and app-armeabi-v7a-release.apk, app-x86_64-release.apk^)
echo.
echo Run "cd client ^&^& flutter run -d chrome" to see the web build live.
echo Run ".\StreamingApp-Setup-x64.exe" to install on Windows.
echo Run "adb install app-arm64-v8a-release.apk" to install on Android.
goto :eof

:error
echo BUILD FAILED with error %errorlevel%.
exit /b %errorlevel%
