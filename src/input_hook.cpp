#include "input_hook.h"
#include "config_store.h"
#include "radial_menu.h"
#include "macro_runner.h"
#include <algorithm>
#include <string>
#include <cmath>
#include <fstream>
#include <ctime>

#define BYPASS_SIGNATURE ((ULONG_PTR)0xDEADC0DE)

extern ConfigStore g_configStore;

void DebugLog(const std::string& msg) {
    if (!g_configStore.GetGlobal().debug_log) {
        return;
    }
    // Filter out verbose events in timing-sensitive paths
    if (msg.rfind("LowLevelKeyboardProc", 0) == 0 ||
        msg.rfind("WndProc", 0) == 0 ||
        msg.rfind("CreateRadialMenu", 0) == 0 ||
        msg.rfind("StartInputHook", 0) == 0 ||
        msg.rfind("HandleHoldTimer", 0) == 0 ||
        msg.rfind("wWinMain", 0) == 0) {
        return;
    }
    std::ofstream ofs("tests/daemon.log", std::ios::app);
    if (ofs.is_open()) {
        std::time_t t = std::time(nullptr);
        char timestamp[30];
        struct tm timeinfo;
        localtime_s(&timeinfo, &t);
        std::strftime(timestamp, sizeof(timestamp), "%Y-%m-%d %H:%M:%S", &timeinfo);
        ofs << "[" << timestamp << "] [PID:" << GetCurrentProcessId() << "] " << msg << std::endl;
    }
}

static HHOOK g_hHook = NULL;
static HWND g_hDaemonWnd = NULL;
static bool g_isHookEnabled = true;
static bool g_isHotkeyHeld = false;
static bool g_menuVisible = false;
static HWND g_hRadialMenuWnd = NULL;
static UINT g_targetVk = VK_VOLUME_MUTE;
static int g_holdThresholdMs = 150;
static HANDLE g_hTimer = NULL;
static UINT g_timerSeq = 0;

VOID CALLBACK HoldTimerCallback(PVOID lpParameter, BOOLEAN TimerOrWaitFired) {
    (void)TimerOrWaitFired;
    ULONG_PTR seq = (ULONG_PTR)lpParameter;
    if (g_hDaemonWnd) {
        PostMessageW(g_hDaemonWnd, WM_HOLD_TIMER, (WPARAM)seq, 0);
    }
}

static UINT ParseHotkeyStringToVk(const std::string& hotkeyStr) {
    if (hotkeyStr.empty()) {
        return VK_VOLUME_MUTE;
    }
    std::string lowerStr = hotkeyStr;
    for (char &c : lowerStr) {
        c = (char)::tolower((unsigned char)c);
    }

    if (lowerStr == "volume_mute" || lowerStr == "volumemute" || lowerStr == "mute") {
        return VK_VOLUME_MUTE;
    }

    if (lowerStr[0] == 'f') {
        try {
            int fNum = std::stoi(lowerStr.substr(1));
            if (fNum >= 1 && fNum <= 24) {
                return VK_F1 + (fNum - 1);
            }
        } catch (...) {
            // parsing failed, fallback
        }
    }

    // Default fallback
    return VK_VOLUME_MUTE;
}

static void SendSimulatedTap(WORD vkCode) {
    INPUT inputs[2] = {};
    UINT scanCode = MapVirtualKeyW(vkCode, 0);

    if (scanCode == 0) {
        if (vkCode == VK_VOLUME_MUTE) {
            scanCode = 0x20;
        } else if (vkCode == 0x7C) { // VK_F13
            scanCode = 0x64;
        }
    }

    inputs[0].type = INPUT_KEYBOARD;
    inputs[0].ki.wVk = vkCode;
    inputs[0].ki.wScan = (WORD)scanCode;
    inputs[0].ki.dwFlags = 0;
    if (vkCode == VK_VOLUME_MUTE || vkCode == 0xAE || vkCode == 0xAF) {
        inputs[0].ki.dwFlags |= KEYEVENTF_EXTENDEDKEY;
    }
    inputs[0].ki.dwExtraInfo = (ULONG_PTR)BYPASS_SIGNATURE;

    inputs[1].type = INPUT_KEYBOARD;
    inputs[1].ki.wVk = vkCode;
    inputs[1].ki.wScan = (WORD)scanCode;
    inputs[1].ki.dwFlags = KEYEVENTF_KEYUP;
    if (vkCode == VK_VOLUME_MUTE || vkCode == 0xAE || vkCode == 0xAF) {
        inputs[1].ki.dwFlags |= KEYEVENTF_EXTENDEDKEY;
    }
    inputs[1].ki.dwExtraInfo = (ULONG_PTR)BYPASS_SIGNATURE;

    SendInput(2, inputs, sizeof(INPUT));
}

