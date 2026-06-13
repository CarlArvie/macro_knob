#include <windows.h>
#include <gdiplus.h>
#include <iostream>

LRESULT CALLBACK DummyWndProc(HWND hWnd, UINT message, WPARAM wParam, LPARAM lParam) {
    return DefWindowProcW(hWnd, message, wParam, lParam);
}

int main() {
    Gdiplus::GdiplusStartupInput gdiplusStartupInput;
    ULONG_PTR gdiplusToken;
    Gdiplus::Status status = Gdiplus::GdiplusStartup(&gdiplusToken, &gdiplusStartupInput, NULL);
    std::cout << "GdiplusStartup status: " << status << std::endl;

    HINSTANCE hInstance = GetModuleHandleW(NULL);

    WNDCLASSEXW wcex = {};
    wcex.cbSize = sizeof(WNDCLASSEXW);
    wcex.style = CS_HREDRAW | CS_VREDRAW;
    wcex.lpfnWndProc = DummyWndProc;
    wcex.hInstance = hInstance;
    wcex.lpszClassName = L"KnobLaunchTrayHelper";
    
    ATOM atom = RegisterClassExW(&wcex);
    std::cout << "RegisterClassExW result: " << atom << " (GetLastError: " << GetLastError() << ")" << std::endl;

    HWND hWnd = CreateWindowExW(
        0,
        L"KnobLaunchTrayHelper",
        L"KnobLaunchTrayHelperWindow",
        WS_OVERLAPPEDWINDOW,
        CW_USEDEFAULT, CW_USEDEFAULT, CW_USEDEFAULT, CW_USEDEFAULT,
        NULL, NULL, hInstance, NULL
    );
    std::cout << "CreateWindowExW result: " << hWnd << " (GetLastError: " << GetLastError() << ")" << std::endl;

    if (hWnd) {
        DestroyWindow(hWnd);
    }
    
    // Also test registering/creating message-only window
    wcex.lpszClassName = L"KnobLaunchTrayHelperMessageOnly";
    RegisterClassExW(&wcex);
    HWND hWndMsg = CreateWindowExW(
        0,
        L"KnobLaunchTrayHelperMessageOnly",
        L"KnobLaunchTrayHelperWindowMsg",
        0,
        0, 0, 0, 0,
        HWND_MESSAGE, NULL, hInstance, NULL
    );
    std::cout << "Message-only CreateWindowExW result: " << hWndMsg << " (GetLastError: " << GetLastError() << ")" << std::endl;
    if (hWndMsg) {
        DestroyWindow(hWndMsg);
    }

    Gdiplus::GdiplusShutdown(gdiplusToken);
    return 0;
}
