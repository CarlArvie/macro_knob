# Handoff Report - Milestone 2 Analysis: Key Hook Implementation

## 1. Observation
- **Project Structure & Files**:
  - `VolumeKnobMacro_ProjectPlan.md` (lines 272–280): Details the `InputHook` specifications (`WH_KEYBOARD_LL`, filtering `VK_VOLUME_MUTE` or override VK, tracking hold/press duration, firing `RadialMenu::Show()` if hold >= threshold, and passing through a short tap).
  - `tests/test_cases/test_hotkey.py`:
    - `test_t1_f1_1_default_hotkey_hold`: Verifies that holding the default hotkey (`VK_VOLUME_MUTE`) for `>hold_threshold_ms` (150ms) creates and displays the radial menu window.
    - `test_t1_f1_3_hotkey_override`: Sets `"hotkey_override": "F24"`, and verifies that holding `VK_F24` opens the menu while the default key no longer opens it.
    - `test_t1_f1_5_disable_enable_toggle`: Verifies that sending `WM_COMMAND` with `ID_TRAY_DISABLE` and `ID_TRAY_ENABLE` to `"KnobLaunchDaemon"` disables and enables the hook.
    - `test_t3_4_ahk_invoke_hook_no_loop`: Verifies that a synthesized key press from a macro does not cause an infinite recursion loop.
  - `src/input_hook.h` (lines 4–5) & `src/input_hook.cpp` (lines 3–8): Currently contains empty/stub implementations for `StartInputHook()` and `StopInputHook()`.
  - `src/main.cpp`:
    - `WndProc` (lines 28–80): Currently lacks handlers for `ID_TRAY_DISABLE` (`40001`), `ID_TRAY_ENABLE` (`40002`), `WM_TIMER` (for hold threshold), and does not call `UpdateHookConfig` or start/stop the hook.
    - `wWinMain` (lines 82–150): Registers the radial menu class but does not create the radial menu window handle `g_hRadialMenuWnd` or invoke `StartInputHook()`.
  - `src/config_store.h` (lines 8–14): Contains `GlobalConfig` with `hold_threshold_ms` (default 150) and `hotkey_override` (default "F13").

## 2. Logic Chain
- **Hotkey Configuration & Parsing**:
  - Since the hotkey override is stored as a string (e.g., `"F24"`, `"F13"`, or empty), a parsing helper `ParseHotkeyStringToVk` is required to translate standard strings to Win32 Virtual Key codes (e.g., `VK_VOLUME_MUTE` for empty/Volume_Mute, `VK_F13` to `VK_F24` for F13-F24).
  - To prevent performance degradation or thread-locking during key interception, the parsed `g_hotkeyVk` and `g_holdThresholdMs` should be cached in global variables and updated via `UpdateHookConfig()` at startup and whenever configuration is reloaded (`ID_TRAY_RELOAD`).
- **Hold vs Tap Detection**:
  - The hook needs to intercept key down events and block them while initiating a hold timer using `SetTimer`. If the key is released before the timer fires (elapsed time < threshold), it is a tap, and the hook must synthesize a fallback tap sequence.
  - If the timer fires before the key is released (elapsed time >= threshold), the daemon transitions to the menu open state, centers the `"KnobLaunchRadialMenu"` window on the mouse cursor, shows it, and warps the cursor to its center.
- **Infinite Loop Prevention**:
  - Since the test suite sends key events using standard Win32 `SendInput` (which marks events as injected via `LLKHF_INJECTED`), the hook *cannot* simply ignore all injected events.
  - Instead, the daemon must append a unique signature (`0xDE1ADEAD`) to its own fallback synthesized `SendInput` events' `dwExtraInfo` parameter.
  - When the hook intercepts an event, it checks if `pKbd->dwExtraInfo == (ULONG_PTR)0xDE1ADEAD`. If it matches, the event is immediately forwarded without blocking. This breaks the recursion loop while allowing external/test injections to function.
- **Message-Based Hook Management**:
  - Sending `WM_COMMAND` with `ID_TRAY_DISABLE` (40001) or `ID_TRAY_ENABLE` (40002) to the `"KnobLaunchDaemon"` window must call `StopInputHook()` and `StartInputHook()` respectively, updating the hook state cleanly.

