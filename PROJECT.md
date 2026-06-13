# Project: KnobLaunch

## Architecture
KnobLaunch is composed of two primary executable elements:
1. **Core C++ Daemon (`knoblaunch.exe`)**:
   - Manages the low-level keyboard hook (`WH_KEYBOARD_LL`) to intercept volume knob/multimedia keys.
   - Hosts a system tray icon with context menu.
   - Manages the transparent, layered Win32 window representing the radial menu GUI.
   - Leverages Win32 GDI+ for rendering the radial sectors, icons, labels, and highlights.
   - Contains a config manager module using `nlohmann/json` to load and save `config.json`.
   - Spawns AutoHotkey v2 subprocesses for executing script macros.
2. **AutoHotkey v2 Script Interpreter (`AutoHotkey64.exe` / scripts)**:
   - Evaluates user AHK macros and custom scripts.
   - Interacts with the daemon via IPC or temporary file execution.

### Module Map
- **InputHook (`input_hook.h/cpp`)**: Hooks keyboard, checks hold/tap duration, fires triggers.
- **RadialMenu (`radial_menu.h/cpp`)**: Creates and updates the layered window, performs GDI+ rendering, mouse position/angle tracking.
- **ConfigStore (`config_store.h/cpp`)**: JSON configurations load/save/default creation.
- **MacroRunner (`macro_runner.h/cpp`)**: Spawns programs, opens URLs, or invokes AHK.
- **TrayIcon (`tray_icon.h/cpp`)**: Handles the system tray icon, notification, and menu.

---

## Milestones

### Implementation Track
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | Milestone 1: Scaffold & Config | CMake, directory layout, JSON config load/save, system tray, nlohmann/json | None | PLANNED |
| 2 | Milestone 2: Key Hook & Hook State | WH_KEYBOARD_LL hook, knob tap/hold logic, hold threshold configuration | M1 | PLANNED |
| 3 | Milestone 3: Radial Menu GUI | WS_EX_LAYERED window, GDI+ rendering (8 sectors, hover highlight), angle calculations | M1, M2 | PLANNED |
| 4 | Milestone 4: Macro Runner & AHK | Run program, open URL, AHK subprocess invocation | M1, M3 | PLANNED |
| 5 | Milestone 5: E2E Integration & Verification | Run tests from E2E suite, fix bugs, ensure 100% E2E test pass | M4, E2E Test Suite | PLANNED |
| 6 | Milestone 6: Adversarial Hardening (Tier 5) | Challenger-guided testing, code coverage audit, bug fixes | M5 | PLANNED |

### E2E Testing Track
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| T1| Milestone T1: Test Harness & Mocking | Setup Python/AHK test runner, mock keyboard hook inputs, window state verify helpers | None | PLANNED |
| T2| Milestone T2: Tier 1-4 Test Suite | Construct E2E tests (Tier 1 coverage, Tier 2 boundaries, Tier 3 combinations, Tier 4 real workloads), publish `TEST_READY.md` | T1 | PLANNED |

---

## Interface Contracts

### 1. Configuration Schema (`config.json`)
The application configuration is saved in `config/config.json`.
- `global`:
  - `hold_threshold_ms`: integer (default 150)
  - `radial_size`: string ("small", "medium", "large")
  - `hotkey_override`: string (default "F13" or empty)
  - `show_tray_icon`: boolean (default true)
  - `debug_log`: boolean (default false)
- `slots`: Array of 8 slots (indices 0 to 7) containing:
  - `index`: integer (0-7)
  - `label`: string
  - `icon`: string (path to PNG)
  - `color`: string
  - `type`: string ("run_program", "open_url", "ahk_script")
  - `config`: details object depending on type (e.g. `path`, `url`, `script_file`)

### 2. Daemon Commands & IPC
- **Window Class Name**: `KnobLaunchRadialMenu` (used by test harness to find window).
- **IPC / Event Bridge**: Not used for minimal implementation. MacroRunner writes scripts to `scripts/user_script_slotN.ahk` and calls `AutoHotkey64.exe` on them.

---

## Code Layout

```
KnobLaunch/
├── CMakeLists.txt                 # CMake configuration
├── src/
│   ├── main.cpp                   # Application entry point & tray menu
│   ├── config_store.h             # Configuration header
│   ├── config_store.cpp           # JSON load, save, default generation
│   ├── input_hook.h               # Low-level keyboard hook header
│   ├── input_hook.cpp             # Hook management, hold threshold logic
│   ├── radial_menu.h              # Radial Menu overlay window header
│   ├── radial_menu.cpp            # GDI+ drawing, window proc, hover detection
│   ├── macro_runner.h             # Macro executor header
│   └── macro_runner.cpp           # Spawning programs, URLs, AutoHotkey scripts
├── include/
│   └── nlohmann/
│       └── json.hpp               # nlohmann/json header-only library
├── resources/
│   └── icons/                     # Pre-packaged icons for slices (default.png, etc.)
├── bin/
│   └── AutoHotkey64.exe           # AutoHotkey v2 executable bundled for scripts
├── tests/
│   ├── test_runner.py             # Main E2E test runner script (using PyAutoGUI or Win32 API)
│   └── test_cases/                # Detailed test definitions
└── README.md
```
