PROJECT: Cross-Platform Streaming App
PHASE: Phase 7 — Accessibility, Performance & Full QA
LOOP: Loop 1 — Initial Verification
DEBUGGER: Agent 14 — Debugger Agent

DEFECT: DEF-P7-01 (HeroBanner title clips under accessibility font scaling due to `maxLines: 1` and lacks root accessibility semantics)
REPRODUCED: YES
ROOT CAUSE:
- In `client/lib/widgets/hero_banner.dart`, lines 122-129 specify `maxLines: 1` on `item.title`. While suitable for default 14sp body text, high-scaling accessibility configurations (e.g. Android Text Magnification 150-200%) inflate `displayLarge` and `headlineLarge` font metrics, causing longer movie titles to overflow available horizontal space and truncate.
- Furthermore, the root widget does not declare `Semantics(container: true, label: "Featured: ${item.title}")`, causing screen readers to read disconnected text fragments rather than announcing the hero banner as a cohesive featured presentation.
AFFECTED COMPONENT:
- client/lib/widgets/hero_banner.dart
SEVERITY:
- Major
RECOMMENDED FIX:
- In `client/lib/widgets/hero_banner.dart`:
  1. Wrap the root `Container` in a `Semantics(container: true, label: 'Featured presentation: ${item.title}. ${item.description}')`.
  2. Increase `maxLines` on `item.title` to `2` to accommodate two-line wrapped titles under accessibility font scaling.
REGRESSION RISK:
- None. Enhances visual reflow and screen reader comprehension.
READY FOR RETEST:
- YES (Pending developer update)
