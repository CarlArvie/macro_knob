import os

file_path = "c:\\Users\\carla\\Desktop\\AHK\\Arvie Knob Macro\\src\\input_hook.cpp"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("static std::vector<int> g_menuPath;", "")

content = content.replace(
    'static bool g_slotEnabled[8] = {true, true, true, true, true, true, true, true};',
    'static bool g_slotEnabled[8] = {true, true, true, true, true, true, true, true};\nstatic std::vector<int> g_menuPath;'
)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("moved g_menuPath")
