import unittest
import os
import time
import ctypes
from test_cases.test_base import KnobLaunchTestBase, User32, VK_VOLUME_MUTE, VK_F13, POINT

# Determine if the daemon executable is available
WORKSPACE_DIR = r"c:\Users\carla\Desktop\AHK\Arvie Knob Macro"
DAEMON_EXE = os.path.join(WORKSPACE_DIR, "knoblaunch.exe")
if not os.path.exists(DAEMON_EXE):
    debug_path = os.path.join(WORKSPACE_DIR, "build", "Debug", "knoblaunch.exe")
    if os.path.exists(debug_path):
        DAEMON_EXE = debug_path

DAEMON_EXISTS = os.path.exists(DAEMON_EXE)

# Check if GUI interactions are supported in the current session
def check_gui_available():
    pt = POINT()
    if not User32.GetCursorPos(ctypes.byref(pt)):
        return False
    ret = User32.SetCursorPos(pt.x, pt.y)
    if ret == 0:
        err = ctypes.windll.kernel32.GetLastError()
        if err == 5:  # ERROR_ACCESS_DENIED
            return False
    return True

GUI_AVAILABLE = check_gui_available()

# Constants
VK_F24 = 0x87
WM_COMMAND = 0x0111
ID_TRAY_DISABLE = 40001 # Mock command ID for tray menu toggle
ID_TRAY_ENABLE = 40002

