#!/usr/bin/env bash
# Build a portable AppImage from the Flutter Linux bundle.
# Requires: appimagetool (https://github.com/AppImage/AppImageKit/releases)
set -e
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
BUNDLE="$ROOT/client/build/linux/x64/release/bundle"
if [[ ! -d "$BUNDLE" ]]; then
    echo "Flutter Linux bundle not found. Run 'flutter build linux --release' first." >&2
    exit 1
fi

APPIMAGETOOL="${APPIMAGETOOL:-appimagetool}"
[[ ! -x "$(command -v $APPIMAGETOOL)" ]] && { echo "appimagetool not found. Set APPIMAGETOOL=/path/to/appimagetool or install it."; exit 1; }

APPDIR="$ROOT/client/build/StreamApp.AppDir"
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin"
mkdir -p "$APPDIR/usr/share/applications"
mkdir -p "$APPDIR/usr/share/icons/hicolor/256x256/apps"

cp -r "$BUNDLE"/* "$APPDIR/usr/bin/"
cp "$ROOT/packaging/linux/appimage/AppRun" "$APPDIR/AppRun"
chmod +x "$APPDIR/AppRun"
cp "$ROOT/packaging/linux/streaming_app.desktop" "$APPDIR/"
# Rename for AppImage convention
sed -i 's/^Name=.*/Name=StreamApp/' "$APPDIR/streaming_app.desktop"
[[ -f "$ROOT/client/assets/icon.png" ]] && cp "$ROOT/client/assets/icon.png" "$APPDIR/streaming_app.png"

OUT="$ROOT/StreamApp-x86_64.AppImage"
"$APPIMAGETOOL" "$APPDIR" "$OUT"
echo "Built: $OUT"
