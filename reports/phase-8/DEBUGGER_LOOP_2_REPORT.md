PROJECT: Cross-Platform Streaming App
PHASE: Phase 8 — Production Readiness, Distribution & Launch
LOOP: Loop 2 — Regression Verification
DEBUGGER: Agent 14 — Debugger Agent

DEFECT: DEF-P8-02 (SettingsScreen lacks accessible dialog or review triggers for Terms of Service and Privacy Policy)
REPRODUCED: YES
ROOT CAUSE:
- In `client/lib/screens/settings_screen.dart`, lines 71-98 provide an `OutlinedButton.icon` solely for DMCA takedown intake.
- App store guidelines (Google Play Developer Program Policy, Apple App Store Review Guidelines, and general consumer protection mandates) require direct, accessible in-app presentation or links to the application's Privacy Policy and Terms of Service.
AFFECTED COMPONENT:
- client/lib/screens/settings_screen.dart
SEVERITY:
- Major
RECOMMENDED FIX:
- In `client/lib/screens/settings_screen.dart`, add buttons in a clean `Wrap` or `Row`:
  1. "Terms of Service": displays an `AlertDialog` summarizing the open-source licensing, acceptable use, and zero commercial copyright policy.
  2. "Privacy Policy": displays an `AlertDialog` summarizing the Zero-PII commitment, DNT/GPC compliance, and local storage guarantees.
  3. "DMCA Takedown": existing takedown dialog.
REGRESSION RISK:
- None.
READY FOR RETEST:
- YES (Pending developer update)
