import os

cpp_path = r"c:\Users\carla\Desktop\AHK\Arvie Knob Macro\src\macro_runner.cpp"
with open(cpp_path, "r", encoding="utf-8") as f:
    cpp = f.read()

cpp = cpp.replace("        std::wstring wpath = ResolvePath(path);\n", "")

with open(cpp_path, "w", encoding="utf-8") as f:
    f.write(cpp)
