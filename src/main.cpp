#include <windows.h>
#include <gdiplus.h>
#include <shellapi.h>
#include <string>
#include "config_store.h"
#include "radial_menu.h"

// Global ConfigStore instance
ConfigStore g_configStore;

#define WM_TRAYICON (WM_USER + 1)
#define ID_OPEN_CONFIG 1001
#define ID_TRAY_RELOAD 40003
#define ID_TRAY_EXIT 40004

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
                AppendMenuW(hMenu, MF_STRING, ID_TRAY_RELOAD, L"Reload Config");
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
        case ID_OPEN_CONFIG: {
            std::wstring configPath = g_configStore.GetResolvedPath();
            ShellExecuteW(NULL, L"open", configPath.c_str(), NULL, NULL, SW_SHOWNORMAL);
            break;
        }
        case ID_TRAY_RELOAD:
            if (g_configStore.Load()) {
                ShowTrayBalloon(hWnd, L"KnobLaunch", L"Configuration reloaded successfully.");
            } else {
                ShowTrayBalloon(hWnd, L"KnobLaunch", L"Failed to reload configuration.");
            }
            break;
        case ID_TRAY_EXIT:
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

int APIENTRY wWinMain(_In_ HINSTANCE hInstance,
                     _In_opt_ HINSTANCE hPrevInstance,
                     _In_ LPWSTR    lpCmdLine,
                     _In_ int       nCmdShow) {
    (void)hPrevInstance;
    (void)lpCmdLine;
    (void)nCmdShow;

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

    return (int)msg.wParam;
}
