import os

cpp_path = r"c:\Users\carla\Desktop\AHK\Arvie Knob Macro\src\config_store.cpp"
with open(cpp_path, "r", encoding="utf-8") as f:
    cpp = f.read()

find_load = """    g.toggle_hotkey = gj.value("toggle_hotkey", "F14");
    g.enable_haptic_sound = gj.value("enable_haptic_sound", true);"""

replace_load = """    g.toggle_hotkey = gj.value("toggle_hotkey", "F14");
    g.enable_haptic_sound = gj.value("enable_haptic_sound", true);
    g.menu_spawn_location = gj.value("menu_spawn_location", "cursor");"""

find_save = """    j["global"]["toggle_hotkey"] = g.toggle_hotkey;
    j["global"]["enable_haptic_sound"] = g.enable_haptic_sound;"""

replace_save = """    j["global"]["toggle_hotkey"] = g.toggle_hotkey;
    j["global"]["enable_haptic_sound"] = g.enable_haptic_sound;
    j["global"]["menu_spawn_location"] = g.menu_spawn_location;"""

if find_load in cpp:
    cpp = cpp.replace(find_load, replace_load)
if find_save in cpp:
    cpp = cpp.replace(find_save, replace_save)

with open(cpp_path, "w", encoding="utf-8") as f:
    f.write(cpp)
print("Patched config_store.cpp!")
