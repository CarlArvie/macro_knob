# plan.md — KnobLaunch Orchestration Plan

## 1. Problem Classification
- **Domain**: SWE / Project
- **Stack**: C++ (Win32, GDI+) + AutoHotkey v2
- **Integrity Level**: development (Integrity Forensics verification required)

## 2. Agent Roles & Strategy
We will use a dual-track parallel structure:
1. **E2E Testing Track**:
   - Spawns a sub-orchestrator (`self` archetype) for test harness and case generation.
   - Deliverable: Comprehensive opaque-box test runner + test suite, resulting in `TEST_READY.md`.
2. **Implementation Track**:
   - Spawns subagents for sequential milestones.
   - Milestone 1: Scaffold, basic tray, JSON configs.
   - Milestone 2: Low-level keyboard hook (`WH_KEYBOARD_LL`) with hold threshold detection.
   - Milestone 3: WS_EX_LAYERED GDI+ drawing of radial menu.
   - Milestone 4: MacroRunner (Process, URL, AHK).
   - Milestone 5: E2E Integration (passing 100% of E2E tests).
   - Milestone 6: Adversarial Hardening (Challenger-led gaps verification).

## 3. Step-by-Step Task Delegation

| Step | Scope / Milestone | Assigned Agent Type | Expected Output | Verification Method |
|---|---|---|---|---|
| Step 1 | E2E Testing Track (Milestones T1 & T2) | `self` (Testing Sub-orch) | Test harness, 40+ test cases, `TEST_READY.md` | Execute test suite on a stub implementation |
| Step 2 | Implementation Milestone 1 | `teamwork_preview_worker` | CMakeLists.txt, config manager, system tray icon | Build check, verify `config.json` is generated |
| Step 3 | Implementation Milestone 2 | `teamwork_preview_worker` | WH_KEYBOARD_LL hook, hold/tap logic | Simulating key inputs, check hook logs |
| Step 4 | Implementation Milestone 3 | `teamwork_preview_worker` | GDI+ overlay window, angle calculation, hovering | Verify window class exists, visual overlay check |
| Step 5 | Implementation Milestone 4 | `teamwork_preview_worker` | MacroRunner & AutoHotkey subprocess execution | Verify AHK macro runs correctly on trigger |
| Step 6 | Implementation Milestone 5 (E2E Pass) | `self` (Impl Sub-orch) | Full integration, debug fixes | All Tier 1-4 tests pass via E2E test runner |
| Step 7 | Milestone 6 (Adversarial Hardening) | `teamwork_preview_challenger` + `teamwork_preview_reviewer` | Hardened coverage, bug fixes | Challenger verifies no gaps in edge cases |
| Step 8 | Forensic Audit | `teamwork_preview_auditor` | Audit report | Verify no hardcoding, no cheats, clean execution |

## 4. Verification Gating
- E2E Tests: 100% pass rate.
- Forensic Audit: Must return verdict CLEAN.
- Reviewer Verdicts: No vetoes.
- Challenger Verification: Successful checks.
