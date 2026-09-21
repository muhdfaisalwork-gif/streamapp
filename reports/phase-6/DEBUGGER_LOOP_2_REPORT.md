PROJECT: Cross-Platform Streaming App
PHASE: Phase 6 — Monetization & Analytics
LOOP: Loop 2 — Regression Verification
DEBUGGER: Agent 14 — Debugger Agent

DEFECT: DEF-P6-02 (`SponsorCard` fails to record impression telemetry when updated with a new campaign in `didUpdateWidget`)
REPRODUCED: YES
ROOT CAUSE:
- In `client/lib/widgets/sponsor_card.dart`, `_SponsorCardState` triggers `widget.onImpression?.call()` only during `initState()`.
- When the parent widget rebuilds with a different `campaign` instance (or when the widget element is reused by Flutter's reconciliation engine for a different movie/campaign), `initState()` is not called again.
- Without an override of `didUpdateWidget(SponsorCard oldWidget)`, dynamic campaign rotations will fail to register impressions for subsequent campaigns.
AFFECTED COMPONENT:
- client/lib/widgets/sponsor_card.dart
SEVERITY:
- Major
RECOMMENDED FIX:
- Implement `didUpdateWidget` in `_SponsorCardState`:
  ```dart
  @override
  void didUpdateWidget(covariant SponsorCard oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.campaign.id != widget.campaign.id) {
      widget.onImpression?.call();
    }
  }
  ```
REGRESSION RISK:
- None. Standard Flutter widget lifecycle practice.
READY FOR RETEST:
- YES (Pending developer update)
