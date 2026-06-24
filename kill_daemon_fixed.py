import ctypes
import time

hwnd = ctypes.windll.user32.FindWindowW(ctypes.c_wchar_p("KnobLaunchDaemon"), ctypes.c_wchar_p("KnobLaunchDaemonWindow"))
if hwnd:
    print("Found daemon window. Sending EXIT command...")
    ctypes.windll.user32.PostMessageW(hwnd, 0x0111, 40004, 0) # 40004 is ID_TRAY_EXIT
    time.sleep(1)
    print("Daemon exited.")
else:
    print("Daemon not found. Looking by class only...")
    hwnd = ctypes.windll.user32.FindWindowW(ctypes.c_wchar_p("KnobLaunchDaemon"), None)
    if hwnd:
        print("Found by class. Exiting...")
        ctypes.windll.user32.PostMessageW(hwnd, 0x0111, 40004, 0)
    else:
        print("Still not found!")
