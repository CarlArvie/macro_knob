import os

cpp_path = r"c:\Users\carla\Desktop\AHK\Arvie Knob Macro\src\config_store.h"
with open(cpp_path, "r", encoding="utf-8") as f:
    cpp = f.read()

find_h = """    std::string radial_size = "medium";
    std::string menu_spawn_location = "cursor";"""

replace_h = """    std::string radial_size = "medium";
    std::string menu_spawn_location = "cursor";
    int auto_hide_timer_s = 10;"""

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

find_load = """    g.menu_spawn_location = gj.value("menu_spawn_location", "cursor");"""
replace_load = """    g.menu_spawn_location = gj.value("menu_spawn_location", "cursor");
    g.auto_hide_timer_s = gj.value("auto_hide_timer_s", 10);"""

find_save = """    j["global"]["menu_spawn_location"] = g.menu_spawn_location;"""
replace_save = """    j["global"]["menu_spawn_location"] = g.menu_spawn_location;
    j["global"]["auto_hide_timer_s"] = g.auto_hide_timer_s;"""

if find_load in cpp2:
    cpp2 = cpp2.replace(find_load, replace_load)
if find_save in cpp2:
    cpp2 = cpp2.replace(find_save, replace_save)

with open(cpp_path2, "w", encoding="utf-8") as f:
    f.write(cpp2)
print("Patched config_store.cpp!")
