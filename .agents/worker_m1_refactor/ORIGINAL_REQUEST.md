## 2026-06-12T15:48:52Z
You are the Worker for Milestone 1 (Scaffold & Config) Refactoring of KnobLaunch.
Your working directory is `c:\Users\carla\Desktop\AHK\Arvie Knob Macro\.agents\worker_m1_refactor`.

Your task is to refactor the Milestone 1 codebase to resolve the following integration, robustness, and compliance issues identified by the reviewers and challengers:

1. **Window Class Name Alignment**:
   In `src/main.cpp`, change the registered helper window class name from `"KnobLaunchTrayHelper"` to `"KnobLaunchDaemon"`. The window class name MUST be exactly `"KnobLaunchDaemon"` for E2E tests to find it.

2. **Command ID Alignment**:
   In `src/main.cpp` (and `src/tray_icon.h` if applicable), change the reload and exit menu command IDs to `40003` (representing reload) and `40004` (representing exit). In other words:
   - `#define ID_TRAY_RELOAD 40003`
   - `#define ID_TRAY_EXIT 40004`
   Update the menu creation and the `WM_COMMAND` switch block accordingly.

3. **ConfigStore Type Safety Robustness**:
   - In `src/config_store.cpp` (inside `ConfigStore::ValidateAndRepair` or `ConfigStore::Load`), add a check: if the parsed JSON `j` is not a JSON object (for example, if it is a JSON array `[]` or a primitive type), reset it immediately to a clean object: `j = nlohmann::json::object();`. This prevents type errors like `nlohmann::detail::type_error` when calling `.contains("global")`.
   - In `ConfigStore::Load()`, check if a leftover temp file (`config.json.tmp`) exists and clean it up (delete it) to avoid leftover files on unclean shutdown.

4. **CMake Custom Command**:
   In `CMakeLists.txt`, add a post-build custom command to copy the compiled binary (`knoblaunch.exe`) from the output directory to the workspace root directory (`${CMAKE_SOURCE_DIR}/knoblaunch.exe`). This ensures that the Python test runner can locate the executable at the root level of the workspace.

5. **Python E2E Test Mismatch**:
   In `tests/test_cases/test_macro.py`, add `import json` at the top of the file to resolve any missing import.

MANDATORY INTEGRITY WARNING:
> DO NOT CHEAT. All implementations must be genuine. DO NOT
> hardcode test results, create dummy/facade implementations, or
> circumvent the intended task. A Forensic Auditor will independently
> verify your work. Integrity violations WILL be detected and your
> work WILL be rejected.

When done:
1. Re-run compile and verification tests (`tests\compile_tests.bat` and `bin\config_store_tests.exe`) to ensure all C++ unit tests pass.
2. Run python config tests (`python tests/test_runner.py`) and verify that configuration tests (sanity, config loader, reload, save on exit) pass successfully.
3. Write your handoff report to `c:\Users\carla\Desktop\AHK\Arvie Knob Macro\.agents\worker_m1_refactor\handoff.md` with build logs and test results.
