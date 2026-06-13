# Handoff Report - Challenger 1 - Milestone 1 Verification

This report provides the empirical verification of correctness, robustness, and potential failure modes for Milestone 1 of KnobLaunch.

## 1. Observation

- **C++ Compilation**: Ran `cmd.exe /c "tests\compile_tests.bat"`. The compilation succeeded, producing `bin\config_store_tests.exe` and `bin\diagnostic.exe`.
  Verbatim success output:
  ```
  Compilation successful
  ```
- **C++ Unit Tests Execution**: Ran `cmd.exe /c "bin\config_store_tests.exe"`. All test cases (including default config generation, malformed JSON handling, top-level array handling, missing fields healing, invalid slots healing, thread safety, and tray icon window verification) passed.
  Verbatim success output:
  ```
  ALL TESTS PASSED SUCCESSFULLY!
  ```
- **Python E2E Configuration & Sanity Tests**: Ran Python sanity and configuration E2E tests:
  ```cmd
  cmd.exe /c "set PYTHONPATH=tests&& python -m unittest tests.test_cases.test_sanity tests.test_cases.test_config.TestConfig.test_t1_f3_1_generate_default_config tests.test_cases.test_config.TestConfig.test_t1_f3_3_config_auto_reload tests.test_cases.test_config.TestConfig.test_t1_f3_4_tray_menu_reload tests.test_cases.test_config.TestConfig.test_t1_f3_5_config_save_on_exit tests.test_cases.test_config.TestConfig.test_t2_f3_1_missing_config_file"
  ```
  Verbatim success output:
  ```
  .......
  ----------------------------------------------------------------------
  Ran 7 tests in 8.420s

  OK
  Skipping cursor assertion: SetCursorPos returned ACCESS_DENIED (likely running in a headless/non-interactive session)
  ```
- **Non-Object JSON Robustness Test**:
  - We verified healing of primitive inputs by writing `12345` to `config\config.json` and running `bin\knoblaunch.exe`. The daemon did not crash, remained running as PID 2064, and successfully healed the file into a default configuration object:
    ```json
    {
        "global": {
            "debug_log": false,
            "hold_threshold_ms": 150,
            "hotkey_override": "F13",
            "radial_size": "medium",
            "show_tray_icon": true
        },
        "slots": [ ... ]
    }
    ```
  - We verified healing of array inputs by writing `[]` to `config\config.json` and running `bin\knoblaunch.exe`. The daemon remained running as PID 14112 and successfully healed the file.
- **Window Class Name**: Verified in `src/main.cpp` line 104:
  ```cpp
  wcex.lpszClassName = L"KnobLaunchDaemon";
  ```
  And in `tests/config_store_tests.cpp` line 295, the unit test asserts:
  ```cpp
  TEST_ASSERT(std::wstring(className) == L"KnobLaunchDaemon");
  ```
- **Menu Commands**: Verified in `src/main.cpp` lines 13-14:
  ```cpp
  #define ID_TRAY_RELOAD 40003
  #define ID_TRAY_EXIT 40004
  ```
  In `tests/config_store_tests.cpp` lines 300 and 307:
  ```cpp
  LRESULT res = SendMessageW(hwnd, WM_COMMAND, 40003, 0);
  ...
  SendMessageW(hwnd, WM_COMMAND, 40004, 0);
  ```

---

## 2. Logic Chain

1. **Robustness against Non-Object JSON**: If `config.json` contains a non-object (primitive or array), the C++ parser in `ConfigStore::Load()` reads it successfully into a JSON object `j` without throwing an exception. `ValidateAndSanitize(j)` checks if `!j.is_object()`. Because this is true, it overrides `j` to an empty JSON object `{}`, setting `modified = true`. The subsequent checks find that `"global"` and `"slots"` keys are missing and create them with default settings. Finally, the healed config is written back to the disk. We empirically verified this with `12345` and `[]` and observed that the daemon ran and generated the valid defaults without crashing.
2. **C++ Unit Tests Compliance**: The compiler command successfully resolves MSVC build tools and outputs `bin/config_store_tests.exe`. Executing the binary runs all 7 test suites, which finish successfully.
3. **E2E Test Execution**: Since the testing environment is a headless/non-interactive Windows session, any test verifying GUI window visibility or mouse movement via `SendInput`/`SetCursorPos` fails or skips. However, the E2E configuration and sanity tests do not check GUI window visibility and instead focus on JSON generation, auto-reload, tray-menu messages, and clean exit, all of which run successfully.
4. **Window Class and Commands**: The daemon source code successfully matches the class name `"KnobLaunchDaemon"` and menu commands `40003`/`40004`. The C++ unit tests verify this dynamically by locating the window, verifying its class name matches `"KnobLaunchDaemon"`, and successfully sending messages `40003` (reload) and `40004` (exit) which are processed synchronously.

