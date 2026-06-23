import os

file_path = "c:\\Users\\carla\\Desktop\\AHK\\Arvie Knob Macro\\src\\radial_menu.cpp"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace(
    '#include "config_store.h"',
    '#include "config_store.h"\n#include "input_hook.h"'
)

content = content.replace(
    'std::vector<SlotConfig> slots = g_configStore.GetSlots();',
    'std::vector<SlotConfig> slots = g_configStore.GetSlotsAtPath(GetCurrentMenuPath());'
)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("radial_menu.cpp patched")
