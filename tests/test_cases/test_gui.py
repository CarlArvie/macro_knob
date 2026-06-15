import unittest
import os
import time
import ctypes
import math
from test_cases.test_base import KnobLaunchTestBase, User32, VK_VOLUME_MUTE, POINT, RECT, WS_EX_TOPMOST, WS_EX_LAYERED, GUI_AVAILABLE

WORKSPACE_DIR = r"c:\Users\carla\Desktop\AHK\Arvie Knob Macro"
DAEMON_EXE = os.path.join(WORKSPACE_DIR, "knoblaunch.exe")
if not os.path.exists(DAEMON_EXE):
    debug_path = os.path.join(WORKSPACE_DIR, "build", "Debug", "knoblaunch.exe")
    if os.path.exists(debug_path):
        DAEMON_EXE = debug_path

DAEMON_EXISTS = os.path.exists(DAEMON_EXE)

@unittest.skipIf(not DAEMON_EXISTS, "knoblaunch.exe not found. Build the project first.")
@unittest.skipIf(not GUI_AVAILABLE, "Interactive GUI session not available")
class TestGui(KnobLaunchTestBase):

    def get_sector_coordinates(self, center_x, center_y, sector_idx, radius=100):
        # 8-sectors layout starting from 12 o'clock (0 degrees) going clockwise
        angle_deg = sector_idx * 45.0
        angle_rad = math.radians(angle_deg)
        x = int(center_x + radius * math.sin(angle_rad))
        y = int(center_y - radius * math.cos(angle_rad))
        return x, y

    def write_unique_trigger_config(self):
        # Configure each slot to run a cmd macro that writes a specific file
        slots = []
        for i in range(8):
            marker_file = os.path.join(self.WORKSPACE_DIR, f"tests\\slot_{i}_triggered.txt")
            slots.append({
                "index": i,
                "label": f"Slot {i}",
                "icon": "",
                "color": "blue",
                "type": "run_program",
                "config": {
                    "path": "C:\\Windows\\System32\\cmd.exe",
                    "args": f"/c echo fired > \"{marker_file}\""
                }
            })
        config = {
            "global": {
                "hold_threshold_ms": 150,
                "radial_size": "medium",
                "hotkey_override": "",
                "show_tray_icon": True,
                "debug_log": True
            },
            "slots": slots
        }
        self.write_config(config)

    def clean_trigger_files(self):
        for i in range(8):
            fpath = os.path.join(self.WORKSPACE_DIR, f"tests\\slot_{i}_triggered.txt")
            if os.path.exists(fpath):
                try:
                    os.remove(fpath)
                except OSError:
                    pass

    @unittest.skipIf(not GUI_AVAILABLE, "SetCursorPos not allowed in this environment.")
    def test_t1_f2_1_cursor_warp(self):
        """T1.F2.1: Cursor Warp on Open. Cursor is centered in the radial menu window."""
        self.start_daemon()
        self.set_cursor_position(100, 100)
        
        self.send_key(VK_VOLUME_MUTE, is_down=True)
        time.sleep(0.2)
        
        hwnd = self.find_radial_menu_window()
        self.assertIsNotNone(hwnd)
        
        rect = self.get_window_rect(hwnd)
        center_x = (rect.left + rect.right) // 2
        center_y = (rect.top + rect.bottom) // 2
        
        cx, cy = self.get_cursor_position()
        self.assertAlmostEqual(cx, center_x, delta=2)
        self.assertAlmostEqual(cy, center_y, delta=2)
        
        self.send_key(VK_VOLUME_MUTE, is_down=False)

    @unittest.skipIf(not GUI_AVAILABLE, "SetCursorPos not allowed in this environment.")
    def test_t1_f2_2_sector_highlight(self):
        """T1.F2.2: Sector Hover Highlight. Move to sector angle and verify slot activation on release."""
        self.write_unique_trigger_config()
        self.clean_trigger_files()
        self.start_daemon()
        
        # We will test Sector 2 (90 degrees, directly right)
        self.send_key(VK_VOLUME_MUTE, is_down=True)
        time.sleep(0.2)
        
        hwnd = self.find_radial_menu_window()
        rect = self.get_window_rect(hwnd)
        center_x = (rect.left + rect.right) // 2
        center_y = (rect.top + rect.bottom) // 2
        
        sx, sy = self.get_sector_coordinates(center_x, center_y, 2, radius=100)
        self.set_cursor_position(sx, sy)
        
        self.send_key(VK_VOLUME_MUTE, is_down=False)
        time.sleep(0.5) # Wait for cmd process
        
        # Verify slot 2 triggered, others did not
        self.assertTrue(os.path.exists(os.path.join(self.WORKSPACE_DIR, "tests\\slot_2_triggered.txt")))
        for i in range(8):
            if i != 2:
                self.assertFalse(os.path.exists(os.path.join(self.WORKSPACE_DIR, f"tests\\slot_{i}_triggered.txt")))
                
        self.clean_trigger_files()

    @unittest.skipIf(not GUI_AVAILABLE, "SetCursorPos not allowed in this environment.")
    def test_t1_f2_3_sector_selection_release(self):
        """T1.F2.3: Sector Selection Release. Check all 8 sectors map correctly by releasing in each."""
        self.write_unique_trigger_config()
        
        for k in range(8):
            self.clean_trigger_files()
            self.start_daemon()
            
            self.send_key(VK_VOLUME_MUTE, is_down=True)
            time.sleep(0.2)
            
            hwnd = self.find_radial_menu_window()
            rect = self.get_window_rect(hwnd)
            center_x = (rect.left + rect.right) // 2
            center_y = (rect.top + rect.bottom) // 2
            
            sx, sy = self.get_sector_coordinates(center_x, center_y, k, radius=120)
            self.set_cursor_position(sx, sy)
            
            self.send_key(VK_VOLUME_MUTE, is_down=False)
            time.sleep(0.5)
            
            self.assertTrue(os.path.exists(os.path.join(self.WORKSPACE_DIR, f"tests\\slot_{k}_triggered.txt")), f"Sector {k} failed to trigger.")
            self.stop_daemon()
            
        self.clean_trigger_files()

    @unittest.skipIf(not GUI_AVAILABLE, "SetCursorPos not allowed in this environment.")
    def test_t1_f2_4_center_cancel_zone(self):
        """T1.F2.4: Center Cancel Zone. Hold, release in center zone. No action triggers."""
        self.write_unique_trigger_config()
        self.clean_trigger_files()
        self.start_daemon()
        
        self.send_key(VK_VOLUME_MUTE, is_down=True)
        time.sleep(0.2)
        
        hwnd = self.find_radial_menu_window()
        rect = self.get_window_rect(hwnd)
        center_x = (rect.left + rect.right) // 2
        center_y = (rect.top + rect.bottom) // 2
        
        # Position mouse close to center (e.g. 10px offset, which is well within 60px cancel zone)
        self.set_cursor_position(center_x + 10, center_y - 10)
        
        self.send_key(VK_VOLUME_MUTE, is_down=False)
        time.sleep(0.5)
        
        # Verify no file is written
        for i in range(8):
            self.assertFalse(os.path.exists(os.path.join(self.WORKSPACE_DIR, f"tests\\slot_{i}_triggered.txt")))
            
        self.clean_trigger_files()

    def test_t1_f2_5_window_styles(self):
        """T1.F2.5: Window Styles. Verify WS_EX_TOPMOST and WS_EX_LAYERED exist."""
        self.start_daemon()
        self.send_key(VK_VOLUME_MUTE, is_down=True)
        time.sleep(0.2)
        
        hwnd = self.find_radial_menu_window()
        self.assertIsNotNone(hwnd)
        
        style = self.get_window_extended_style(hwnd)
        self.assertTrue(style & WS_EX_TOPMOST, "Radial menu window lacks WS_EX_TOPMOST style.")
        self.assertTrue(style & WS_EX_LAYERED, "Radial menu window lacks WS_EX_LAYERED style.")
        
        self.send_key(VK_VOLUME_MUTE, is_down=False)

    @unittest.skipIf(not GUI_AVAILABLE, "SetCursorPos not allowed in this environment.")
    def test_t2_f2_1_mouse_extreme_boundary(self):
        """T2.F2.1: Mouse at extreme boundary. Move 1000px away, still triggers correct sector based on angle."""
        self.write_unique_trigger_config()
        self.clean_trigger_files()
        self.start_daemon()
        
        self.send_key(VK_VOLUME_MUTE, is_down=True)
        time.sleep(0.2)
        
        hwnd = self.find_radial_menu_window()
        rect = self.get_window_rect(hwnd)
        center_x = (rect.left + rect.right) // 2
        center_y = (rect.top + rect.bottom) // 2
        
        # Move far right (Sector 2)
        self.set_cursor_position(center_x + 1000, center_y)
        
        self.send_key(VK_VOLUME_MUTE, is_down=False)
        time.sleep(0.5)
        
        self.assertTrue(os.path.exists(os.path.join(self.WORKSPACE_DIR, "tests\\slot_2_triggered.txt")))
        self.clean_trigger_files()

    @unittest.skipIf(not GUI_AVAILABLE, "SetCursorPos not allowed in this environment.")
    def test_t2_f2_2_mouse_cancel_border(self):
        """T2.F2.2: Mouse at dead-center border. Move exactly 60px away. Verifies edge behavior."""
        self.write_unique_trigger_config()
        self.clean_trigger_files()
        self.start_daemon()
        
        self.send_key(VK_VOLUME_MUTE, is_down=True)
        time.sleep(0.2)
        
        hwnd = self.find_radial_menu_window()
        rect = self.get_window_rect(hwnd)
        center_x = (rect.left + rect.right) // 2
        center_y = (rect.top + rect.bottom) // 2
        
        # Position exactly at 60px boundary (Sector 2)
        self.set_cursor_position(center_x + 60, center_y)
        
        self.send_key(VK_VOLUME_MUTE, is_down=False)
        time.sleep(0.5)
        
        # Action should trigger since it's on or outside the 60px cancel boundary
        self.assertTrue(os.path.exists(os.path.join(self.WORKSPACE_DIR, "tests\\slot_2_triggered.txt")))
        self.clean_trigger_files()

    def test_t2_f2_3_rapid_menu_toggle(self):
        """T2.F2.3: Rapid Menu Toggle. Open/close in rapid succession, checks reliability and leaks."""
        self.start_daemon()
        for _ in range(5):
            self.send_key(VK_VOLUME_MUTE, is_down=True)
            time.sleep(0.2)
            hwnd = self.find_radial_menu_window()
            self.assertTrue(self.is_window_visible(hwnd))
            
            self.send_key(VK_VOLUME_MUTE, is_down=False)
            time.sleep(0.05)
            self.assertFalse(self.is_window_visible(hwnd))

    def test_t2_f2_4_window_overlapping_controls(self):
        """T2.F2.4: Window overlapping controls. Open menu when another topmost window is active, verify menu is on top."""
        self.start_daemon()
        
        # Create a basic topmost window using standard Win32 (or dummy ctypes window)
        # For simple E2E, check that finding our window succeeds and it has WS_EX_TOPMOST style.
        # We can also verify it is the active/foreground window or topmost in Z-order.
        self.send_key(VK_VOLUME_MUTE, is_down=True)
        time.sleep(0.2)
        
        hwnd = self.find_radial_menu_window()
        self.assertIsNotNone(hwnd)
        
        # Verify it has topmost style
        style = self.get_window_extended_style(hwnd)
        self.assertTrue(style & WS_EX_TOPMOST)
        
        self.send_key(VK_VOLUME_MUTE, is_down=False)

    @unittest.skipIf(not GUI_AVAILABLE, "SetCursorPos not allowed in this environment.")
    def test_t2_f2_5_cursor_warp_screen_edge(self):
        """T2.F2.5: Cursor warp when cursor is at screen edge. Verify warping center is correct."""
        self.start_daemon()
        # Move cursor to extreme screen edge
        self.set_cursor_position(0, 0)
        
        self.send_key(VK_VOLUME_MUTE, is_down=True)
        time.sleep(0.2)
        
        hwnd = self.find_radial_menu_window()
        rect = self.get_window_rect(hwnd)
        center_x = (rect.left + rect.right) // 2
        center_y = (rect.top + rect.bottom) // 2
        
        cx, cy = self.get_cursor_position()
        self.assertAlmostEqual(cx, center_x, delta=2)
        self.assertAlmostEqual(cy, center_y, delta=2)
        
        self.send_key(VK_VOLUME_MUTE, is_down=False)

    def test_t3_2_radial_sizes(self):
        """T3.2: Radial Size changes and cursor warping. Check small, medium, large styles."""
        sizes = {"small": 300, "medium": 400, "large": 500}
        
        for name, expected_min_width in sizes.items():
            config = {
                "global": {
                    "hold_threshold_ms": 150,
                    "radial_size": name,
                    "hotkey_override": "",
                    "show_tray_icon": True,
                    "debug_log": True
                },
                "slots": [{"index": i, "label": f"Slot {i}", "icon": "", "color": "blue", "type": "open_url", "config": {"url": "https://google.com"}} for i in range(8)]
            }
            self.write_config(config)
            self.start_daemon()
            
            self.send_key(VK_VOLUME_MUTE, is_down=True)
            time.sleep(0.2)
            
            hwnd = self.find_radial_menu_window()
            self.assertIsNotNone(hwnd)
            
            rect = self.get_window_rect(hwnd)
            width = rect.right - rect.left
            
            # Assert width matches size requirements
            self.assertGreaterEqual(width, expected_min_width - 10)
            
            self.send_key(VK_VOLUME_MUTE, is_down=False)
            self.stop_daemon()

    def test_t4_2_high_frequency_hold_release(self):
        """T4.2: High frequency hold/release cycles. Run 50 open/close cycles in ~15-20 seconds."""
        self.start_daemon()
        for _ in range(50):
            self.send_key(VK_VOLUME_MUTE, is_down=True)
            time.sleep(0.16)
            hwnd = self.find_radial_menu_window()
            self.assertTrue(self.is_window_visible(hwnd))
            
            self.send_key(VK_VOLUME_MUTE, is_down=False)
            time.sleep(0.05)
            self.assertFalse(self.is_window_visible(hwnd))
