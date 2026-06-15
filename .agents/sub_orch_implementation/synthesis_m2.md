# Milestone 2 Synthesis & Implementation Plan

## 1. Consensus
- **Hook Strategy**: Low-level keyboard hook (`WH_KEYBOARD_LL`) registered via `SetWindowsHookExW`.
- **Hotkey Targeting**: Support either the default `VK_VOLUME_MUTE` or a configurable `hotkey_override` (e.g. "F24") dynamically parsed from the configuration.
- **Suppression & Interception**: Suppress both key down and key up events of the target hotkey by returning `1` from the hook callback when the hook is enabled.
- **State Machine**:
  - Track `g_isHotkeyHeld` to ignore repeat keystrokes.
  - Track `g_menuVisible` (or `g_menuOpened`) to determine the visibility state of the menu.
- **Timer-Driven Hold**: Initiated on key down with a Win32 timer set to the cached `hold_threshold_ms`.
- **Simulated Tap fallback**: If key up is received before the timer fires, kill the timer and inject a tap using `SendInput` with a special signature (`0xDEADC0DE` or `0xDE1ADEAD`) in `dwExtraInfo` to bypass hook recursion.
- **Tray Menu Command Integration**: Handle `ID_TRAY_DISABLE` and `ID_TRAY_ENABLE` messages in the main window proc to pause and resume hook actions cleanly.

## 2. Refined Design & Implementation Details
- **Window Lifecycle**: To ensure responsiveness and compatibility with the test suite:
  - We will register the `KnobLaunchRadialMenu` window class at startup.
  - The radial menu window will be dynamically created on hold detection and destroyed on key release. This keeps memory footprint minimal and makes sure resources are correctly freed between activations.
- **Mouse Warping**:
  - When the menu opens, get the current mouse coordinates, center the menu on the cursor, show it, and warp the cursor to the center of the menu.
- **Settings Caching**:
  - The target hotkey Virtual Key code and hold threshold will be cached in global variables and updated on start and configuration reload. This prevents slow disk or thread-safe memory reads on every keyboard callback event.

## 3. Implementation Steps
1. Modify `src/input_hook.h` to declare hook control functions:
   - `bool StartInputHook(HWND hDaemonWnd);`
   - `void StopInputHook();`
   - `void UpdateHookConfig();`
   - `void EnableInputHook(bool enable);`
   - `bool IsInputHookEnabled();`
   - `void HandleHoldTimer();`
2. Implement `src/input_hook.cpp` with the low-level hook procedure, parsing helper, simulated tap, and enable/disable handlers.
3. Modify `src/radial_menu.h` and `src/radial_menu.cpp` to add `HWND CreateRadialMenu(HWND hParentWnd)` that creates a layered topmost window, centers it on the cursor, and warps the cursor to its center.
4. Modify `src/main.cpp` to:
   - Initialize and stop the input hook.
   - Handle the hold timer via `WM_TIMER`.
   - Process `ID_TRAY_DISABLE` and `ID_TRAY_ENABLE` from the tray menu.
