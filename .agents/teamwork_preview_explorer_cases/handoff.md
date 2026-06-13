# Handoff Report — E2E Test Suite Design (Milestone T2)

## 1. Observation
- `TEST_INFRA.md` lines 21-80 lists the E2E test inventory with:
  - Tier 1: Feature Coverage (20 tests)
  - Tier 2: Boundary & Corner Cases (20 tests)
  - Tier 3: Cross-Feature Combinations (5 tests)
  - Tier 4: Real-World Workloads (5 tests)
- `PROJECT.md` line 64 identifies the Win32 Window Class Name as `"KnobLaunchRadialMenu"`.
- `tests/test_cases/test_base.py` lines 116-305 implements `KnobLaunchTestBase`, which contains key Win32 helpers (`send_key`, `press_and_hold_key`, `find_radial_menu_window`, `is_window_visible`, `get_window_rect`, `get_window_extended_style`, `get_cursor_position`, `set_cursor_position`), config writers (`write_config`, `write_default_config`), and daemon process controls (`start_daemon`, `stop_daemon`, `force_cleanup`).
- `tests/test_cases/test_sanity.py` lines 17-30 demonstrates a headless safety check for `SetCursorPos` returning `0` and catching error code `5` (ACCESS_DENIED) which occurs in headless sessions.

## 2. Logic Chain
- Based on `TEST_INFRA.md`, a total of 50 E2E tests are planned.
- To organize these logically and avoid a single monolithic file, the tests are partitioned into 4 suite files:
  1. `test_hotkey.py` (13 tests): Handles keyboard hook triggers, thresholds, overrides, toggle commands, and system volume tap fallback events.
  2. `test_gui.py` (12 tests): Handles cursor warping, sector angle-to-index mapping, selection release, center cancel zone, window styles (topmost, layered), and overlapping windows.
  3. `test_config.py` (12 tests): Handles default generation, custom loading, watcher-based auto-reload, tray-triggered manual reload, malformed JSON recovery, and slot validations.
  4. `test_macro.py` (13 tests): Handles program spawning, url shell execution, AutoHotkey v2 script running, execution overlaps, and cleanup of subprocesses on exit.
- To handle the lack of a built executable (`knoblaunch.exe`) during early testing phases, the tests must dynamically search for the executable in the workspace root or debug build output directories, and use `@unittest.skipIf` to skip execution if the executable is missing.
- To support headless VM runners where mouse control and window creation are constrained, the tests must check API accessibility (using `SetCursorPos` / `GetCursorPos` checks) and conditionally bypass assertions that are impossible to execute under headless environments.
- To verify menu actions without UI introspection, the config can be written to trigger temporary marker files. Measuring which marker file is generated provides a reliable black-box method of verifying sector activation.
- An interface contract for tray icon messages is established using standard Win32 `WM_COMMAND` identifiers (`ID_TRAY_DISABLE = 40001`, `ID_TRAY_ENABLE = 40002`, `ID_TRAY_RELOAD = 40003`, `ID_TRAY_EXIT = 40004`) to enable programmatic tray testing.

## 3. Caveats
- Testing `ShellExecute` for URLs (`open_url`) cannot easily verify that a browser window opened on the host system without polluting the OS. The verification method instead checks the daemon log file for a successful `ShellExecute` call.
- Interactive keyboard hook simulation relies on `SendInput`, which requires the test runner to run in an active interactive session. Under VM/CI, these tests may skip or require mock input injectors if `SendInput` fails.

## 4. Conclusion
The design of all 50 E2E tests is complete. They have been structured into the 4 target test suite files and written to the working directory as proposed files (`proposed_test_hotkey.py`, `proposed_test_gui.py`, `proposed_test_config.py`, `proposed_test_macro.py`). They are fully compatible with `test_runner.py` and `KnobLaunchTestBase`.

## 5. Verification Method
To verify the proposed test cases:
1. Compile `knoblaunch.exe` to the workspace directory.
2. Copy the four proposed test files from the working directory `.agents/teamwork_preview_explorer_cases/proposed_test_*.py` into the workspace test directory `tests/test_cases/` as `test_hotkey.py`, `test_gui.py`, `test_config.py`, and `test_macro.py`.
3. Run the python test runner:
   ```powershell
   python tests/test_runner.py
   ```
4. Verify that all 50 test cases run, skip appropriately when required, or fail/succeed in accordance with the binary status.
