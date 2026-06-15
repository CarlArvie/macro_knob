# Handoff Report - Milestone 2: Key Hook Implementation Adversarial Review

## 1. Observation
- **File Checked**: `src/input_hook.cpp`
- **Lines of Interest**:
  - Timer creation in `LowLevelKeyboardProc` (lines 161-167):
    ```cpp
    if (!g_isHotkeyHeld) {
        g_isHotkeyHeld = true;
        DebugLog("LowLevelKeyboardProc: Setting hold timer.");
        if (g_hTimer) {
            DeleteTimerQueueTimer(NULL, g_hTimer, NULL);
            g_hTimer = NULL;
        }
        UINT timerDuration = (g_holdThresholdMs > 0) ? (UINT)g_holdThresholdMs : 0;
        CreateTimerQueueTimer(&g_hTimer, NULL, HoldTimerCallback, NULL, timerDuration, 0, WT_EXECUTEONLYONCE);
    }
    ```
  - Hold Timer Callback (lines 49-55) posting a window message:
    ```cpp
    VOID CALLBACK HoldTimerCallback(PVOID lpParameter, BOOLEAN TimerOrWaitFired) {
        (void)lpParameter;
        (void)TimerOrWaitFired;
        if (g_hDaemonWnd) {
            PostMessageW(g_hDaemonWnd, WM_TIMER, TIMER_ID_HOLD, 0);
        }
    }
    ```
  - Hold Timer Handler `HandleHoldTimer` (lines 281-297):
    ```cpp
    void HandleHoldTimer() {
        DebugLog("HandleHoldTimer called.");
        if (g_hTimer) {
            DeleteTimerQueueTimer(NULL, g_hTimer, NULL);
            g_hTimer = NULL;
        }
        if (!g_isHotkeyHeld) {
            DebugLog("HandleHoldTimer: hotkey is not held, aborting radial menu creation.");
            return;
        }
        if (!g_menuVisible) {
            g_menuVisible = true;
            DebugLog("HandleHoldTimer: Creating radial menu.");
            g_hRadialMenuWnd = CreateRadialMenu(g_hDaemonWnd);
            DebugLog("HandleHoldTimer: Radial menu created. HWND=" + std::to_string((unsigned long long)g_hRadialMenuWnd));
        }
    }
    ```
  - Simulated Event Bypass (lines 146-149):
    ```cpp
    if (pKeyInfo->dwExtraInfo == BYPASS_SIGNATURE) {
        DebugLog("LowLevelKeyboardProc: Bypassing signature event: vkCode=" + std::to_string(pKeyInfo->vkCode));
        return CallNextHookEx(g_hHook, nCode, wParam, lParam);
    }
    ```

- **Stress Test Output**:
  - We compiled and executed a custom C++ test binary `tests/hook_stress_tests.cpp`. When simulating rapid sequential keypresses where a new down press occurs after the previous timer fires but before its message is processed, we observed:
    ```
    Starting Input Hook Empirical Stress Tests...
    [Test Info] Hotkey Vk:  (hold_threshold: 150ms)
    Running TEST 1: Normal Tap (should NOT spawn radial menu)...
    TEST 1 passed.
    Running TEST 2: Normal Hold (should spawn radial menu)...
    TEST 2 passed.
    Running TEST 3: Bypass Signature (should bypass hook)...
    TEST 3 passed.
    Running TEST 4: Hold Timer Race Condition under rapid keypresses...
     - Tap 1 Down
     - Waiting for Timer 1 to fire asynchronously...
     - Tap 1 Up
     - Tap 2 Down
     - Pumping message queue to process delayed WM_TIMER...
     [BUG DETECTED] Radial menu was created prematurely! (FindWindow returned non-null HWND: 0000000000140798)
       The race condition allowed the stale WM_TIMER from Tap 1 to trigger menu creation on Tap 2 down immediately.
    Input Hook Empirical Stress Tests complete.
    ```

## 2. Logic Chain
1. `CreateTimerQueueTimer` runs asynchronously on a worker thread. When the duration passes, it calls `HoldTimerCallback` which executes `PostMessageW(g_hDaemonWnd, WM_TIMER, TIMER_ID_HOLD, 0)` to place the timer message in the window's queue.
2. In a busy UI thread or under rapid key sequence, the physical key can be released (Tap 1 Up) and pressed again (Tap 2 Down) before that queued `WM_TIMER` is dispatched by the main message loop.
3. Tap 1 Up sets `g_isHotkeyHeld = false` and cancels Timer 1.
4. Tap 2 Down sets `g_isHotkeyHeld = true` and starts a new timer (Timer 2, assigned to `g_hTimer`).
5. Next, the main thread dispatches the stale `WM_TIMER` (Message A) from Timer 1.
6. `HandleHoldTimer()` runs:
   - It checks `if (g_hTimer)` which is currently non-null pointing to **Timer 2**. It calls `DeleteTimerQueueTimer` on it, destroying the valid Timer 2, and setting `g_hTimer = NULL`.
   - It checks `if (!g_isHotkeyHeld)`. Since `g_isHotkeyHeld` was set to `true` by Tap 2 Down, this check fails to catch the stale message.
   - It proceeds to set `g_menuVisible = true` and spawns the radial menu.
