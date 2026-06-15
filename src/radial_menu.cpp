#include "radial_menu.h"
#include "config_store.h"

extern ConfigStore g_configStore;

LRESULT CALLBACK RadialMenuWndProc(HWND hWnd, UINT message, WPARAM wParam, LPARAM lParam) {
    switch (message) {
    case WM_PAINT: {
        PAINTSTRUCT ps;
        HDC hdc = BeginPaint(hWnd, &ps);
        RECT rect;
        GetClientRect(hWnd, &rect);
        // Paint a simple solid background
        HBRUSH hBrush = CreateSolidBrush(RGB(50, 50, 50));
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

HWND CreateRadialMenu(HWND hParentWnd) {
    POINT pt;
    GetCursorPos(&pt);

    int width = 400;
    int height = 400;

    std::string sz = g_configStore.GetGlobal().radial_size;
    if (sz == "small") {
        width = height = 300;
    } else if (sz == "large") {
        width = height = 500;
    }

    int x = pt.x - width / 2;
    int y = pt.y - height / 2;

    HWND hWnd = CreateWindowExW(
        WS_EX_TOPMOST | WS_EX_LAYERED | WS_EX_NOACTIVATE,
        L"KnobLaunchRadialMenu",
        L"KnobLaunchRadialMenuWindow",
        WS_POPUP | WS_VISIBLE,
        x, y, width, height,
        hParentWnd, NULL, GetModuleHandle(NULL), NULL
    );

    if (!hWnd) {
        return NULL;
    }

    SetLayeredWindowAttributes(hWnd, 0, 220, LWA_ALPHA);

    ShowWindow(hWnd, SW_SHOWNOACTIVATE);
    UpdateWindow(hWnd);

    RECT rect;
    if (GetWindowRect(hWnd, &rect)) {
        int cx = (rect.left + rect.right) / 2;
        int cy = (rect.top + rect.bottom) / 2;
        SetCursorPos(cx, cy);
    }

    return hWnd;
}
