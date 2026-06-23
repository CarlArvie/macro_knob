#include <windows.h>
#include <gdiplus.h>
#include "config_store.h"
#include "radial_menu.h"

// Global ConfigStore instance required by radial_menu.cpp
ConfigStore g_configStore;

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

    // Load configuration
    g_configStore.Load();

    // Register radial menu window class
    if (!RegisterRadialMenuClass(hInstance)) {
        Gdiplus::GdiplusShutdown(gdiplusToken);
        return 1;
    }

    // Create the radial menu with no parent (NULL)
    HWND hWnd = CreateRadialMenu(NULL);
    if (!hWnd) {
        Gdiplus::GdiplusShutdown(gdiplusToken);
        return 1;
    }

    // Run message loop indefinitely
    MSG msg;
    while (GetMessageW(&msg, NULL, 0, 0)) {
        TranslateMessage(&msg);
        DispatchMessageW(&msg);
    }

    // Shutdown GDI+
    Gdiplus::GdiplusShutdown(gdiplusToken);

    return (int)msg.wParam;
}