## 3. Caveats
- Direct keyboard layout changes are assumed not to dynamically alter the virtual key codes of multimedia keys or function keys.
- This implementation assumes standard mouse warping coordinate spaces. In high-DPI environments, `GetCursorPos` and `SetCursorPos` coordinate scales are handled correctly by the OS if DPI awareness is enabled.

## 4. Conclusion
To fully implement Milestone 2, the following changes are proposed:

### Proposed File Modifications

#### File 1: `src/input_hook.h`
Add function declarations and export global hook/timer variables.
```cpp
#pragma once
#include <windows.h>

// Starts the low-level keyboard hook
bool StartInputHook();

// Stops the low-level keyboard hook
void StopInputHook();

// Updates local cached settings from the config store
void UpdateHookConfig();

// Externalized Hook State Variables
extern HHOOK g_hHook;
extern HWND g_hDaemonWnd;
extern HWND g_hRadialMenuWnd;
extern bool g_isHotkeyHeld;
extern bool g_menuVisible;
extern DWORD g_pressTime;
extern UINT g_hotkeyVk;
extern int g_holdThresholdMs;
```

#### File 2: `src/input_hook.cpp`
Implement parsing, low-level hook procedure, thread-safe cache update, and timer-driven hold logic.
```cpp
#include "input_hook.h"
#include "config_store.h"

// Initialize globals
HHOOK g_hHook = NULL;
HWND g_hDaemonWnd = NULL;
HWND g_hRadialMenuWnd = NULL;
bool g_isHotkeyHeld = false;
bool g_menuVisible = false;
DWORD g_pressTime = 0;
UINT g_hotkeyVk = VK_VOLUME_MUTE;
int g_holdThresholdMs = 150;

#define DAEMON_INJECTED_SIGNATURE 0xDE1ADEAD
#define TIMER_ID_HOLD 1002

extern ConfigStore g_configStore; // Defined in main.cpp

// Convert override string to VK code
UINT ParseHotkeyStringToVk(const std::string& hotkeyStr) {
    if (hotkeyStr.empty()) {
        return VK_VOLUME_MUTE;
    }
    if (hotkeyStr == "Volume_Mute" || hotkeyStr == "VOLUME_MUTE") {
        return VK_VOLUME_MUTE;
    }
    if (hotkeyStr.size() >= 2 && (hotkeyStr[0] == 'F' || hotkeyStr[0] == 'f')) {
        try {
            int num = std::stoi(hotkeyStr.substr(1));
            if (num >= 13 && num <= 24) {
                return VK_F13 + (num - 13);
            }
            if (num >= 1 && num <= 12) {
                return VK_F1 + (num - 1);
            }
        } catch (...) {}
    }
    try {
        int num = std::stoi(hotkeyStr);
        if (num > 0 && num < 256) {
            return (UINT)num;
        }
    } catch (...) {}
    
    return VK_VOLUME_MUTE; // default fallback
}

// Low-level Keyboard Hook Procedure
LRESULT CALLBACK LowLevelKeyboardProc(int nCode, WPARAM wParam, LPARAM lParam) {
    if (nCode >= 0) {
        KBDLLHOOKSTRUCT* pKbd = (KBDLLHOOKSTRUCT*)lParam;
        
        // 1. Loop Prevention: Pass through our own synthesized events
        if (pKbd->dwExtraInfo == (ULONG_PTR)DAEMON_INJECTED_SIGNATURE) {
            return CallNextHookEx(NULL, nCode, wParam, lParam);
        }
        
        // 2. Intercept hotkey
        if (pKbd->vkCode == g_hotkeyVk) {
            bool isKeyDown = (wParam == WM_KEYDOWN || wParam == WM_SYSKEYDOWN);
            bool isKeyUp = (wParam == WM_KEYUP || wParam == WM_SYSKEYUP);
            
            if (isKeyDown) {
                if (!g_isHotkeyHeld) {
                    g_isHotkeyHeld = true;
                    g_pressTime = GetTickCount();
                    g_menuVisible = false;
                    
                    // Set non-blocking Win32 timer
                    SetTimer(g_hDaemonWnd, TIMER_ID_HOLD, g_holdThresholdMs, NULL);
                }
                return 1; // Intercept
            }
            else if (isKeyUp) {
                if (g_isHotkeyHeld) {
                    KillTimer(g_hDaemonWnd, TIMER_ID_HOLD);
                    g_isHotkeyHeld = false;
                    
                    if (g_menuVisible) {
                        // Close menu on release
                        ShowWindow(g_hRadialMenuWnd, SW_HIDE);
                        g_menuVisible = false;
                    }
                    else {
                        // Short tap: simulate fallback key down and up sequence
                        INPUT inputs[2] = {};
                        
                        // Down
                        inputs[0].type = INPUT_KEYBOARD;
                        inputs[0].ki.wVk = (WORD)g_hotkeyVk;
                        inputs[0].ki.wScan = (WORD)MapVirtualKeyW(g_hotkeyVk, MAPVK_VK_TO_VSC);
                        inputs[0].ki.dwFlags = 0;
                        if (g_hotkeyVk == VK_VOLUME_MUTE || g_hotkeyVk == VK_VOLUME_DOWN || g_hotkeyVk == VK_VOLUME_UP) {
                            inputs[0].ki.dwFlags |= KEYEVENTF_EXTENDEDKEY;
                        }
                        inputs[0].ki.dwExtraInfo = (ULONG_PTR)DAEMON_INJECTED_SIGNATURE;
                        
                        // Up
                        inputs[1].type = INPUT_KEYBOARD;
                        inputs[1].ki.wVk = (WORD)g_hotkeyVk;
                        inputs[1].ki.wScan = inputs[0].ki.wScan;
                        inputs[1].ki.dwFlags = KEYEVENTF_KEYUP;
                        if (g_hotkeyVk == VK_VOLUME_MUTE || g_hotkeyVk == VK_VOLUME_DOWN || g_hotkeyVk == VK_VOLUME_UP) {
                            inputs[1].ki.dwFlags |= KEYEVENTF_EXTENDEDKEY;
                        }
                        inputs[1].ki.dwExtraInfo = (ULONG_PTR)DAEMON_INJECTED_SIGNATURE;
                        
                        SendInput(2, inputs, sizeof(INPUT));
                    }
                }
                return 1; // Intercept
            }
        }
    }
    return CallNextHookEx(NULL, nCode, wParam, lParam);
}

bool StartInputHook() {
    if (g_hHook == NULL) {
        g_hHook = SetWindowsHookExW(WH_KEYBOARD_LL, LowLevelKeyboardProc, GetModuleHandle(NULL), 0);
        return g_hHook != NULL;
    }
    return true;
}

void StopInputHook() {
    if (g_hHook != NULL) {
        UnhookWindowsHookEx(g_hHook);
        g_hHook = NULL;
    }
}

void UpdateHookConfig() {
    GlobalConfig cfg = g_configStore.GetGlobal();
    UINT newVk = ParseHotkeyStringToVk(cfg.hotkey_override);
    int newThreshold = cfg.hold_threshold_ms;
    
    // Safety check: if hotkey is currently held while config changes, reset state
    if (g_isHotkeyHeld && (newVk != g_hotkeyVk || newThreshold != g_holdThresholdMs)) {
        KillTimer(g_hDaemonWnd, TIMER_ID_HOLD);
        g_isHotkeyHeld = false;
        if (g_menuVisible) {
            ShowWindow(g_hRadialMenuWnd, SW_HIDE);
            g_menuVisible = false;
        }
    }
    
    g_hotkeyVk = newVk;
    g_holdThresholdMs = newThreshold;
}
```

