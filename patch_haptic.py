import os, wave, struct, math

# 1. Create tick.wav
sounds_dir = r"c:\Users\carla\Desktop\AHK\Arvie Knob Macro\resources\sounds"
if not os.path.exists(sounds_dir):
    os.makedirs(sounds_dir)

wav_path = os.path.join(sounds_dir, "tick.wav")
sample_rate = 44100
duration = 0.015 # 15ms
freq = 600.0

with wave.open(wav_path, 'w') as obj:
    obj.setnchannels(1)
    obj.setsampwidth(2)
    obj.setframerate(sample_rate)
    for i in range(int(sample_rate * duration)):
        t = float(i) / sample_rate
        env = math.exp(-t * 500)
        value = int(12000.0 * env * math.sin(2.0 * math.pi * freq * t))
        data = struct.pack('<h', value)
        obj.writeframesraw(data)
print("tick.wav created")

# 2. Update CMakeLists.txt
cmake_path = r"c:\Users\carla\Desktop\AHK\Arvie Knob Macro\CMakeLists.txt"
with open(cmake_path, "r", encoding="utf-8") as f:
    cmake = f.read()
cmake = cmake.replace("shlwapi", "shlwapi\n    winmm")
with open(cmake_path, "w", encoding="utf-8") as f:
    f.write(cmake)

# 3. Update config_store.h
hdr_path = r"c:\Users\carla\Desktop\AHK\Arvie Knob Macro\src\config_store.h"
with open(hdr_path, "r", encoding="utf-8") as f:
    hdr = f.read()
hdr = hdr.replace('std::string toggle_hotkey = "F14";', 'std::string toggle_hotkey = "F14";\n    bool enable_haptic_sound = true;')
with open(hdr_path, "w", encoding="utf-8") as f:
    f.write(hdr)

# 4. Update config_store.cpp
cpp_path = r"c:\Users\carla\Desktop\AHK\Arvie Knob Macro\src\config_store.cpp"
with open(cpp_path, "r", encoding="utf-8") as f:
    cpp = f.read()
cpp = cpp.replace('g.toggle_hotkey = gj.value("toggle_hotkey", "F14");', 'g.toggle_hotkey = gj.value("toggle_hotkey", "F14");\n    g.enable_haptic_sound = gj.value("enable_haptic_sound", true);')
cpp = cpp.replace('j["global"]["toggle_hotkey"] = g.toggle_hotkey;', 'j["global"]["toggle_hotkey"] = g.toggle_hotkey;\n    j["global"]["enable_haptic_sound"] = g.enable_haptic_sound;')
cpp = cpp.replace('if (!g.contains("toggle_hotkey") || !g["toggle_hotkey"].is_string()) {\n        g["toggle_hotkey"] = "F14";\n        modified = true;\n    }', 'if (!g.contains("toggle_hotkey") || !g["toggle_hotkey"].is_string()) {\n        g["toggle_hotkey"] = "F14";\n        modified = true;\n    }\n    if (!g.contains("enable_haptic_sound") || !g["enable_haptic_sound"].is_boolean()) {\n        g["enable_haptic_sound"] = true;\n        modified = true;\n    }')
with open(cpp_path, "w", encoding="utf-8") as f:
    f.write(cpp)

# 5. Update input_hook.cpp
ih_path = r"c:\Users\carla\Desktop\AHK\Arvie Knob Macro\src\input_hook.cpp"
with open(ih_path, "r", encoding="utf-8") as f:
    ih = f.read()
if '#pragma comment(lib, "winmm.lib")' not in ih:
    ih = ih.replace('#include "macro_runner.h"', '#include "macro_runner.h"\n#include <mmsystem.h>\n#pragma comment(lib, "winmm.lib")')

# When rotaryHovered changes in input_hook.cpp:
# We find: g_rotaryHovered = nextSlot;
ih = ih.replace('g_rotaryHovered = nextSlot;\n                            }', 'g_rotaryHovered = nextSlot;\n                                if (g_configStore.GetGlobal().enable_haptic_sound) PlaySoundW(L"resources\\\\sounds\\\\tick.wav", NULL, SND_FILENAME | SND_ASYNC | SND_NODEFAULT);\n                            }')

with open(ih_path, "w", encoding="utf-8") as f:
    f.write(ih)

# 6. Update radial_menu.cpp (for mouse hover)
rm_path = r"c:\Users\carla\Desktop\AHK\Arvie Knob Macro\src\radial_menu.cpp"
with open(rm_path, "r", encoding="utf-8") as f:
    rm = f.read()
if '#pragma comment(lib, "winmm.lib")' not in rm:
    rm = rm.replace('#include "input_hook.h"', '#include "input_hook.h"\n#include <mmsystem.h>\n#pragma comment(lib, "winmm.lib")')
    
rm_hover_find = """                int currentHovered = (int)GetWindowLongPtrW(hWnd, GWLP_USERDATA);
                if (hovered != currentHovered) {
                    SetWindowLongPtrW(hWnd, GWLP_USERDATA, hovered);
                    RedrawRadialMenu(hWnd, hovered);
                }"""
rm_hover_replace = """                int currentHovered = (int)GetWindowLongPtrW(hWnd, GWLP_USERDATA);
                if (hovered != currentHovered) {
                    SetWindowLongPtrW(hWnd, GWLP_USERDATA, hovered);
                    RedrawRadialMenu(hWnd, hovered);
                    if (hovered != -1 && g_configStore.GetGlobal().enable_haptic_sound) {
                        PlaySoundW(L"resources\\\\sounds\\\\tick.wav", NULL, SND_FILENAME | SND_ASYNC | SND_NODEFAULT);
                    }
                }"""
rm = rm.replace(rm_hover_find, rm_hover_replace)
with open(rm_path, "w", encoding="utf-8") as f:
    f.write(rm)

# 7. Update Web UI
html_path = r"c:\Users\carla\Desktop\AHK\Arvie Knob Macro\ui\index.html"
with open(html_path, "r", encoding="utf-8") as f:
    html = f.read()
html = html.replace(
    '<label for="is_enabled" style="font-weight: 700; color: #fff;">Master App Enable</label>\n                </div>',
    '<label for="is_enabled" style="font-weight: 700; color: #fff;">Master App Enable</label>\n                </div>\n                <div class="checkbox-group" style="margin-bottom: 1.5rem;">\n                    <input type="checkbox" id="enable_haptic_sound">\n                    <label for="enable_haptic_sound">Enable Haptic Audio Tick</label>\n                </div>'
)
with open(html_path, "w", encoding="utf-8") as f:
    f.write(html)

js_path = r"c:\Users\carla\Desktop\AHK\Arvie Knob Macro\ui\app.js"
with open(js_path, "r", encoding="utf-8") as f:
    js = f.read()
js = js.replace("isEnabled: document.getElementById('is_enabled'),", "isEnabled: document.getElementById('is_enabled'),\n    enableHapticSound: document.getElementById('enable_haptic_sound'),")
js = js.replace("DOM.isEnabled.checked = g.is_enabled ?? true;", "DOM.isEnabled.checked = g.is_enabled ?? true;\n    DOM.enableHapticSound.checked = g.enable_haptic_sound ?? true;")
js = js.replace("configData.global.is_enabled = DOM.isEnabled.checked;", "configData.global.is_enabled = DOM.isEnabled.checked;\n    configData.global.enable_haptic_sound = DOM.enableHapticSound.checked;")
with open(js_path, "w", encoding="utf-8") as f:
    f.write(js)

print("All haptic updates complete!")
