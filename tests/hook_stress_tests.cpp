#include <windows.h>
#include <iostream>
#include <cassert>
#include <thread>
#include <chrono>
#include <vector>
#include "config_store.h"
#include "radial_menu.h"
#include "input_hook.h"

// Define test assertions
#define TEST_ASSERT(cond) \
    do { \
        if (!(cond)) { \
            std::cerr << "Assertion failed at line " << __LINE__ << ": " << #cond << std::endl; \
            std::exit(1); \
        } \
    } while (0)

// Reference the hook callback
extern LRESULT CALLBACK LowLevelKeyboardProc(int nCode, WPARAM wParam, LPARAM lParam);

// Define global config store since it is extern in input_hook.cpp
ConfigStore g_configStore;

LRESULT CALLBACK TestWndProc(HWND hWnd, UINT message, WPARAM wParam, LPARAM lParam) {
    if (message == WM_HOLD_TIMER) {
        HandleHoldTimer(wParam);
        return 0;
    }
    return DefWindowProcW(hWnd, message, wParam, lParam);
}

// Helper to pump messages for a short duration
void PumpMessages(DWORD limitMs) {
    DWORD start = GetTickCount();
    MSG msg;
    while (GetTickCount() - start < limitMs) {
        if (PeekMessageW(&msg, NULL, 0, 0, PM_REMOVE)) {
            TranslateMessage(&msg);
            DispatchMessageW(&msg);
        }
        Sleep(5);
    }
}

