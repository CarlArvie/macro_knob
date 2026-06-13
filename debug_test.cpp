#include <windows.h>
#include <gdiplus.h>
#include <shellapi.h>
#include <iostream>
#include "src/config_store.h"
#include "src/radial_menu.h"

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
        break;
    case WM_COMMAND:
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
    std::cout << "Starting debug test..." << std::endl;
    
    // Initialize GDI+
    Gdiplus::GdiplusStartupInput gdiplusStartupInput;
    ULONG_PTR gdiplusToken;
    Gdiplus::GpStatus status = Gdiplus::GdiplusStartup(&gdiplusToken, &gdiplusStartupInput, NULL);
    std::cout << "GdiplusStartup status: " << status << std::endl;

    // Load configuration
    bool loadRes = g_configStore.Load();
    std::cout << "ConfigStore::Load() result: " << loadRes << std::endl;

    HINSTANCE hInstance = GetModuleHandle(NULL);

    // Register helper class
    WNDCLASSEXW wcex = {};
    wcex.cbSize = sizeof(WNDCLASSEXW);
    wcex.style = CS_HREDRAW | CS_VREDRAW;
    wcex.lpfnWndProc = WndProc;
    wcex.hInstance = hInstance;
    wcex.lpszClassName = L"KnobLaunchTrayHelper";
    
    ATOM atom = RegisterClassExW(&wcex);
    std::cout << "RegisterClassExW (KnobLaunchTrayHelper) result: " << atom;
    if (!atom) {
        std::cout << " (Failed, GetLastError: " << GetLastError() << ")";
    }
    std::cout << std::endl;

    // Register KnobLaunchRadialMenu class
    bool radRes = RegisterRadialMenuClass(hInstance);
    std::cout << "RegisterRadialMenuClass result: " << radRes;
    if (!radRes) {
        std::cout << " (Failed, GetLastError: " << GetLastError() << ")";
    }
    std::cout << std::endl;

    // Create hidden helper window
    HWND hWnd = CreateWindowExW(
        0,
        L"KnobLaunchTrayHelper",
        L"KnobLaunchTrayHelperWindow",
        WS_OVERLAPPEDWINDOW,
        CW_USEDEFAULT, CW_USEDEFAULT, CW_USEDEFAULT, CW_USEDEFAULT,
        NULL, NULL, hInstance, NULL
    );

    std::cout << "CreateWindowExW result: " << hWnd;
    if (!hWnd) {
        std::cout << " (Failed, GetLastError: " << GetLastError() << ")";
    }
    std::cout << std::endl;

    if (hWnd) {
        // Setup tray icon
        NOTIFYICONDATAW nid = {};
        nid.cbSize = sizeof(nid);
        nid.hWnd = hWnd;
        nid.uID = 1;
        nid.uFlags = NIF_MESSAGE | NIF_ICON | NIF_TIP;
        nid.uCallbackMessage = WM_TRAYICON;
        nid.hIcon = LoadIconW(NULL, (LPCWSTR)IDI_APPLICATION);
        wcscpy_s(nid.szTip, L"KnobLaunch");
        BOOL trayRes = Shell_NotifyIconW(NIM_ADD, &nid);
        std::cout << "Shell_NotifyIconW result: " << trayRes;
        if (!trayRes) {
            std::cout << " (Failed, GetLastError: " << GetLastError() << ")";
        }
        std::cout << std::endl;
    }

    Gdiplus::GdiplusShutdown(gdiplusToken);
    std::cout << "Done." << std::endl;
    return 0;
}
