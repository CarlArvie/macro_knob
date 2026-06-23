import os

cs_path = r"c:\Users\carla\Desktop\AHK\Arvie Knob Macro\config_server.py"
with open(cs_path, "r", encoding="utf-8") as f:
    cs = f.read()

find_auto = """                # Auto-reload daemon
                try:
                    hwnd = ctypes.windll.user32.FindWindowW(ctypes.c_wchar_p("KnobLaunchDaemon"), ctypes.c_wchar_p("KnobLaunchDaemonWindow"))
                    if hwnd:
                        ctypes.windll.user32.PostMessageW(hwnd, 0x0111, 40003, 0) # WM_COMMAND, ID_TRAY_RELOAD
                except Exception as ex:
                    pass"""

replace_auto = """                # Auto-reload daemon
                try:
                    import subprocess
                    subprocess.run(["taskkill", "/IM", "knoblaunch.exe", "/F"], capture_output=True)
                    subprocess.Popen(["bin\\\\knoblaunch.exe"], cwd=os.path.dirname(os.path.abspath(__file__)), creationflags=subprocess.CREATE_NO_WINDOW)
                except Exception as ex:
                    print("Error restarting daemon:", ex)"""

if find_auto in cs:
    cs = cs.replace(find_auto, replace_auto)
    with open(cs_path, "w", encoding="utf-8") as f:
        f.write(cs)
    print("Auto-restart patched in config_server.py!")
else:
    print("Could not find auto-reload block.")
