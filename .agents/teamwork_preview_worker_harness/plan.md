# Plan: Milestone T1 Implementation

This plan outlines the steps to implement the test runner and the base testing framework in Python.

## Step 1: Create Directories and Init Files
- Ensure `tests` and `tests/test_cases` directories exist.
- Create empty `tests/__init__.py` and `tests/test_cases/__init__.py`.

## Step 2: Implement Test Runner
- Implement `tests/test_runner.py` using `unittest`'s `TestLoader` to automatically discover and run all tests under `tests/test_cases/` matching `test_*.py`.
- Ensure it exits with a non-zero exit code on failure.

## Step 3: Implement Base Test Case Class
- Implement `tests/test_cases/test_base.py`.
- Define all required ctypes structures: `INPUT`, `KEYBDINPUT`, `MOUSEINPUT`, `HARDWAREINPUT`, `INPUT_UNION`, `RECT`, `POINT`.
- Define standard Win32 constants (`VK_F13`, `VK_VOLUME_MUTE`, `INPUT_KEYBOARD`, `KEYEVENTF_KEYUP`, `KEYEVENTF_EXTENDEDKEY`, `GWL_EXSTYLE`, `WS_EX_TOPMOST`, `WS_EX_LAYERED`).
- Declare Win32 API functions via ctypes, specifying `argtypes` and `restype` for:
  - `SendInput`
  - `MapVirtualKeyW`
  - `FindWindowW`
  - `IsWindowVisible`
  - `GetWindowRect`
  - `GetCursorPos`
  - `SetCursorPos`
  - `GetWindowLongW` / `GetWindowLongPtrW` (with correct 32/64-bit architecture logic)
- Write helpers:
  - Configuration: `write_config`, `write_default_config`.
  - Daemon lifecycle: `start_daemon`, `stop_daemon`, `force_cleanup`.
  - Input simulation: `send_key`, `press_and_hold_key`, `set_cursor_position`, `get_cursor_position`.
  - Window inspection: `find_radial_menu_window`, `is_window_visible`, `get_window_rect`, `get_window_extended_style`.

## Step 4: Perform Syntax and Import Sanity Checks
- Run python compilation command on the files:
  - `python -m py_compile tests/test_runner.py`
  - `python -m py_compile tests/test_cases/test_base.py`
- Run a simple test execution or test discovery run to verify no import or execution errors exist.

## Step 5: Document and Finalize Handoff
- Update BRIEFING.md and progress.md.
- Create handoff.md.
