# Handoff Report: Milestone 1 (Scaffold & Config) — Explorer 1

## 1. Observation
- The workspace root `c:\Users\carla\Desktop\AHK\Arvie Knob Macro` is currently empty of any source code files. It only contains:
  - `PROJECT.md`
  - `VolumeKnobMacro_ProjectPlan.md`
  - `TEST_INFRA.md`
  - `.agents/` (metadata directory)
- **PROJECT.md** specifies the Code Layout (lines 69-95):
  ```
  KnobLaunch/
  ├── CMakeLists.txt                 # CMake configuration
  ├── src/
  │   ├── main.cpp                   # Application entry point & tray menu
  │   ├── config_store.h             # Configuration header
  │   ├── config_store.cpp           # JSON load, save, default generation
  │   ├── input_hook.h               # Low-level keyboard hook header
  │   ├── input_hook.cpp             # Hook management, hold threshold logic
  │   ├── radial_menu.h              # Radial Menu overlay window header
  │   ├── radial_menu.cpp            # GDI+ drawing, window proc, hover detection
  │   ├── macro_runner.h             # Macro executor header
  │   └── macro_runner.cpp           # Spawning programs, URLs, AutoHotkey scripts
  ├── include/
  │   └── nlohmann/
  │       └── json.hpp               # nlohmann/json header-only library
  ├── resources/
  │   └── icons/                     # Pre-packaged icons for slices (default.png, etc.)
  ├── bin/
  │   └── AutoHotkey64.exe           # AutoHotkey v2 executable bundled for scripts
  ├── tests/
  │   ├── test_runner.py             # Main E2E test runner script (using PyAutoGUI or Win32 API)
  │   └── test_cases/                # Detailed test definitions
  └── README.md
  ```
- **SCOPE.md** for the Implementation Track specifies the scope of Milestone 1:
  - "CMakeLists.txt, project directory structure, config_store load/save, default config, TrayIcon minimal stub"
  - Configuration schema matches the `config.json` contract (global settings + 8 slots).
- **TEST_INFRA.md** specifies test cases (lines 34-38):
  - **T1.F3.1: Generate Default Config**: Delete `config.json`, run daemon, verify `config.json` is recreated with default values.
  - **T1.F3.2: Custom Config Load**: Write custom config, launch daemon, verify settings are respected.
  - **T1.F3.3: Config Auto-Reload on Edit**: Edit `config.json` while running. Verify the daemon reloads settings without restart. (Note: In Milestone 1, tray icon reload trigger is sufficient; file system watcher will be implemented in subsequent steps if needed, but manual tray trigger works).
  - **T1.F3.4: Tray Icon Menu Reload**: Trigger reload config from tray menu, verify config is re-read.
  - **T1.F3.5: Config Save on Exit**: Trigger daemon exit, check if configuration integrity is preserved.

---

## 2. Logic Chain
1. **Empty Workspace (Observation 1)** -> Since there is no directory structure or code, the implementation agent must start by scaffolding the folders (`src`, `include`, `resources`, `bin`, `tests`) and generating stub source files so that the CMake project builds correctly from day one.
2. **Milestone 1 Scope (Observation 2)** -> We need to build `knoblaunch.exe` using MSVC. Therefore, we propose a standard `CMakeLists.txt` using C++17 (or C++20), defining Unicode support and treating warnings as errors (/WX) for high-quality production code.
3. **ConfigStore Requirements (Observation 2 & 3)** -> The JSON library is header-only (`nlohmann/json`). The config module must support load/save, auto-generation of default values, thread safety, and atomic writing to prevent corruption.
   - *Atomic Write*: We propose writing to `config.json.tmp` and using `std::filesystem::rename` to swap.
   - *Directory Protection*: If the parent directory of `config.json` does not exist, it should be created recursively using `std::filesystem::create_directories`.
   - *Padding Slots*: To avoid out-of-bounds errors in subsequent modules, the slots vector must be padded to exactly 8 elements (indices 0 to 7), filling missing slots with default empty settings.
4. **Path Resolution** -> To run the daemon during development (from build/Release folders) and deployment (from the bin folder), the config path should be resolved relative to the executable using `GetModuleFileNameW`. We propose searching both sibling and parent-sibling structures.
5. **System Tray & Menu (Observation 2 & 4)** -> We need a basic Win32 application entry point. A hidden utility window using a standard message loop handles system tray events. We map the right-click event (`WM_RBUTTONUP`) to show a Win32 popup menu containing "Open Config", "Reload Config", and "Exit".
6. **Open Config Action** -> Since we do not have a Settings GUI in Milestone 1, "Open Config" should open `config.json` using the system's default text editor via `ShellExecuteW`.

---

