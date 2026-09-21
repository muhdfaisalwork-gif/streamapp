#!/usr/bin/env bash
# Build a .deb package from the Flutter Linux bundle.
set -e
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
BUNDLE="$ROOT/client/build/linux/x64/release/bundle"
if [[ ! -d "$BUNDLE" ]]; then
    echo "Flutter Linux bundle not found at $BUNDLE. Run 'flutter build linux --release' first." >&2
    exit 1
fi

WORK="$ROOT/client/build/deb-stage"
rm -rf "$WORK"
mkdir -p "$WORK/DEBIAN"
mkdir -p "$WORK/usr/bin"
mkdir -p "$WORK/usr/share/applications"
mkdir -p "$WORK/usr/share/icons/hicolor/256x256/apps"

cp -r "$BUNDLE"/* "$WORK/usr/bin/" 2>/dev/null || cp "$BUNDLE/streaming_app" "$WORK/usr/bin/"
cp "$ROOT/packaging/linux/streaming_app.desktop" "$WORK/usr/share/applications/"
# Icon (optional)
[[ -f "$ROOT/client/assets/icon.png" ]] && cp "$ROOT/client/assets/icon.png" "$WORK/usr/share/icons/hicolor/256x256/apps/streaming_app.png"

cat > "$WORK/DEBIAN/control" <<EOF
Package: streaming-app
Version: 1.0.0
Section: video
Priority: optional
Architecture: amd64
Depends: libc6 (>= 2.31), libgtk-3-0 (>= 3.24), libmpv1 (>= 0.32)
Maintainer: Streaming App Foundation <engineering@streaming-app.local>
Description: Cross-platform legal streaming app
 StreamApp delivers curated public-domain and Creative Commons media
 from Blender Open Movies, Archive.org, and TMDB-enriched catalog data.
EOF

cat > "$WORK/DEBIAN/postinst" <<'EOF'
#!/bin/sh
update-desktop-database /usr/share/applications || true
EOF
chmod +x "$WORK/DEBIAN/postinst"

OUT="$ROOT/streaming-app_1.0.0_amd64.deb"
dpkg-deb --build "$WORK" "$OUT"
echo "Built: $OUT"
