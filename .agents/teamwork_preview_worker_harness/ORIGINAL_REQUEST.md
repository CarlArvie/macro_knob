## 2026-06-12T11:54:40Z

You are a teamwork_preview_worker subagent named worker_harness.
Your workspace directory is c:\Users\carla\Desktop\AHK\Arvie Knob Macro.
Your working directory (where you write metadata and handoff.md) is c:\Users\carla\Desktop\AHK\Arvie Knob Macro\.agents\teamwork_preview_worker_harness.
Your mission is to implement the test runner and base testing framework (Milestone T1) in python.
Specifically, you must:
1. Create `tests/__init__.py` and `tests/test_cases/__init__.py`.
2. Write the test runner script `tests/test_runner.py` based on the design in `c:\Users\carla\Desktop\AHK\Arvie Knob Macro\.agents\teamwork_preview_explorer_harness\handoff.md`.
3. Write the base test case class `tests/test_cases/test_base.py` containing:
   - ctypes structures for Win32 API interactions (`INPUT`, `KEYBDINPUT`, `MOUSEINPUT`, `RECT`, `POINT`).
   - Win32 constant definitions.
   - ctypes function declarations with `argtypes` and `restype` specified (SendInput, MapVirtualKeyW, FindWindowW, IsWindowVisible, GetWindowRect, GetCursorPos, SetCursorPos, GetWindowLong/GetWindowLongPtrW).
   - Configuration management helpers (`write_config`, `write_default_config`).
   - Daemon lifecycle management helpers (`start_daemon`, `stop_daemon`, `force_cleanup` using subprocess).
   - Input simulation helpers (`send_key`, `press_and_hold_key`, `set_cursor_position`, `get_cursor_position`).
   - Window inspection helpers (`find_radial_menu_window`, `is_window_visible`, `get_window_rect`, `get_window_extended_style`).
4. Perform a sanity run of the python scripts to verify there are no syntax or import errors. You can invoke python with compilation checks (`python -m py_compile tests/test_runner.py` etc.).

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.
