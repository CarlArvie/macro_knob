# KnobLaunch E2E Testing Harness & Mocking Strategy (Milestone T1)

## 1. Observation
- The workspace directory `c:\Users\carla\Desktop\AHK\Arvie Knob Macro` contains design files (`PROJECT.md`, `TEST_INFRA.md`, `VolumeKnobMacro_ProjectPlan.md`) but no codebase implementation yet.
- From `PROJECT.md` line 64: The daemon window class name is `"KnobLaunchRadialMenu"`.
- From `PROJECT.md` line 48: The configuration is saved at `config/config.json`.
- From `TEST_INFRA.md` line 16-17: The E2E test runner must be written in Python (`tests/test_runner.py`), execute unit-test format case files in `tests/test_cases/`, and use standard python `ctypes` library to simulate keypress events, move cursor, inspect window classes, and retrieve window rects.
- Tested `ctypes` struct alignments and sizes using host Python command line:
  - `INPUT` size: 40 bytes (correctly aligned on 64-bit Windows)
  - `KEYBDINPUT` size: 24 bytes
  - `MOUSEINPUT` size: 32 bytes
  - `GetWindowLongPtrW` correctly fetches desktop styles.

---

## 2. Logic Chain
- To achieve zero external dependencies and ease of execution, the test suite must rely strictly on standard Python libraries (`ctypes`, `unittest`, `subprocess`, `json`, `shutil`).
- Keyboard hooks (`WH_KEYBOARD_LL`) in the core daemon capture hardware events. To bypass physical interaction and inject events into the hook, we must use the Win32 `SendInput` API.
- Injecting keyboard events requires configuring both Virtual Key (VK) codes and hardware scan codes. Since layouts vary, we dynamically resolve scan codes using `MapVirtualKeyW` and supply hardcoded fallback values for virtual keys like `F13` (`0x64`) and `Volume Mute` (`0x20`) which might not be mapped on all standard keyboards.
- Checking window presence and attributes is done using `FindWindowW`, `IsWindowVisible`, and `GetWindowRect`.
- Validating the GTA-style overlay's `WS_EX_TOPMOST` and `WS_EX_LAYERED` styles requires querying the window's extended style long value (`GWL_EXSTYLE = -20`) using `GetWindowLongPtrW` (with a fallback to `GetWindowLongW` on 32-bit Python).
- Validating the cursor warp feature requires setting the cursor position (`SetCursorPos`) and verifying coordinates (`GetCursorPos`) relative to the window's center rect.
- Controlling the daemon lifecycle requires spawning `knoblaunch.exe` using `subprocess.Popen`. Standard output/error should be piped to a file `tests/daemon.log` to prevent internal buffer blocks and capture logs for debugging.
- To prevent test contamination and orphaned threads, the test runner must run a global teardown function using `taskkill /F` for both `knoblaunch.exe` and `AutoHotkey64.exe` after each test case.
- Safe config backup/restoration is achieved by copying `config/config.json` to a temporary backup file `config/config.json.bak` in `setUpClass`, restoring it in `tearDownClass`, and clearing temporary test configurations after execution.

---

## 3. Caveats
- **User Interface Privilege Isolation (UIPI)**: If `knoblaunch.exe` is run with Administrator privileges, the Python test runner must also be launched as Administrator, otherwise Windows will block the simulated `SendInput` events from reaching the hook.
- **Active Desktop Session**: Since the tests involve virtual mouse movement, window rendering, and keyboard simulation, the target machine must have an active desktop session. Running in a headless, non-interactive CI runner (like SSH or standard service-based actions) will cause `SendInput` and window queries to fail.
- **DPI Scaling**: Depending on Windows display scaling, coordinates returned by `GetWindowRect` vs mouse cursor position might have discrepancies if the daemon is DPI-aware and the Python process is not. However, since the math uses relative centering (`rect.left + width // 2`), it remains robust.

---

## 4. Conclusion
Below is the complete architectural design and code structure proposed for Milestone T1. This includes the test runner entry point, the base test class containing all the required ctypes wrappers and helper methods, and a sample test case demonstrating usage.

### A. Directory Structure
```
c:\Users\carla\Desktop\AHK\Arvie Knob Macro\
├── tests/
│   ├── test_runner.py               # Test suite entry point
│   └── test_cases/
│       ├── __init__.py
│       ├── test_base.py             # Base class containing ctypes, helpers, setup/teardown
│       ├── test_hotkey.py           # Test cases for Hotkey Tap/Hold/Override
│       └── test_gui.py              # Test cases for GUI visibility, centering, warping
```

### B. Implementation Details

#### 1. Test Suite Entry Point (`tests/test_runner.py`)
This file is the main command line entry point that dynamically discovers and executes all test cases.

```python
# filepath: tests/test_runner.py
import unittest
import os
import sys

def main():
    # Setup test discovery in the test_cases directory
    loader = unittest.TestLoader()
    start_dir = os.path.join(os.path.dirname(__file__), 'test_cases')
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # Run test suite
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return exit code (0 for success, 1 for failure)
    sys.exit(not result.wasSuccessful())

if __name__ == '__main__':
    main()
```

#### 2. Base Test Class (`tests/test_cases/test_base.py`)
This file houses all of the ctypes Win32 API structures, keyboard event simulations, window searches, cursor tracking, process lifecycle handlers, and configuration management helpers.

