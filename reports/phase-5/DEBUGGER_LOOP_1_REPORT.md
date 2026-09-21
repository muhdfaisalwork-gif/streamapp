PROJECT: Cross-Platform Streaming App
PHASE: Phase 5 — Windows & Linux Desktop
LOOP: Loop 1 — Initial Verification
DEBUGGER: Agent 14 — Debugger Agent

DEFECT: DEF-P5-01 (Missing Windows Add/Remove Programs registry configuration in installer.nsi)
REPRODUCED: YES
ROOT CAUSE:
- In `packaging/windows/installer.nsi`, the installation section copies files and writes an `uninstall.exe`, but does not create entries under `HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\StreamApp"`. Without these entries (`DisplayName`, `UninstallString`, `DisplayVersion`, `Publisher`), Windows Settings / Control Panel cannot detect or cleanly uninstall the application.
AFFECTED COMPONENT:
- packaging/windows/installer.nsi
SEVERITY:
- Major
RECOMMENDED FIX:
- Add `WriteRegStr` entries for `DisplayName`, `UninstallString`, `DisplayVersion`, `Publisher`, and `DisplayIcon` under the HKLM Uninstall key in `installer.nsi`, and corresponding `DeleteRegKey` in the Uninstall section.
REGRESSION RISK:
- None.
READY FOR RETEST:
- YES (Pending developer update)

---

DEFECT: DEF-P5-02 (Missing Ctrl+Q desktop shortcut for clean exit)
REPRODUCED: YES
ROOT CAUSE:
- In `client/lib/desktop/desktop_window_manager.dart`, `DesktopShortcutManager._handleKeyEvent` tests for `Ctrl + F`, but has no check for `Ctrl + Q`. On Windows and Linux, `Ctrl + Q` is the universal convention for exiting desktop applications.
AFFECTED COMPONENT:
- client/lib/desktop/desktop_window_manager.dart
SEVERITY:
- Minor
RECOMMENDED FIX:
- Add an optional `VoidCallback? onQuit` parameter to `DesktopShortcutManager` and check:
  `if (isControl && event.logicalKey == LogicalKeyboardKey.keyQ) { onQuit?.call(); return KeyEventResult.handled; }`
REGRESSION RISK:
- None.
READY FOR RETEST:
- YES (Pending developer update)
