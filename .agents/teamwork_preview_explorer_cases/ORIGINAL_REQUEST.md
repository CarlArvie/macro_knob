## 2026-06-12T11:56:14Z

You are a teamwork_preview_explorer subagent named explorer_cases.
Your workspace directory is c:\Users\carla\Desktop\AHK\Arvie Knob Macro.
Your working directory (where you write metadata and handoff.md) is c:\Users\carla\Desktop\AHK\Arvie Knob Macro\.agents\teamwork_preview_explorer_cases.
Your mission is to design the complete set of 45-50 E2E test cases across Tiers 1-4 for the KnobLaunch project (Milestone T2).
Specifically:
1. Examine `TEST_INFRA.md` for the planned test case list.
2. Structure the test cases into 4 logical test suite files under `tests/test_cases/`:
   - `test_hotkey.py` (all hotkey trigger, hold durations, override, toggle, and tap fallback tests)
   - `test_gui.py` (all radial menu GUI styles, cursor warping, sector highlights, center cancel zone, topmost checks)
   - `test_config.py` (all default creation, custom loading, dynamic reload, malformed json recovery, missing settings/slots, reload tray menu events)
   - `test_macro.py` (all program launch, URL opening, AHK subprocess invocation, process cleanup on exit, invalid paths/scripts, overlapping execution)
3. For every single test case, describe the exact step-by-step logic (e.g., config changes, keyboard/mouse events to send, window/process state checks, file validations, and teardown assertions).
4. Outline how tests will deal with missing executables (e.g., how to skip or assert clean failures when knoblaunch.exe is not yet built) and headless session limitations (e.g., SetCursorPos failure checks).
Write your findings and comprehensive design to handoff.md in your working directory.
