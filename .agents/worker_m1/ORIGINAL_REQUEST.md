## 2026-06-12T11:54:29Z

You are the Worker for Milestone 1 (Scaffold & Config) of KnobLaunch.
Your working directory is `c:\Users\carla\Desktop\AHK\Arvie Knob Macro\.agents\worker_m1`.

Your task is to implement the directories, CMake configuration, source files, and stubs for Milestone 1.

Milestone 1 Scope:
1. Directory Structure:
   Ensure `src`, `include`, `resources`, `bin`, and `config` directories are created.
2. CMakeLists.txt:
   Write a `CMakeLists.txt` at the workspace root (`c:\Users\carla\Desktop\AHK\Arvie Knob Macro\CMakeLists.txt`). It should target MSVC with C++17, enable Unicode, set warnings as errors, target binary output to `bin/knoblaunch.exe`, and link user32, shell32, gdi32, gdiplus, and shlwapi.
   To obtain the `nlohmann/json.hpp` header, write a CMake download step or fetch it, e.g.:
   ```cmake
   if(NOT EXISTS ${CMAKE_SOURCE_DIR}/include/nlohmann/json.hpp)
       message(STATUS "Downloading nlohmann/json.hpp...")
       file(DOWNLOAD 
           https://github.com/nlohmann/json/releases/download/v3.11.3/json.hpp 
           ${CMAKE_SOURCE_DIR}/include/nlohmann/json.hpp
           SHOW_PROGRESS
       )
   endif()
   ```
3. ConfigStore (`src/config_store.h` & `src/config_store.cpp`):
   - Implement thread-safe read/write configuration store. Use `std::shared_mutex` for concurrent read/write protection.
   - Use `nlohmann/json` to load and save `config.json`.
   - On Load: If the file is missing or invalid, generate default configurations (with 8 slots, slot 0 is Notepad, slot 1 is GitHub), write it to disk, and load it.
   - Self-Healing/Validation: Ensure the loaded config has a valid `global` section and exactly 8 slots (indices 0 to 7) matching the schema in PROJECT.md. Auto-pad missing slots or fix invalid values, then write the sanitized version back to disk.
   - Atomic Save: Write the updated config to `config.json.tmp` first, then swap it atomically with `config.json` using Win32 API `MoveFileExW` with flags `MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH`.
   - Executable Relative Path: Resolve the configuration path dynamically relative to the executable path (`GetModuleFileNameW`), checking both sibling/parent-sibling folders (e.g. `../config/config.json` when binary is in `bin/`).
4. Main Entry Point (`src/main.cpp`):
   - Register a helper window class named `KnobLaunchTrayHelper`.
   - Create a hidden window to run a standard Win32 message loop and host the tray icon.
   - Setup tray icon via `Shell_NotifyIconW`.
   - Implement context menu on right-click (`WM_RBUTTONUP`) with "Open Config", "Reload Config", and "Exit".
   - "Open Config" must launch the system default JSON editor for `config.json` using `ShellExecuteW`.
   - "Reload Config" must re-read `config.json` via ConfigStore. Show a tray balloon notification if successful.
   - "Exit" must destroy the window, remove the tray icon, and terminate the process.
5. Header/Source Stubs:
   - Provide minimal compiling stubs in `src/` for:
     - `input_hook.h` / `input_hook.cpp`
     - `radial_menu.h` / `radial_menu.cpp` (register class `KnobLaunchRadialMenu` in main or stub)
     - `macro_runner.h` / `macro_runner.cpp`