```python
# filepath: tests/test_cases/test_base.py
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

if ctypes.sizeof(ctypes.c_void_p) == 8:
    GetWindowLong = User32.GetWindowLongPtrW
    GetWindowLong.restype = ctypes.c_int64
else:
    GetWindowLong = User32.GetWindowLongW
    GetWindowLong.restype = ctypes.c_int32
GetWindowLong.argtypes = [ctypes.c_void_p, ctypes.c_int]


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
            shutil.move(cls.BACKUP_PATH, cls.CONFIG_PATH)
        elif os.path.exists(cls.CONFIG_PATH):
            os.remove(cls.CONFIG_PATH)
        
        # 2. Cleanup processes
        cls.force_cleanup()

    def setUp(self):
        # Reset daemon processes list
        self.daemon_process = None
        self.log_file = None
        # Start each test case with a clean config if not specified otherwise
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
        self.log_file = open(os.path.join(log_dir, "daemon.log"), "w")
        
        daemon_exe = os.path.join(self.WORKSPACE_DIR, "knoblaunch.exe")
        
        # If the binary is not in root, adjust path (e.g. check build folders if necessary)
        if not os.path.exists(daemon_exe):
            # Fallback check for build directory configurations (e.g. build/Debug/knoblaunch.exe)
            debug_path = os.path.join(self.WORKSPACE_DIR, "build", "Debug", "knoblaunch.exe")
            if os.path.exists(debug_path):
                daemon_exe = debug_path
        
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
        if self.daemon_process:
            if self.daemon_process.poll() is None:
                self.daemon_process.terminate()
                try:
                    self.daemon_process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self.daemon_process.kill()
            self.daemon_process = None
        
        if self.log_file:
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
        User32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))

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
```

#### 3. Sample Hotkey Test Case (`tests/test_cases/test_hotkey.py`)
This file shows how a Worker can use the base class to easily write test cases matching requirements.

```python
# filepath: tests/test_cases/test_hotkey.py
import time
from test_cases.test_base import KnobLaunchTestBase, VK_F13, VK_VOLUME_MUTE, WS_EX_TOPMOST, WS_EX_LAYERED

class TestHotkey(KnobLaunchTestBase):

    def test_default_hotkey_hold_opens_radial_menu(self):
        """T1.F1.1: Default Hotkey Press & Hold opens radial menu."""
        self.start_daemon()
        
        # Press and hold F13 (default key code mapped to the knob press)
        self.send_key(VK_F13, is_down=True)
        time.sleep(0.3)  # Wait longer than 150ms hold_threshold_ms
        
        # Verify the window exists and is visible
        hwnd = self.find_radial_menu_window()
        self.assertIsNotNone(hwnd, "Radial Menu window should exist")
        self.assertTrue(self.is_window_visible(hwnd), "Radial Menu window should be visible during hold")
        
        # Release key and check that the window closes
        self.send_key(VK_F13, is_down=False)
        time.sleep(0.2)
        self.assertFalse(self.is_window_visible(hwnd), "Radial Menu window should close on key release")

    def test_hotkey_tap_does_not_open_radial_menu(self):
        """T1.F1.2: Hotkey Tap (Short Press) does not open the radial menu."""
        self.start_daemon()
        
        # Tap key (duration < 150ms hold_threshold_ms)
        self.press_and_hold_key(VK_F13, duration_seconds=0.05)
        time.sleep(0.2)
        
        # Verify window is not visible
        hwnd = self.find_radial_menu_window()
        if hwnd:
            self.assertFalse(self.is_window_visible(hwnd), "Radial Menu should not be visible for short press taps")

    def test_hotkey_override_config(self):
        """T1.F1.3: Custom hotkey_override triggers radial menu."""
        # Write config with a custom hotkey (Volume Mute)
        custom_config = {
            "global": {
                "hold_threshold_ms": 150,
                "radial_size": "medium",
                "hotkey_override": "Volume_Mute",
                "show_tray_icon": True,
                "debug_log": True
            },
            "slots": [
                {"index": i, "label": f"Slot {i}", "icon": "", "color": "blue", "type": "open_url", "config": {"url": "https://google.com"}}
                for i in range(8)
            ]
        }
        self.write_config(custom_config)
        self.start_daemon()
        
        # Hold Volume Mute
        self.send_key(VK_VOLUME_MUTE, is_down=True)
        time.sleep(0.3)
        
        hwnd = self.find_radial_menu_window()
        self.assertIsNotNone(hwnd, "Radial Menu should open with Volume Mute hotkey override")
        self.assertTrue(self.is_window_visible(hwnd), "Radial Menu should be visible on Volume Mute hold")
        
        self.send_key(VK_VOLUME_MUTE, is_down=False)
```

---

## 5. Verification Method

To verify the test runner works properly:
1. Compile the daemon binary `knoblaunch.exe` and place it in the workspace root `c:\Users\carla\Desktop\AHK\Arvie Knob Macro` (or build it under `build/Debug/knoblaunch.exe`).
2. Run the test runner from the workspace root:
   ```cmd
   python tests/test_runner.py
   ```
3. Observe the output:
   - Output must list tests discovery and execution status (e.g. `test_default_hotkey_hold_opens_radial_menu (test_cases.test_hotkey.TestHotkey) ... ok`).
   - If tests fail, inspect the generated logs in `tests/daemon.log` to see daemon startup state.
4. Verify cleanup:
   - Run `tasklist | findstr /i knob` and `tasklist | findstr /i autohot` after the runner completes to ensure no dangling processes exist.
   - Verify `config/config.json` was restored to its pre-testing state.
