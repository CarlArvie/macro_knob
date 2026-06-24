import os

cpp_path = r"c:\Users\carla\Desktop\AHK\Arvie Knob Macro\src\input_hook.cpp"
with open(cpp_path, "r", encoding="utf-8") as f:
    cpp = f.read()

find_str = """CreateTimerQueueTimer(&g_hRotaryTimer, NULL, RotaryTimerCallback, NULL, 10000, 0, WT_EXECUTEONLYONCE);"""

replace_str = """int autoHideMs = g_configStore.GetGlobal().auto_hide_timer_s * 1000;
                        if (autoHideMs > 0) {
                            CreateTimerQueueTimer(&g_hRotaryTimer, NULL, RotaryTimerCallback, NULL, autoHideMs, 0, WT_EXECUTEONLYONCE);
                        }"""

if find_str in cpp:
    cpp = cpp.replace(find_str, replace_str)
    with open(cpp_path, "w", encoding="utf-8") as f:
        f.write(cpp)
    print("Patched input_hook.cpp for dynamic rotary timeout!")
else:
    print("Could not find the 10000 timer creation code!")