static void TriggerSlotMacro(int sector) {
    SlotConfig slot = g_configStore.GetSlot(sector);
    if (slot.config_data.is_object()) {
        if (slot.type == "run_program") {
            std::string path = slot.config_data.value("path", "");
            std::string args = slot.config_data.value("args", "");
            if (!path.empty()) {
                RunProgram(path, args);
            }
        } else if (slot.type == "open_url") {
            std::string url = slot.config_data.value("url", "");
            if (!url.empty()) {
                OpenURL(url);
            }
        } else if (slot.type == "ahk_script") {
            std::string scriptFile = slot.config_data.value("script_file", "");
            if (!scriptFile.empty()) {
                RunAHKScript(scriptFile);
            }
        }
    }
}

LRESULT CALLBACK LowLevelKeyboardProc(int nCode, WPARAM wParam, LPARAM lParam) {

    if (nCode == HC_ACTION && g_isHookEnabled) {
        KBDLLHOOKSTRUCT* pKeyInfo = (KBDLLHOOKSTRUCT*)lParam;

        if (pKeyInfo->dwExtraInfo == BYPASS_SIGNATURE) {
            DebugLog("LowLevelKeyboardProc: Bypassing signature event: vkCode=" + std::to_string(pKeyInfo->vkCode));
            return CallNextHookEx(g_hHook, nCode, wParam, lParam);
        }

        if (pKeyInfo->vkCode == g_targetVk) {
            bool isDown = (wParam == WM_KEYDOWN || wParam == WM_SYSKEYDOWN);
            bool isUp = (wParam == WM_KEYUP || wParam == WM_SYSKEYUP);

            DebugLog("LowLevelKeyboardProc: target hotkey matched. vkCode=" + std::to_string(pKeyInfo->vkCode) + " isDown=" + std::to_string(isDown) + " isUp=" + std::to_string(isUp));

            if (isDown) {
                if (!g_isHotkeyHeld) {
                    g_isHotkeyHeld = true;
                    DebugLog("LowLevelKeyboardProc: Setting hold timer.");
                    if (g_hTimer) {
                        DeleteTimerQueueTimer(NULL, g_hTimer, NULL);
                        g_hTimer = NULL;
                    }
                    g_timerSeq++;
                    UINT timerDuration = (g_holdThresholdMs > 0) ? (UINT)g_holdThresholdMs : 0;
                    CreateTimerQueueTimer(&g_hTimer, NULL, HoldTimerCallback, (PVOID)(ULONG_PTR)g_timerSeq, timerDuration, 0, WT_EXECUTEONLYONCE);
                }
                return 1;
            }
            else if (isUp) {
                g_isHotkeyHeld = false;
                DebugLog("LowLevelKeyboardProc: Killing hold timer.");
                if (g_hTimer) {
                    DeleteTimerQueueTimer(NULL, g_hTimer, NULL);
                    g_hTimer = NULL;
                }

                if (g_menuVisible) {
                    g_menuVisible = false;
                    DebugLog("LowLevelKeyboardProc: Menu was visible, closing and triggering.");

                    POINT pt;
                    GetCursorPos(&pt);

                    RECT rect = {};
                    if (g_hRadialMenuWnd) {
                        GetWindowRect(g_hRadialMenuWnd, &rect);
                    }

                    int cx = (rect.left + rect.right) / 2;
                    int cy = (rect.top + rect.bottom) / 2;

                    double dx = pt.x - cx;
                    double dy = cy - pt.y;

                    double dist = sqrt(dx * dx + dy * dy);
                    DebugLog("LowLevelKeyboardProc: Mouse distance=" + std::to_string(dist));
                    if (dist >= 60.0) {
                        double angle = atan2(dx, dy);
                        double deg = angle * 180.0 / 3.14159265358979323846;
                        if (deg < 0) deg += 360.0;
                        int sector = (int)floor((deg + 22.5) / 45.0) % 8;
                        DebugLog("LowLevelKeyboardProc: Triggering sector " + std::to_string(sector));
                        TriggerSlotMacro(sector);
                    }

                    if (g_hRadialMenuWnd) {
                        DestroyWindow(g_hRadialMenuWnd);
                        g_hRadialMenuWnd = NULL;
                    }
                } else {
                    DebugLog("LowLevelKeyboardProc: Menu not visible, sending simulated tap.");
                    SendSimulatedTap((WORD)g_targetVk);
                }
                return 1;
            }
        }
    }
    return CallNextHookEx(g_hHook, nCode, wParam, lParam);
}

