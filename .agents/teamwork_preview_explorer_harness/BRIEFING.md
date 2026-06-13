# BRIEFING — 2026-06-12T11:53:43Z

## Mission
Explore and design the E2E testing harness and mocking strategy for the KnobLaunch project (Milestone T1).

## 🔒 My Identity
- Archetype: teamwork_preview_explorer
- Roles: explorer_harness
- Working directory: c:\Users\carla\Desktop\AHK\Arvie Knob Macro\..agents\teamwork_preview_explorer_harness
- Original parent: 7089ff27-7749-43a4-a86c-8dabc5ba56b9
- Milestone: T1

## 🔒 Key Constraints
- Read-only investigation — do NOT implement
- Explore ctypes SendInput for key simulation, Win32 window query, mouse control, daemon lifecycle, and config backup/restoration.
- Formulate a clear design for tests/test_runner.py.

## Current Parent
- Conversation ID: 7089ff27-7749-43a4-a86c-8dabc5ba56b9
- Updated: 2026-06-12T11:54:30Z

## Investigation State
- **Explored paths**:
  - Investigated ctypes structures required for `SendInput` on Windows 64-bit and verified sizes using interactive python check.
  - Investigated Win32 APIs: `FindWindowW`, `IsWindowVisible`, `GetWindowRect`, `GetWindowLongPtrW` (styles), `GetCursorPos`, `SetCursorPos`.
  - Investigated process lifecycle management using `subprocess` and `taskkill` for daemon cleanup.
  - Investigated safe config backup/restoration strategy using file copy operations.
- **Key findings**:
  - Native `INPUT` size is 40 bytes, `KEYBDINPUT` is 24 bytes, and `MOUSEINPUT` is 32 bytes on Windows 64-bit.
  - We can dynamically retrieve virtual key scan codes using `MapVirtualKeyW` and provide a fallback.
  - We must kill both `knoblaunch.exe` and `AutoHotkey64.exe` using `taskkill /F` to avoid leaky tests.
- **Unexplored areas**: None. All requested investigation items are complete.

## Key Decisions Made
- Use standard Python `unittest` framework for running tests and structuring cases.
- Avoid external Python packages (like PyAutoGUI or pynput) to keep tests portable and zero-dependency.
- Implement a base class `KnobLaunchTestBase` containing all ctypes definitions and Win32 helpers to minimize duplicate code in test cases.

## Artifact Index
- c:\Users\carla\Desktop\AHK\Arvie Knob Macro\.agents\teamwork_preview_explorer_harness\handoff.md — Design findings and recommendations
