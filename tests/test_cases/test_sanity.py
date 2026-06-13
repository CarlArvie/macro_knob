from test_cases.test_base import KnobLaunchTestBase, User32
import os
import json
import time
import ctypes

class TestSanity(KnobLaunchTestBase):
    def test_config_helpers(self):
        # Write custom config
        custom = {"global": {"hold_threshold_ms": 200}}
        self.write_config(custom)
        self.assertTrue(os.path.exists(self.CONFIG_PATH))
        with open(self.CONFIG_PATH) as f:
            data = json.load(f)
        self.assertEqual(data["global"]["hold_threshold_ms"], 200)

    def test_cursor_helpers(self):
        # Test get and set cursor position
        orig_x, orig_y = self.get_cursor_position()
        ret_set = User32.SetCursorPos(100, 100)
        if ret_set == 0:
            err = ctypes.windll.kernel32.GetLastError()
            if err == 5: # ERROR_ACCESS_DENIED
                print("Skipping cursor assertion: SetCursorPos returned ACCESS_DENIED (likely running in a headless/non-interactive session)")
                return
        
        time.sleep(0.1)
        new_x, new_y = self.get_cursor_position()
        self.assertEqual(new_x, 100)
        self.assertEqual(new_y, 100)
        # Restore cursor
        User32.SetCursorPos(orig_x, orig_y)
