import unittest
import os
import time
import json
import shutil
import ctypes
from test_cases.test_base import KnobLaunchTestBase, User32, VK_VOLUME_MUTE

WORKSPACE_DIR = r"c:\Users\carla\Desktop\AHK\Arvie Knob Macro"
DAEMON_EXE = os.path.join(WORKSPACE_DIR, "knoblaunch.exe")
if not os.path.exists(DAEMON_EXE):
    debug_path = os.path.join(WORKSPACE_DIR, "build", "Debug", "knoblaunch.exe")
    if os.path.exists(debug_path):
        DAEMON_EXE = debug_path

DAEMON_EXISTS = os.path.exists(DAEMON_EXE)

WM_COMMAND = 0x0111
ID_TRAY_RELOAD = 40003
ID_TRAY_EXIT = 40004

@unittest.skipIf(not DAEMON_EXISTS, "knoblaunch.exe not found. Build the project first.")
class TestConfig(KnobLaunchTestBase):

    def setUp(self):
        # We override setUp to ensure we start tests in different states
        super().setUp()
        self.clean_temp_files()

    def tearDown(self):
        super().tearDown()
        self.clean_temp_files()

    def clean_temp_files(self):
        for path in [
            os.path.join(self.WORKSPACE_DIR, "tests\\slot_2_new.txt"),
            os.path.join(self.WORKSPACE_DIR, "tests\\slot_2_old.txt"),
            os.path.join(self.WORKSPACE_DIR, "tests\\slot_2_recovered.txt")
        ]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass

    def test_t1_f3_1_generate_default_config(self):
        """T1.F3.1: Generate Default Config. Delete config.json, verify daemon creates default."""
        if os.path.exists(self.CONFIG_PATH):
            os.remove(self.CONFIG_PATH)
            
        self.start_daemon()
        time.sleep(0.5)
        
        self.assertTrue(os.path.exists(self.CONFIG_PATH), "Default config.json was not generated.")
        
        with open(self.CONFIG_PATH) as f:
            config = json.load(f)
            
        self.assertIn("global", config)
        self.assertIn("slots", config)
        self.assertEqual(config["global"]["hold_threshold_ms"], 150)
        self.assertEqual(config["global"]["radial_size"], "medium")
        self.assertEqual(len(config["slots"]), 8)

    def test_t1_f3_2_custom_config_load(self):
        """T1.F3.2: Custom Config Load. Verify custom settings are loaded and respected on start."""
        config = {
            "global": {
                "hold_threshold_ms": 400,
                "radial_size": "large",
                "hotkey_override": "",
                "show_tray_icon": True,
                "debug_log": True
            },
            "slots": [{"index": i, "label": f"Slot {i}", "icon": "", "color": "blue", "type": "open_url", "config": {"url": "https://google.com"}} for i in range(8)]
        }
        self.write_config(config)
        self.start_daemon()
        
        # Hold key for 300ms (should NOT open menu since threshold is 400)
        self.send_key(VK_VOLUME_MUTE, is_down=True)
        time.sleep(0.3)
        hwnd = self.find_radial_menu_window()
        self.assertFalse(self.is_window_visible(hwnd))
        
        # Hold key for another 150ms (total 450ms, should open)
        time.sleep(0.15)
        hwnd = self.find_radial_menu_window()
        self.assertTrue(self.is_window_visible(hwnd))
        self.send_key(VK_VOLUME_MUTE, is_down=False)

    def test_t1_f3_3_config_auto_reload(self):
        """T1.F3.3: Config Auto-Reload on Edit. Modify config while running, verify update."""
        self.start_daemon()
        
        # Change threshold from 150ms to 500ms
        config = {
            "global": {
                "hold_threshold_ms": 500,
                "radial_size": "medium",
                "hotkey_override": "",
                "show_tray_icon": True,
                "debug_log": True
            },
            "slots": [{"index": i, "label": f"Slot {i}", "icon": "", "color": "blue", "type": "open_url", "config": {"url": "https://google.com"}} for i in range(8)]
        }
        self.write_config(config)
        time.sleep(0.8) # Wait for file watcher
        
        # Try holding for 300ms (should not trigger now)
        self.send_key(VK_VOLUME_MUTE, is_down=True)
        time.sleep(0.3)
        hwnd = self.find_radial_menu_window()
        self.assertFalse(self.is_window_visible(hwnd))
        
        self.send_key(VK_VOLUME_MUTE, is_down=False)

    def test_t1_f3_4_tray_menu_reload(self):
        """T1.F3.4: Tray Icon Menu Reload. Send WM_COMMAND for reload, verify config is re-read."""
        self.start_daemon()
        
        # Change threshold in config file
        config = {
            "global": {
                "hold_threshold_ms": 600,
                "radial_size": "medium",
                "hotkey_override": "",
                "show_tray_icon": True,
                "debug_log": True
            },
            "slots": [{"index": i, "label": f"Slot {i}", "icon": "", "color": "blue", "type": "open_url", "config": {"url": "https://google.com"}} for i in range(8)]
        }
        self.write_config(config)
        
        # Trigger reload from tray
        daemon_hwnd = User32.FindWindowW("KnobLaunchDaemon", None)
        if daemon_hwnd:
            User32.SendMessageW(daemon_hwnd, WM_COMMAND, ID_TRAY_RELOAD, 0)
        time.sleep(0.2)
        
        # Test if new threshold is respected
        self.send_key(VK_VOLUME_MUTE, is_down=True)
        time.sleep(0.4)
        hwnd = self.find_radial_menu_window()
        self.assertFalse(self.is_window_visible(hwnd))
        
        self.send_key(VK_VOLUME_MUTE, is_down=False)

    def test_t1_f3_5_config_save_on_exit(self):
        """T1.F3.5: Config Save on Exit. Exit daemon, check if config integrity is preserved."""
        self.start_daemon()
        time.sleep(0.2)
        
        daemon_hwnd = User32.FindWindowW("KnobLaunchDaemon", None)
        if daemon_hwnd:
            User32.SendMessageW(daemon_hwnd, WM_COMMAND, ID_TRAY_EXIT, 0)
            
        time.sleep(1.0)
        # Verify process exited
        self.assertIsNotNone(self.daemon_process.poll())
        
        # Check config still valid JSON
        with open(self.CONFIG_PATH) as f:
            config = json.load(f)
        self.assertIn("global", config)

    def test_t2_f3_1_missing_config_file(self):
        """T2.F3.1: Missing Config File. Delete config directory, verify daemon recreates directory & config."""
        config_dir = os.path.dirname(self.CONFIG_PATH)
        if os.path.exists(config_dir):
            shutil.rmtree(config_dir)
            
        self.start_daemon()
        time.sleep(0.5)
        
        self.assertTrue(os.path.exists(self.CONFIG_PATH))

    def test_t2_f3_2_malformed_config(self):
        """T2.F3.2: Malformed config.json. Write corrupt JSON, verify fallback to default."""
        with open(self.CONFIG_PATH, "w") as f:
            f.write("{ corrupt json: [ ")
            
        self.start_daemon()
        
        # Daemon should start and use default threshold (150ms)
        self.send_key(VK_VOLUME_MUTE, is_down=True)
        time.sleep(0.2)
        hwnd = self.find_radial_menu_window()
        self.assertTrue(self.is_window_visible(hwnd))
        self.send_key(VK_VOLUME_MUTE, is_down=False)

    def test_t2_f3_3_config_missing_slots(self):
        """T2.F3.3: Config with missing slots. Write config with 4 slots, verify undefined slots disabled."""
        config = {
            "global": {
                "hold_threshold_ms": 150,
                "radial_size": "medium",
                "hotkey_override": "",
                "show_tray_icon": True,
                "debug_log": True
            },
            "slots": [{"index": i, "label": f"Slot {i}", "icon": "", "color": "blue", "type": "open_url", "config": {"url": "https://google.com"}} for i in range(4)]
        }
        self.write_config(config)
        self.start_daemon()
        
        # Hold and verify daemon doesn't crash
        self.send_key(VK_VOLUME_MUTE, is_down=True)
        time.sleep(0.2)
        hwnd = self.find_radial_menu_window()
        self.assertTrue(self.is_window_visible(hwnd))
        self.send_key(VK_VOLUME_MUTE, is_down=False)

    def test_t2_f3_4_config_invalid_slot_types(self):
        """T2.F3.4: Config with invalid slot types. Verify invalid types are handled gracefully."""
        config = {
            "global": {
                "hold_threshold_ms": 150,
                "radial_size": "medium",
                "hotkey_override": "",
                "show_tray_icon": True,
                "debug_log": True
            },
            "slots": [
                {"index": 0, "label": "Slot 0", "icon": "", "color": "blue", "type": "invalid_type_name", "config": {}},
                *([{"index": i, "label": f"Slot {i}", "icon": "", "color": "blue", "type": "open_url", "config": {"url": "https://google.com"}} for i in range(1, 8)])
            ]
        }
        self.write_config(config)
        self.start_daemon()
        
        # Trigger slot 0, verify no crash
        self.send_key(VK_VOLUME_MUTE, is_down=True)
        time.sleep(0.2)
        # Move to Sector 0 and release
        hwnd = self.find_radial_menu_window()
        rect = self.get_window_rect(hwnd)
        center_x = (rect.left + rect.right) // 2
        center_y = (rect.top + rect.bottom) // 2
        
        # Move up (Sector 0)
        User32.SetCursorPos(center_x, center_y - 80)
        self.send_key(VK_VOLUME_MUTE, is_down=False)
        
        time.sleep(0.2)
        # Verify daemon is still running
        self.assertIsNone(self.daemon_process.poll())

    def test_t2_f3_5_extremely_long_labels(self):
        """T2.F3.5: Extremely long labels. Verify GDI+ doesn't crash on very long labels."""
        long_label = "X" * 100
        config = {
            "global": {
                "hold_threshold_ms": 150,
                "radial_size": "medium",
                "hotkey_override": "",
                "show_tray_icon": True,
                "debug_log": True
            },
            "slots": [
                {"index": 0, "label": long_label, "icon": "", "color": "blue", "type": "open_url", "config": {"url": "https://google.com"}},
                *([{"index": i, "label": f"Slot {i}", "icon": "", "color": "blue", "type": "open_url", "config": {"url": "https://google.com"}} for i in range(1, 8)])
            ]
        }
        self.write_config(config)
        self.start_daemon()
        
        self.send_key(VK_VOLUME_MUTE, is_down=True)
        time.sleep(0.2)
        hwnd = self.find_radial_menu_window()
        self.assertTrue(self.is_window_visible(hwnd))
        self.send_key(VK_VOLUME_MUTE, is_down=False)

    def test_t3_3_auto_reload_while_menu_open(self):
        """T3.3: Config Auto-Reload while Menu is Open. Modify config while menu is visible. Verify updated action."""
        # Initial config: Slot 2 writes slot_2_old.txt
        old_marker = os.path.join(self.WORKSPACE_DIR, "tests\\slot_2_old.txt")
        new_marker = os.path.join(self.WORKSPACE_DIR, "tests\\slot_2_new.txt")
        
        config = {
            "global": {
                "hold_threshold_ms": 150,
                "radial_size": "medium",
                "hotkey_override": "",
                "show_tray_icon": True,
                "debug_log": True
            },
            "slots": [
                {"index": 2, "label": "Slot 2", "icon": "", "color": "blue", "type": "run_program", "config": {"path": "C:\\Windows\\System32\\cmd.exe", "args": f"/c echo fired > \"{old_marker}\""}},
                *([{"index": i, "label": f"Slot {i}", "icon": "", "color": "blue", "type": "open_url", "config": {"url": "https://google.com"}} for i in range(8) if i != 2])
            ]
        }
        self.write_config(config)
        self.start_daemon()
        
        # Open menu
        self.send_key(VK_VOLUME_MUTE, is_down=True)
        time.sleep(0.2)
        
        # Modify config to point to slot_2_new.txt
        config["slots"][2]["config"]["args"] = f"/c echo fired > \"{new_marker}\""
        self.write_config(config)
        time.sleep(0.8) # Allow reload
        
        # Warp to Sector 2 and release
        hwnd = self.find_radial_menu_window()
        rect = self.get_window_rect(hwnd)
        center_x = (rect.left + rect.right) // 2
        center_y = (rect.top + rect.bottom) // 2
        User32.SetCursorPos(center_x + 100, center_y) # Sector 2 (Right)
        
        self.send_key(VK_VOLUME_MUTE, is_down=False)
        time.sleep(0.5)
        
        self.assertTrue(os.path.exists(new_marker), "Updated config action was not executed.")
        self.assertFalse(os.path.exists(old_marker), "Stale config action was executed.")

    def test_t4_4_invalid_config_recovery(self):
        """T4.4: Invalid config recovery workflow. Write invalid -> verify default -> replace valid -> verify custom."""
        recovery_marker = os.path.join(self.WORKSPACE_DIR, "tests\\slot_2_recovered.txt")
        
        # 1. Write malformed JSON
        with open(self.CONFIG_PATH, "w") as f:
            f.write("{ invalid json: ")
            
        self.start_daemon()
        
        # 2. Verify it runs using default threshold (150ms)
        self.send_key(VK_VOLUME_MUTE, is_down=True)
        time.sleep(0.2)
        hwnd = self.find_radial_menu_window()
        self.assertTrue(self.is_window_visible(hwnd))
        self.send_key(VK_VOLUME_MUTE, is_down=False)
        time.sleep(0.2)
        
        # 3. Overwrite with valid config pointing to recovery file and 500ms threshold
        config = {
            "global": {
                "hold_threshold_ms": 500,
                "radial_size": "medium",
                "hotkey_override": "",
                "show_tray_icon": True,
                "debug_log": True
            },
            "slots": [
                {"index": 2, "label": "Slot 2", "icon": "", "color": "blue", "type": "run_program", "config": {"path": "C:\\Windows\\System32\\cmd.exe", "args": f"/c echo fired > \"{recovery_marker}\""}},
                *([{"index": i, "label": f"Slot {i}", "icon": "", "color": "blue", "type": "open_url", "config": {"url": "https://google.com"}} for i in range(8) if i != 2])
            ]
        }
        self.write_config(config)
        time.sleep(0.8) # Wait reload
        
        # 4. Verify new 500ms threshold is loaded (holding for 300ms does NOT open menu)
        self.send_key(VK_VOLUME_MUTE, is_down=True)
        time.sleep(0.3)
        hwnd = self.find_radial_menu_window()
        self.assertFalse(self.is_window_visible(hwnd))
        
        # 5. Hold up to 550ms, move to Sector 2, release, verify recovery file written
        time.sleep(0.25)
        hwnd = self.find_radial_menu_window()
        self.assertTrue(self.is_window_visible(hwnd))
        
        rect = self.get_window_rect(hwnd)
        center_x = (rect.left + rect.right) // 2
        center_y = (rect.top + rect.bottom) // 2
        User32.SetCursorPos(center_x + 100, center_y) # Sector 2 (Right)
        
        self.send_key(VK_VOLUME_MUTE, is_down=False)
        time.sleep(0.5)
        
        self.assertTrue(os.path.exists(recovery_marker))