@unittest.skipIf(not DAEMON_EXISTS, "knoblaunch.exe not found. Build the project first.")
class TestHotkey(KnobLaunchTestBase):

    def test_t1_f1_1_default_hotkey_hold(self):
        """T1.F1.1: Press and hold default hotkey for >hold_threshold_ms. Radial menu window is created and visible."""
        self.start_daemon()
        
        # Send volume mute down and hold
        self.send_key(VK_VOLUME_MUTE, is_down=True)
        time.sleep(0.2)  # threshold is 150ms
        
        hwnd = self.find_radial_menu_window()
        self.assertIsNotNone(hwnd, "Radial menu window handle was not found after press-and-hold.")
        self.assertTrue(self.is_window_visible(hwnd), "Radial menu window is not visible.")
        
        self.send_key(VK_VOLUME_MUTE, is_down=False)

    def test_t1_f1_2_hotkey_tap_short(self):
        """T1.F1.2: Press and release hotkey within <hold_threshold_ms. Radial menu does not open."""
        self.start_daemon()
        
        self.send_key(VK_VOLUME_MUTE, is_down=True)
        time.sleep(0.05)  # threshold is 150ms
        self.send_key(VK_VOLUME_MUTE, is_down=False)
        
        time.sleep(0.1)
        hwnd = self.find_radial_menu_window()
        self.assertFalse(self.is_window_visible(hwnd), "Radial menu opened on a short tap.")

    def test_t1_f1_3_hotkey_override(self):
        """T1.F1.3: Modify hotkey_override to F24, press and hold F24, radial menu opens."""
        config = {
            "global": {
                "hold_threshold_ms": 150,
                "radial_size": "medium",
                "hotkey_override": "F24",
                "show_tray_icon": True,
                "debug_log": True
            },
            "slots": [{"index": i, "label": f"Slot {i}", "icon": "", "color": "blue", "type": "open_url", "config": {"url": "https://google.com"}} for i in range(8)]
        }
        self.write_config(config)
        self.start_daemon()
        
        # Hold override key F24
        self.send_key(VK_F24, is_down=True)
        time.sleep(0.2)
        
        hwnd = self.find_radial_menu_window()
        self.assertIsNotNone(hwnd, "Radial menu did not open with F24 override hotkey.")
        self.assertTrue(self.is_window_visible(hwnd))
        
        self.send_key(VK_F24, is_down=False)
        
        # Verify default key no longer opens it
        time.sleep(0.2)
        self.send_key(VK_VOLUME_MUTE, is_down=True)
        time.sleep(0.2)
        hwnd_default = self.find_radial_menu_window()
        self.assertFalse(self.is_window_visible(hwnd_default), "Radial menu opened with default key despite override.")
        self.send_key(VK_VOLUME_MUTE, is_down=False)

    def test_t1_f1_4_hotkey_release_close(self):
        """T1.F1.4: Press and hold to open, then release. Radial menu window closes."""
        self.start_daemon()
        
        self.send_key(VK_VOLUME_MUTE, is_down=True)
        time.sleep(0.2)
        
        hwnd = self.find_radial_menu_window()
        self.assertTrue(self.is_window_visible(hwnd))
        
        self.send_key(VK_VOLUME_MUTE, is_down=False)
        time.sleep(0.1)
        
        self.assertFalse(self.is_window_visible(hwnd), "Radial menu remained visible after hotkey release.")

    def test_t1_f1_5_disable_enable_toggle(self):
        """T1.F1.5: Trigger key hook disable. Hold key. Verify no menu opens."""
        self.start_daemon()
        
        # Simulate disabling hook from tray context menu
        # Find daemon background/tray window (typically class is KnobLaunchDaemon or similar)
        daemon_hwnd = User32.FindWindowW("KnobLaunchDaemon", None)
        if daemon_hwnd:
            User32.SendMessageW(daemon_hwnd, WM_COMMAND, ID_TRAY_DISABLE, 0)
        else:
            # Fallback to direct DLL hook disable mock if IPC/tray handles are not accessible
            pass
        
        self.send_key(VK_VOLUME_MUTE, is_down=True)
        time.sleep(0.2)
        hwnd = self.find_radial_menu_window()
        self.assertFalse(self.is_window_visible(hwnd), "Radial menu opened while hook was disabled.")
        self.send_key(VK_VOLUME_MUTE, is_down=False)
        
        # Re-enable hook
        if daemon_hwnd:
            User32.SendMessageW(daemon_hwnd, WM_COMMAND, ID_TRAY_ENABLE, 0)
            
        time.sleep(0.1)
        self.send_key(VK_VOLUME_MUTE, is_down=True)
        time.sleep(0.2)
        hwnd = self.find_radial_menu_window()
        self.assertTrue(self.is_window_visible(hwnd), "Radial menu failed to open after re-enabling hook.")
        self.send_key(VK_VOLUME_MUTE, is_down=False)

    def test_t2_f1_1_hold_exact_threshold(self):
        """T2.F1.1: Hold duration exactly at threshold ms. Verify menu opens."""
        self.start_daemon()
        self.send_key(VK_VOLUME_MUTE, is_down=True)
        time.sleep(0.15)  # exactly 150ms
        hwnd = self.find_radial_menu_window()
        self.assertTrue(self.is_window_visible(hwnd), "Radial menu did not open at exact threshold.")
        self.send_key(VK_VOLUME_MUTE, is_down=False)

    def test_t2_f1_2_hold_just_below_threshold(self):
        """T2.F1.2: Hold duration just below threshold (threshold - 5 ms). Verify menu doesn't open."""
        self.start_daemon()
        self.send_key(VK_VOLUME_MUTE, is_down=True)
        time.sleep(0.145)  # threshold - 5ms
        self.send_key(VK_VOLUME_MUTE, is_down=False)
        time.sleep(0.05)
        hwnd = self.find_radial_menu_window()
        self.assertFalse(self.is_window_visible(hwnd), "Radial menu opened just below threshold.")

    def test_t2_f1_3_hold_just_above_threshold(self):
        """T2.F1.3: Hold duration just above threshold (threshold + 5 ms). Verify menu opens."""
        self.start_daemon()
        self.send_key(VK_VOLUME_MUTE, is_down=True)
        time.sleep(0.155)  # threshold + 5ms
        hwnd = self.find_radial_menu_window()
        self.assertTrue(self.is_window_visible(hwnd), "Radial menu did not open just above threshold.")
        self.send_key(VK_VOLUME_MUTE, is_down=False)

    def test_t2_f1_4_extreme_threshold_small(self):
        """T2.F1.4: Set threshold to 10ms. Verify it triggers reliably."""
        config = {
            "global": {
                "hold_threshold_ms": 10,
                "radial_size": "medium",
                "hotkey_override": "",
                "show_tray_icon": True,
                "debug_log": True
            },
            "slots": [{"index": i, "label": f"Slot {i}", "icon": "", "color": "blue", "type": "open_url", "config": {"url": "https://google.com"}} for i in range(8)]
        }
        self.write_config(config)
        self.start_daemon()
        
        self.send_key(VK_VOLUME_MUTE, is_down=True)
        time.sleep(0.015)  # 15ms
        hwnd = self.find_radial_menu_window()
        self.assertTrue(self.is_window_visible(hwnd), "Radial menu did not trigger at extreme low threshold.")
        self.send_key(VK_VOLUME_MUTE, is_down=False)

    def test_t2_f1_5_extreme_threshold_large(self):
        """T2.F1.5: Set threshold to 3000ms. Verify hold of 1000ms doesn't trigger, 3100ms triggers."""
        config = {
            "global": {
                "hold_threshold_ms": 3000,
                "radial_size": "medium",
                "hotkey_override": "",
                "show_tray_icon": True,
                "debug_log": True
            },
            "slots": [{"index": i, "label": f"Slot {i}", "icon": "", "color": "blue", "type": "open_url", "config": {"url": "https://google.com"}} for i in range(8)]
        }
        self.write_config(config)
        self.start_daemon()
        
        # Test 1000ms hold (should not open)
        self.send_key(VK_VOLUME_MUTE, is_down=True)
        time.sleep(1.0)
        hwnd = self.find_radial_menu_window()
        self.assertFalse(self.is_window_visible(hwnd), "Radial menu opened prematurely during long threshold test.")
        
        # Continue holding up to 3100ms
        time.sleep(2.1)
        hwnd = self.find_radial_menu_window()
        self.assertTrue(self.is_window_visible(hwnd), "Radial menu did not open after required 3000ms threshold.")
        self.send_key(VK_VOLUME_MUTE, is_down=False)

    def test_t3_1_override_custom_threshold(self):
        """T3.1: Hotkey Override + Custom Hold Threshold. F24 override key respects custom duration."""
        config = {
            "global": {
                "hold_threshold_ms": 500,
                "radial_size": "medium",
                "hotkey_override": "F24",
                "show_tray_icon": True,
                "debug_log": True
            },
            "slots": [{"index": i, "label": f"Slot {i}", "icon": "", "color": "blue", "type": "open_url", "config": {"url": "https://google.com"}} for i in range(8)]
        }
        self.write_config(config)
        self.start_daemon()
        
        self.send_key(VK_F24, is_down=True)
        time.sleep(0.4)
        hwnd = self.find_radial_menu_window()
        self.assertFalse(self.is_window_visible(hwnd), "Radial menu opened before custom threshold (500ms) with override key.")
        
        time.sleep(0.15)
        hwnd = self.find_radial_menu_window()
        self.assertTrue(self.is_window_visible(hwnd), "Radial menu failed to open after custom threshold with override key.")
        self.send_key(VK_F24, is_down=False)

    def test_t3_4_ahk_invoke_hook_no_loop(self):
        """T3.4: AHK macro invoking key hook does not cause infinite recursion loop."""
        ahk_script_path = os.path.join(self.WORKSPACE_DIR, "tests", "self_press.ahk")
        # Write script that sends volume mute
        with open(ahk_script_path, "w") as f:
            f.write('#Requires AutoHotkey v2.0\nSend "{Volume_Mute}"\n')
            
        config = {
            "global": {
                "hold_threshold_ms": 150,
                "radial_size": "medium",
                "hotkey_override": "",
                "show_tray_icon": True,
                "debug_log": True
            },
            "slots": [
                {"index": 0, "label": "Self Press", "icon": "", "color": "red", "type": "ahk_script", "config": {"script_file": "tests/self_press.ahk"}},
                *([{"index": i, "label": f"Slot {i}", "icon": "", "color": "blue", "type": "open_url", "config": {"url": "https://google.com"}} for i in range(1, 8)])
            ]
        }
        self.write_config(config)
        self.start_daemon()
        
        # Open menu
        self.send_key(VK_VOLUME_MUTE, is_down=True)
        time.sleep(0.2)
        hwnd = self.find_radial_menu_window()
        self.assertTrue(self.is_window_visible(hwnd))
        
        # Warp to Sector 0 (typically top or 0 degrees)
        rect = self.get_window_rect(hwnd)
        center_x = (rect.left + rect.right) // 2
        center_y = (rect.top + rect.bottom) // 2
        
        if GUI_AVAILABLE:
            self.set_cursor_position(center_x, center_y - 80)
            
        # Release key to trigger Sector 0
        self.send_key(VK_VOLUME_MUTE, is_down=False)
        time.sleep(1.0) # wait for script to execute
        
        # Verify daemon did not crash or get stuck in loop
        self.stop_daemon()
        
        # Cleanup script
        if os.path.exists(ahk_script_path):
            os.remove(ahk_script_path)

    def test_t4_3_volume_fallback_tap_sequence(self):
        """T4.3: Send 10 quick taps. Radial menu never opens, fallback taps are ignored or forwarded."""
        self.start_daemon()
        
        for _ in range(10):
            self.send_key(VK_VOLUME_MUTE, is_down=True)
            time.sleep(0.02)
            self.send_key(VK_VOLUME_MUTE, is_down=False)
            time.sleep(0.05)
            
        time.sleep(0.2)
        hwnd = self.find_radial_menu_window()
        self.assertFalse(self.is_window_visible(hwnd), "Radial menu opened during rapid tap fallback sequence.")
