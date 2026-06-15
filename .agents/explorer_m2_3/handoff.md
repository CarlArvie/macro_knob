# Milestone 2: Key Hook Analysis and Recommendations

This report outlines the implementation strategy for the low-level keyboard hook and hook state detection in the KnobLaunch project.

---

## 1. Observation

In the repository, the following scaffolding and test cases were observed:

- **Hook Scaffolding** (`src/input_hook.h` / `src/input_hook.cpp`):
  Currently, the hook manager is a set of empty stubs:
  ```cpp
  // src/input_hook.h
  #pragma once
  #include <windows.h>

  bool StartInputHook();
  void StopInputHook();
  ```
  ```cpp
  // src/input_hook.cpp
  #include "input_hook.h"

  bool StartInputHook() {
      return true;
  }

  void StopInputHook() {
  }
  ```

- **Tray Daemon Window** (`src/main.cpp`):
  Registers class `L"KnobLaunchDaemon"` and runs a standard message loop:
  ```cpp
  wcex.lpszClassName = L"KnobLaunchDaemon";
  ```

- **Config Variables** (`src/config_store.h`):
  `GlobalConfig` contains the `hold_threshold_ms` and `hotkey_override` fields:
  ```cpp
  struct GlobalConfig {
      int hold_threshold_ms = 150;
      std::string radial_size = "medium";
      std::string hotkey_override = "F13";
      bool show_tray_icon = true;
      bool debug_log = false;
  };
  ```

- **E2E Hotkey Tests** (`tests/test_cases/test_hotkey.py`):
  Verifies the following behaviors:
  - **Hold & Open**: Holds the hotkey for `> hold_threshold_ms` to check if the radial menu opens.
  - **Tap Pass-Through**: Verifies that short taps `< hold_threshold_ms` do not open the menu.
  - **Hotkey Override**: Support for overriding keys like `F24` (VK 0x87).
  - **Enable/Disable**: Sending `ID_TRAY_DISABLE` (40001) and `ID_TRAY_ENABLE` (40002) via `WM_COMMAND` to the daemon window must toggle hook interception.
  - **Infinite Loop Prevention**: AHK scripts invoking `Volume_Mute` must not trigger recursion.
  - **Tap Fallback Sequence**: Sending 10 quick taps does not open the menu and forwards them to the OS safely.

---

## 2. Logic Chain

1. **Interception (WH_KEYBOARD_LL)**:
   A low-level keyboard hook `WH_KEYBOARD_LL` installed via `SetWindowsHookExW` receives global keyboard events. Returning `1` from the hook callback blocks key propagation to other applications and the OS, which is required to prevent the hotkey (e.g., volume mute) from taking effect during press-and-hold.

2. **Classification (Hold vs. Tap)**:
   - When the hotkey `WM_KEYDOWN` is intercepted, we must distinguish between auto-repeat and initial press. We track a boolean flag `g_isHotkeyHeld`. If it is already true, we ignore it and return `1`.
   - On initial press, we start a Win32 timer on the daemon window with the timeout set to `hold_threshold_ms`. We return `1` to block.
   - If the timer fires (`WM_TIMER` is received in the daemon window proc), the hold threshold has been exceeded. We open the radial menu and set `g_menuOpened = true`.
   - If a key up (`WM_KEYUP`) is received before the timer fires:
     - We kill the timer (`KillTimer(g_hDaemonWnd, TIMER_HOLD)`).
     - Since `g_menuOpened` is false, this is a short tap. We simulate the keypress using `SendInput` to forward it to the OS.
     - If `g_menuOpened` is true, the menu is open. We destroy the menu window and trigger the macro for the selected slot on key up.

3. **Avoiding Infinite Recursion**:
   - Simulated keystrokes sent by the daemon (for tap fallback) or by an AHK script (for macro loops, as checked in `test_t3_4_ahk_invoke_hook_no_loop`) will trigger the hook callback.
   - Windows automatically sets the `LLKHF_INJECTED` flag on simulated keystrokes.
   - Additionally, we can set `dwExtraInfo = 0xDEADC0DE` on simulated inputs from the daemon.
   - By checking `(kbd->flags & LLKHF_INJECTED) || kbd->dwExtraInfo == 0xDEADC0DE` in the hook procedure, we can instantly bypass interception and call `CallNextHookEx`, preventing any loops.

