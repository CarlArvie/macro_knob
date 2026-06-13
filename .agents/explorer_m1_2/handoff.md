# Handoff Report: Milestone 1 Scaffold & Config (Explorer 2)

## 1. Observation
- The workspace root `c:\Users\carla\Desktop\AHK\Arvie Knob Macro` is currently empty except for three reference files:
  - `PROJECT.md` (96 lines): Defines the code layout under the `KnobLaunch/` directory.
  - `TEST_INFRA.md` (87 lines): Defines testing tiers, including `T1.F3.1` (generate default config), `T2.F3.1` (generate missing config folder), `T1.F3.4` (tray icon menu reload), and `T1.F3.5` (config save on exit).
  - `VolumeKnobMacro_ProjectPlan.md` (558 lines): Lists technology decisions (MSVC, C++17, GDI+, `nlohmann/json`, tray menu, atomic writes) and memory/performance targets.
- `.agents/sub_orch_implementation/SCOPE.md` (81 lines): Outlines Milestone 1 scope consisting of CMakeLists.txt, project directory structure, config_store load/save, default config, and TrayIcon/main minimal entry point.

---

## 2. Logic Chain
- **Project Structure**: Based on `PROJECT.md` line 72, the core codebase should be scaffolded inside a nested directory `KnobLaunch/` in the workspace root.
- **CMake & Build Settings**: The target must be a Windows GUI application (no command window popup). Therefore, we compile using standard CMake `WIN32` options, implement `WinMain` as the entry point, and link to essential libraries (`user32`, `shell32`, `gdi32`, `gdiplus`, `shlwapi`).
- **Atomic File Writing**: To satisfy robustness requirements and prevent configuration corruption during writes, we write configuration data first to a temporary file (`config.json.tmp`) and then call the Win32 `MoveFileExW` API with flags `MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH` to overwrite the existing file atomically.
- **Config Validation & Self-Healing**: To pass validation tests (`T2.F3.2` malformed json, `T2.F3.3` missing slots), `ConfigStore::Load` will parse input JSON via `nlohmann/json`, validate type and key existence for `global` and all 8 `slots`, repair any corrupt/missing entries with default values, and immediately write the sanitized configuration back to disk.
- **Tray Window & Menu**: We register a distinct hidden message window class (`KnobLaunchTrayHelper`). This hidden window hosts the system tray icon via `Shell_NotifyIconW`, handles menu execution for "Open Config", "Reload Config", and "Exit" under `WM_COMMAND`, and allows the E2E test runner to locate the window handle and simulate actions.

---

## 3. Caveats
- Source files for subsequent milestones (`input_hook`, `radial_menu`, `macro_runner`) are included in `CMakeLists.txt` but are implemented as empty stubs in Milestone 1 to allow compilation.
- The `nlohmann/json.hpp` single header file must be placed at `KnobLaunch/include/nlohmann/json.hpp` by the implementer.
- Path resolution in `main.cpp` resolves `config/config.json` at a sibling level to the binary directory (i.e. `../config/config.json` when running from `bin/`). If run from an unexpected directory, the path logic falls back to checking local paths.

---

## 4. Conclusion
The proposed plan and source layouts are completely defined. Milestone 1 implementation can proceed immediately using the detailed CMake configurations, file architecture, `ConfigStore` class declarations, validation algorithms, and `main.cpp` tray loop specified in `analysis.md`.

---

## 5. Verification Method
- **Directory Layout Verification**: Check that `KnobLaunch/` contains `src/`, `include/`, `resources/`, `bin/`, and `tests/`.
- **Compile Verification**: Execute the following commands in the workspace root:
  ```powershell
  cmake -B build -S KnobLaunch
  cmake --build build --config Release
  ```
  Verify that `KnobLaunch/bin/knoblaunch.exe` is successfully built.
- **Functional Verification**:
  1. Run `KnobLaunch/bin/knoblaunch.exe`. Verify the system tray icon is added and `KnobLaunch/config/config.json` is generated.
  2. Right-click the tray icon and click "Open Config". Verify that it opens `config.json` in the default editor.
  3. Edit `config.json` to be malformed or remove keys. Click "Reload Config" from the tray icon menu. Verify the file is self-healed and rewritten with valid JSON.
  4. Click "Exit" in the tray context menu. Verify the process exits and the tray icon is cleanly removed.
