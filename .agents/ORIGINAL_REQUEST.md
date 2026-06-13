# Original User Request

## 2026-06-12T19:52:04+08:00

A lightweight volume knob interceptor daemon (KnobLaunch) that opens a GTA 5-style radial menu on press, with 8 configurable slices for various macros. The core is a Win32 GUI daemon intercepting low-level keys, delegating macro execution to AutoHotkey v2.

Working directory: c:/Users/carla/Desktop/AHK/Arvie Knob Macro/KnobLaunch
Integrity mode: development

## Requirements

### R1. Core Daemon & Key Hook
Implement the C++ daemon using Win32 API to set a low-level keyboard hook (`WH_KEYBOARD_LL`). It must intercept volume knob presses (or a configurable hotkey) and measure hold duration.

### R2. Radial Menu GUI
Implement a topmost, layered Win32 window (GTA5-style radial menu) using GDI+ to render 8 slices. It must highlight slices based on mouse angle from the center.

### R3. Configuration & Macros
Implement the JSON config store using `nlohmann/json` to load/save `config.json`. Integrate AutoHotkey v2 (via subprocess or COM) to execute scripts/commands based on the selected radial slice.

## Acceptance Criteria

### Programmatic Verification
- [ ] A test script simulating a volume key press for >150ms successfully triggers the creation of the radial menu window (verifiable via `FindWindow`).
- [ ] The `config.json` file is correctly generated with default settings on first launch.
- [ ] The core daemon maintains an idle memory footprint of under 8MB (target <4MB).
- [ ] Triggering a slot configured with AHK script successfully spawns the AutoHotkey process or executes the script via DLL.