4. **Message Toggling (Enable/Disable)**:
   - To handle the tray menu toggle commands `ID_TRAY_DISABLE` and `ID_TRAY_ENABLE`, the daemon window procedure `WndProc` must capture `WM_COMMAND` with these IDs and call a toggle function `EnableInputHook(bool)`.
   - When disabled, the hook callback should simply pass all keys directly to `CallNextHookEx`.

---

## 3. Caveats

- **Hook Time Limits**: Windows has a hook timeout (`LowLevelHooksTimeout`). If the hook callback takes too long, Windows will silently unhook it. The hook callback must execute in constant time $O(1)$ without doing disk I/O, network requests, or blocking window creation. Window creation and macro execution should be handled asynchronously or delegated to the message queue.
- **Admin Privilege Levels**: If an active application is running with higher UAC privileges (as Administrator), a non-elevated daemon's hook may not receive key events when that application has focus due to User Interface Privilege Isolation (UIPI). The daemon must be run with elevated privileges if matching elevated apps is required.

---

## 4. Conclusion & Implementation Strategy

### Recommended File Modifications

#### A. `src/input_hook.h`
Expand the interface to handle the daemon window parent, enable/disable states, and the hold timer event:
```cpp
#pragma once
#include <windows.h>

#define TIMER_HOLD 2001
#define ID_TRAY_DISABLE 40001
#define ID_TRAY_ENABLE 40002

bool StartInputHook(HWND hDaemonWnd);
void StopInputHook();
void EnableInputHook(bool enable);
bool IsInputHookEnabled();
void HandleHoldTimer();
```