---

## 3. Caveats

- **Headless Environment Restrictions**: Full Python E2E suite (`python tests/test_runner.py`) cannot pass completely in this environment because `WH_KEYBOARD_LL` hooks and interactive GUI input events (`SendInput`) are restricted by Windows in non-interactive sessions. Thus, only the non-GUI configuration and sanity tests (7 tests) pass.
- **Asynchronous Taskkill Race**: The E2E test suite uses `taskkill /F /IM knoblaunch.exe` to clean up the daemon. However, `taskkill` is asynchronous, which can lead to a race condition where the next test case tries to run the daemon before the previous class name is fully reclaimed, causing the daemon to exit with code 1 due to `RegisterClassEx` failure.

---

## 4. Adversarial Review (Challenge Report)

### Challenge Summary
**Overall risk assessment**: MEDIUM

### Challenges

#### [High] Challenge 1: Destructive Auto-Recovery on JSON Parse Error
- **Assumption challenged**: If the JSON is malformed, it is safe to regenerate the default configuration.
- **Attack scenario**: A user is editing `config.json` to customize their macro slots. They make a typo (e.g. missing a comma). On save, the file watcher triggers `ConfigStore::Load()`. The parser throws a parse exception. The exception handler in `ConfigStore::Load()` immediately calls `GenerateDefaultConfig()`, which **overwrites** the user's config file on disk with the defaults, permanently erasing the user's custom macros.
- **Blast radius**: High. Users will lose all their configuration settings upon any minor formatting error.
- **Mitigation**: When `ConfigStore::Load()` fails to parse due to malformed JSON, it should log the error and use the last successfully loaded configuration (or a memory fallback), but it should **never** overwrite the user's file on disk with defaults.

#### [Medium] Challenge 2: Asynchronous Process Termination Race in E2E Tests
- **Assumption challenged**: Killing the process with `taskkill /F` completes before the next test case starts.
- **Attack scenario**: During rapid sequential test execution, the OS takes several milliseconds to terminate the previous process. The next test starts `knoblaunch.exe` immediately. The registration of `KnobLaunchDaemon` window class fails, and the daemon exits with code 1.
- **Blast radius**: Medium. Unstable/flaky E2E test results in automated CI environments.
- **Mitigation**: Update `start_daemon` or `force_cleanup` in the Python test suite to wait until the process is fully dead (e.g., checking if the process exists or using `wait()`).

#### [Low] Challenge 3: Lack of GDI+ Startup Status Checking
- **Assumption challenged**: GDI+ initialization always succeeds.
- **Attack scenario**: In resource-constrained environments (e.g. low memory or missing graphics driver hooks), `GdiplusStartup` returns a failure status. The daemon ignores it and proceeds, leading to undefined behavior or crash when creating the radial menu GUI window.
- **Blast radius**: Low/Medium. Silent startup crashes.
- **Mitigation**: Assert or check the return status of `Gdiplus::GdiplusStartup`.

---

## 5. Verification Method

To independently verify these results, perform the following:

1. **Rebuild the Daemon**:
   Run `cmd.exe /c "build.bat"` to build the latest version of `knoblaunch.exe` from source.
2. **Compile and Run C++ Unit Tests**:
   Run `cmd.exe /c "tests\compile_tests.bat" && bin\config_store_tests.exe`. All tests should pass and print `ALL TESTS PASSED SUCCESSFULLY!`.
3. **Run E2E Config & Sanity Tests**:
   Run:
   ```cmd
   cmd.exe /c "set PYTHONPATH=tests&& python -m unittest tests.test_cases.test_sanity tests.test_cases.test_config.TestConfig.test_t1_f3_1_generate_default_config tests.test_cases.test_config.TestConfig.test_t1_f3_3_config_auto_reload tests.test_cases.test_config.TestConfig.test_t1_f3_4_tray_menu_reload tests.test_cases.test_config.TestConfig.test_t1_f3_5_config_save_on_exit tests.test_cases.test_config.TestConfig.test_t2_f3_1_missing_config_file"
   ```
   The result must be `OK` (7 tests passed).
4. **Manual Primitive/Array Healing Verification**:
   - Write `12345` to `config\config.json`.
   - Start the daemon: `start bin\knoblaunch.exe`.
   - Wait 1-2 seconds, then read `config\config.json`. It must be healed to the valid JSON structure.
   - Clean up by running `taskkill /F /IM knoblaunch.exe`.
