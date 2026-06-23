# Handoff Report - Explorer 3

## 1. Observation
*   **Window attributes in `src/radial_menu.cpp` (lines 70-73)**:
    ```cpp
    SetLayeredWindowAttributes(hWnd, 0, 220, LWA_ALPHA);
    ShowWindow(hWnd, SW_SHOWNOACTIVATE);
    ```
*   **`WM_PAINT` handling in `src/radial_menu.cpp` (lines 8-18)**:
    ```cpp
    case WM_PAINT: {
        PAINTSTRUCT ps;
        HDC hdc = BeginPaint(hWnd, &ps);
        RECT rect;
        GetClientRect(hWnd, &rect);
        // Paint a simple solid background
        HBRUSH hBrush = CreateSolidBrush(RGB(50, 50, 50));
        FillRect(hdc, &rect, hBrush);
        DeleteObject(hBrush);
        EndPaint(hWnd, &ps);
        break;
    }
    ```
*   **Macro stubs in `src/macro_runner.cpp`**:
    ```cpp
    bool RunProgram(const std::string& path, const std::string& args) {
        (void)path;
        (void)args;
        return true;
    }
    ```
*   **Test Case configuration for angles and boundaries in `tests/test_cases/test_gui.py`**:
    *   Cancel zone boundary: `dist >= 60.0` is expected to trigger (line 234), and smaller distance is cancelled (line 162).
    *   Sectors center formula (lines 23-27):
        ```python
        angle_deg = sector_idx * 45.0
        angle_rad = math.radians(angle_deg)
        x = int(center_x + radius * math.sin(angle_rad))
        y = int(center_y - radius * math.cos(angle_rad))
        ```
    *   Subprocess clean up on exit: `test_t4_5_full_cleanup_on_exit` (line 483 in `test_macro.py`) checks that spawned processes like `ping.exe` are terminated when the daemon exits.
    *   Error logging checks: `test_t1_f4_5_ahk_script_macro_error_logging` (line 215 in `test_macro.py`) asserts that `"bad_script.ahk"` and `"exit code"` or `"error"` are in `daemon.log`.

---

## 2. Logic Chain
1. **Window rendering violates R1**: `SetLayeredWindowAttributes` cannot achieve per-pixel alpha transparency and conflicts with `UpdateLayeredWindow`. The solid gray rectangle fill in `WM_PAINT` results in a solid window rather than a transparent circle.
2. **Hover highlighting violates R3**: The window proc doesn't capture mouse movements or perform angle calculations. Since standard Windows message loops do not receive mouse messages over transparent layered areas, a high-frequency timer (e.g. 16ms) calling `GetCursorPos` is required to accurately track the hover state and trigger redraws.
3. **Macro execution fails**: The macro runner functions (`RunProgram`, `OpenURL`, `RunAHKScript`) are stubs and do not execute processes or log messages, causing all macro test cases to fail.
4. **Coordinate translation is necessary**: GDI+ defines 0° as 3 o'clock, whereas the test suite defines 0° as 12 o'clock. We must map the angle via `gdi_deg = test_deg - 90` to render the slices in the correct positions.
5. **Subprocess leaks violate acceptance criteria**: The test suite launches child processes through macros and expects them to die on daemon exit. A Windows Job Object (`JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE`) is required to bind macro processes to the daemon lifecycle.

---

## 3. Caveats
*   Tests were run in a headless CLI environment, where `GUI_AVAILABLE` is set to `False` due to `ACCESS_DENIED` on `SetCursorPos` and `SendInput`. Consequently, interactive GUI and macro tests are skipped in this headless sandbox, but they will execute and must pass in an interactive Windows desktop environment.

---

## 4. Conclusion
*   To resolve Milestone 3:
    1.  Implement `UpdateLayeredWindow` inside `src/radial_menu.cpp` using a 32-bit PARGB DIB section and GDI+.
    2.  Add a `WM_TIMER` to track the cursor, calculate angle and distance, update the hovered sector, and redraw on change.
    3.  Draw slices as outer-to-inner arcs using `GraphicsPath` with the correct angle offset, leaving the 60px cancel zone completely transparent.
    4.  Implement `RunProgram`, `OpenURL`, and `RunAHKScript` in `src/macro_runner.cpp` with proper subprocess handling (Windows Job Objects), relative path resolution (to the configuration directory), and error logging.

---

## 5. Verification Method
*   Run the test runner to verify compilation and baseline execution:
    `python tests/test_runner.py`
*   Compile and run the diagnostic UI to inspect the GDI+ circular menu:
    *   Build command:
        `cl.exe /EHsc /std:c++17 tests/diagnostic_ui.cpp src/radial_menu.cpp src/config_store.cpp /Iinclude /Isrc /link user32.lib gdi32.lib gdiplus.lib shell32.lib shlwapi.lib /out:bin/diagnostic_ui.exe`
    *   Run command: `bin\diagnostic_ui.exe`
*   Inspect the generated `tests/daemon.log` to verify correct log output format.