## 3. Caveats
- **AHK Subprocesses**: Milestone 1 does not execute AHK scripts, but we layout the stubs for `macro_runner.h/cpp` to ensure the project builds successfully.
- **nlohmann/json**: The header file `json.hpp` is not present. The implementer must copy or download it into `include/nlohmann/json.hpp`.
- **Keyboard Hook**: The low-level keyboard hook (`input_hook.h/cpp`) is stubbed and does not capture input in Milestone 1.

---

## 4. Conclusion

### A. Proposed Directory Layout Scaffolding
Create the following directories and empty/stub files at the project root:
```
KnobLaunch/
├── CMakeLists.txt
├── src/
│   ├── main.cpp
│   ├── config_store.h
│   ├── config_store.cpp
│   ├── input_hook.h (stub)
│   ├── input_hook.cpp (stub)
│   ├── radial_menu.h (stub)
│   ├── radial_menu.cpp (stub)
│   ├── macro_runner.h (stub)
│   └── macro_runner.cpp (stub)
├── include/
│   └── nlohmann/
│       └── json.hpp (Vendor copy of nlohmann/json header)
├── resources/
│   └── icons/
└── bin/
```

### B. Proposed CMakeLists.txt
This CMake configuration is tailored for MSVC, enforces C++17, sets up Unicode, and includes strict warning configurations.
```cmake
cmake_minimum_required(VERSION 3.20)
project(KnobLaunch LANGUAGES CXX)

# Require C++17 standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Enable Unicode definitions and clean windows headers
add_compile_definitions(UNICODE _UNICODE WIN32_LEAN_AND_MEAN NOMINMAX)

# MSVC Compiler Warning Configurations
if(MSVC)
    target_compile_options(KnobLaunch PRIVATE /W4 /WX) # Warning Level 4, Warnings as Errors
endif()

# Header Include Directories
include_directories(include src)

# Project Sources
set(SOURCES
    src/main.cpp
    src/config_store.h
    src/config_store.cpp
    src/input_hook.h
    src/input_hook.cpp
    src/radial_menu.h
    src/radial_menu.cpp
    src/macro_runner.h
    src/macro_runner.cpp
)

# Output Executable (Builds as windowless Win32 executable)
add_executable(knoblaunch WIN32 ${SOURCES})

# Link Required Windows SDK libraries
target_link_libraries(knoblaunch PRIVATE
    user32
    shell32
    gdi32
    gdiplus
)
```

### C. Proposed Header Declarations

#### 1. `src/config_store.h`
```cpp
#pragma once
#include <string>
#include <vector>
#include <mutex>
#include <nlohmann/json.hpp>

namespace KnobLaunch {

struct SlotConfig {
    int index = 0;
    std::string label;
    std::string icon;
    std::string color;
    std::string type; // "run_program", "open_url", "ahk_script"
    nlohmann::json config; // Dynamic details object depending on type
};

struct GlobalSettings {
    int hold_threshold_ms = 150;
    std::string radial_size = "medium";
    std::string hotkey_override = "F13";
    bool show_tray_icon = true;
    bool debug_log = false;
};

struct AppConfig {
    GlobalSettings global;
    std::vector<SlotConfig> slots;
};

// Serialization support using nlohmann/json macro-free integration
void to_json(nlohmann::json& j, const GlobalSettings& g);
void from_json(const nlohmann::json& j, GlobalSettings& g);

void to_json(nlohmann::json& j, const SlotConfig& s);
void from_json(const nlohmann::json& j, SlotConfig& s);

void to_json(nlohmann::json& j, const AppConfig& a);
void from_json(const nlohmann::json& j, AppConfig& a);

class ConfigStore {
public:
    static ConfigStore& GetInstance();

    // Prevent copying
    ConfigStore(const ConfigStore&) = delete;
    ConfigStore& operator=(const ConfigStore&) = delete;

    // Load configuration from config.json.
    // Generates a default config and writes it if file is missing/corrupt.
    bool Load();

    // Save current configuration atomic-style.
    bool Save();

    // Thread-safe config accessors
    AppConfig GetConfig();
    void SetConfig(const AppConfig& config);

    // Get the fully resolved filesystem path to config.json
    std::string GetConfigFilePath() const;

private:
    ConfigStore();
    ~ConfigStore() = default;

    AppConfig CreateDefaultConfig() const;
    std::string ResolveConfigFilePath() const;

    mutable std::mutex m_mutex;
    AppConfig m_config;
};

} // namespace KnobLaunch
```