#### File 3: `src/main.cpp`
Integrate input hook functions, define tray command constants, handle WM_TIMER for radial menu display, and set up layered radial window creation.
```cpp
// Add to imports
#include "input_hook.h"

// Define command and timer constants
#define ID_TRAY_DISABLE 40001
#define ID_TRAY_ENABLE 40002
#define TIMER_ID_HOLD 1002

// Add to WndProc
LRESULT CALLBACK WndProc(HWND hWnd, UINT message, WPARAM wParam, LPARAM lParam) {
    switch (message) {
    // ... Existing messages ...
    case WM_COMMAND:
        switch (LOWORD(wParam)) {
        // ... Existing cases ...
        case ID_TRAY_RELOAD:
            if (g_configStore.Load()) {
                UpdateHookConfig(); // Update cached hook configuration
                ShowTrayBalloon(hWnd, L"KnobLaunch", L"Configuration reloaded successfully.");
            } else {
                ShowTrayBalloon(hWnd, L"KnobLaunch", L"Failed to reload configuration.");
            }
            break;
        case ID_TRAY_DISABLE:
            StopInputHook();
            if (g_hRadialMenuWnd) {
                ShowWindow(g_hRadialMenuWnd, SW_HIDE);
            }
            g_isHotkeyHeld = false;
            g_menuVisible = false;
            break;
        case ID_TRAY_ENABLE:
            StartInputHook();
            break;
        case ID_TRAY_EXIT:
            DestroyWindow(hWnd);
            break;
        }
        break;
    case WM_TIMER:
        if (wParam == TIMER_ID_HOLD) {
            KillTimer(hWnd, TIMER_ID_HOLD);
            if (g_isHotkeyHeld) {
                g_menuVisible = true;
                if (g_hRadialMenuWnd) {
                    POINT pt = {};
                    GetCursorPos(&pt);
                    int width = 320;
                    int height = 320;
                    int x = pt.x - width / 2;
                    int y = pt.y - height / 2;
                    
                    // Reposition radial menu to cursor center and show on top
                    SetWindowPos(g_hRadialMenuWnd, HWND_TOPMOST, x, y, width, height, SWP_NOACTIVATE);
                    ShowWindow(g_hRadialMenuWnd, SW_SHOWNOACTIVATE);
                    
                    // Warp mouse to center
                    SetCursorPos(pt.x, pt.y);
                }
            }
        }
        break;
    case WM_DESTROY: {
        StopInputHook(); // Clean up hook before exiting
        NOTIFYICONDATAW nid = {};
        nid.cbSize = sizeof(nid);
        nid.hWnd = hWnd;
        nid.uID = 1;
        Shell_NotifyIconW(NIM_DELETE, &nid);
        PostQuitMessage(0);
        break;
    }
    // ...
```

