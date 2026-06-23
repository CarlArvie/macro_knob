import os, sys

config_server_path = "c:\\Users\\carla\\Desktop\\AHK\\Arvie Knob Macro\\config_server.py"
with open(config_server_path, "r", encoding="utf-8") as f:
    code = f.read()

# Add ctypes at top
if "import ctypes" not in code:
    code = code.replace("import json", "import json\nimport ctypes")

# In do_POST /api/save
find_str = """                with open(CONFIG_PATH, 'w') as f:
                    json.dump(data, f, indent=4)
                
                self.send_response(200)"""

replace_str = """                with open(CONFIG_PATH, 'w') as f:
                    json.dump(data, f, indent=4)
                
                # Auto-reload daemon
                try:
                    hwnd = ctypes.windll.user32.FindWindowW("KnobLaunchDaemon", "KnobLaunchDaemonWindow")
                    if hwnd:
                        ctypes.windll.user32.PostMessageW(hwnd, 0x0111, 40003, 0) # WM_COMMAND, ID_TRAY_RELOAD
                except Exception as ex:
                    pass

                self.send_response(200)"""

code = code.replace(find_str, replace_str)

with open(config_server_path, "w", encoding="utf-8") as f:
    f.write(code)

print("config_server.py patched")