#### 2. `src/tray_icon.h`
```cpp
#pragma once
#include <windows.h>
#include <shellapi.h>
#include <string>

namespace KnobLaunch {

// Custom tray message mapping
#define WM_TRAYICON (WM_USER + 1)

// Popup Menu Action IDs
#define ID_TRAY_OPEN_CONFIG    2001
#define ID_TRAY_RELOAD_CONFIG  2002
#define ID_TRAY_EXIT           2003

class TrayIcon {
public:
    TrayIcon(HWND hwnd);
    ~TrayIcon();

    // Registers the tray icon with the system shell
    bool Create(HINSTANCE hInst);

    // Displays a balloon message tip
    void ShowNotification(const std::wstring& title, const std::wstring& message);

    // Pops up right-click menu at cursor coordinates
    void ShowContextMenu();

    // Removes the tray icon
    void Remove();

private:
    HWND m_hwnd = nullptr;
    NOTIFYICONDATAW m_nid = {};
    bool m_created = false;
};

} // namespace KnobLaunch
```

### D. Implementation Details for main.cpp and config_store.cpp

1. **ConfigStore Load/Save**:
   - `Load()`: Retrieve the path via `ResolveConfigFilePath()`. Open using `std::ifstream`. If it fails or `nlohmann::json::parse` throws, catch the exception, generate the default config using `CreateDefaultConfig()`, call `Save()`, and load it.
   - **Post-Processing (Padding)**: Always verify that `slots` contains exactly 8 entries corresponding to indices 0–7. Pad any missing slot config using a default template.
   - `Save()`: Serialize the `AppConfig` struct to `nlohmann::json`. Write it to `<resolved_path>.tmp`. Close the file. Call `std::filesystem::rename` to atomically overwrite the real `config.json`.
   - `ResolveConfigFilePath()`: Use `GetModuleFileNameW(NULL, ...)` to locate the running executable. Let `exe_dir` be the parent path. Check:
     - `exe_dir / "config" / "config.json"`
     - `exe_dir.parent_path() / "config" / "config.json"`
     - If neither exists, use `exe_dir.parent_path() / "config" / "config.json"` if `exe_dir` matches standard build/bin folders, otherwise sibling folder.

2. **wWinMain Application Entry Point**:
   - Call `CoInitializeEx(NULL, COINIT_APARTMENTTHREADED)` to initialize COM (useful for future shell operations).
   - Register a dummy window class (e.g. name `KnobLaunchDaemon`).
   - Create a hidden window (`CreateWindowExW(0, L"KnobLaunchDaemon", L"KnobLaunch", ...)`).
   - Instantiate `TrayIcon` passing the `HWND`. Call `Create(hInstance)`.
   - Start the main loop:
     ```cpp
     MSG msg;
     while (GetMessageW(&msg, NULL, 0, 0)) {
         TranslateMessage(&msg);
         DispatchMessageW(&msg);
     }
     ```
   - On exit, call `CoUninitialize()`.

3. **WndProc Handlers**:
   - `WM_TRAYICON`: 
     - If `lParam == WM_RBUTTONUP`, call `g_TrayIcon->ShowContextMenu()`.
     - If `lParam == WM_LBUTTONDBLCLK`, trigger `SendMessage(hwnd, WM_COMMAND, ID_TRAY_OPEN_CONFIG, 0)`.
   - `WM_COMMAND`:
     - `ID_TRAY_OPEN_CONFIG`: Call `ConfigStore::GetInstance().GetConfigFilePath()`. Launch it via `ShellExecuteW(NULL, L"open", config_path_wide.c_str(), NULL, NULL, SW_SHOWNORMAL)`.
     - `ID_TRAY_RELOAD_CONFIG`: Invoke `ConfigStore::GetInstance().Load()`. If successful, call `ShowNotification(L"KnobLaunch", L"Configuration reloaded successfully.")`. Otherwise, notify failure.
     - `ID_TRAY_EXIT`: Call `DestroyWindow(hwnd)`.
   - `WM_DESTROY`: Call `g_TrayIcon->Remove()` and `PostQuitMessage(0)`.

---

## 5. Verification Method

To verify the Milestone 1 implementation:
1. **Compilation Check**:
   Configure and build the application:
   ```powershell
   cmake -B build -G "Visual Studio 17 2022" -A x64
   cmake --build build --config Release
   ```
   Check that `build/Release/knoblaunch.exe` builds with zero errors and zero warnings.
2. **Scaffolding Validation**:
   - Move or delete any existing `config/config.json`.
   - Double-click `knoblaunch.exe`.
   - Inspect that `config/config.json` is automatically generated with the default settings (containing notepad and google presets, padded to exactly 8 slots).
3. **Tray Menu Verification**:
   - Find the system tray icon (represented by the application icon).
   - Right-click the icon: verify "Open Config", "Reload Config", and "Exit" menus appear.
   - Click "Open Config": verify it opens `config.json` in standard Notepad or the registered json editor.
   - Modify the file (e.g., change `hold_threshold_ms` to `200`) and save.
   - Right-click the tray icon and click "Reload Config": verify a balloon notification appears confirming the reload, and verify that the internal config is updated.
   - Click "Exit": verify the process terminates cleanly and the icon disappears from the system tray.
