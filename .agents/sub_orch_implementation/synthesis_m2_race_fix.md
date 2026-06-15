# Milestone 2 Hold Timer Race Condition Fix Plan

## 1. Objective
Eliminate the stale timer race condition reported by Challenger 2, where a delayed `WM_TIMER` message from a previous hold session could cancel a new timer and prematurely open the menu on a subsequent key down event.

## 2. Design

### A. Custom Message and Sequence Counter
- Define `WM_HOLD_TIMER` as `(WM_USER + 2)` in `src/input_hook.h`.
- Maintain a static counter `g_timerSeq` in `src/input_hook.cpp`, initialized to 0.
- Declare `void HandleHoldTimer(WPARAM wParam);` in `src/input_hook.h`.

### B. Input Hook Callback (`src/input_hook.cpp`)
- On key down, increment `g_timerSeq` and pass it as the timer callback parameter:
  ```cpp
  g_timerSeq++;
  CreateTimerQueueTimer(&g_hTimer, NULL, HoldTimerCallback, (PVOID)(ULONG_PTR)g_timerSeq, timerDuration, 0, WT_EXECUTEONLYONCE);
  ```
- In `HoldTimerCallback`, post the custom message with the sequence ID as the `wParam`:
  ```cpp
  VOID CALLBACK HoldTimerCallback(PVOID lpParameter, BOOLEAN TimerOrWaitFired) {
      (void)TimerOrWaitFired;
      ULONG_PTR seq = (ULONG_PTR)lpParameter;
      if (g_hDaemonWnd) {
          PostMessageW(g_hDaemonWnd, WM_HOLD_TIMER, (WPARAM)seq, 0);
      }
  }
  ```
- In `HandleHoldTimer(WPARAM wParam)`, validate the sequence:
  ```cpp
  void HandleHoldTimer(WPARAM wParam) {
      UINT seq = (UINT)wParam;
      DebugLog("HandleHoldTimer called with seq=" + std::to_string(seq));
      if (seq != g_timerSeq) {
          DebugLog("HandleHoldTimer: stale timer message (seq mismatch), ignoring.");
          return;
      }
      // Continue with deleting timer and showing radial menu...
  }
  ```

### C. Daemon Window Procedure (`src/main.cpp`)
- Import `WM_HOLD_TIMER` and handle it in `WndProc`:
  ```cpp
  case WM_HOLD_TIMER:
      HandleHoldTimer(wParam);
      break;
  ```
  Ensure any legacy `WM_TIMER` logic targeting `TIMER_ID_HOLD` is cleaned up/removed.

### D. Stress Test Adaptation (`tests/hook_stress_tests.cpp`)
- Update `TestWndProc` to handle `WM_HOLD_TIMER` instead of `WM_TIMER`, and pass `wParam` to `HandleHoldTimer`:
  ```cpp
  LRESULT CALLBACK TestWndProc(HWND hWnd, UINT message, WPARAM wParam, LPARAM lParam) {
      if (message == WM_HOLD_TIMER) {
          HandleHoldTimer(wParam);
          return 0;
      }
      return DefWindowProcW(hWnd, message, wParam, lParam);
  }
  ```

## 3. Verification Tasks
1. Compile the project and stress tests using `build.bat` / MSVC.
2. Run `.\bin\hook_stress_tests.exe` and confirm that all tests, including `TEST 4`, pass successfully.
3. Run `.\bin\config_store_tests.exe` and confirm it passes.
4. Run Python tests `python tests/test_runner.py` and confirm they run and pass (or skip).
