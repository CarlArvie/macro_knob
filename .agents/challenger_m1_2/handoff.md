# Handoff Report — Milestone 1 Challenger 2

## 1. Observation
- **Direct C++ Verification**:
  - We compiled and ran the test suite in `tests/config_store_tests.cpp` using the project batch file `tests/compile_tests.bat`:
    ```
    cl.exe /EHsc /std:c++17 tests/config_store_tests.cpp src/config_store.cpp /Iinclude /Isrc /link user32.lib shell32.lib shlwapi.lib /out:bin/config_store_tests.exe
    ```
  - Running `bin/config_store_tests.exe` outputs:
    ```
    Resolved configuration path: C:\Users\carla\Desktop\AHK\Arvie Knob Macro\bin\..\config\config.json
    Running TestDefaultConfigGeneration...
    TestDefaultConfigGeneration passed.
    Running TestSelfHealingMalformed...
    TestSelfHealingMalformed passed.
    Running TestSelfHealingTopLevelArray...
    Exception occurred during testing!
    ```
  - We observed that when `config.json` contains a valid JSON array `[]` (a non-object type) instead of a JSON object, `ConfigStore::Load()` crashes with an uncaught `nlohmann::detail::type_error` exception.
- **Tray Icon Window Messaging**:
  - In `src/main.cpp`, the tray helper window class is registered as `L"KnobLaunchTrayHelper"` and created with window title `L"KnobLaunchTrayHelperWindow"` (lines 104 and 117):
    ```cpp
    wcex.lpszClassName = L"KnobLaunchTrayHelper";
    ...
    HWND hWnd = CreateWindowExW(
        0,
        L"KnobLaunchTrayHelper",
        L"KnobLaunchTrayHelperWindow",
        ...
    );
    ```
  - The tray helper window proc `WndProc` handles commands (lines 55 and 62):
    ```cpp
    case ID_RELOAD_CONFIG: // 1002
        ...
    case ID_EXIT:          // 1003
        DestroyWindow(hWnd);
    ```
  - We verified via `SendMessageW(hwnd, WM_COMMAND, 1002, 0)` that the running daemon receives and handles the reload config command correctly.
- **Python Integration Test Conformance**:
  - Running the python integration suite `python tests/test_runner.py` reports failures in the GUI, hotkeys, and macro execution because these features are implemented as empty stubs in Milestone 1.
  - We observed that `test_t1_f3_5_config_save_on_exit` in `tests/test_cases/test_config.py` attempts to find the daemon window using the class name `"KnobLaunchDaemon"`:
    ```python
    daemon_hwnd = User32.FindWindowW("KnobLaunchDaemon", None)
    ```
    This class name is mismatching, as the actual class name in the implementation is `"KnobLaunchTrayHelper"`.
  - We observed that `tests/test_cases/test_macro.py` line 286 throws:
    ```
    NameError: name 'json' is not defined
    ```
    due to a missing `import json` statement in that test script.

## 2. Logic Chain
1. When `ConfigStore::Load()` parses the JSON file, it wraps only the parsing step `ifs >> j` in a try-catch block.
2. If the JSON is valid but parses to a non-object value (e.g. `[]` or `"string"`), no exception is thrown during parsing, and the code proceeds to `ValidateAndSanitize(j)`.
3. In `ConfigStore::ValidateAndSanitize`, it checks `!j.contains("global")`. Because `j` is not a JSON object, the library method `.contains()` throws a `type_error` exception.
4. Since `ValidateAndSanitize` is called outside the try-catch block, the exception escapes `Load()`, causing a program crash (exit code 1).
5. The window class mismatch (`KnobLaunchDaemon` vs `KnobLaunchTrayHelper`) causes the python E2E exit test to fail because the Python test suite is unable to locate the tray helper window.

## 3. Caveats
- The keyboard hook and radial menu window rendering are not yet verified because they are stubs in Milestone 1.

## 4. Conclusion
Milestone 1 is functional in default generation, slots count, tray messaging, and thread safety. However, the configuration parser is not robust against non-object valid JSON inputs (like arrays `[]`), which crashes the program. Additionally, the Python integration tests have window class mismatches and missing imports.

## 5. Verification Method
1. Recompile and run the C++ unit tests:
   ```cmd
   tests\compile_tests.bat
   bin\config_store_tests.exe
   ```
2. Verify that it prints `Exception occurred during testing!` when loading `[]` in `config.json`.
3. Verify that changing `config/config.json` to `{}` or deleting it allows the binary to start and self-heal successfully.