#### B. `src/input_hook.cpp`
Implement the low-level hook callback with state machine classification and recursion prevention:
```cpp
#include "input_hook.h"
#include "config_store.h"
#include "radial_menu.h"
#include <string>

extern ConfigStore g_configStore;

static HHOOK g_hHook = NULL;
static HWND g_hDaemonWnd = NULL;
static HWND g_hRadialMenuWnd = NULL;

static bool g_hookEnabled = true;
static bool g_isHotkeyHeld = false;
static bool g_menuOpened = false;

#define MAGIC_VAL 0xDEADC0DE

// Parse hotkey_override string to VK code
static WORD GetCurrentHotkeyVK() {
    std::string overrideKey = g_configStore.GetGlobal().hotkey_override;
    if (overrideKey.empty() || overrideKey == "VOLUME_MUTE" || overrideKey == "Volume_Mute") {
        return VK_VOLUME_MUTE;
    }
    if (overrideKey[0] == 'F' || overrideKey[0] == 'f') {
        try {
            int num = std::stoi(overrideKey.substr(1));
            if (num >= 1 && num <= 24) {
                return (WORD)(VK_F1 + (num - 1));
            }
        } catch (...) {}
    }
    return VK_VOLUME_MUTE;
}

// Send simulated keypress to OS
static void SimulateTap(WORD vk, ULONG_PTR extraInfo) {
    INPUT inputs[2] = {};
    
    inputs[0].type = INPUT_KEYBOARD;
    inputs[0].ki.wVk = vk;
    inputs[0].ki.wScan = (WORD)MapVirtualKeyW(vk, MAPVK_VK_TO_VSC);
    inputs[0].ki.dwFlags = 0;
    if (vk == VK_VOLUME_MUTE || vk == VK_VOLUME_DOWN || vk == VK_VOLUME_UP) {
        inputs[0].ki.dwFlags |= KEYEVENTF_EXTENDEDKEY;
    }
    inputs[0].ki.dwExtraInfo = extraInfo;
    
    inputs[1].type = INPUT_KEYBOARD;
    inputs[1].ki.wVk = vk;
    inputs[1].ki.wScan = inputs[0].ki.wScan;
    inputs[1].ki.dwFlags = KEYEVENTF_KEYUP;
    if (vk == VK_VOLUME_MUTE || vk == VK_VOLUME_DOWN || vk == VK_VOLUME_UP) {
        inputs[1].ki.dwFlags |= KEYEVENTF_EXTENDEDKEY;
    }
    inputs[1].ki.dwExtraInfo = extraInfo;
    
    SendInput(2, inputs, sizeof(INPUT));
}

LRESULT CALLBACK LowLevelKeyboardProc(int nCode, WPARAM wParam, LPARAM lParam) {
    if (nCode == HC_ACTION) {
        KBDLLHOOKSTRUCT* kbd = (KBDLLHOOKSTRUCT*)lParam;
        
        // Skip simulated keys to prevent recursion loop
        if ((kbd->flags & LLKHF_INJECTED) || kbd->dwExtraInfo == MAGIC_VAL) {
            return CallNextHookEx(NULL, nCode, wParam, lParam);
        }
        
        if (g_hookEnabled) {
            WORD hotkey = GetCurrentHotkeyVK();
            if (kbd->vkCode == hotkey) {
                bool isDown = (wParam == WM_KEYDOWN || wParam == WM_SYSKEYDOWN);
                bool isUp = (wParam == WM_KEYUP || wParam == WM_SYSKEYUP);
                
                if (isDown) {
                    if (!g_isHotkeyHeld) {
                        g_isHotkeyHeld = true;
                        g_menuOpened = false;
                        int threshold = g_configStore.GetGlobal().hold_threshold_ms;
                        SetTimer(g_hDaemonWnd, TIMER_HOLD, threshold, NULL);
                    }
                    return 1; // Intercept
                }
                else if (isUp) {
                    if (g_isHotkeyHeld) {
                        g_isHotkeyHeld = false;
                        KillTimer(g_hDaemonWnd, TIMER_HOLD);
                        
                        if (g_menuOpened) {
                            g_menuOpened = false;
                            if (g_hRadialMenuWnd) {
                                DestroyWindow(g_hRadialMenuWnd);
                                g_hRadialMenuWnd = NULL;
                            }
                        } else {
                            SimulateTap(hotkey, MAGIC_VAL);
                        }
                    }
                    return 1; // Intercept
                }
            }
        }
    }
    return CallNextHookEx(NULL, nCode, wParam, lParam);
}

bool StartInputHook(HWND hDaemonWnd) {
    g_hDaemonWnd = hDaemonWnd;
    g_hHook = SetWindowsHookExW(WH_KEYBOARD_LL, LowLevelKeyboardProc, GetModuleHandleW(NULL), 0);
    return g_hHook != NULL;
}

void StopInputHook() {
    if (g_hHook) {
        UnhookWindowsHookEx(g_hHook);
        g_hHook = NULL;
    }
    if (g_hRadialMenuWnd) {
        DestroyWindow(g_hRadialMenuWnd);
        g_hRadialMenuWnd = NULL;
    }
}

void EnableInputHook(bool enable) {
    g_hookEnabled = enable;
    if (!enable) {
        if (g_isHotkeyHeld) {
            g_isHotkeyHeld = false;
            KillTimer(g_hDaemonWnd, TIMER_HOLD);
        }
        if (g_hRadialMenuWnd) {
            DestroyWindow(g_hRadialMenuWnd);
            g_hRadialMenuWnd = NULL;
        }
        g_menuOpened = false;
    }
}

bool IsInputHookEnabled() {
    return g_hookEnabled;
}

void HandleHoldTimer() {
    if (g_isHotkeyHeld && !g_menuOpened) {
        g_menuOpened = true;
        g_hRadialMenuWnd = CreateRadialMenu(g_hDaemonWnd);
    }
}
```

