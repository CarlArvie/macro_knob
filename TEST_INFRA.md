# E2E Test Infra: KnobLaunch

## Test Philosophy
- Opaque-box, requirement-driven. No dependency on implementation design.
- Methodology: Category-Partition + Boundary Value Analysis + Pairwise + Workload Testing.

## Feature Inventory
| # | Feature | Source (requirement) | Tier 1 | Tier 2 | Tier 3 |
|---|---------|---------------------|:------:|:------:|:------:|
| 1 | Keyboard Hook & Hotkey Triggers | ORIGINAL_REQUEST §R1 | 5 | 5 | ✓ |
| 2 | Radial Menu GUI & Interaction   | ORIGINAL_REQUEST §R2 | 5 | 5 | ✓ |
| 3 | Config Store & Reloading        | ORIGINAL_REQUEST §R3 | 5 | 5 | ✓ |
| 4 | Macro Runner Execution          | ORIGINAL_REQUEST §R3 | 5 | 5 | ✓ |

## Test Architecture
- **Test Runner**: Written in Python (`tests/test_runner.py`), executes unit-test format case files in `tests/test_cases/`.
- **Win32 Interaction**: Uses standard python `ctypes` library to simulate keypress events, move cursor, inspect window classes, and retrieve window rects.
- **Config Mocking**: Manages `config/config.json` per test case, backup and restore of initial configuration.
- **Verification Details**: Processes are tracked using python `subprocess` / `ctypes` or checking running processes (via tasklist or process names).

## Test Case Inventory

### Tier 1: Feature Coverage
- **T1.F1.1: Default Hotkey Press & Hold**: Simulate pressing and holding the hotkey for >`hold_threshold_ms`. Verify the radial menu window is created and visible.
- **T1.F1.2: Hotkey Tap (Short Press)**: Press and release the hotkey within `<hold_threshold_ms`. Verify the radial menu does not open.
- **T1.F1.3: Hotkey Override Config**: Modify `hotkey_override` to `F24`. Send this key and hold. Verify the radial menu opens.
- **T1.F1.4: Hotkey Release Close**: Press and hold the hotkey to open the menu, then release it. Verify the radial menu window is closed.
- **T1.F1.5: Disable/Enable Toggle**: Verify triggering the hook disable prevents menu display.
- **T1.F2.1: Cursor Warp on Open**: Verify that upon menu open, the mouse cursor is centered in the radial menu window.
- **T1.F2.2: Sector Hover Highlight (Angle Calc)**: Position mouse at specific angles (Sector 0) and verify slot activation on release.
- **T1.F2.3: Sector Selection Release**: Hold hotkey, move mouse to a sector, release. Verify sector action triggers.
- **T1.F2.4: Center Cancel Zone**: Hold hotkey, release in the center cancel circle. Verify no action is triggered.
- **T1.F2.5: Window Styles**: Verify radial menu window has `WS_EX_TOPMOST` and `WS_EX_LAYERED` styles.
- **T1.F3.1: Generate Default Config**: Delete `config.json`, run daemon, verify `config.json` is recreated with default values.
- **T1.F3.2: Custom Config Load**: Write custom config, launch daemon, verify settings are respected.
- **T1.F3.3: Config Auto-Reload on Edit**: Edit `config.json` while running. Verify the daemon reloads settings without restart.
- **T1.F3.4: Tray Icon Menu Reload**: Trigger reload config from tray menu, verify config is re-read.
- **T1.F3.5: Config Save on Exit**: Trigger daemon exit, check if configuration integrity is preserved.
- **T1.F4.1: Run Program Macro (Basic)**: Trigger a slot configured with `run_program` (Notepad). Verify process is spawned.
- **T1.F4.2: Run Program with Arguments**: Trigger `run_program` with specific command-line args. Verify the process has correct args.
- **T1.F4.3: Open URL Macro (Default Browser)**: Trigger `open_url`. Verify browser invocation.
- **T1.F4.4: AHK Script Macro (Basic)**: Trigger `ahk_script`. Verify execution via `AutoHotkey64.exe` (creates a marker file).
- **T1.F4.5: AHK Script Macro Error Logging**: Trigger invalid AHK script, check error logs/behavior.

