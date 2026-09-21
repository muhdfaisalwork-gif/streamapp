# MANDATORY THREE-LOOP E2E VERIFICATION GATE PROTOCOL

## 1. PURPOSE AND MANDATE

Every phase in the Cross-Platform Streaming App must undergo and pass **three full, independent verification loops** before submission to the Project Manager (PM) for final phase sign-off.

A developer declaring work "done" is merely a request for initial review.

```text
Phase Development
      ↓
Phase Internal Check
      ↓
QA LOOP 1 (Initial Verification)
      ↓
Debugger Loop 1 (Root Cause & Reproduction)
      ↓
Developer Loop 1 Corrections
      ↓
E2E Tester Loop 1 (Journey Verification)
      ↓
QA LOOP 2 (Regression & Edge Cases)
      ↓
Debugger Loop 2 (Fix Verification & Residual Defects)
      ↓
Developer Loop 2 Corrections
      ↓
E2E Tester Loop 2 (Full Journey Retest)
      ↓
QA LOOP 3 (Final Release Verification)
      ↓
Debugger Loop 3 (Stability & Non-Regression Sign-off)
      ↓
Developer Loop 3 Final Polish
      ↓
E2E Tester Loop 3 (End-to-End User Experience Validation)
      ↓
PM Final Review (15-Point Inspection)
      ↓
PHASE APPROVED or PHASE REJECTED (Return for Rework)
```

---

## 2. LOOP 1: INITIAL VERIFICATION

### QA Agent (QA Loop 1 Report)
- Verifies deliverables against phase acceptance criteria.
- Validates functional requirements, UI/layout behavior, API contract schemas, and error states.
- Documents all identified defects with severity (Blocker, Critical, Major, Minor).

### Debugger Agent (Debugger Loop 1 Report)
- Reproduces each defect reported in QA Loop 1.
- Analyzes code, logs, and traces to determine root cause and affected components.
- Formulates technical diagnosis and provides targeted fix recommendations.

### Development Agent(s) (Developer Loop 1 Fix Log)
- Implements fixes strictly addressing diagnosed root causes.
- Documents what was changed, why, affected files, and potential regression risks.

### E2E Tester Agent (E2E Tester Loop 1 Report)
- Executes end-to-end user journeys encompassing the corrected workflows.
- Validates that primary user flows succeed without breaking related functions.

---

## 3. LOOP 2: REGRESSION VERIFICATION

### QA Agent (QA Loop 2 Report)
- Confirms resolution of Loop 1 defects.
- Performs regression testing across related modules, edge cases, and cross-platform boundaries.
- Identifies any secondary defects introduced by Loop 1 fixes.

### Debugger Agent (Debugger Loop 2 Report)
- Re-verifies remaining or new defects.
- Verifies that Loop 1 fixes did not introduce architectural side-effects or regressions.

### Development Agent(s) (Developer Loop 2 Fix Log)
- Resolves residual issues with regression safety analysis.

### E2E Tester Agent (E2E Tester Loop 2 Report)
- Re-executes the complete suite of user journeys with edge conditions, offline scenarios, and error-recovery paths.

---

## 4. LOOP 3: FINAL VERIFICATION

### QA Agent (QA Loop 3 Report)
- Executes full functional regression suite.
- Performs accessibility checks, platform compatibility checks, and boundary tests.
- Issues QA sign-off recommendation.

### Debugger Agent (Debugger Loop 3 Report)
- Performs final stability, memory, and error-budget audit.
- Confirms zero unresolved high-severity defects.
- Issues Debugger sign-off recommendation.

### E2E Tester Agent (E2E Tester Loop 3 Report)
- Executes full customer-perspective validation across all supported platforms.
- Validates complete lifecycle journeys from cold start to media playback and teardown.
- Issues E2E Tester sign-off recommendation.

---

## 5. PM FINAL PHASE CHECK

The PM conducts a comprehensive review of:
1. Original phase requirements.
2. Development report.
3. QA Loop 1, 2, and 3 reports.
4. Debugger Loop 1, 2, and 3 reports.
5. E2E Tester Loop 1, 2, and 3 reports.
6. Known issues and risk mitigations.
7. Security, performance, legal, and accessibility audit status.

The PM renders the binary decision:
- **PHASE APPROVED**: Movement to next phase authorized.
- **PHASE REJECTED**: Immediate return to development agent for targeted rework, restarting the verification cycle.
