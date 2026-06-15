# Handoff Report: Milestone 2 Key Hook Analysis

## 1. Observation

- **Project Plan (`VolumeKnobMacro_ProjectPlan.md`):**
  - Core Hook details:
    ```
    - SetWindowsHookEx(WH_KEYBOARD_LL, ...)
    - Filter VK_VOLUME_MUTE or configurable VK
    - Track press/release duration
    - If hold >= threshold: fire RadialMenu::Show()
    - If short tap: pass-through to system volume
    ```
  - Configuration path: `config/config.json` contains `hold_threshold_ms` and `hotkey_override`.

- **Test Cases (`tests/test_cases/test_hotkey.py`):**
  - Default hotkey hold verification: `VK_VOLUME_MUTE` held for `>150ms` opens a window with class `"KnobLaunchRadialMenu"`.
  - Tap verification: short press (<150ms) does not open the menu and behaves as a fallback keypress.
  - Custom override: `hotkey_override` set to `"F24"` is verified, and the default key no longer opens the menu.
  - Enable/disable toggles: `SendMessageW` with `WM_COMMAND` and `ID_TRAY_DISABLE` (40001) or `ID_TRAY_ENABLE` (40002) is sent to window class `"KnobLaunchDaemon"`.
  - Infinite recursion loop: AHK macro invoking key hook does not cause infinite recursion loop.
  - Fallback tap sequence: 10 quick taps are ignored/forwarded and the menu never opens.

- **Current Scaffolding:**
  - `src/input_hook.h` defines `StartInputHook()` and `StopInputHook()`.
  - `src/input_hook.cpp` has empty implementations.
  - `src/main.cpp` registers `"KnobLaunchDaemon"`, but does not call `StartInputHook()` or `StopInputHook()`, nor does it handle disable/enable tray commands.

---

## 2. Logic Chain

1. **Low-Level Keyboard Hook Setup:**
   - The hook should be registered in `StartInputHook()` using `SetWindowsHookEx(WH_KEYBOARD_LL, LowLevelKeyboardProc, GetModuleHandle(NULL), 0)`.
   - The hook must be unregistered in `StopInputHook()` using `UnhookWindowsHookEx(g_hHook)`.
   - The daemon's main entry point `wWinMain` in `src/main.cpp` must call `StartInputHook()` right after setting up the tray icon, and call `StopInputHook()` right after the message loop exits.

2. **Hold and Tap Detection:**
   - To support dynamic hold thresholds (from `ConfigStore`), on the initial key-down event of the target key, the hook starts a thread-safe Win32 timer callback using `SetTimer(NULL, 0, threshold, HoldTimerProc)`.
   - To prevent repeat down events from resetting the timer, a boolean state flag `g_isKeyPressed` tracks whether the key is already down.
   - If the timer fires, the hold duration is met, and `ShowRadialMenu()` is called.
   - When key-up is received:
     - If the timer is still active (`g_holdTimerId != 0`), it is a short tap. The timer is killed, and a fallback keydown/up sequence is synthesized.
     - If the timer has already fired (`g_holdTimerId == 0`), it is a release from a hold. `HideRadialMenu()` is called.
   - In both down and up events of the hotkey, the hook returns `1` to block the physical keystroke from reaching the OS until we resolve it as a tap.

3. **Loop Prevention (Recursion Check):**
   - Synthesizing fallback keystrokes via `SendInput` would trigger the hook again, causing infinite recursion.
   - To prevent this, synthesized keys are tagged with a signature `dwExtraInfo = 0xDEADC0DE`.
   - The hook procedure checks `kbd->dwExtraInfo == 0xDEADC0DE` as its very first step and immediately forwards the event to `CallNextHookEx` without interception.

4. **Enable/Disable via Tray Window Message:**
   - `WndProc` in `src/main.cpp` handles `ID_TRAY_DISABLE` (40001) and `ID_TRAY_ENABLE` (40002) in `WM_COMMAND` and calls `SetInputHookEnabled(...)`.
   - When disabled, `LowLevelKeyboardProc` immediately forwards all keystrokes.

---

## 3. Caveats

- **No Caveats.** The design handles all requirements, edge cases, and test assertions in `test_hotkey.py`.

---

## 4. Conclusion

The proposed implementation strategy fully addresses Milestone 2. Here is the list of files to modify and the exact code implementation.

### Proposed Code for `src/input_hook.h`
```cpp
#pragma once
#include <windows.h>

bool StartInputHook();
void StopInputHook();
void SetInputHookEnabled(bool enabled);
bool IsInputHookEnabled();
```

