import unittest
import ctypes
import os
import time
import subprocess
import json
import shutil

# --- Ctypes structures for Keyboard & Mouse Simulation ---

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", ctypes.c_long),
        ("dy", ctypes.c_long),
        ("mouseData", ctypes.c_ulong),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ctypes.c_void_p)
    ]

class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", ctypes.c_ushort),
        ("wScan", ctypes.c_ushort),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ctypes.c_void_p)
    ]

class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", ctypes.c_ulong),
        ("wParamL", ctypes.c_ushort),
        ("wParamH", ctypes.c_ushort)
    ]

class INPUT_UNION(ctypes.Union):
    _fields_ = [
        ("mi", MOUSEINPUT),
        ("ki", KEYBDINPUT),
        ("hi", HARDWAREINPUT)
    ]

class INPUT(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.c_ulong),
        ("union", INPUT_UNION)
    ]

class RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long)
    ]

class POINT(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_long),
        ("y", ctypes.c_long)
    ]

# Win32 Constants
VK_F13 = 0x7C
VK_VOLUME_MUTE = 0xAD

INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_EXTENDEDKEY = 0x0001

GWL_EXSTYLE = -20
WS_EX_TOPMOST = 0x00000008
WS_EX_LAYERED = 0x00080000

# Win32 DLL Functions
User32 = ctypes.windll.user32

# Set argument and return types
User32.SendInput.argtypes = [ctypes.c_uint, ctypes.POINTER(INPUT), ctypes.c_int]
User32.SendInput.restype = ctypes.c_uint

User32.MapVirtualKeyW.argtypes = [ctypes.c_uint, ctypes.c_uint]
User32.MapVirtualKeyW.restype = ctypes.c_uint

User32.FindWindowW.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p]
User32.FindWindowW.restype = ctypes.c_void_p

User32.IsWindowVisible.argtypes = [ctypes.c_void_p]
User32.IsWindowVisible.restype = ctypes.c_int

User32.GetWindowRect.argtypes = [ctypes.c_void_p, ctypes.POINTER(RECT)]
User32.GetWindowRect.restype = ctypes.c_int

User32.GetCursorPos.argtypes = [ctypes.POINTER(POINT)]
User32.GetCursorPos.restype = ctypes.c_int

User32.SetCursorPos.argtypes = [ctypes.c_int, ctypes.c_int]
User32.SetCursorPos.restype = ctypes.c_int

# Resolve GetWindowLong / GetWindowLongPtrW based on architecture
if ctypes.sizeof(ctypes.c_void_p) == 8:
    try:
        GetWindowLong = User32.GetWindowLongPtrW
        GetWindowLong.argtypes = [ctypes.c_void_p, ctypes.c_int]
        GetWindowLong.restype = ctypes.c_ssize_t
    except AttributeError:
        GetWindowLong = User32.GetWindowLongW
        GetWindowLong.argtypes = [ctypes.c_void_p, ctypes.c_int]
        GetWindowLong.restype = ctypes.c_long
else:
    GetWindowLong = User32.GetWindowLongW
    GetWindowLong.argtypes = [ctypes.c_void_p, ctypes.c_int]
    GetWindowLong.restype = ctypes.c_long

def check_gui_available():
    pt = POINT()
    if not User32.GetCursorPos(ctypes.byref(pt)):
        return False
    ret = User32.SetCursorPos(pt.x, pt.y)
    if ret == 0:
        err = ctypes.windll.kernel32.GetLastError()
        if err == 5:  # ERROR_ACCESS_DENIED
            return False

    # Send a key up for a dummy key (VK_F24) to verify SendInput doesn't fail with ACCESS_DENIED
    ki = KEYBDINPUT(wVk=0x87, wScan=0, dwFlags=KEYEVENTF_KEYUP, time=0, dwExtraInfo=None)
    inp = INPUT(type=INPUT_KEYBOARD, union=INPUT_UNION(ki=ki))
    ret = User32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))
    if ret == 0:
        err = ctypes.windll.kernel32.GetLastError()
        if err == 5:  # ERROR_ACCESS_DENIED
            return False
            
    return True

GUI_AVAILABLE = check_gui_available()

