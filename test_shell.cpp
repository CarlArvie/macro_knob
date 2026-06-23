#include <windows.h>
#include <shellapi.h>
#include <iostream>

int main() {
    HINSTANCE hInst = ShellExecuteW(NULL, L"open", L"C:\\Users\\carla\\Desktop\\AHK\\Arvie Knob Macro", NULL, NULL, SW_SHOWNORMAL);
    std::cout << "Result: " << (intptr_t)hInst << std::endl;
    return 0;
}