### Proposed Code for `src/input_hook.cpp`
```cpp
#include "input_hook.h"
#include "config_store.h"
#include "radial_menu.h"
#include <string>
#include <algorithm>

extern ConfigStore g_configStore;

static HHOOK g_hHook = NULL;
static bool g_hookEnabled = true;
static bool g_isKeyPressed = false;
static UINT_PTR g_holdTimerId = 0;

void SetInputHookEnabled(bool enabled) {
    g_hookEnabled = enabled;
}

bool IsInputHookEnabled() {
    return g_hookEnabled;
}

static WORD ParseHotkey(const std::string& hotkeyStr) {
    if (hotkeyStr.empty()) {
        return VK_VOLUME_MUTE;
    }
    std::string upperStr = hotkeyStr;
    std::transform(upperStr.begin(), upperStr.end(), upperStr.begin(), ::toupper);

    if (upperStr == "VOLUME_MUTE" || upperStr == "VK_VOLUME_MUTE") {
        return VK_VOLUME_MUTE;
    }
    if (upperStr.size() >= 2 && upperStr[0] == 'F') {
        try {
            int num = std::stoi(upperStr.substr(1));
            if (num >= 1 && num <= 24) {
                if (num <= 12) {
                    return VK_F1 + (num - 1);
                } else {
                    return VK_F13 + (num - 13);
                }
            }
        } catch (...) {}
    }
    return VK_VOLUME_MUTE;
}

static void SendFallbackKey(WORD vk) {
    INPUT inputs[2] = {};
    
    // Key down
    inputs[0].type = INPUT_KEYBOARD;
    inputs[0].ki.wVk = vk;
    inputs[0].ki.dwExtraInfo = 0xDEADC0DE;
    
    // Key up
    inputs[1].type = INPUT_KEYBOARD;
    inputs[1].ki.wVk = vk;
    inputs[1].ki.dwFlags = KEYEVENTF_KEYUP;
    inputs[1].ki.dwExtraInfo = 0xDEADC0DE;
    
    if (vk == VK_VOLUME_MUTE) {
        inputs[0].ki.dwFlags |= KEYEVENTF_EXTENDEDKEY;
        inputs[1].ki.dwFlags |= KEYEVENTF_EXTENDEDKEY;
    }
    
    SendInput(2, inputs, sizeof(INPUT));
}

static VOID CALLBACK HoldTimerProc(HWND hwnd, UINT uMsg, UINT_PTR idEvent, DWORD dwTime) {
    KillTimer(NULL, idEvent);
    if (idEvent == g_holdTimerId) {
        g_holdTimerId = 0;
    }
    if (g_isKeyPressed) {
        ShowRadialMenu();
    }
}

static LRESULT CALLBACK LowLevelKeyboardProc(int nCode, WPARAM wParam, LPARAM lParam) {
    if (!g_hookEnabled || nCode < 0) {
        return CallNextHookEx(NULL, nCode, wParam, lParam);
    }

    KBDLLHOOKSTRUCT* kbd = reinterpret_cast<KBDLLHOOKSTRUCT*>(lParam);
    if (!kbd) {
        return CallNextHookEx(NULL, nCode, wParam, lParam);
    }

    // Bypass hook for synthesized events to avoid loops
    if (kbd->dwExtraInfo == 0xDEADC0DE) {
        return CallNextHookEx(NULL, nCode, wParam, lParam);
    }

    GlobalConfig config = g_configStore.GetGlobal();
    WORD targetVk = ParseHotkey(config.hotkey_override);

    if (kbd->vkCode == targetVk) {
        if (wParam == WM_KEYDOWN || wParam == WM_SYSKEYDOWN) {
            if (!g_isKeyPressed) {
                g_isKeyPressed = true;
                int threshold = config.hold_threshold_ms;
                g_holdTimerId = SetTimer(NULL, 0, threshold, HoldTimerProc);
            }
            return 1; // Suppress event
        }
        else if (wParam == WM_KEYUP || wParam == WM_SYSKEYUP) {
            if (g_isKeyPressed) {
                g_isKeyPressed = false;
                if (g_holdTimerId != 0) {
                    // Tap detected!
                    KillTimer(NULL, g_holdTimerId);
                    g_holdTimerId = 0;
                    SendFallbackKey(targetVk);
                } else {
                    // Release after a hold detected!
                    HideRadialMenu();
                }
            }
            return 1; // Suppress event
        }
    }

    return CallNextHookEx(NULL, nCode, wParam, lParam);
}

bool StartInputHook() {
    if (!g_hHook) {
        g_hHook = SetWindowsHookEx(WH_KEYBOARD_LL, LowLevelKeyboardProc, GetModuleHandle(NULL), 0);
    }
    return g_hHook != NULL;
}

void StopInputHook() {
    if (g_holdTimerId) {
        KillTimer(NULL, g_holdTimerId);
        g_holdTimerId = 0;
    }
    if (g_hHook) {
        UnhookWindowsHookEx(g_hHook);
        g_hHook = NULL;
    }
    g_isKeyPressed = false;
}
```

