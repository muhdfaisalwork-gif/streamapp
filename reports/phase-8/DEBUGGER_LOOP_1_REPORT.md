PROJECT: Cross-Platform Streaming App
PHASE: Phase 8 — Production Readiness, Distribution & Launch
LOOP: Loop 1 — Initial Verification
DEBUGGER: Agent 14 — Debugger Agent

DEFECT: DEF-P8-01 (Linux distribution packages lack standard `/usr/bin/streaming-app` alias symlink)
REPRODUCED: YES
ROOT CAUSE:
- In `packaging/linux/rpm/streaming_app.spec`, line 26 copies `streaming_app` to `$RPM_BUILD_ROOT/usr/bin/`.
- In Debian and Fedora package naming conventions, users expect invoking the package name `streaming-app` directly in their terminal. Because Flutter default executable names use snake_case (`streaming_app`), without creating a symbolic link `ln -s streaming_app $RPM_BUILD_ROOT/usr/bin/streaming-app`, terminal invocation of `streaming-app` fails.
AFFECTED COMPONENTS:
- packaging/linux/rpm/streaming_app.spec
SEVERITY:
- Major
RECOMMENDED FIX:
- In `packaging/linux/rpm/streaming_app.spec`:
  1. Add `ln -sf streaming_app $RPM_BUILD_ROOT/usr/bin/streaming-app` in the `%install` section.
  2. Add `/usr/bin/streaming-app` to the `%files` section.
REGRESSION RISK:
- None.
READY FOR RETEST:
- YES (Pending developer update)