7. Thus, the radial menu is spawned prematurely on Tap 2 Down immediately (0ms wait instead of 150ms), and its hold tracking is permanently broken because Timer 2 was cancelled.

## 3. Caveats
- The race condition was simulated using direct invocation of `LowLevelKeyboardProc` because `SendInput` is blocked with `ERROR_ACCESS_DENIED` in this environment's non-interactive window station. However, the simulation matches the exact serialized execution model of the Win32 message loop and low-level keyboard hooks.
- No other code paths were modified during testing, ensuring the integrity of the codebase.

## 4. Conclusion
The key hook implementation contains a critical race condition/correctness bug under rapid successive keypresses due to a lack of transaction/session tracking in the asynchronous timer messages. While simulated events bypass the hook cleanly and basic tap/hold thresholds function correctly under slow inputs, the hold timer state machine is fragile and can be broken under rapid tap sequences.

## 5. Verification Method
To reproduce this finding:
1. Compile the project and tests:
   ```powershell
   # First initialize MSVC build tools, then compile the stress test
   # We have created compile_stress.bat to make this easy:
   # cl.exe /EHsc /std:c++17 tests/hook_stress_tests.cpp src/input_hook.cpp src/config_store.cpp src/radial_menu.cpp src/macro_runner.cpp /Iinclude /Isrc /link user32.lib shell32.lib shlwapi.lib gdi32.lib gdiplus.lib /out:bin/hook_stress_tests.exe
   ```
   Note: The stress test binary has been successfully compiled and placed at `bin/hook_stress_tests.exe`.
2. Run the test binary:
   ```powershell
   .\bin\hook_stress_tests.exe
   ```
3. Observe the output of `TEST 4` demonstrating the premature menu creation.

---

## Adversarial Review Challenge Report

### Challenge Summary
- **Overall risk assessment**: HIGH

### Challenges

#### [High] Challenge 1: Hold Timer Race Condition Under Rapid Keypresses
- **Assumption challenged**: Assumes that checking `g_isHotkeyHeld` alone is sufficient to validate if a timer message in the queue belongs to the current hold session.
- **Attack scenario**: Tap 1 is held just long enough to trigger the timer, then released. Before the resulting `WM_TIMER` is processed by the main thread, Tap 2 is pressed down.
- **Blast radius**: The radial menu is created immediately upon Tap 2 Down, and the active timer for Tap 2 is cancelled, leaving the application in an out-of-sync state.
- **Mitigation**: Introduce a sequence counter (`g_timerSeq`) incremented on keydown. Pass this sequence ID to the timer callback and verify it matches the active sequence in `HandleHoldTimer`.

#### [Medium] Challenge 2: Tap Latency and Compressed Duration
- **Assumption challenged**: Assumes that delaying keydown events and simulating them as a 0ms press/release sequence is transparent to all target applications.
- **Attack scenario**: A target application expects a minimum hold duration to register a tap (e.g. 50ms) or is sensitive to key down latency.
- **Blast radius**: Target application fails to register volume mute taps, or experiences noticeable latency (equal to the time the user held the key before releasing it).
- **Mitigation**: Introduce a non-zero hold duration for simulated taps, or allow down events to pass through and only block them if they exceed the hold threshold (though the latter is difficult with Win32 hooks since events cannot be retroactively blocked).

### Stress Test Results
- **Scenario 1: Normal Tap** → No radial menu shown, simulated tap sent. → **PASS**
- **Scenario 2: Normal Hold** → Radial menu shown, closed on release. → **PASS**
- **Scenario 3: Bypass Signature** → Hook bypasses event (`dwExtraInfo == BYPASS_SIGNATURE`). → **PASS**
- **Scenario 4: Rapid Successive Taps (Race Condition)** → Radial menu is NOT created for Tap 2 until held for 150ms. → **FAIL** (Radial menu is created immediately on Tap 2 Down, and Timer 2 is deleted).

### Unchallenged Areas
- **Subprocess handling and GDI+ rendering details**: Outside the scope of the key hook state machine verification.
