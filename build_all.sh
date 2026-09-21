#!/usr/bin/env bash
# StreamApp — Master build orchestrator (Linux/macOS).
# Builds all artifacts that can be produced on this machine:
#   - Backend Node bundle (no build step; just verifies)
#   - Flutter web (single-binary web deployment)
#   - Flutter Linux AppImage + .deb + .rpm
#   - Flutter Android APK (per-ABI split)
#   - iOS only on macOS
#
# Usage:  ./build_all.sh                  (release builds)
#         ./build_all.sh --debug          (debug builds, faster)

set -e
FLAGS=""
if [[ "$1" == "--debug" ]]; then FLAGS="--debug"; fi

ROOT="$(cd "$(dirname "$0")" && pwd)"
echo "========================================================"
echo " StreamApp build orchestrator"
echo " Flags: $FLAGS"
echo "========================================================"

# 1. Verify backend syntax
echo "[1/5] Backend lint..."
cd "$ROOT/backend"
node --check src/index.js
node --check src/api/routes.js
node --check src/scrapers/MovieBoxScraper.js
echo "Backend OK."

# 2. Flutter web
echo "[2/5] Flutter web build..."
cd "$ROOT/client"
flutter build web --release $FLAGS

# 3. Flutter Linux bundles + .deb + .rpm + AppImage
echo "[3/5] Flutter Linux..."
flutter build linux --release $FLAGS
bash "$ROOT/packaging/linux/build-deb.sh"
bash "$ROOT/packaging/linux/build-rpm.sh"
bash "$ROOT/packaging/linux/appimage/build-appimage.sh"

# 4. Flutter Android APK
echo "[4/5] Flutter Android APK..."
flutter build apk --release --split-per-abi $FLAGS

# 5. iOS — only on macOS
if [[ "$(uname)" == "Darwin" ]]; then
    echo "[5/5] Flutter iOS..."
    flutter build ios --release $FLAGS
else
    echo "[5/5] iOS skipped (requires macOS)"
fi

echo "========================================================"
echo " BUILD COMPLETE."
echo "========================================================"
echo ""
echo "Artifacts:"
echo "  Flutter web:        client/build/web/"
echo "  Linux AppImage:     client/build/linux/x64/release/bundle/StreamApp-x86_64.AppImage"
echo "  Linux .deb:         streaming-app_1.0.0_amd64.deb"
echo "  Linux .rpm:         streaming-app-1.0.0-1.x86_64.rpm"
echo "  Android APK:        client/build/app/outputs/flutter-apk/"
[[ "$(uname)" == "Darwin" ]] && echo "  iOS .app:          client/build/ios/iphoneos/Runner.app"
