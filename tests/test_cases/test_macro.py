import unittest
import json
import os
import time
import ctypes
import subprocess
from test_cases.test_base import KnobLaunchTestBase, User32, VK_VOLUME_MUTE, GUI_AVAILABLE

WORKSPACE_DIR = r"c:\Users\carla\Desktop\AHK\Arvie Knob Macro"
DAEMON_EXE = os.path.join(WORKSPACE_DIR, "knoblaunch.exe")
if not os.path.exists(DAEMON_EXE):
    debug_path = os.path.join(WORKSPACE_DIR, "build", "Debug", "knoblaunch.exe")
    if os.path.exists(debug_path):
        DAEMON_EXE = debug_path

DAEMON_EXISTS = os.path.exists(DAEMON_EXE)

AHK_EXE = os.path.join(WORKSPACE_DIR, "bin", "AutoHotkey64.exe")
AHK_EXISTS = os.path.exists(AHK_EXE)

@unittest.skipIf(not DAEMON_EXISTS, "knoblaunch.exe not found. Build the project first.")
@unittest.skipIf(not GUI_AVAILABLE, "Interactive GUI session not available")
class TestMacro(KnobLaunchTestBase):

    def setUp(self):
        super().setUp()
        self.clean_markers()

    def tearDown(self):
        super().tearDown()
        self.clean_markers()

    def clean_markers(self):
        for path in [
            os.path.join(self.WORKSPACE_DIR, "tests\\macro_ran.txt"),
            os.path.join(self.WORKSPACE_DIR, "tests\\macro_ran2.txt"),
            os.path.join(self.WORKSPACE_DIR, "tests\\test_marker.txt")
        ]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass

    def trigger_sector_0(self):
        self.send_key(VK_VOLUME_MUTE, is_down=True)
        time.sleep(0.2)
        
        hwnd = self.find_radial_menu_window()
        self.assertIsNotNone(hwnd)
        rect = self.get_window_rect(hwnd)
        center_x = (rect.left + rect.right) // 2
        center_y = (rect.top + rect.bottom) // 2
        
        # Warp cursor to Sector 0 (top-center, e.g. angle 0, offset (0, -80))
        User32.SetCursorPos(center_x, center_y - 80)
        time.sleep(0.05)
        
        self.send_key(VK_VOLUME_MUTE, is_down=False)
        time.sleep(0.2)

    def test_t1_f4_1_run_program_basic(self):
        """T1.F4.1: Run Program Macro (Basic). Trigger slot configured with run_program. Verify process spawns."""
        # Check if notepad.exe is running already, kill it to start clean
        subprocess.run(["taskkill", "/F", "/IM", "notepad.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        config = {
            "global": {
                "hold_threshold_ms": 150,
                "radial_size": "medium",
                "hotkey_override": "",
                "show_tray_icon": True,
                "debug_log": True
            },
            "slots": [
                {"index": 0, "label": "Notepad", "icon": "", "color": "blue", "type": "run_program", "config": {"path": "C:\\Windows\\System32\\notepad.exe", "args": ""}},
                *([{"index": i, "label": f"Slot {i}", "icon": "", "color": "blue", "type": "open_url", "config": {"url": "https://google.com"}} for i in range(1, 8)])
            ]
        }
        self.write_config(config)
        self.start_daemon()
        
        self.trigger_sector_0()
        time.sleep(1.0)
        
        # Verify notepad is running using tasklist
        out = subprocess.check_output(["tasklist", "/FI", "IMAGENAME eq notepad.exe"], text=True)
        self.assertIn("notepad.exe", out, "notepad.exe was not spawned by the macro.")
        
        # Cleanup notepad
        subprocess.run(["taskkill", "/F", "/IM", "notepad.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def test_t1_f4_2_run_program_with_arguments(self):
        """T1.F4.2: Run Program with Arguments. Verify program macro executes with command-line arguments."""
        marker = os.path.join(self.WORKSPACE_DIR, "tests\\macro_ran.txt")
        config = {
            "global": {
                "hold_threshold_ms": 150,
                "radial_size": "medium",
                "hotkey_override": "",
                "show_tray_icon": True,
                "debug_log": True
            },
            "slots": [
                {"index": 0, "label": "Args Test", "icon": "", "color": "blue", "type": "run_program", "config": {"path": "C:\\Windows\\System32\\cmd.exe", "args": f"/c echo fired > \"{marker}\""}},
                *([{"index": i, "label": f"Slot {i}", "icon": "", "color": "blue", "type": "open_url", "config": {"url": "https://google.com"}} for i in range(1, 8)])
            ]
        }
        self.write_config(config)
        self.start_daemon()
        
        self.trigger_sector_0()
        time.sleep(0.5)
        
        self.assertTrue(os.path.exists(marker), "Program macro failed to execute with arguments.")

    def test_t1_f4_3_open_url_macro(self):
        """T1.F4.3: Open URL Macro (Default Browser). Trigger open_url and check for log verification."""
        config = {
            "global": {
                "hold_threshold_ms": 150,
                "radial_size": "medium",
                "hotkey_override": "",
                "show_tray_icon": True,
                "debug_log": True
            },
            "slots": [
                {"index": 0, "label": "URL Test", "icon": "", "color": "blue", "type": "open_url", "config": {"url": "https://example.com"}},
                *([{"index": i, "label": f"Slot {i}", "icon": "", "color": "blue", "type": "open_url", "config": {"url": "https://google.com"}} for i in range(1, 8)])
            ]
        }
        self.write_config(config)
        self.start_daemon()
        
        self.trigger_sector_0()
        
        # Read log and verify ShellExecute was triggered
        time.sleep(0.5)
        self.stop_daemon()
        
        log_path = os.path.join(self.WORKSPACE_DIR, "tests\\daemon.log")
        with open(log_path, "r") as f:
            log_content = f.read()
            
        self.assertIn("https://example.com", log_content, "ShellExecute for URL did not appear in daemon logs.")

    @unittest.skipIf(not AHK_EXISTS, "AutoHotkey64.exe not found.")
    def test_t1_f4_4_ahk_script_macro_basic(self):
        """T1.F4.4: AHK Script Macro (Basic). Trigger ahk_script, verify execution via AutoHotkey64.exe."""
        script_path = os.path.join(self.WORKSPACE_DIR, "tests\\test_script.ahk")
        marker_path = os.path.join(self.WORKSPACE_DIR, "tests\\test_marker.txt")
        
        with open(script_path, "w") as f:
            f.write(f'#Requires AutoHotkey v2.0\nFileAppend "ahk_success", "{marker_path.replace("\\", "\\\\")}"\n')
            
        config = {
            "global": {
                "hold_threshold_ms": 150,
                "radial_size": "medium",
                "hotkey_override": "",
                "show_tray_icon": True,
                "debug_log": True
            },
            "slots": [
                {"index": 0, "label": "AHK Test", "icon": "", "color": "blue", "type": "ahk_script", "config": {"script_file": "tests/test_script.ahk"}},
                *([{"index": i, "label": f"Slot {i}", "icon": "", "color": "blue", "type": "open_url", "config": {"url": "https://google.com"}} for i in range(1, 8)])
            ]
        }
        self.write_config(config)
        self.start_daemon()
        
        self.trigger_sector_0()
        time.sleep(1.0)
        
        self.assertTrue(os.path.exists(marker_path), "AHK script failed to write output marker file.")
        with open(marker_path) as f:
            self.assertEqual(f.read().strip(), "ahk_success")
            
        if os.path.exists(script_path):
            os.remove(script_path)

    @unittest.skipIf(not AHK_EXISTS, "AutoHotkey64.exe not found.")
    def test_t1_f4_5_ahk_script_macro_error_logging(self):
        """T1.F4.5: AHK Script Macro Error Logging. Trigger invalid syntax script, verify failure logs."""
        script_path = os.path.join(self.WORKSPACE_DIR, "tests\\bad_script.ahk")
        with open(script_path, "w") as f:
            f.write('#Requires AutoHotkey v2.0\nThis is invalid AHK syntax!\n')
            
        config = {
            "global": {
                "hold_threshold_ms": 150,
                "radial_size": "medium",
                "hotkey_override": "",
                "show_tray_icon": True,
                "debug_log": True
            },
            "slots": [
                {"index": 0, "label": "Bad AHK", "icon": "", "color": "blue", "type": "ahk_script", "config": {"script_file": "tests/bad_script.ahk"}},
                *([{"index": i, "label": f"Slot {i}", "icon": "", "color": "blue", "type": "open_url", "config": {"url": "https://google.com"}} for i in range(1, 8)])
            ]
        }
        self.write_config(config)
        self.start_daemon()
        
        self.trigger_sector_0()
        time.sleep(1.0)
        
        self.stop_daemon()
        
        # Verify daemon logs report the process exit error code or warning
        log_path = os.path.join(self.WORKSPACE_DIR, "tests\\daemon.log")
        with open(log_path, "r") as f:
            log_content = f.read()
            
        self.assertIn("bad_script.ahk", log_content)
        # Typically AHK exit code for syntax error is non-zero
        self.assertTrue("exit code" in log_content.lower() or "error" in log_content.lower())
        
        if os.path.exists(script_path):
            os.remove(script_path)

    def test_t2_f4_1_run_program_invalid_path(self):
        """T2.F4.1: Run Program with invalid path. Verify graceful failure and logs."""
        config = {
            "global": {
                "hold_threshold_ms": 150,
                "radial_size": "medium",
                "hotkey_override": "",
                "show_tray_icon": True,
                "debug_log": True
            },
            "slots": [
                {"index": 0, "label": "Invalid Exe", "icon": "", "color": "blue", "type": "run_program", "config": {"path": "C:\\InvalidFolder\\non_existent_app.exe", "args": ""}},
                *([{"index": i, "label": f"Slot {i}", "icon": "", "color": "blue", "type": "open_url", "config": {"url": "https://google.com"}} for i in range(1, 8)])
            ]
        }
        self.write_config(config)
        self.start_daemon()
        
        self.trigger_sector_0()
        time.sleep(0.5)
        
        # Daemon must still be running (no crash)
        self.assertIsNone(self.daemon_process.poll())
        
        self.stop_daemon()
        
        log_path = os.path.join(self.WORKSPACE_DIR, "tests\\daemon.log")
        with open(log_path, "r") as f:
            log_content = f.read()
        self.assertTrue("failed" in log_content.lower() or "error" in log_content.lower() or "not found" in log_content.lower())

    def test_t2_f4_2_open_url_malformed(self):
        """T2.F4.2: Open URL with malformed URL. Verify graceful error response."""
        config = {
            "global": {
                "hold_threshold_ms": 150,
                "radial_size": "medium",
                "hotkey_override": "",
                "show_tray_icon": True,
                "debug_log": True
            },
            "slots": [
                {"index": 0, "label": "Bad URL", "icon": "", "color": "blue", "type": "open_url", "config": {"url": "invalid_scheme_no_host"}},
                *([{"index": i, "label": f"Slot {i}", "icon": "", "color": "blue", "type": "open_url", "config": {"url": "https://google.com"}} for i in range(1, 8)])
            ]
        }
        self.write_config(config)
        self.start_daemon()
        
        self.trigger_sector_0()
        time.sleep(0.5)
        
        self.assertIsNone(self.daemon_process.poll())

    def test_t2_f4_3_ahk_script_missing_file(self):
        """T2.F4.3: AHK Script missing script file. Verify error logging."""
        config = {
            "global": {
                "hold_threshold_ms": 150,
                "radial_size": "medium",
                "hotkey_override": "",
                "show_tray_icon": True,
                "debug_log": True
            },
            "slots": [
                {"index": 0, "label": "Missing AHK", "icon": "", "color": "blue", "type": "ahk_script", "config": {"script_file": "tests/missing_file_random_123.ahk"}},
                *([{"index": i, "label": f"Slot {i}", "icon": "", "color": "blue", "type": "open_url", "config": {"url": "https://google.com"}} for i in range(1, 8)])
            ]
        }
        self.write_config(config)
        self.start_daemon()
        
        self.trigger_sector_0()
        time.sleep(0.5)
        self.stop_daemon()
        
        log_path = os.path.join(self.WORKSPACE_DIR, "tests\\daemon.log")
        with open(log_path, "r") as f:
            log_content = f.read()
        self.assertTrue("missing" in log_content.lower() or "not found" in log_content.lower() or "error" in log_content.lower())

    def test_t2_f4_4_run_program_admin_without_elevation(self):
        """T2.F4.4: Run Program run_as_admin without elevation. Verify fallback/handling."""
        config = {
            "global": {
                "hold_threshold_ms": 150,
                "radial_size": "medium",
                "hotkey_override": "",
                "show_tray_icon": True,
                "debug_log": True
            },
            "slots": [
                {"index": 0, "label": "Admin App", "icon": "", "color": "blue", "type": "run_program", "config": {"path": "C:\\Windows\\System32\\cmd.exe", "args": "/c exit", "run_as_admin": True}},
                *([{"index": i, "label": f"Slot {i}", "icon": "", "color": "blue", "type": "open_url", "config": {"url": "https://google.com"}} for i in range(1, 8)])
            ]
        }
        self.write_config(config)
        self.start_daemon()
        
        self.trigger_sector_0()
        time.sleep(0.5)
        
        # Verify daemon process is still running and did not block/crash
        self.assertIsNone(self.daemon_process.poll())

    def test_t2_f4_5_multiple_macro_execution_overlap(self):
        """T2.F4.5: Multiple macro execution overlap. Run two slow macros, check concurrency."""
        marker1 = os.path.join(self.WORKSPACE_DIR, "tests\\macro_ran.txt")
        marker2 = os.path.join(self.WORKSPACE_DIR, "tests\\macro_ran2.txt")
        
        config = {
            "global": {
                "hold_threshold_ms": 150,
                "radial_size": "medium",
                "hotkey_override": "",
                "show_tray_icon": True,
                "debug_log": True
            },
            "slots": [
                {"index": 0, "label": "Slow 1", "icon": "", "color": "blue", "type": "run_program", "config": {"path": "C:\\Windows\\System32\\cmd.exe", "args": f"/c ping 127.0.0.1 -n 3 > nul && echo fired > \"{marker1}\""}},
                {"index": 1, "label": "Slow 2", "icon": "", "color": "blue", "type": "run_program", "config": {"path": "C:\\Windows\\System32\\cmd.exe", "args": f"/c ping 127.0.0.1 -n 3 > nul && echo fired > \"{marker2}\""}},
                *([{"index": i, "label": f"Slot {i}", "icon": "", "color": "blue", "type": "open_url", "config": {"url": "https://google.com"}} for i in range(2, 8)])
            ]
        }
        self.write_config(config)
        self.start_daemon()
        
        # Trigger Slot 0
        self.send_key(VK_VOLUME_MUTE, is_down=True)
        time.sleep(0.2)
        hwnd = self.find_radial_menu_window()
        rect = self.get_window_rect(hwnd)
        center_x = (rect.left + rect.right) // 2
        center_y = (rect.top + rect.bottom) // 2
        User32.SetCursorPos(center_x, center_y - 80) # Slot 0 (Up)
        self.send_key(VK_VOLUME_MUTE, is_down=False)
        
        # Wait a short moment and trigger Slot 1
        time.sleep(0.1)
        self.send_key(VK_VOLUME_MUTE, is_down=True)
        time.sleep(0.2)
        hwnd = self.find_radial_menu_window()
        rect = self.get_window_rect(hwnd)
        center_x = (rect.left + rect.right) // 2
        center_y = (rect.top + rect.bottom) // 2
        
        # Slot 1 is up-right (approx angle 45 degrees)
        # x offset ~ 56px, y offset ~ -56px
        User32.SetCursorPos(center_x + 56, center_y - 56)
        self.send_key(VK_VOLUME_MUTE, is_down=False)
        
        # Check that they haven't finished immediately but run concurrently
        self.assertFalse(os.path.exists(marker1))
        self.assertFalse(os.path.exists(marker2))
        
        # Wait for ping to finish
        time.sleep(4.0)
        self.assertTrue(os.path.exists(marker1))
        self.assertTrue(os.path.exists(marker2))

    def test_t3_5_run_program_starts_another_macro(self):
        """T3.5: Run program macro starting another macro. Slot 0 changes config to alter Slot 1."""
        marker = os.path.join(self.WORKSPACE_DIR, "tests\\macro_ran.txt")
        new_config_data = {
            "global": {
                "hold_threshold_ms": 150,
                "radial_size": "medium",
                "hotkey_override": "",
                "show_tray_icon": True,
                "debug_log": True
            },
            "slots": [
                {"index": 0, "label": "Change Slot 1", "icon": "", "color": "blue", "type": "run_program", "config": {"path": "C:\\Windows\\System32\\cmd.exe", "args": ""}},
                {"index": 1, "label": "Slot 1 Updated", "icon": "", "color": "blue", "type": "run_program", "config": {"path": "C:\\Windows\\System32\\cmd.exe", "args": f"/c echo fired > \"{marker}\""}},
                *([{"index": i, "label": f"Slot {i}", "icon": "", "color": "blue", "type": "open_url", "config": {"url": "https://google.com"}} for i in range(2, 8)])
            ]
        }
        
        # Write config helper script
        script_path = os.path.join(self.WORKSPACE_DIR, "tests\\modify_config.bat")
        with open(script_path, "w") as f:
            f.write(f'@echo off\n')
            # Echo new JSON content to config.json
            f.write(f'echo {json.dumps(new_config_data)} > "{self.CONFIG_PATH}"\n')
            
        config = {
            "global": {
                "hold_threshold_ms": 150,
                "radial_size": "medium",
                "hotkey_override": "",
                "show_tray_icon": True,
                "debug_log": True
            },
            "slots": [
                {"index": 0, "label": "Run Script", "icon": "", "color": "blue", "type": "run_program", "config": {"path": "cmd.exe", "args": f"/c \"{script_path}\""}},
                {"index": 1, "label": "Slot 1 Old", "icon": "", "color": "blue", "type": "open_url", "config": {"url": "https://google.com"}},
                *([{"index": i, "label": f"Slot {i}", "icon": "", "color": "blue", "type": "open_url", "config": {"url": "https://google.com"}} for i in range(2, 8)])
            ]
        }
        self.write_config(config)
        self.start_daemon()
        
        # Trigger Slot 0 (runs script which overwrites config.json)
        self.trigger_sector_0()
        time.sleep(1.0) # wait for batch and file watcher reload
        
        # Trigger Slot 1 (which should now write the file)
        self.send_key(VK_VOLUME_MUTE, is_down=True)
        time.sleep(0.2)
        hwnd = self.find_radial_menu_window()
        rect = self.get_window_rect(hwnd)
        center_x = (rect.left + rect.right) // 2
        center_y = (rect.top + rect.bottom) // 2
        
        # Slot 1 coordinates (up-right)
        User32.SetCursorPos(center_x + 56, center_y - 56)
        self.send_key(VK_VOLUME_MUTE, is_down=False)
        time.sleep(0.5)
        
        self.assertTrue(os.path.exists(marker))
        
        if os.path.exists(script_path):
            os.remove(script_path)

    def test_t4_1_multi_slot_setup(self):
        """T4.1: Multi-slot setup execution workflow. Activate Program, then URL, then standard slot, verify stability."""
        config = {
            "global": {
                "hold_threshold_ms": 150,
                "radial_size": "medium",
                "hotkey_override": "",
                "show_tray_icon": True,
                "debug_log": True
            },
            "slots": [
                {"index": 0, "label": "Program Slot", "icon": "", "color": "blue", "type": "run_program", "config": {"path": "C:\\Windows\\System32\\cmd.exe", "args": "/c exit"}},
                {"index": 1, "label": "URL Slot", "icon": "", "color": "blue", "type": "open_url", "config": {"url": "https://example.com"}},
                *([{"index": i, "label": f"Slot {i}", "icon": "", "color": "blue", "type": "open_url", "config": {"url": "https://google.com"}} for i in range(2, 8)])
            ]
        }
        self.write_config(config)
        self.start_daemon()
        
        # Trigger 0
        self.trigger_sector_0()
        time.sleep(0.5)
        
        # Trigger 1
        self.send_key(VK_VOLUME_MUTE, is_down=True)
        time.sleep(0.2)
        hwnd = self.find_radial_menu_window()
        rect = self.get_window_rect(hwnd)
        center_x = (rect.left + rect.right) // 2
        center_y = (rect.top + rect.bottom) // 2
        User32.SetCursorPos(center_x + 56, center_y - 56) # Slot 1
        self.send_key(VK_VOLUME_MUTE, is_down=False)
        time.sleep(0.5)
        
        self.assertIsNone(self.daemon_process.poll())

    def test_t4_5_full_cleanup_on_exit(self):
        """T4.5: Full cleanup on exit. Verify that when daemon exits, spawned subprocesses are terminated."""
        # Spawn a slow ping subprocess via macro
        config = {
            "global": {
                "hold_threshold_ms": 150,
                "radial_size": "medium",
                "hotkey_override": "",
                "show_tray_icon": True,
                "debug_log": True
            },
            "slots": [
                {"index": 0, "label": "Slow Ping", "icon": "", "color": "blue", "type": "run_program", "config": {"path": "C:\\Windows\\System32\\ping.exe", "args": "127.0.0.1 -n 20"}},
                *([{"index": i, "label": f"Slot {i}", "icon": "", "color": "blue", "type": "open_url", "config": {"url": "https://google.com"}} for i in range(1, 8)])
            ]
        }
        self.write_config(config)
        self.start_daemon()
        
        # Trigger ping
        self.trigger_sector_0()
        time.sleep(0.5)
        
        # Check ping.exe is running
        out = subprocess.check_output(["tasklist", "/FI", "IMAGENAME eq ping.exe"], text=True)
        self.assertIn("ping.exe", out)
        
        # Close daemon via exit command
        daemon_hwnd = User32.FindWindowW("KnobLaunchDaemon", None)
        if daemon_hwnd:
            User32.SendMessageW(daemon_hwnd, 0x0111, 40004, 0)
        time.sleep(1.0)
        
        # Verify daemon is dead
        self.stop_daemon()
        
        # Verify ping.exe was terminated as part of process group cleanup or exit handling
        # Note: Standard Windows process groups or explicit job objects are used.
        out = subprocess.check_output(["tasklist", "/FI", "IMAGENAME eq ping.exe"], text=True)
        self.assertNotIn("ping.exe", out, "ping.exe subprocess was not cleaned up on daemon exit.")
