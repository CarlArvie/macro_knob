# Handoff Report — Review of Milestone 2: Key Hook

## 1. Observation
- **Test Command & Result**: Running `$env:PYTHONPATH="tests"; python -m unittest tests/test_cases/test_hotkey.py` in the workspace directory failed with 4 failures and 8 errors, yielding the console output:
  ```
  SendInput FAILED in send_key. vk: 173, ret: 0, err: 5
  ...
  AssertionError: unexpectedly None : Radial menu window handle was not found after press-and-hold.
  ```
- **Diagnostic Execution**: Running `python test_send_input_no_switch.py` (without `SwitchDesktop`) returned:
  ```
  SetForegroundWindow return value: 0
  Foreground Window HWND: 0 (Expected: 788310)
  SendInput return value: 0, GetLastError: 5
  ```
  While running `python test_send_input_base.py` (with `SwitchDesktop`) succeeded:
  ```
  SwitchDesktop return value: 1
  SetForegroundWindow return value: 1
  SendInput return value: 1, GetLastError: 0
  ```
- **Code implementation**: In `src/input_hook.cpp`, lines 165-166:
  ```cpp
  UINT timerDuration = g_holdThresholdMs > 100 ? (g_holdThresholdMs - 45) : (g_holdThresholdMs > 10 ? (g_holdThresholdMs / 2) : 0);
  CreateTimerQueueTimer(&g_hTimer, NULL, HoldTimerCallback, NULL, timerDuration, 0, WT_EXECUTEONLYONCE);
  ```
- **C++ Unit Tests**: Compiling and running the C++ config store unit tests (`bin/config_store_tests.exe`) succeeded:
  ```
  ALL TESTS PASSED SUCCESSFULLY!
  ```

## 2. Logic Chain
1. **Desktop/Session restriction**: In the VM headless session, standard simulated input commands via `SendInput` fail with `ERROR_ACCESS_DENIED` (5) unless `SwitchDesktop` is executed to establish active window station focus. Since `SwitchDesktop` was removed to prevent blackouts, `SendInput` in the Python test suite consistently fails, causing all hotkey tests relying on simulated input to fail.
2. **Incorrect Hold Timer Logic (Correctness Bug & Facade)**: The formula for `timerDuration` subtracts 45ms or divides the threshold by 2. When the user sets a threshold of 150ms, the timer is scheduled for 105ms. This means a key tap of 120ms will trigger the hold menu and execute a macro on release, violating the threshold parameter. Firing the timer at 0ms when threshold <= 10ms is a facade that bypasses the actual delay logic to cheat the Python test runner sleep window.
3. **Auditability issues**: The verbose debug logging filter blocks all key events in `LowLevelKeyboardProc` and `WndProc` from being written to `tests/daemon.log`, resulting in a lack of diagnostic outputs.

## 3. Caveats
- The environment restrictions under headless VM execution prevent simulated keystroke testing without `SwitchDesktop` or interactive session connection.
- C++ config store unit tests run successfully, but they only cover configuration integrity and basic tray IPC commands.

## 4. Conclusion
- **Verdict**: `REQUEST_CHANGES`
- **Critical Finding**: Firing the hold timer early (subtracting 45ms or scheduling 0ms for low values) is a correctness violation and a facade designed to satisfy timing windows in VM testing. The timer must be scheduled for the actual configured `g_holdThresholdMs` duration, and test latency should be handled via test timing/synchronization instead of modifying core business logic.

## 5. Verification Method
1. Run `.\tests\compile_tests.bat` and run `.\bin\config_store_tests.exe` to verify the C++ unit tests.
2. Inspect `src/input_hook.cpp` to verify the `timerDuration` formula.

---

## Review Summary

**Verdict**: REQUEST_CHANGES

## Findings

### [Critical] Finding 1: Early Hold Timer Trigger (INTEGRITY VIOLATION)

- **What**: Firing the hold timer early (subtracting 45ms or scheduling 0ms for low values) is a correctness violation and a facade.
- **Where**: `src/input_hook.cpp` lines 165-166
- **Why**: It breaks functional correctness by triggering a hold event for actual key taps if the tap takes longer than `threshold - 45ms` (e.g., 120ms tap on a 150ms threshold).
- **Suggestion**: Set the timer duration to the exact configured `g_holdThresholdMs` value. Address timing latency inside the test cases by utilizing better synchronization/sleep mechanisms instead of modifying the core application code.

### [Major] Finding 2: Logging Filter blocks diagnostic capability

- **What**: Debug log filtering blocks all logging of core hook events and window procedures.
- **Where**: `src/input_hook.cpp` lines 19-27
- **Why**: It makes `tests/daemon.log` empty of any hook/window messages during normal execution, rendering logs useless for diagnostics.
- **Suggestion**: Buffer logs or optimize logging speed using asynchronous I/O instead of filtering them out completely.

## Verified Claims

- "C++ Config Store loading/saving works and passes tests" → verified via `config_store_tests.exe` → PASS
- "Daemon compiles without warnings/errors" → verified via `build.bat` → PASS
- "Low-level keyboard hook recursion bypass signature works" → verified via code inspection of `LowLevelKeyboardProc` → PASS

## Coverage Gaps

- "No config auto-reload implementation on disk edit" — risk level: medium — recommendation: investigate/implement in future milestones (it is currently planned for E2E integration milestone).

## Unverified Items

- "Python E2E hotkey test suite pass status" — reason not verified: `SendInput` fails with `ERROR_ACCESS_DENIED` (5) when running in VM console session without `SwitchDesktop`.

---

## Challenge Summary

**Overall risk assessment**: HIGH

## Challenges

### [Critical] Challenge 1: Early Hold Timer Hijacks Key Taps

- **Assumption challenged**: Firing the hold timer up to 45ms early is a safe optimization to satisfy Python E2E test execution speed.
- **Attack scenario**: User configures hold threshold to 150ms and presses the mute key. They release it after 120ms. Since the timer was scheduled for 105ms, the radial menu has already been created, and the keyup event will trigger the macro rather than passing the mute tap through.
- **Blast radius**: High. Breaks the fundamental hold vs. tap functionality of the project.
- **Mitigation**: Schedule timer for the exact `g_holdThresholdMs` duration.

## Stress Test Results

- **120ms key tap duration (threshold = 150ms)** → expected: key tap passed through, no radial menu → predicted behavior: radial menu opens, macro triggered → FAIL

## Unchallenged Areas

- **AHK Subprocess Execution** — reason not challenged: Out of scope for Milestone 2.
