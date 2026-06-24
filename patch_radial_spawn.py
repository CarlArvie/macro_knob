import os

cpp_path = r"c:\Users\carla\Desktop\AHK\Arvie Knob Macro\src\radial_menu.cpp"
with open(cpp_path, "r", encoding="utf-8") as f:
    cpp = f.read()

find_spawn = """HWND CreateRadialMenu(HWND hParentWnd) {
    POINT pt;
    GetCursorPos(&pt);

    int width = 400;
    int height = 400;"""

replace_spawn = """HWND CreateRadialMenu(HWND hParentWnd) {
    int width = 400;
    int height = 400;

    std::string sz = g_configStore.GetGlobal().radial_size;
    if (sz == "small") {
        width = height = 300;
    } else if (sz == "large") {
        width = height = 500;
    }

    std::string spawnLoc = g_configStore.GetGlobal().menu_spawn_location;
    POINT pt;
    GetCursorPos(&pt); // Default to cursor

    if (spawnLoc != "cursor") {
        HMONITOR hMonitor = MonitorFromPoint(pt, MONITOR_DEFAULTTONEAREST);
        MONITORINFO mi = { sizeof(mi) };
        if (GetMonitorInfoW(hMonitor, &mi)) {
            int monW = mi.rcWork.right - mi.rcWork.left;
            int monH = mi.rcWork.bottom - mi.rcWork.top;
            if (spawnLoc == "center") {
                pt.x = mi.rcWork.left + monW / 2;
                pt.y = mi.rcWork.top + monH / 2;
            } else if (spawnLoc == "top_left") {
                pt.x = mi.rcWork.left + width / 2;
                pt.y = mi.rcWork.top + height / 2;
            } else if (spawnLoc == "top_right") {
                pt.x = mi.rcWork.right - width / 2;
                pt.y = mi.rcWork.top + height / 2;
            } else if (spawnLoc == "bottom_left") {
                pt.x = mi.rcWork.left + width / 2;
                pt.y = mi.rcWork.bottom - height / 2;
            } else if (spawnLoc == "bottom_right") {
                pt.x = mi.rcWork.right - width / 2;
                pt.y = mi.rcWork.bottom - height / 2;
            }
        }
    }"""

# Remove old size setting logic that is now earlier
find_size_old = """    std::string sz = g_configStore.GetGlobal().radial_size;
    if (sz == "small") {
        width = height = 300;
    } else if (sz == "large") {
        width = height = 500;
    }"""

if find_spawn in cpp:
    cpp = cpp.replace(find_spawn, replace_spawn)
    # Be careful to remove the duplicate size logic if it existed right below
    if find_size_old in cpp:
        cpp = cpp.replace(find_size_old, "")

    with open(cpp_path, "w", encoding="utf-8") as f:
        f.write(cpp)
    print("Patched radial_menu.cpp!")
else:
    print("Could not find block in radial_menu.cpp")
