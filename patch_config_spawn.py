import os

cpp_path = r"c:\Users\carla\Desktop\AHK\Arvie Knob Macro\src\config_store.h"
with open(cpp_path, "r", encoding="utf-8") as f:
    cpp = f.read()

find_h = """    int hold_threshold_ms = 150;
    std::string radial_size = "medium";"""

replace_h = """    int hold_threshold_ms = 150;
    std::string radial_size = "medium";
    std::string menu_spawn_location = "cursor";"""

if find_h in cpp:
    cpp = cpp.replace(find_h, replace_h)
    with open(cpp_path, "w", encoding="utf-8") as f:
        f.write(cpp)
    print("Patched config_store.h!")
else:
    print("Could not find block in config_store.h")


cpp_path2 = r"c:\Users\carla\Desktop\AHK\Arvie Knob Macro\src\config_store.cpp"
with open(cpp_path2, "r", encoding="utf-8") as f:
    cpp2 = f.read()

find_to_json = """        {"radial_size", g.radial_size},
        {"show_tray_icon", g.show_tray_icon},"""

replace_to_json = """        {"radial_size", g.radial_size},
        {"menu_spawn_location", g.menu_spawn_location},
        {"show_tray_icon", g.show_tray_icon},"""

if find_to_json in cpp2:
    cpp2 = cpp2.replace(find_to_json, replace_to_json)
else:
    print("Could not find to_json block in config_store.cpp")

find_from_json = """    if (j.contains("radial_size")) g.radial_size = j["radial_size"];
    if (j.contains("show_tray_icon")) g.show_tray_icon = j["show_tray_icon"];"""

replace_from_json = """    if (j.contains("radial_size")) g.radial_size = j["radial_size"];
    if (j.contains("menu_spawn_location")) g.menu_spawn_location = j["menu_spawn_location"];
    if (j.contains("show_tray_icon")) g.show_tray_icon = j["show_tray_icon"];"""

if find_from_json in cpp2:
    cpp2 = cpp2.replace(find_from_json, replace_from_json)
else:
    print("Could not find from_json block in config_store.cpp")

with open(cpp_path2, "w", encoding="utf-8") as f:
    f.write(cpp2)
print("Patched config_store.cpp!")