```cpp
// Add to wWinMain after registering classes and creating the daemon helper window
int APIENTRY wWinMain(...) {
    // ...
    // Register KnobLaunchRadialMenu class from radial_menu stub
    RegisterRadialMenuClass(hInstance);

    // Create the hidden radial menu layered window
    g_hRadialMenuWnd = CreateWindowExW(
        WS_EX_LAYERED | WS_EX_TOPMOST | WS_EX_NOACTIVATE,
        L"KnobLaunchRadialMenu",
        L"KnobLaunchRadialMenuWindow",
        WS_POPUP,
        0, 0, 0, 0,
        NULL, NULL, hInstance, NULL
    );

    // Create hidden helper window
    HWND hWnd = CreateWindowExW(...);
    if (!hWnd) {
        Gdiplus::GdiplusShutdown(gdiplusToken);
        return 1;
    }
    
    // Assign daemon window globally
    g_hDaemonWnd = hWnd;

    // Load configuration & cache hook settings
    g_configStore.Load();
    UpdateHookConfig();

    // Start input hook
    StartInputHook();
    // ...
```

## 5. Verification Method
1. **Compilation Verification**:
   - Re-run CMake to generate build files:
     ```cmd
     cmake -B build -G "Visual Studio 17 2022" -A x64
     ```
   - Build target:
     ```cmd
     cmake --build build --config Release
     ```
     Ensure that `/WX` compiler option resolves with zero warnings.
2. **E2E Test Execution**:
   - Execute the python-based hotkey test suite:
     ```cmd
     python -m unittest tests/test_cases/test_hotkey.py
     ```
   - Successful pass verification criteria:
     - `test_t1_f1_1_default_hotkey_hold`: Pass (Radial menu visible after >150ms).
     - `test_t1_f1_2_hotkey_tap_short`: Pass (Radial menu hidden after <150ms).
     - `test_t1_f1_3_hotkey_override`: Pass (F24 opens menu, default key ignored).
     - `test_t1_f1_4_hotkey_release_close`: Pass (Release hides menu).
     - `test_t1_f1_5_disable_enable_toggle`: Pass (Tray toggle prevents/allows menu opening).
     - `test_t3_4_ahk_invoke_hook_no_loop`: Pass (No recursion/crash on simulated key event).
