# Scope: E2E Testing Track

## Architecture
The E2E Test Suite interacts with the KnobLaunch system as a black box:
1. **Config Modification**: Manipulates `config/config.json` to configure hotkeys, thresholds, and slot actions.
2. **Process Management**: Launches and terminates the daemon `knoblaunch.exe`.
3. **Input Simulation**: Uses Windows `SendInput` API (via python ctypes) to mock low-level keyboard (hotkey/volume knob) and mouse inputs.
4. **State Verification**: Uses Windows APIs (`FindWindow`, `GetWindowRect`, etc.) to verify window visibility, dimensions, and cursor position. Inspected processes and output files verify macro execution.

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| T1 | Milestone T1: Test Harness & Mocking | Implement `tests/test_runner.py` with ctypes Win32 wrappers, process controls, event simulation, window checks, and test runner infrastructure. | None | PLANNED |
| T2 | Milestone T2: Tier 1-4 Test Suite | Implement the test cases in `tests/test_cases/` for Tier 1 (Feature Coverage), Tier 2 (Boundary & Corner), Tier 3 (Cross-Feature), and Tier 4 (Workloads), and generate `TEST_READY.md`. | T1 | PLANNED |

## Interface Contracts
- **Tested Daemon**: `build/Release/knoblaunch.exe` (or `knoblaunch.exe` in the workspace/build folders).
- **Config Path**: `config/config.json` relative to daemon.
- **Window Class Name**: `KnobLaunchRadialMenu`.
- **AutoHotkey v2 Executable**: `bin/AutoHotkey64.exe`.
- **E2E Test Execution Entry Point**: `python tests/test_runner.py` (which runs all test files matching `test_*.py` in `tests/test_cases/`).