### Tier 2: Boundary & Corner Cases
- **T2.F1.1: Hold Duration exactly at threshold**: Hold key for exactly threshold ms. Verify menu opens.
- **T2.F1.2: Hold Duration just below threshold**: Hold key for threshold - 5 ms. Verify menu does not open.
- **T2.F1.3: Hold Duration just above threshold**: Hold key for threshold + 5 ms. Verify menu opens.
- **T2.F1.4: Extreme Thresholds (Very Small)**: Set threshold to 10ms. Verify it triggers reliably.
- **T2.F1.5: Extreme Thresholds (Very Large)**: Set threshold to 3000ms. Verify hold of 1000ms doesn't trigger, 3100ms triggers.
- **T2.F2.1: Mouse at extreme boundary**: Move mouse way outside menu bounds, verify it still maps to correct sector based on angle.
- **T2.F2.2: Mouse at dead-center border**: Move mouse exactly on border of 60px inner cancel radius. Verify predictable cancel behavior.
- **T2.F2.3: Rapid Menu Toggle**: Press/hold/release/hold in rapid sequence. Verify no crash or resource leak.
- **T2.F2.4: Window overlapping controls**: Open menu when another topmost window is active, verify KnobLaunch is on top.
- **T2.F2.5: Cursor warp when cursor is at screen edge**: Position mouse at edge, open radial menu. Verify cursor warps correctly.
- **T2.F3.1: Missing Config File**: Launch daemon with missing config folder. Verify folder/file generation.
- **T2.F3.2: Malformed config.json**: Write invalid JSON. Verify fallback to default and no crash.
- **T2.F3.3: Config with missing slots**: Write config with only 4 slots. Verify daemon loads and undefined slots are disabled.
- **T2.F3.4: Config with invalid slot types**: Write invalid type. Verify graceful handle.
- **T2.F3.5: Extremely long labels**: Configure 100-char label. Verify GDI+ handles without crash.
- **T2.F4.1: Run Program with invalid path**: Configure non-existent executable. Verify graceful failure.
- **T2.F4.2: Open URL with malformed URL**: Verify malformed URL is handled.
- **T2.F4.3: AHK Script missing script file**: Verify graceful failure when script file is missing.
- **T2.F4.4: Run Program run_as_admin without elevation**: Verify behavior when not running as admin.
- **T2.F4.5: Multiple macro execution overlap**: Trigger two macros in rapid succession. Verify concurrency.

### Tier 3: Cross-Feature Combinations
- **T3.1: Hotkey Override + Custom Hold Threshold**: Verify override key respects custom hold duration.
- **T3.2: Radial Size changes and cursor warping**: Test `small`, `medium`, `large` sizes, check center coordinates are correct.
- **T3.3: Config Auto-Reload while Menu is Open**: Edit config while menu is visible. Verify updated selection.
- **T3.4: AHK macro invoking key hook**: AHK macro sending the hotkey itself does not trigger infinite loop.
- **T3.5: Run program macro starting another macro**: Execute a program that changes config.json and triggers reload.

### Tier 4: Real-World Workloads
- **T4.1: Multi-slot setup execution workflow**: Configure and execute multiple slots (Program, URL, AHK) in sequence.
- **T4.2: High frequency hold/release cycles**: Open/close menu 50 times in 30 seconds. Verify memory stability and correctness.
- **T4.3: System volume fallback tap sequence**: Send 10 quick taps. Verify menu never opens.
- **T4.4: Invalid config recovery workflow**: Malformed config -> check default fallback -> replace with valid config -> verify function.
- **T4.5: Full cleanup on exit**: Exit via tray menu, check all sub-processes/windows are terminated.

## Coverage Thresholds
- Tier 1: ≥5 per feature (Total 20)
- Tier 2: ≥5 per feature (Total 20)
- Tier 3: pairwise/combination coverage (Total 5)
- Tier 4: realistic application scenarios (Total 5)
- **Total Minimum: 50 tests**
