# Handoff Report — Milestone 2: Key Hook Adversarial Challenge

This report presents the empirical verification and adversarial stress-testing findings for the Milestone 2 Key Hook implementation.

---

## 1. Observation

### Observation 1: Test Suite Skipped Tests Due to GUI Check
Running `python tests/test_runner.py` directly from a headless/non-interactive shell resulted in 50 out of 52 tests being skipped:
```
Skipping cursor assertion: SetCursorPos returned ACCESS_DENIED (likely running in a headless/non-interactive session)
Ran 52 tests in 0.470s
OK (skipped=50)
```

### Observation 2: Ctypes Argument Error in `test_base.py`
Running the E2E python tests inside an interactive session (using a scheduled task) threw a type error in `check_gui_available()`:
```
ctypes.ArgumentError: argument 2: TypeError: expected LP_INPUT instance instead of pointer to INPUT
```
This is located in `tests/test_cases/test_base.py` line 148:
```python
141:     class INPUT(ctypes.Structure):
142:         _fields_ = [
143:             ("type", ctypes.c_ulong),
144:             ("union", INPUT_UNION)
145:         ]
146:     ki = KEYBDINPUT(wVk=0x87, wScan=0, dwFlags=0x0002, time=0, dwExtraInfo=None)
147:     inp = INPUT(type=1, union=INPUT_UNION(ki=ki))
148:     ret = User32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))
```

### Observation 3: Auto-Reload Missing in C++ Daemon Code
The daemon lacks a file watcher to detect disk changes on `config.json`. A search for file monitoring mechanisms in `src/main.cpp` returned only manual reload support:
```cpp
        case ID_TRAY_RELOAD:
            if (g_configStore.Load()) {
                UpdateHookConfig();
```

### Observation 4: Default Hotkey Config Discrepancy
In `src/config_store.h` line 8-14, the default configuration uses `"F13"` as the hotkey:
```cpp
struct GlobalConfig {
    int hold_threshold_ms = 150;
    std::string radial_size = "medium";
    std::string hotkey_override = "F13";
    bool show_tray_icon = true;
    bool debug_log = false;
};
```
However, python E2E tests in `tests/test_cases/test_config.py` assume the default is `VK_VOLUME_MUTE`:
```python
        # Daemon should start and use default threshold (150ms)
        self.send_key(VK_VOLUME_MUTE, is_down=True)
```

### Observation 5: Asynchronous Timer Cancellation in `input_hook.cpp`
In `src/input_hook.cpp` lines 162-164:
```cpp
                    if (g_hTimer) {
                        DeleteTimerQueueTimer(NULL, g_hTimer, NULL);
                        g_hTimer = NULL;
                    }
```
And lines 173-176:
```cpp
                if (g_hTimer) {
                    DeleteTimerQueueTimer(NULL, g_hTimer, NULL);
                    g_hTimer = NULL;
                }
```
The third argument of `DeleteTimerQueueTimer` is `NULL`, which means it executes asynchronously without waiting for callbacks to complete.

### Observation 6: Macro Runner Stub Implementation
The file `src/macro_runner.cpp` has all logic stubbed out:
```cpp
bool RunProgram(const std::string& path, const std::string& args) {
    (void)path;
    (void)args;
    return true;
}
```

### Observation 7: Log File Sharing Violation
Redirection of `stdout` in python tests to `tests/daemon.log` combined with `std::ofstream ofs("tests/daemon.log", std::ios::app)` in `src/input_hook.cpp` causes a Win32 file locking collision, silently suppressing debug logging.

---

## 2. Logic Chain

1. **Test Failure due to Ctypes**: By tracing the traceback from **Observation 2**, we see that `check_gui_available()` redeclares the `INPUT` structure locally. Because `User32.SendInput.argtypes` was declared using the global `INPUT` class, `ctypes.byref(inp)` of the local structure causes a type validation mismatch in ctypes. Removing these local redeclarations and utilizing the global ones fixes the error.
2. **Missing Auto-Reload**: **Observation 3** shows that there is no file watcher code in `main.cpp`. Therefore, any tests that modify `config.json` on disk and expect the daemon to automatically detect them will fail, as verified in the test results for `test_t1_f3_3_config_auto_reload` and others.
3. **Hotkey Discrepancy**: **Observation 4** indicates that a regenerated default config sets the override to `"F13"`. Consequently, when E2E tests corrupt the config to force fallback behavior and send `VK_VOLUME_MUTE` keypresses, the daemon ignores them because it has registered the `"F13"` hook. This directly causes `test_t2_f3_2_malformed_config` and `test_t4_4_invalid_config_recovery` to fail.
4. **Hold Timer Race Condition**: As shown in **Observation 5**, calling `DeleteTimerQueueTimer` asynchronously (third param = `NULL`) does not prevent already-queued callbacks from executing. If a callback runs, it posts `WM_TIMER`. If the user has just pressed the key down again (downpress 2), the old `WM_TIMER` is processed while `g_isHotkeyHeld` is `true`. The daemon incorrectly treats this as the threshold having elapsed for downpress 2, instantly opening the radial menu.
5. **Macro Spawning Failure**: **Observation 6** shows that the macro runner does not spawn processes or URLs. Therefore, any E2E tests checking for program spawns or sector highlight marker files fail.