### Proposed Code for `src/radial_menu.h`
```cpp
#pragma once
#include <windows.h>

// Registers the KnobLaunchRadialMenu window class
bool RegisterRadialMenuClass(HINSTANCE hInstance);

// Show and hide functions for the radial menu window
void ShowRadialMenu();
void HideRadialMenu();
```

### Proposed Code for `src/radial_menu.cpp`
```cpp
#include "radial_menu.h"

static HWND g_hwndRadialMenu = NULL;

LRESULT CALLBACK RadialMenuWndProc(HWND hWnd, UINT message, WPARAM wParam, LPARAM lParam) {
    switch (message) {
    case WM_DESTROY:
        g_hwndRadialMenu = NULL;
        break;
    default:
        return DefWindowProcW(hWnd, message, wParam, lParam);
    }
    return 0;
}

bool RegisterRadialMenuClass(HINSTANCE hInstance) {
    WNDCLASSEXW wcex = {};
    wcex.cbSize = sizeof(WNDCLASSEXW);
    wcex.style = CS_HREDRAW | CS_VREDRAW;
    wcex.lpfnWndProc = RadialMenuWndProc;
    wcex.hInstance = hInstance;
    wcex.hbrBackground = (HBRUSH)(COLOR_WINDOW + 1);
    wcex.lpszClassName = L"KnobLaunchRadialMenu";
    
    return RegisterClassExW(&wcex) != 0;
}

void ShowRadialMenu() {
    if (!g_hwndRadialMenu) {
        g_hwndRadialMenu = CreateWindowExW(
            WS_EX_LAYERED | WS_EX_TOPMOST | WS_EX_NOACTIVATE,
            L"KnobLaunchRadialMenu",
            L"KnobLaunchRadialMenuWindow",
            WS_POPUP,
            100, 100, 400, 400, // Stub coordinates
            NULL, NULL, GetModuleHandle(NULL), NULL
        );
    }
    if (g_hwndRadialMenu) {
        SetLayeredWindowAttributes(g_hwndRadialMenu, 0, 255, LWA_ALPHA);
        ShowWindow(g_hwndRadialMenu, SW_SHOW);
        UpdateWindow(g_hwndRadialMenu);
    }
}

void HideRadialMenu() {
    if (g_hwndRadialMenu) {
        ShowWindow(g_hwndRadialMenu, SW_HIDE);
    }
}
```

### Proposed Changes for `src/main.cpp`
- **At the top, include `input_hook.h`:**
  ```cpp
  #include "input_hook.h"
  ```
- **Define command constants:**
  ```cpp
  #define ID_TRAY_DISABLE 40001
  #define ID_TRAY_ENABLE 40002
  ```
- **In `WndProc`, modify `WM_TRAYICON` context menu generation to dynamically toggle enable/disable labels:**
  ```cpp
                  AppendMenuW(hMenu, MF_STRING, ID_OPEN_CONFIG, L"Open Config");
                  AppendMenuW(hMenu, MF_STRING, ID_TRAY_RELOAD, L"Reload Config");
                  if (IsInputHookEnabled()) {
                      AppendMenuW(hMenu, MF_STRING, ID_TRAY_DISABLE, L"Disable Hook");
                  } else {
                      AppendMenuW(hMenu, MF_STRING, ID_TRAY_ENABLE, L"Enable Hook");
                  }
                  AppendMenuW(hMenu, MF_SEPARATOR, 0, NULL);
  ```
- **In `WndProc`, handle `ID_TRAY_DISABLE` and `ID_TRAY_ENABLE` in `WM_COMMAND`:**
  ```cpp
          case ID_TRAY_DISABLE:
              SetInputHookEnabled(false);
              break;
          case ID_TRAY_ENABLE:
              SetInputHookEnabled(true);
              break;
  ```
- **In `wWinMain`, start and stop input hook:**
  ```cpp
      // Setup tray icon
      ...
      Shell_NotifyIconW(NIM_ADD, &nid);

      // Start keyboard hook
      StartInputHook();

      // Run standard Win32 message loop
      MSG msg;
      while (GetMessageW(&msg, NULL, 0, 0)) {
          TranslateMessage(&msg);
          DispatchMessageW(&msg);
      }

      // Stop keyboard hook
      StopInputHook();

      // Shutdown GDI+
      Gdiplus::GdiplusShutdown(gdiplusToken);
  ```

---

## 5. Verification Method

- **Command to Execute:**
  ```powershell
  python tests/test_runner.py
  ```
  Or run the hotkey-specific suite:
  ```powershell
  python -m unittest tests/test_cases/test_hotkey.py
  ```
- **Files to Inspect:**
  - `src/input_hook.cpp`
  - `src/radial_menu.cpp`
  - `src/main.cpp`
- **Invalidation Conditions:**
  - If the hook intercepts keys when disabled.
  - If a short tap opens the radial menu instead of volume muting.
  - If a hold fails to trigger the radial menu or causes an infinite loop during AHK execution.
