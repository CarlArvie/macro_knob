import os

cpp_path = r"c:\Users\carla\Desktop\AHK\Arvie Knob Macro\src\radial_menu.cpp"
with open(cpp_path, "r", encoding="utf-8") as f:
    cpp = f.read()

find_top = """#include "radial_menu.h"
#include "config_store.h"
#include <windows.h>
#include <gdiplus.h>
#include <cmath>
#include <string>"""

replace_top = """#include "radial_menu.h"
#include "config_store.h"
#include <windows.h>
#include <gdiplus.h>
#include <cmath>
#include <string>

extern void ForceCloseMenu();

static ULONGLONG g_lastInteractionTime = 0;
static POINT g_lastMousePt = {0, 0};"""

if find_top in cpp:
    cpp = cpp.replace(find_top, replace_top)

find_wmcreate = """    case WM_CREATE: {
        SetWindowLongPtrW(hWnd, GWLP_USERDATA, (LONG_PTR)-1);
        SetTimer(hWnd, 1, 16, NULL);
        RedrawRadialMenu(hWnd, -1);
        break;
    }"""

replace_wmcreate = """    case WM_CREATE: {
        SetWindowLongPtrW(hWnd, GWLP_USERDATA, (LONG_PTR)-1);
        SetTimer(hWnd, 1, 16, NULL);
        RedrawRadialMenu(hWnd, -1);
        g_lastInteractionTime = GetTickCount64();
        GetCursorPos(&g_lastMousePt);
        break;
    }"""

if find_wmcreate in cpp:
    cpp = cpp.replace(find_wmcreate, replace_wmcreate)

find_wmtimer = """            POINT pt;
            if (GetCursorPos(&pt)) {
                RECT rect;"""

replace_wmtimer = """            POINT pt;
            if (GetCursorPos(&pt)) {
                if (pt.x != g_lastMousePt.x || pt.y != g_lastMousePt.y) {
                    g_lastInteractionTime = GetTickCount64();
                    g_lastMousePt = pt;
                }

                int autoHideS = g_configStore.GetGlobal().auto_hide_timer_s;
                if (autoHideS > 0 && (GetTickCount64() - g_lastInteractionTime) > (ULONGLONG)autoHideS * 1000) {
                    ForceCloseMenu();
                    return 0;
                }

                RECT rect;"""

if find_wmtimer in cpp:
    cpp = cpp.replace(find_wmtimer, replace_wmtimer)

with open(cpp_path, "w", encoding="utf-8") as f:
    f.write(cpp)
print("Patched radial_menu.cpp!")
