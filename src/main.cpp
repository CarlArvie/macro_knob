#include <windows.h>
#include <gdiplus.h>
#include <shellapi.h>
#include <string>
#include "config_store.h"
#include "radial_menu.h"
#include "input_hook.h"

// Global ConfigStore instance
ConfigStore g_configStore;

#define WM_TRAYICON (WM_USER + 1)
#define ID_OPEN_CONFIG 1001
#define ID_TRAY_RELOAD 40003
#define ID_TRAY_EXIT 40004
#define ID_TRAY_DISABLE 40001
#define ID_TRAY_ENABLE 40002

void ShowTrayBalloon(HWND hWnd, const std::wstring& title, const std::wstring& message) {
    NOTIFYICONDATAW nid = {};
    nid.cbSize = sizeof(nid);
    nid.hWnd = hWnd;
    nid.uID = 1;
    nid.uFlags = NIF_INFO;
    wcscpy_s(nid.szInfoTitle, title.c_str());
    wcscpy_s(nid.szInfo, message.c_str());
    nid.dwInfoFlags = NIIF_INFO;
    Shell_NotifyIconW(NIM_MODIFY, &nid);
}

extern void DebugLog(const std::string& msg);

LRESULT CALLBACK WndProc(HWND hWnd, UINT message, WPARAM wParam, LPARAM lParam) {
    switch (message) {
    case WM_TRAYICON:
        if (lParam == WM_RBUTTONUP) {
            POINT pt;
            GetCursorPos(&pt);
            HMENU hMenu = CreatePopupMenu();
            if (hMenu) {
                AppendMenuW(hMenu, MF_STRING, ID_OPEN_CONFIG, L"Open Config");
                AppendMenuW(hMenu, MF_STRING, ID_TRAY_RELOAD, L"Reload Config");
                AppendMenuW(hMenu, MF_SEPARATOR, 0, NULL);
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
    case WM_HOLD_TIMER:
        HandleHoldTimer(wParam);
        break;
    case WM_COMMAND:
        switch (LOWORD(wParam)) {
        case ID_OPEN_CONFIG: {
            std::wstring configPath = g_configStore.GetResolvedPath();
            ShellExecuteW(NULL, L"open", configPath.c_str(), NULL, NULL, SW_SHOWNORMAL);
            break;
        }
        case ID_TRAY_RELOAD:
            if (g_configStore.Load()) {
                UpdateHookConfig();
                ShowTrayBalloon(hWnd, L"KnobLaunch", L"Configuration reloaded successfully.");
            } else {
                ShowTrayBalloon(hWnd, L"KnobLaunch", L"Failed to reload configuration.");
            }
            break;
        case ID_TRAY_DISABLE:
            EnableInputHook(false);
            ShowTrayBalloon(hWnd, L"KnobLaunch", L"Hotkey input hook disabled.");
            break;
        case ID_TRAY_ENABLE:
            EnableInputHook(true);
            ShowTrayBalloon(hWnd, L"KnobLaunch", L"Hotkey input hook enabled.");
            break;
        case ID_TRAY_EXIT:
            DestroyWindow(hWnd);
            break;
        }
        break;
    case WM_DESTROY: {
        StopInputHook();
        NOTIFYICONDATAW nid = {};
        nid.cbSize = sizeof(nid);
        nid.hWnd = hWnd;
        nid.uID = 1;
        Shell_NotifyIconW(NIM_DELETE, &nid);
        PostQuitMessage(0);
        break;
    }
    default:
        return DefWindowProcW(hWnd, message, wParam, lParam);
    }
    return 0;
}

int APIENTRY wWinMain(_In_ HINSTANCE hInstance,
                     _In_opt_ HINSTANCE hPrevInstance,
                     _In_ LPWSTR    lpCmdLine,
                     _In_ int       nCmdShow) {
    (void)hPrevInstance;
    (void)lpCmdLine;
    (void)nCmdShow;

    // Set process priority class to above normal for responsive hook processing
    SetPriorityClass(GetCurrentProcess(), ABOVE_NORMAL_PRIORITY_CLASS);
    // Removed THREAD_PRIORITY_TIME_CRITICAL to prevent system-wide freezes

    // Load winmm for high precision timers
    HMODULE hWinmm = LoadLibraryA("winmm.dll");
    typedef UINT(WINAPI* PfnTimeBeginPeriod)(UINT);
    typedef UINT(WINAPI* PfnTimeEndPeriod)(UINT);
    PfnTimeBeginPeriod pTimeBeginPeriod = nullptr;
    PfnTimeEndPeriod pTimeEndPeriod = nullptr;
    if (hWinmm) {
        pTimeBeginPeriod = (PfnTimeBeginPeriod)GetProcAddress(hWinmm, "timeBeginPeriod");
        pTimeEndPeriod = (PfnTimeEndPeriod)GetProcAddress(hWinmm, "timeEndPeriod");
        if (pTimeBeginPeriod) {
            pTimeBeginPeriod(1);
        }
    }

    // Initialize GDI+
    Gdiplus::GdiplusStartupInput gdiplusStartupInput;
    ULONG_PTR gdiplusToken;
    Gdiplus::GdiplusStartup(&gdiplusToken, &gdiplusStartupInput, NULL);

    // Load configuration (resolves config path and creates defaults if missing)
    g_configStore.Load();

    // Register helper class
    WNDCLASSEXW wcex = {};
    wcex.cbSize = sizeof(WNDCLASSEXW);
    wcex.style = CS_HREDRAW | CS_VREDRAW;
    wcex.lpfnWndProc = WndProc;
    wcex.hInstance = hInstance;
    wcex.lpszClassName = L"KnobLaunchDaemon";
    if (!RegisterClassExW(&wcex)) {
        Gdiplus::GdiplusShutdown(gdiplusToken);
        return 1;
    }

    // Register KnobLaunchRadialMenu class from radial_menu stub
    RegisterRadialMenuClass(hInstance);

    // Create hidden helper window
    HWND hWnd = CreateWindowExW(
        0,
        L"KnobLaunchDaemon",
        L"KnobLaunchDaemonWindow",
        WS_OVERLAPPEDWINDOW,
        CW_USEDEFAULT, CW_USEDEFAULT, CW_USEDEFAULT, CW_USEDEFAULT,
        NULL, NULL, hInstance, NULL
    );

    if (!hWnd) {
        Gdiplus::GdiplusShutdown(gdiplusToken);
        return 1;
    }

    // Start input hook
    StartInputHook(hWnd);

    // Setup tray icon
    NOTIFYICONDATAW nid = {};
    nid.cbSize = sizeof(nid);
    nid.hWnd = hWnd;
    nid.uID = 1;
    nid.uFlags = NIF_MESSAGE | NIF_ICON | NIF_TIP;
    nid.uCallbackMessage = WM_TRAYICON;
    nid.hIcon = LoadIconW(NULL, (LPCWSTR)IDI_APPLICATION);
    wcscpy_s(nid.szTip, L"KnobLaunch");
    Shell_NotifyIconW(NIM_ADD, &nid);

    // Run standard Win32 message loop
    MSG msg;
    while (GetMessageW(&msg, NULL, 0, 0)) {
        TranslateMessage(&msg);
        DispatchMessageW(&msg);
    }

    // Shutdown GDI+
    Gdiplus::GdiplusShutdown(gdiplusToken);

    if (pTimeEndPeriod) {
        pTimeEndPeriod(1);
    }
    if (hWinmm) {
        FreeLibrary(hWinmm);
    }

    return (int)msg.wParam;
}
