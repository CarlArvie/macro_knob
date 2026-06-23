import os

file_path = "c:\\Users\\carla\\Desktop\\AHK\\Arvie Knob Macro\\src\\input_hook.cpp"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace(
    'static UINT g_toggleHotkeyVk = 0;',
    'static std::vector<UINT> g_toggleHotkeys;'
)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("input_hook.cpp fixed")
