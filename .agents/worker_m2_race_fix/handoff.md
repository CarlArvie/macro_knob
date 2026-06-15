# Handoff Report — Milestone 2 Hold Timer Race Condition Fix

## 1. Observation
- The project originally compiled cleanly, but running `bin\hook_stress_tests.exe` failed with:
  ```
  Starting Input Hook Empirical Stress Tests...
  [Test Info] Hotkey Vk: F13 (hold_threshold: 150ms)
  Running TEST 1: Normal Tap (should NOT spawn radial menu)...
  Assertion failed at line 94: resDown == 1
  ```
  This occurred because the local config file `config/config.json` had `"hotkey_override": "F13"`, which mismatched the default `VK_VOLUME_MUTE` used inside `hook_stress_tests.cpp`'s simulated events.
- In the original design, `HoldTimerCallback` posted `WM_TIMER` with `TIMER_ID_HOLD`. Because `WM_TIMER` was handled in `WndProc` without sequence validation, a stale timer event from a previous tap (timer fired asynchronously but main thread hadn't processed it yet) could sit in the queue.
- If a new tap began (`g_isHotkeyHeld = true`) and the stale `WM_TIMER` message was then processed, `HandleHoldTimer()` would inspect `g_isHotkeyHeld`, see it as true, and prematurely create the radial menu for the new tap session.

## 2. Logic Chain
- To eliminate this race condition, we must ensure each timer execution is tagged with a unique sequence number.
- In `src/input_hook.h`, we defined:
  ```cpp
  #define WM_HOLD_TIMER (WM_USER + 2)
  void HandleHoldTimer(WPARAM wParam);
  ```
- In `src/input_hook.cpp`, we implemented:
  - A static sequence counter: `static UINT g_timerSeq = 0;`
  - On keydown: `g_timerSeq++` is executed, and `(PVOID)(ULONG_PTR)g_timerSeq` is passed as the parameter to `CreateTimerQueueTimer`.
  - In `HoldTimerCallback`: the sequence ID is extracted from `lpParameter` and posted to the daemon window as the `wParam` of `WM_HOLD_TIMER`.
  - In `HandleHoldTimer(WPARAM wParam)`: the sequence ID from `wParam` is compared to `g_timerSeq`. If they do not match, the stale timer message is ignored.
- In `src/main.cpp`:
  - The legacy `WM_TIMER` case for `TIMER_ID_HOLD` was removed.
  - The `WM_HOLD_TIMER` message case was added, routing `wParam` to `HandleHoldTimer(wParam)`.
- In `tests/hook_stress_tests.cpp`:
  - `TestWndProc` was updated to handle `WM_HOLD_TIMER` and pass `wParam` to `HandleHoldTimer(wParam)`.
  - A config override step was added at the start of `main()` to dynamically reset the `g_configStore` parameters (`hotkey_override = ""` and `hold_threshold_ms = 150`), forcing the tests to consistently run against the default `VK_VOLUME_MUTE` mapping.
  - In TEST 4, a `TEST_ASSERT(hMenu == NULL)` was added to immediately abort with a failure code if premature menu creation is detected.
- In `tests/compile_tests.bat`:
  - Added the compilation command for `tests/hook_stress_tests.cpp` to ensure the stress test binary compiles cleanly when rebuilding the test suite.

## 3. Caveats
- Non-interactive session: During Python test execution (`python tests/test_runner.py`), E2E GUI-related tests (50 tests) are skipped due to a headless environment. This is expected and standard for this testing container.
- No other caveats.

## 4. Conclusion
- The race condition has been successfully fixed using the `WM_HOLD_TIMER` custom message and the `g_timerSeq` sequence-counter validation. Stale timer messages from previous hold sessions are now safely ignored, preventing premature menu creation.

## 5. Verification Method
- Recompile the project using `.\build.bat`.
- Recompile the C++ test suite by running `.\tests\compile_tests.bat`.
- Run the stress tests:
  ```
  .\bin\hook_stress_tests.exe
  ```
  Verify it outputs `[PASS] Radial menu was not created prematurely.` for TEST 4 and ends with `Input Hook Empirical Stress Tests complete.` with exit code 0.
- Run the C++ unit tests:
  ```
  .\bin\config_store_tests.exe
  ```
  Verify it output `ALL TESTS PASSED SUCCESSFULLY!`.
- Run the Python test suite:
  ```
  python tests/test_runner.py
  ```
  Verify that all tests run and pass (or skip).