#### C. `src/main.cpp`
Integrate the hook calls, window commands, and timers inside the main daemon window class:
```cpp
// In WndProc:
    case WM_TIMER:
        if (wParam == TIMER_HOLD) {
            KillTimer(hWnd, TIMER_HOLD);
            HandleHoldTimer();
        }
        break;
    case WM_TRAYICON:
        if (lParam == WM_RBUTTONUP) {
            POINT pt;
            GetCursorPos(&pt);
            HMENU hMenu = CreatePopupMenu();
            if (hMenu) {
                AppendMenuW(hMenu, MF_STRING, ID_OPEN_CONFIG, L"Open Config");
                AppendMenuW(hMenu, MF_STRING, ID_TRAY_RELOAD, L"Reload Config");
                
                // Show dynamic Enable/Disable item
                if (IsInputHookEnabled()) {
                    AppendMenuW(hMenu, MF_STRING, ID_TRAY_DISABLE, L"Disable");
                } else {
                    AppendMenuW(hMenu, MF_STRING, ID_TRAY_ENABLE, L"Enable");
                }
                
                AppendMenuW(hMenu, MF_SEPARATOR, 0, NULL);
                AppendMenuW(hMenu, MF_STRING, ID_TRAY_EXIT, L"Exit");
                
                SetForegroundWindow(hWnd);
                TrackPopupMenu(hMenu, TPM_RIGHTBUTTON | TPM_BOTTOMALIGN, pt.x, pt.y, 0, hWnd, NULL);
                PostMessageW(hWnd, WM_NULL, 0, 0);
                DestroyMenu(hMenu);
            }
        }
        break;
    case WM_COMMAND:
        switch (LOWORD(wParam)) {
        case ID_TRAY_DISABLE:
            EnableInputHook(false);
            break;
        case ID_TRAY_ENABLE:
            EnableInputHook(true);
            break;
        // ... (other commands)
        }
        break;

// In wWinMain:
    // ... (after CreateWindowExW for L"KnobLaunchDaemon")
    StartInputHook(hWnd);
    
    // Message Loop
    MSG msg;
    while (GetMessageW(&msg, NULL, 0, 0)) {
        TranslateMessage(&msg);
        DispatchMessageW(&msg);
    }
    
    StopInputHook();
```

#### D. `src/radial_menu.h` / `src/radial_menu.cpp`
Add creation capabilities with `WS_EX_TOPMOST | WS_EX_LAYERED | WS_EX_NOACTIVATE` styles and warp the mouse cursor to the center:
```cpp
// src/radial_menu.h
#pragma once
#include <windows.h>

bool RegisterRadialMenuClass(HINSTANCE hInstance);
HWND CreateRadialMenu(HWND hParentWnd);
```
```cpp
// src/radial_menu.cpp
#include "radial_menu.h"

LRESULT CALLBACK RadialMenuWndProc(HWND hWnd, UINT message, WPARAM wParam, LPARAM lParam) {
    switch (message) {
    case WM_PAINT: {
        PAINTSTRUCT ps;
        HDC hdc = BeginPaint(hWnd, &ps);
        RECT rect;
        GetClientRect(hWnd, &rect);
        HBRUSH hBrush = CreateSolidBrush(RGB(45, 45, 45));
        FillRect(hdc, &rect, hBrush);
        DeleteObject(hBrush);
        EndPaint(hWnd, &ps);
        break;
    }
    case WM_DESTROY:
        break;
    default:
        return DefWindowProcW(hWnd, message, wParam, lParam);
    }
    return 0;
}

HWND CreateRadialMenu(HWND hParentWnd) {
    HINSTANCE hInst = GetModuleHandleW(NULL);
    int size = 400; // Medium menu diameter placeholder
    
    POINT pt;
    GetCursorPos(&pt);
    int x = pt.x - size / 2;
    int y = pt.y - size / 2;
    
    HWND hwnd = CreateWindowExW(
        WS_EX_TOPMOST | WS_EX_LAYERED | WS_EX_NOACTIVATE,
        L"KnobLaunchRadialMenu",
        L"KnobLaunchRadialMenuWindow",
        WS_POPUP,
        x, y, size, size,
        hParentWnd, NULL, hInst, NULL
    );
    
    if (hwnd) {
        SetLayeredWindowAttributes(hwnd, 0, 220, LWA_ALPHA);
        ShowWindow(hwnd, SW_SHOW);
        UpdateWindow(hwnd);
        
        // Warp cursor to the exact center of the newly created window
        RECT rect;
        GetWindowRect(hwnd, &rect);
        int centerX = (rect.left + rect.right) / 2;
        int centerY = (rect.top + rect.bottom) / 2;
        SetCursorPos(centerX, centerY);
    }
    return hwnd;
}
```

---

## 5. Verification Method

1. **Compilation Check**:
   Build the project using `build.bat` in the workspace directory.
   ```cmd
   cmd /c build.bat
   ```

2. **Automated Test Run**:
   Run the dedicated E2E hotkey test cases:
   ```cmd
   python tests/test_runner.py
   ```
   Alternatively, run the test suite using `unittest` targeting `test_hotkey.py`:
   ```cmd
   python -m unittest tests/test_cases/test_hotkey.py
   ```

3. **Check Test Log File**:
   View `tests/daemon.log` during execution to confirm correct window class creation, timing behavior, and enable/disable state toggles.
