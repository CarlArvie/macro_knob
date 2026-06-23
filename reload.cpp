#include <windows.h>
#include <iostream>

int main() {
    HWND hwnd = FindWindowW(L"KnobLaunchDaemon", L"KnobLaunchDaemonWindow");
    std::cout << "HWND: " << hwnd << std::endl;
    if (hwnd) {
        PostMessageW(hwnd, WM_COMMAND, 40003, 0);
        std::cout << "Reload message posted!" << std::endl;
    } else {
        std::cout << "Failed to find window." << std::endl;
    }
    return 0;
}
