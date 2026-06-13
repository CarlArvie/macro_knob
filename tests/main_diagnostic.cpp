#include <windows.h>
#include <gdiplus.h>
#include <shellapi.h>
#include <string>
#include <iostream>
#include "config_store.h"
#include "radial_menu.h"

// Global ConfigStore instance
ConfigStore g_configStore;

#define WM_TRAYICON (WM_USER + 1)
#define ID_OPEN_CONFIG 1001
#define ID_RELOAD_CONFIG 1002
#define ID_EXIT 1003

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

LRESULT CALLBACK WndProc(HWND hWnd, UINT message, WPARAM wParam, LPARAM lParam) {
    switch (message) {
    case WM_TRAYICON:
        if (lParam == WM_RBUTTONUP) {
            POINT pt;
            GetCursorPos(&pt);
            HMENU hMenu = CreatePopupMenu();
            if (hMenu) {
                AppendMenuW(hMenu, MF_STRING, ID_OPEN_CONFIG, L"Open Config");
                AppendMenuW(hMenu, MF_STRING, ID_RELOAD_CONFIG, L"Reload Config");
                AppendMenuW(hMenu, MF_SEPARATOR, 0, NULL);
                AppendMenuW(hMenu, MF_STRING, ID_EXIT, L"Exit");
                
                SetForegroundWindow(hWnd);
                TrackPopupMenu(hMenu, TPM_RIGHTBUTTON | TPM_BOTTOMALIGN, pt.x, pt.y, 0, hWnd, NULL);
                PostMessageW(hWnd, WM_NULL, 0, 0);
                DestroyMenu(hMenu);
            }
        }
        break;
    case WM_COMMAND:
        switch (LOWORD(wParam)) {
        case ID_OPEN_CONFIG: {
            std::wstring configPath = g_configStore.GetResolvedPath();
            ShellExecuteW(NULL, L"open", configPath.c_str(), NULL, NULL, SW_SHOWNORMAL);
            break;
        }
        case ID_RELOAD_CONFIG:
            if (g_configStore.Load()) {
                ShowTrayBalloon(hWnd, L"KnobLaunch", L"Configuration reloaded successfully.");
            } else {
                ShowTrayBalloon(hWnd, L"KnobLaunch", L"Failed to reload configuration.");
            }
            break;
        case ID_EXIT:
            DestroyWindow(hWnd);
            break;
        }
        break;
    case WM_DESTROY: {
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

int main() {
    std::cout << "[Diagnostic] Starting main_diagnostic..." << std::endl;
    HINSTANCE hInstance = GetModuleHandleW(NULL);

    // Initialize GDI+
    Gdiplus::GdiplusStartupInput gdiplusStartupInput;
    ULONG_PTR gdiplusToken;
    Gdiplus::Status gdiStatus = Gdiplus::GdiplusStartup(&gdiplusToken, &gdiplusStartupInput, NULL);
    std::cout << "[Diagnostic] GdiplusStartup status: " << gdiStatus << std::endl;

    // Load configuration (resolves config path and creates defaults if missing)
    bool configLoaded = g_configStore.Load();
    std::cout << "[Diagnostic] configStore.Load() returned: " << configLoaded << std::endl;

    // Register helper class
    WNDCLASSEXW wcex = {};
    wcex.cbSize = sizeof(WNDCLASSEXW);
    wcex.style = CS_HREDRAW | CS_VREDRAW;
    wcex.lpfnWndProc = WndProc;
    wcex.hInstance = hInstance;
    wcex.lpszClassName = L"KnobLaunchTrayHelper";
    if (!RegisterClassExW(&wcex)) {
        std::cerr << "[Diagnostic] RegisterClassExW failed. GetLastError: " << GetLastError() << std::endl;
        Gdiplus::GdiplusShutdown(gdiplusToken);
        return 1;
    }
    std::cout << "[Diagnostic] RegisterClassExW succeeded." << std::endl;

    // Register KnobLaunchRadialMenu class from radial_menu stub
    bool radialRegistered = RegisterRadialMenuClass(hInstance);
    std::cout << "[Diagnostic] RegisterRadialMenuClass returned: " << radialRegistered << std::endl;

    // Create hidden helper window
    HWND hWnd = CreateWindowExW(
        0,
        L"KnobLaunchTrayHelper",
        L"KnobLaunchTrayHelperWindow",
        WS_OVERLAPPEDWINDOW,
        CW_USEDEFAULT, CW_USEDEFAULT, CW_USEDEFAULT, CW_USEDEFAULT,
        NULL, NULL, hInstance, NULL
    );

    if (!hWnd) {
        std::cerr << "[Diagnostic] CreateWindowExW failed. GetLastError: " << GetLastError() << std::endl;
        Gdiplus::GdiplusShutdown(gdiplusToken);
        return 1;
    }
    std::cout << "[Diagnostic] CreateWindowExW succeeded. HWND: " << hWnd << std::endl;

    // Setup tray icon
    NOTIFYICONDATAW nid = {};
    nid.cbSize = sizeof(nid);
    nid.hWnd = hWnd;
    nid.uID = 1;
    nid.uFlags = NIF_MESSAGE | NIF_ICON | NIF_TIP;
    nid.uCallbackMessage = WM_TRAYICON;
    nid.hIcon = LoadIconW(NULL, (LPCWSTR)IDI_APPLICATION);
    wcscpy_s(nid.szTip, L"KnobLaunch");
    BOOL trayAdded = Shell_NotifyIconW(NIM_ADD, &nid);
    std::cout << "[Diagnostic] Shell_NotifyIconW (NIM_ADD) returned: " << trayAdded << " (GetLastError: " << GetLastError() << ")" << std::endl;

    // Wait a brief moment to check if it keeps running or fails
    std::cout << "[Diagnostic] Entering message loop for 2 seconds..." << std::endl;
    
    // Run message loop for a short time to verify
    DWORD startTick = GetTickCount();
    MSG msg;
    while (GetTickCount() - startTick < 2000) {
        if (PeekMessageW(&msg, NULL, 0, 0, PM_REMOVE)) {
            TranslateMessage(&msg);
            DispatchMessageW(&msg);
        }
        Sleep(10);
    }

    std::cout << "[Diagnostic] Diagnostic complete, destroying window." << std::endl;
    DestroyWindow(hWnd);
    Gdiplus::GdiplusShutdown(gdiplusToken);
    return 0;
}