bool StartInputHook(HWND hDaemonWnd) {
    g_hDaemonWnd = hDaemonWnd;
    UpdateHookConfig();
    HDESK hDesk = GetThreadDesktop(GetCurrentThreadId());
    char dName[256] = {0};
    DWORD needed = 0;
    GetUserObjectInformationA(hDesk, UOI_NAME, dName, sizeof(dName), &needed);
    DebugLog("StartInputHook: Thread desktop name = " + std::string(dName));
    DebugLog("StartInputHook: Hooking targetVk=" + std::to_string(g_targetVk) + " threshold=" + std::to_string(g_holdThresholdMs));
    g_hHook = SetWindowsHookExW(WH_KEYBOARD_LL, LowLevelKeyboardProc, GetModuleHandle(NULL), 0);
    DebugLog("StartInputHook: Hook registered. Result=" + std::to_string(g_hHook != NULL));
    return g_hHook != NULL;
}

void StopInputHook() {
    if (g_hHook) {
        UnhookWindowsHookEx(g_hHook);
        g_hHook = NULL;
    }
    if (g_hTimer) {
        DeleteTimerQueueTimer(NULL, g_hTimer, NULL);
        g_hTimer = NULL;
    }
    if (g_hRadialMenuWnd) {
        DestroyWindow(g_hRadialMenuWnd);
        g_hRadialMenuWnd = NULL;
    }
    g_menuVisible = false;
    g_isHotkeyHeld = false;
}

void UpdateHookConfig() {
    GlobalConfig cfg = g_configStore.GetGlobal();
    g_holdThresholdMs = cfg.hold_threshold_ms;
    g_targetVk = ParseHotkeyStringToVk(cfg.hotkey_override);
}

void EnableInputHook(bool enable) {
    g_isHookEnabled = enable;
    if (!enable) {
        if (g_hTimer) {
            DeleteTimerQueueTimer(NULL, g_hTimer, NULL);
            g_hTimer = NULL;
        }
        g_isHotkeyHeld = false;
        if (g_menuVisible) {
            if (g_hRadialMenuWnd) {
                DestroyWindow(g_hRadialMenuWnd);
                g_hRadialMenuWnd = NULL;
            }
            g_menuVisible = false;
        }
    }
}

bool IsInputHookEnabled() {
    return g_isHookEnabled;
}

void HandleHoldTimer(WPARAM wParam) {
    UINT seq = (UINT)wParam;
    DebugLog("HandleHoldTimer called with seq=" + std::to_string(seq));
    if (seq != g_timerSeq) {
        DebugLog("HandleHoldTimer: stale timer message (seq mismatch), ignoring.");
        return;
    }
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