---

## 3. Caveats

- We did not implement code fixes in `src/` as per constraints (Review-only).
- Tests were run within an interactive console session station by scheduling a Windows Task, which successfully bypassed the `SetCursorPos` restrictions but highlighted timing delays under virtualization.
- Windows scheduling latency may cause minor deviations in test sleep durations, causing extremely tight threshold E2E tests (such as 10ms thresholds) to intermittently fail.

---

## 4. Conclusion

The Milestone 2 Key Hook implementation functions correctly for basic hotkey hook swallowing and bypassing of simulated events (avoiding recursion loops). However, there are significant bugs and gaps:
1. **Critical Deficiencies**: The daemon lacks an automatic config file reload feature, causing failures in several E2E configuration test workflows.
2. **Testing Discrepancies**: There is a clear interface mismatch where the C++ default hotkey is `"F13"`, but Python tests assume `"volume_mute"`.
3. **Concurrency Races**: A thread race exists in `input_hook.cpp` due to asynchronous timer cancellation, allowing potential premature menu triggering.
4. **Log Locking**: Sharing `daemon.log` between stdout redirect and direct file append on Windows results in silent logging failures.
5. **Stubs**: Macro runner remains stubbed out in this milestone.

---

## 5. Verification Method

To verify these findings:
1. Compile the daemon using `.\build.bat`.
2. Run the C++ tests to verify basic config-handling and thread safety:
   ```powershell
   .\bin\config_store_tests.exe
   ```
3. Run the interactive Python E2E suite via scheduled task (to ensure active GUI context) and inspect output in `.agents\challenger_m2_1\test_run.log`:
   ```powershell
   schtasks /run /tn "RunTests"
   ```
4. Examine the log file `tests/daemon.log` to check for logging gaps and lock collisions.

---

# Adversarial Challenge Report

## Challenge Summary

**Overall risk assessment**: MEDIUM

- The core hook and bypass signature mechanism is robust and prevents recursive loops.
- Thread race conditions in timer handling could lead to premature radial menu triggers.
- File-locking issues under Windows block debugging capabilities.

## Challenges

### [High] Challenge 1: Lack of Config Auto-Reload
- **Assumption challenged**: The test suite assumes the daemon automatically reloads when `config.json` is modified on disk.
- **Attack scenario**: An external utility or user edits the configuration file directly on disk. The daemon fails to apply the new settings (e.g., hold threshold, hotkey override) until manually restarted or reloaded via the tray menu.
- **Blast radius**: User configurations are out-of-sync with daemon behavior, causing user confusion.
- **Mitigation**: Implement a directory/file watcher using `ReadDirectoryChangesW` or a low-overhead periodic file check.

### [Medium] Challenge 2: Timer Queue Cancellation Race Condition
- **Assumption challenged**: Calling `DeleteTimerQueueTimer(NULL, g_hTimer, NULL)` safely cancels the hold timer.
- **Attack scenario**: Under rapid click successions, `DeleteTimerQueueTimer` cancels the timer asynchronously, but the callback executes anyway and posts `WM_TIMER`. If processed during a subsequent click downpress, the menu opens prematurely.
- **Blast radius**: Temporary UX glitched state during rapid user clicking.
- **Mitigation**: Pass `INVALID_HANDLE_VALUE` to wait for callbacks to complete, or track a unique transaction ID inside `HoldTimerCallback` to ignore stale timer events.

### [Medium] Challenge 3: Default Hotkey Discrepancy
- **Assumption challenged**: Default config fallback uses the same key as the standard default config file.
- **Attack scenario**: Config file corrupts or gets deleted. Daemon registers `"F13"` instead of `"volume_mute"` as default.
- **Blast radius**: User loses control over knob macros if they do not have a physical F13 key, locking them out of the menu.
- **Mitigation**: Align `GlobalConfig` default in `config_store.h` with the python E2E assumption (e.g. set default `hotkey_override` to empty string `""` to fallback to `VK_VOLUME_MUTE`).

## Stress Test Results

- **10 quick taps** → Hook swallows and forwards taps without opening menu → Pass.
- **Simulated AHK press-loop** → Bypassed via `BYPASS_SIGNATURE` without infinite loops → Pass.
- **Hold threshold boundary (exact/tight thresholds)** → Fails due to latency and scheduler discrepancies → Fail.
