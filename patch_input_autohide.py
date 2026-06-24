import os

cpp_path = r"c:\Users\carla\Desktop\AHK\Arvie Knob Macro\src\input_hook.cpp"
with open(cpp_path, "r", encoding="utf-8") as f:
    cpp = f.read()

find_func = """bool StartInputHook(HWND hDaemonWnd) {"""

replace_func = """void ForceCloseMenu() {
    if (g_hRadialMenuWnd) {
        DestroyWindow(g_hRadialMenuWnd);
        g_hRadialMenuWnd = NULL;
        SetMenuVisible(false);
    }
}

bool StartInputHook(HWND hDaemonWnd) {"""

if find_func in cpp:
    cpp = cpp.replace(find_func, replace_func)
    with open(cpp_path, "w", encoding="utf-8") as f:
        f.write(cpp)
    print("Patched input_hook.cpp!")
else:
    print("Could not find StartInputHook")