class KnobLaunchTestBase(unittest.TestCase):
    # Workspace paths
    WORKSPACE_DIR = r"c:\Users\carla\Desktop\AHK\Arvie Knob Macro"
    CONFIG_DIR = os.path.join(WORKSPACE_DIR, "config")
    CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")
    BACKUP_PATH = os.path.join(CONFIG_DIR, "config.json.bak")
    
    daemon_process = None
    log_file = None

    @classmethod
    def setUpClass(cls):
        # 1. Ensure config backup
        os.makedirs(cls.CONFIG_DIR, exist_ok=True)
        if os.path.exists(cls.CONFIG_PATH):
            shutil.copy2(cls.CONFIG_PATH, cls.BACKUP_PATH)
        
        # 2. Kill any stale daemon instances
        cls.force_cleanup()

    @classmethod
    def tearDownClass(cls):
        # 1. Restore original configuration
        if os.path.exists(cls.BACKUP_PATH):
            if os.path.exists(cls.CONFIG_PATH):
                os.remove(cls.CONFIG_PATH)
            shutil.move(cls.BACKUP_PATH, cls.CONFIG_PATH)
        elif os.path.exists(cls.CONFIG_PATH):
            os.remove(cls.CONFIG_PATH)
        
        # 2. Cleanup processes
        cls.force_cleanup()

    def setUp(self):
        # Reset daemon processes list
        self.daemon_process = None
        self.log_file = None
        # Start each test case with a clean config
        self.write_default_config()

    def tearDown(self):
        self.stop_daemon()
        self.force_cleanup()

    # --- Configuration Management Helpers ---

    def write_config(self, config_dict):
        os.makedirs(self.CONFIG_DIR, exist_ok=True)
        with open(self.CONFIG_PATH, 'w') as f:
            json.dump(config_dict, f, indent=4)

    def write_default_config(self):
        default_config = {
            "global": {
                "hold_threshold_ms": 150,
                "radial_size": "medium",
                "hotkey_override": "",
                "show_tray_icon": True,
                "debug_log": True
            },
            "slots": [
                {"index": i, "label": f"Slot {i}", "icon": "", "color": "blue", "type": "open_url", "config": {"url": "https://google.com"}}
                for i in range(8)
            ]
        }
        self.write_config(default_config)

    # --- Daemon Lifecycle Management Helpers ---

    def start_daemon(self):
        # Ensure log directory/file is accessible
        log_dir = os.path.join(self.WORKSPACE_DIR, "tests")
        os.makedirs(log_dir, exist_ok=True)
        self.log_file = open(os.path.join(log_dir, "daemon.log"), "a")
        self.log_file.write(f"\n=================== TEST: {self.id()} ===================\n")
        self.log_file.flush()
        
        daemon_exe = os.path.join(self.WORKSPACE_DIR, "knoblaunch.exe")
        
        # If the binary is not in root, adjust path (e.g. check build folders if necessary)
        if not os.path.exists(daemon_exe):
            debug_path = os.path.join(self.WORKSPACE_DIR, "build", "Debug", "knoblaunch.exe")
            if os.path.exists(debug_path):
                daemon_exe = debug_path
        
        if not os.path.exists(daemon_exe):
            raise FileNotFoundError(f"Daemon executable not found at: {daemon_exe}. Please build the project first.")

        self.daemon_process = subprocess.Popen(
            [daemon_exe],
            cwd=self.WORKSPACE_DIR,
            stdout=self.log_file,
            stderr=subprocess.STDOUT
        )
        
        # Verify it started and didn't crash immediately
        time.sleep(0.5)
        if self.daemon_process.poll() is not None:
            raise RuntimeError(f"Daemon failed to start. Return code: {self.daemon_process.poll()}")

    def stop_daemon(self):
        if hasattr(self, 'daemon_process') and self.daemon_process:
            if self.daemon_process.poll() is None:
                self.daemon_process.terminate()
                try:
                    self.daemon_process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self.daemon_process.kill()
            self.daemon_process = None
        
        if hasattr(self, 'log_file') and self.log_file:
            self.log_file.close()
            self.log_file = None

    @classmethod
    def force_cleanup(cls):
        # Force terminate all processes to prevent test leakage
        subprocess.run(["taskkill", "/F", "/IM", "knoblaunch.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["taskkill", "/F", "/IM", "AutoHotkey64.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # --- Keyboard Input Simulation Helpers ---

    def send_key(self, vk, is_down):
        # Map virtual key to scan code
        scan_code = User32.MapVirtualKeyW(vk, 0)
        if scan_code == 0:
            # Fallbacks if MapVirtualKey returns 0
            if vk == VK_F13:
                scan_code = 0x64
            elif vk == VK_VOLUME_MUTE:
                scan_code = 0x20
        
        dwFlags = 0
        if not is_down:
            dwFlags |= KEYEVENTF_KEYUP
        if vk in [VK_VOLUME_MUTE, 0xAE, 0xAF]:  # Mute, Volume Down, Volume Up
            dwFlags |= KEYEVENTF_EXTENDEDKEY
            
        ki = KEYBDINPUT(
            wVk=vk,
            wScan=scan_code,
            dwFlags=dwFlags,
            time=0,
            dwExtraInfo=None
        )
        inp = INPUT(
            type=INPUT_KEYBOARD,
            union=INPUT_UNION(ki=ki)
        )
        ret = User32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))
        if ret == 0:
            err = ctypes.windll.kernel32.GetLastError()
            print(f"SendInput FAILED in send_key. vk: {vk}, ret: {ret}, err: {err}")

    def press_and_hold_key(self, vk, duration_seconds):
        self.send_key(vk, is_down=True)
        time.sleep(duration_seconds)
        self.send_key(vk, is_down=False)

    # --- Win32 Window State Helpers ---

    def find_radial_menu_window(self):
        # Find window by class name
        return User32.FindWindowW("KnobLaunchRadialMenu", None)

    def is_window_visible(self, hwnd):
        if not hwnd:
            return False
        return bool(User32.IsWindowVisible(hwnd))

    def get_window_rect(self, hwnd):
        if not hwnd:
            return None
        rect = RECT()
        if User32.GetWindowRect(hwnd, ctypes.byref(rect)):
            return rect
        return None

    def get_window_extended_style(self, hwnd):
        if not hwnd:
            return 0
        return GetWindowLong(hwnd, GWL_EXSTYLE)

    # --- Mouse Cursor Control Helpers ---

    def get_cursor_position(self):
        pt = POINT()
        if User32.GetCursorPos(ctypes.byref(pt)):
            return (pt.x, pt.y)
        return (0, 0)

    def set_cursor_position(self, x, y):
        User32.SetCursorPos(x, y)
        time.sleep(0.05) # Wait for event loop to register movement
