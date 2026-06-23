# plan.md — Rotary Knob Support & Input Hook Interception Plan

## 1. Problem Classification
- **Domain**: SWE / Project
- **Stack**: C++ (Win32, WH_KEYBOARD_LL / WM_INPUT / WM_APPCOMMAND) + Python (verification script)
- **Integrity Level**: demo (Integrity Forensics verification required)

## 2. Agent Roles & Strategy
We will execute the implementation of the rotary menu navigation via hardware volume knob rotations using the standard Explorer -> Worker -> Reviewer -> Challenger -> Auditor cycle.
To ensure the requirements are met, we will address:
1. **R1. Reliable Hardware Interception**:
   - The low-level hook `WH_KEYBOARD_LL` might block due to thread locking. We will cache configuration variables (like `interaction_mode`, `rotary_prev`, `rotary_next`, `hotkey_override`) instead of calling `g_configStore.GetGlobal()` in the timing-critical hook function.
   - If physical knob rotation events are bypassed by the keyboard hook, we will add support for raw input via `RegisterRawInputDevices` for HID Consumer Control devices (`UsagePage = 0x0C`, `Usage = 0x01` / `0x02` or similar) or handle `WM_APPCOMMAND` messages in the daemon window.
2. **R2. Swallow Volume Change Events**:
   - When the menu is triggered or navigated in `"rotary"` mode, we must ensure that `VK_VOLUME_UP` and `VK_VOLUME_DOWN` keystrokes (either from raw input or keyboard hook) are entirely swallowed so the Windows system volume remains unchanged.
3. **R3. Execution Key Reliability**:
   - The execution key `PgUp` must be reliable. We will verify that pressing `PgUp` while the radial menu is open triggers `TriggerSlotMacro` for the hovered slot and immediately destroys the menu cleanly.
4. **Acceptance Criteria Script (`test_rotary_hook.py`)**:
   - We will write a python script `tests/test_rotary_hook.py` that simulates low-level events for `Volume_Up`, `Volume_Down`, and `PgUp` using ctypes. It will verify that:
     - The menu appears on rotation.
     - System volume does not change.
     - PgUp executes the macro and closes the UI window.

## 3. Step-by-Step Task Delegation

| Step | Scope / Milestone | Assigned Agent Type | Expected Output | Verification Method |
|---|---|---|---|---|
| Step 1 | Exploration & Hook Strategy | `teamwork_preview_explorer` | Analysis of why current hook fails, raw input device registration options, and clean hook implementation strategy | Review explorer handoff |
| Step 2 | Implementation (Hook + Test Script) | `teamwork_preview_worker` | Modified `src/input_hook.cpp`, `src/main.cpp`, and newly created `tests/test_rotary_hook.py` | Compiles, test script successfully runs |
| Step 3 | Reviewer Verification | `teamwork_preview_reviewer` | Review of changes to ensure no thread blocking, proper swallowing, and code conformance | Reviewer handoff check |
| Step 4 | Challenger Verification | `teamwork_preview_challenger` | Executes `tests/test_rotary_hook.py` and other test cases, verifies volume changes are swallowed | Challenger logs verification |
| Step 5 | Forensic Audit | `teamwork_preview_auditor` | Audit report validating clean, non-cheating implementation | Audit verdict must be CLEAN |

## 4. Verification Gating
- `test_rotary_hook.py` must pass 100%.
- Volume level remains completely unchanged before and after the simulated volume keystrokes.
- Forensic Audit returns CLEAN.
- Reviewer Verdicts: No vetoes.
