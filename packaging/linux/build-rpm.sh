#!/usr/bin/env bash
# Build an .rpm package from the Flutter Linux bundle.
# Requires rpmbuild installed.
set -e
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
BUNDLE="$ROOT/client/build/linux/x64/release/bundle"
if [[ ! -d "$BUNDLE" ]]; then
    echo "Flutter Linux bundle not found. Run 'flutter build linux --release' first." >&2
    exit 1
fi

RPMBUILD="$HOME/rpmbuild"
mkdir -p "$RPMBUILD"/{BUILD,RPMS,SOURCES,SPECS,SRPMS}

cp "$ROOT/packaging/linux/rpm/streaming_app.spec" "$RPMBUILD/SPECS/"
cp -r "$BUNDLE" "$RPMBUILD/BUILD/streaming-app-1.0.0/"
[[ -f "$ROOT/client/assets/icon.png" ]] && cp "$ROOT/client/assets/icon.png" "$RPMBUILD/BUILD/streaming-app-1.0.0/icon.png"

cd "$RPMBUILD/BUILD"
tar czf "$RPMBUILD/SOURCES/streaming-app-1.0.0.tar.gz" "streaming-app-1.0.0"

rpmbuild -ba "$RPMBUILD/SPECS/streaming_app.spec"

cp "$RPMBUILD/RPMS/x86_64/"*.rpm "$ROOT/"
echo "Built: $ROOT/streaming-app-1.0.0-1.x86_64.rpm"
