## 2026-06-12T11:53:36Z
You are a teamwork_preview_explorer subagent named explorer_harness.
Your workspace directory is c:\Users\carla\Desktop\AHK\Arvie Knob Macro.
Your working directory (where you write metadata and handoff.md) is c:\Users\carla\Desktop\AHK\Arvie Knob Macro\.agents\teamwork_preview_explorer_harness.
Your mission is to explore and design the E2E testing harness and mocking strategy for the KnobLaunch project (Milestone T1).
Investigate and document:
1. How to simulate keyboard events (specifically holding F13 or Volume Mute) using Python ctypes SendInput.
2. How to query Win32 window states (checking if window class "KnobLaunchRadialMenu" exists and is visible, fetching window position).
3. How to control mouse cursor position (GetCursorPos, SetCursorPos).
4. How to manage daemon lifecycle (starting knoblaunch.exe, verifying it's running, stopping it, cleaning up child processes).
5. How to handle config backup and restoration safely.
Provide a clear, detailed step-by-step strategy for the Worker to implement tests/test_runner.py, including ctypes wrappers, helper methods, and test case structure. Write your findings to handoff.md in your working directory.