int main() {
    std::cout << "Starting Input Hook Empirical Stress Tests..." << std::endl;

    // 1. Initialize configuration and GDI+
    g_configStore.Load();
    GlobalConfig defaultGlobal = g_configStore.GetGlobal();
    defaultGlobal.hotkey_override = ""; // Use default (VK_VOLUME_MUTE)
    defaultGlobal.hold_threshold_ms = 150;
    g_configStore.UpdateGlobal(defaultGlobal);
    HINSTANCE hInstance = GetModuleHandleW(NULL);
    
    // Register window classes
    WNDCLASSEXW wcex = {};
    wcex.cbSize = sizeof(WNDCLASSEXW);
    wcex.style = CS_HREDRAW | CS_VREDRAW;
    wcex.lpfnWndProc = TestWndProc;
    wcex.hInstance = hInstance;
    wcex.lpszClassName = L"KnobLaunchTrayHelper";
    RegisterClassExW(&wcex);

    RegisterRadialMenuClass(hInstance);

    // Create a dummy daemon window
    HWND hDaemonWnd = CreateWindowExW(
        0,
        L"KnobLaunchTrayHelper",
        L"KnobLaunchTrayHelperWindow",
        WS_OVERLAPPEDWINDOW,
        CW_USEDEFAULT, CW_USEDEFAULT, CW_USEDEFAULT, CW_USEDEFAULT,
        NULL, NULL, hInstance, NULL
    );
    TEST_ASSERT(hDaemonWnd != NULL);

    // Initialize hook config
    UpdateHookConfig();
    GlobalConfig cfg = g_configStore.GetGlobal();
    std::cout << "[Test Info] Hotkey Vk: " << cfg.hotkey_override << " (hold_threshold: " << cfg.hold_threshold_ms << "ms)" << std::endl;
    
    // Start input hook
    bool hookStarted = StartInputHook(hDaemonWnd);
    TEST_ASSERT(hookStarted);

    // --- TEST 1: Hold vs Tap Threshold (Normal Tap) ---
    std::cout << "Running TEST 1: Normal Tap (should NOT spawn radial menu)..." << std::endl;
    {
        KBDLLHOOKSTRUCT kbd = {};
        kbd.vkCode = VK_VOLUME_MUTE; // default vk
        kbd.dwExtraInfo = 0;

        // Key down
        LRESULT resDown = LowLevelKeyboardProc(HC_ACTION, WM_KEYDOWN, (LPARAM)&kbd);
        TEST_ASSERT(resDown == 1); // Hook should block the hotkey down

        // Wait 50ms (well below threshold of 150ms)
        PumpMessages(50);

        // Key up
        LRESULT resUp = LowLevelKeyboardProc(HC_ACTION, WM_KEYUP, (LPARAM)&kbd);
        TEST_ASSERT(resUp == 1); // Hook should block the hotkey up

        // Check if radial menu exists
        HWND hMenu = FindWindowW(L"KnobLaunchRadialMenu", NULL);
        TEST_ASSERT(hMenu == NULL);
        std::cout << "TEST 1 passed." << std::endl;
    }

    // --- TEST 2: Hold vs Tap Threshold (Normal Hold) ---
    std::cout << "Running TEST 2: Normal Hold (should spawn radial menu)..." << std::endl;
    {
        KBDLLHOOKSTRUCT kbd = {};
        kbd.vkCode = VK_VOLUME_MUTE;
        kbd.dwExtraInfo = 0;

        // Key down
        LRESULT resDown = LowLevelKeyboardProc(HC_ACTION, WM_KEYDOWN, (LPARAM)&kbd);
        TEST_ASSERT(resDown == 1);

        // Wait 200ms (above 150ms threshold to trigger timer)
        PumpMessages(200);

        // Check if radial menu exists now
        HWND hMenu = FindWindowW(L"KnobLaunchRadialMenu", NULL);
        TEST_ASSERT(hMenu != NULL);

        // Key up
        LRESULT resUp = LowLevelKeyboardProc(HC_ACTION, WM_KEYUP, (LPARAM)&kbd);
        TEST_ASSERT(resUp == 1);

        // Process message queue (menu destruction is handled in WM_KEYUP directly)
        PumpMessages(50);

        // Check if radial menu was destroyed
        hMenu = FindWindowW(L"KnobLaunchRadialMenu", NULL);
        TEST_ASSERT(hMenu == NULL);
        std::cout << "TEST 2 passed." << std::endl;
    }

    // --- TEST 3: Bypass Signature (Simulated Events) ---
    std::cout << "Running TEST 3: Bypass Signature (should bypass hook)..." << std::endl;
    {
        KBDLLHOOKSTRUCT kbd = {};
        kbd.vkCode = VK_VOLUME_MUTE;
        kbd.dwExtraInfo = 0xDEADC0DE; // BYPASS_SIGNATURE

        // Key down with bypass signature
        LRESULT resDown = LowLevelKeyboardProc(HC_ACTION, WM_KEYDOWN, (LPARAM)&kbd);
        TEST_ASSERT(resDown == 0); // Hook should NOT block this keydown (returns 0 / CallNextHookEx)

        // Key up with bypass signature
        LRESULT resUp = LowLevelKeyboardProc(HC_ACTION, WM_KEYUP, (LPARAM)&kbd);
        TEST_ASSERT(resUp == 0); // Hook should NOT block this keyup

        std::cout << "TEST 3 passed." << std::endl;
    }

    // --- TEST 4: Hold Timer Race Condition (Rapid Taps) ---
    std::cout << "Running TEST 4: Hold Timer Race Condition under rapid keypresses..." << std::endl;
    {
        // Destroy any existing window
        HWND hMenu = FindWindowW(L"KnobLaunchRadialMenu", NULL);
        if (hMenu) DestroyWindow(hMenu);

        KBDLLHOOKSTRUCT kbd = {};
        kbd.vkCode = VK_VOLUME_MUTE;
        kbd.dwExtraInfo = 0;

        // 1. Tap 1 Down: starts Timer 1
        std::cout << " - Tap 1 Down" << std::endl;
        LRESULT res1 = LowLevelKeyboardProc(HC_ACTION, WM_KEYDOWN, (LPARAM)&kbd);
        TEST_ASSERT(res1 == 1);

        // 2. Wait until Timer 1 fires (170ms) WITHOUT pumping messages.
        // This simulates high thread load / queue delay: the threadpool timer callback will
        // execute and post WM_TIMER to the queue, but the main thread hasn't processed it yet.
        std::cout << " - Waiting for Timer 1 to fire asynchronously..." << std::endl;
        Sleep(170);

        // 3. Tap 1 Up: should cancel Timer 1
        std::cout << " - Tap 1 Up" << std::endl;
        LRESULT res2 = LowLevelKeyboardProc(HC_ACTION, WM_KEYUP, (LPARAM)&kbd);
        TEST_ASSERT(res2 == 1);

        // 4. Tap 2 Down immediately: starts Timer 2. State is now: g_isHotkeyHeld = true, g_hTimer = Timer 2
        std::cout << " - Tap 2 Down" << std::endl;
        LRESULT res3 = LowLevelKeyboardProc(HC_ACTION, WM_KEYDOWN, (LPARAM)&kbd);
        TEST_ASSERT(res3 == 1);

        // 5. Now, pump messages to let the queued WM_HOLD_TIMER (from Timer 1) process.
        std::cout << " - Pumping message queue to process delayed WM_HOLD_TIMER..." << std::endl;
        PumpMessages(50);

        // 6. Check if the menu was created.
        hMenu = FindWindowW(L"KnobLaunchRadialMenu", NULL);
        if (hMenu != NULL) {
            std::cout << " [BUG DETECTED] Radial menu was created prematurely! (FindWindow returned non-null HWND: " << hMenu << ")" << std::endl;
            std::cout << "   The race condition allowed the stale WM_HOLD_TIMER from Tap 1 to trigger menu creation on Tap 2 down immediately." << std::endl;
            
            // Clean up window
            DestroyWindow(hMenu);
            TEST_ASSERT(false);
        } else {
            std::cout << " [PASS] Radial menu was not created prematurely." << std::endl;
        }

        // Clean up Tap 2 state by releasing key
        LowLevelKeyboardProc(HC_ACTION, WM_KEYUP, (LPARAM)&kbd);
        PumpMessages(50);
    }

    // Cleanup
    StopInputHook();
    DestroyWindow(hDaemonWnd);

    std::cout << "Input Hook Empirical Stress Tests complete." << std::endl;
    return 0;
}
