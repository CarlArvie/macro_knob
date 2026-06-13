# Milestone 1 Analysis & Handoff Report: Scaffold & Config

## 1. Observation

Based on direct investigation of the workspace and project documents:
* **Workspace Directory State**: The workspace is empty except for the three documentation files in the root and the `.agents/` metadata directory, as verified by running a search tool:
  ```
  Found 3 results:
  - PROJECT.md
  - TEST_INFRA.md
  - VolumeKnobMacro_ProjectPlan.md
  ```
* **Code Layout Contract** (from `.agents/sub_orch_implementation/SCOPE.md` lines 56-80 and `PROJECT.md` lines 69-80):
  * Root path contains: `CMakeLists.txt`, `README.md`.
  * Core C++ sources: `src/main.cpp`, `src/config_store.h`, `src/config_store.cpp`, etc.
  * Third-party headers: `include/nlohmann/json.hpp` (header-only).
  * Resources: `resources/icons/`.
  * Outputs: `bin/AutoHotkey64.exe` (bundled AHK runtime) and target output binary `bin/knoblaunch.exe`.
* **Config Schema Contract** (from `SCOPE.md` lines 33-49):
  * Config path: `config/config.json`.
  * `global` settings: `hold_threshold_ms` (int, default 150), `radial_size` (string, default "medium"), `hotkey_override` (string, default "F13" or empty), `show_tray_icon` (bool, default true), `debug_log` (bool, default false).
  * `slots`: Array of exactly 8 slots (indices 0 to 7) containing `index` (int), `label` (string), `icon` (string), `color` (string), `type` (string: "run_program", "open_url", "ahk_script"), and a `config` object containing type-specific parameters.
* **Win32 System Tray Contract** (from `SCOPE.md` lines 23-32 and `PROJECT.md` lines 74-75):
  * Main entry point `main.cpp` must run a system tray icon with a right-click context menu containing "Open Config", "Reload Config", and "Exit".

---

## 2. Logic Chain

1. **Codebase Scaffolding**: Since the workspace is empty, we must create a scaffolding directory layout matching the Code Layout contract. To facilitate smooth compilation and asset loading, the CMake output directory must be forced to `bin/` so `knoblaunch.exe` is placed next to `AutoHotkey64.exe` and has a fixed relative path to the `config/` and `resources/` folders.
2. **Path Resolution**: Win32 applications run with a working directory that depends on how they are launched (e.g. at startup or via command-line). Hardcoding relative paths like `config/config.json` will cause failures when launched from other directories. Thus, path resolution must be computed dynamically relative to the running executable's path via `GetModuleFileNameW`.
3. **Robust Config Loading**: Configuration loading must handle the following cases:
   - File doesn't exist -> Generate default and save.
   - File is invalid JSON -> Rename the corrupted file to `config.json.bad` to preserve user data, generate defaults, and save.
   - Keys are missing -> Gracefully merge with defaults using `nlohmann::json`'s `.value()` fallback helper.
4. **Thread-Safety**: Configuration may be read by the keyboard hook thread or the macro execution thread, and written/read by the Win32 tray thread. Therefore, `ConfigStore` must use a reader-writer lock (`std::shared_mutex`) to ensure thread-safe operations.
5. **Atomic Writing**: Writing configuration must be atomic. A crash during serialization could wipe out `config.json`. We will write to `config.json.tmp` first, then rename it using `std::filesystem::rename` (or `MoveFileExW` with `MOVEFILE_REPLACE_EXISTING`) to swap it atomically.
6. **Tray Interaction & Menu Loop**: In Windows, system tray icons require a window handle to receive mouse messages. We will create a utility message-only hidden window. In the window procedure, upon receiving right-click (`WM_RBUTTONUP`), we will retrieve the cursor position, call `SetForegroundWindow` (necessary to prevent menu ghosting), present the popup menu via `TrackPopupMenu`, and dispatch menu commands (`ID_TRAY_OPEN_CONFIG`, `ID_TRAY_RELOAD_CONFIG`, `ID_TRAY_EXIT`).

---

## 3. Caveats

* **nlohmann/json Header Acquisition**: Since we are in `CODE_ONLY` network mode, we cannot download `json.hpp` via network. The implementer must copy/obtain `json.hpp` locally or place it in the `include/nlohmann/` directory before building.
* **Unicode / Wide APIs**: The application should be configured to compile with Unicode character sets. Therefore, all Win32 API calls must explicitly use the `W` suffix (e.g., `Shell_NotifyIconW`, `CreateWindowExW`, `NOTIFYICONDATAW`) or rely on clean conversions between `std::wstring` and `std::string`.
* **GDI+ Dependency**: GDI+ is not heavily used in Milestone 1, but we should link standard libraries (like `Gdi32`, `User32`, `Shell32`, `Ole32`, `Shlwapi`) in `CMakeLists.txt` so subsequent UI milestones do not require modifying the build structure.

---

## 4. Conclusion

We propose the following concrete structures, folder layouts, and declarations for Milestone 1.

### 4.1 Folder Layout
Create the following directories under the workspace root:
* `src/` (main application and config store sources)
* `include/nlohmann/` (to host `json.hpp` header)
* `resources/icons/` (placeholders for slice icons)
* `config/` (contains generated `config.json`)
* `bin/` (contains target binary `knoblaunch.exe` and `AutoHotkey64.exe`)

### 4.2 CMakeLists.txt Configuration
Save the following as `CMakeLists.txt` in the workspace root:
```cmake
cmake_minimum_required(VERSION 3.20)
project(KnobLaunch VERSION 1.0.0 LANGUAGES CXX)

# Configure C++17 Standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Compiler Warnings & Unicode Configuration for MSVC
if(MSVC)
    add_compile_options(/W4 /WX /permissive- /utf-8 /DUNICODE /D_UNICODE)
endif()

# Source & Include directories
set(INCLUDE_DIRS "${CMAKE_CURRENT_SOURCE_DIR}/include")
set(SRC_DIR "${CMAKE_CURRENT_SOURCE_DIR}/src")

set(SOURCES
    "${SRC_DIR}/main.cpp"
    "${SRC_DIR}/config_store.h"
    "${SRC_DIR}/config_store.cpp"
)

set(HEADERS
    "${SRC_DIR}/config_store.h"
)

# Build as a Win32 GUI application (no console window)
add_executable(knoblaunch WIN32 ${SOURCES} ${HEADERS})

target_include_directories(knoblaunch PRIVATE 
    "${INCLUDE_DIRS}"
    "${SRC_DIR}"
)

# Standard Win32 system libraries
target_link_libraries(knoblaunch PRIVATE
    User32
    Shell32
    Ole32
    Shlwapi
)

# Force MSVC binary output directly into the bin/ directory
set_target_properties(knoblaunch PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/bin"
    RUNTIME_OUTPUT_DIRECTORY_DEBUG "${CMAKE_CURRENT_SOURCE_DIR}/bin"
    RUNTIME_OUTPUT_DIRECTORY_RELEASE "${CMAKE_CURRENT_SOURCE_DIR}/bin"
)
```

### 4.3 ConfigStore Header (`src/config_store.h`)
```cpp
#pragma once

#include <string>
#include <vector>
#include <shared_mutex>
#include <nlohmann/json.hpp>

namespace KnobLaunch {

struct SlotConfig {
    int index = 0;
    std::string label;
    std::string icon;
    std::string color;
    std::string type; // "run_program", "open_url", "ahk_script"
    nlohmann::json config_details; // Stores type-specific key-value pairs
};

struct GlobalConfig {
    int hold_threshold_ms = 150;
    std::string radial_size = "medium";
    std::string hotkey_override = "";
    bool show_tray_icon = true;
    bool debug_log = false;
};

struct AppConfig {
    GlobalConfig global;
    std::vector<SlotConfig> slots; // Exactly 8 elements (indices 0 to 7)
};

class ConfigStore {
public:
    ConfigStore() = default;
    ~ConfigStore() = default;

    // Delete copy/assignment operators for safety
    ConfigStore(const ConfigStore&) = delete;
    ConfigStore& operator=(const ConfigStore&) = delete;

    // Load configuration. If missing or invalid, fallback to defaults, backup, and save.
    bool Load(const std::wstring& path);

    // Save configuration atomically (write to .tmp first, then rename).
    bool Save(const std::wstring& path);

    // Thread-safe copy retrieval
    AppConfig GetConfig() const;

    // Thread-safe config update
    void SetConfig(const AppConfig& config);

    // Factory method for default configurations
    static AppConfig CreateDefaultConfig();

private:
    AppConfig m_config;
    mutable std::shared_mutex m_mutex;
};

// JSON conversion declarations
void to_json(nlohmann::json& j, const GlobalConfig& c);
void from_json(const nlohmann::json& j, GlobalConfig& c);

void to_json(nlohmann::json& j, const SlotConfig& c);
void from_json(const nlohmann::json& j, SlotConfig& c);

} // namespace KnobLaunch
```

### 4.4 ConfigStore Source (`src/config_store.cpp` structure)
The implementation should follow this logic:
```cpp
#include "config_store.h"
#include <fstream>
#include <filesystem>

namespace KnobLaunch {

void to_json(nlohmann::json& j, const GlobalConfig& c) {
    j = nlohmann::json{
        {"hold_threshold_ms", c.hold_threshold_ms},
        {"radial_size", c.radial_size},
        {"hotkey_override", c.hotkey_override},
        {"show_tray_icon", c.show_tray_icon},
        {"debug_log", c.debug_log}
    };
}

void from_json(const nlohmann::json& j, GlobalConfig& c) {
    c.hold_threshold_ms = j.value("hold_threshold_ms", 150);
    c.radial_size = j.value("radial_size", "medium");
    c.hotkey_override = j.value("hotkey_override", "");
    c.show_tray_icon = j.value("show_tray_icon", true);
    c.debug_log = j.value("debug_log", false);
}

void to_json(nlohmann::json& j, const SlotConfig& c) {
    j = nlohmann::json{
        {"index", c.index},
        {"label", c.label},
        {"icon", c.icon},
        {"color", c.color},
        {"type", c.type},
        {"config", c.config_details}
    };
}

void from_json(const nlohmann::json& j, SlotConfig& c) {
    c.index = j.value("index", 0);
    c.label = j.value("label", "Unassigned");
    c.icon = j.value("icon", "resources/icons/default.png");
    c.color = j.value("color", "blue");
    c.type = j.value("type", "run_program");
    if (j.contains("config")) {
        c.config_details = j["config"];
    } else {
        c.config_details = nlohmann::json::object();
    }
}

AppConfig ConfigStore::CreateDefaultConfig() {
    AppConfig config;
    config.global.hold_threshold_ms = 150;
    config.global.radial_size = "medium";
    config.global.hotkey_override = "";
    config.global.show_tray_icon = true;
    config.global.debug_log = false;

    config.slots.resize(8);
    for (int i = 0; i < 8; ++i) {
        config.slots[i].index = i;
        config.slots[i].color = "blue";
        config.slots[i].icon = "resources/icons/default.png";
        if (i == 0) {
            config.slots[i].label = "Notepad";
            config.slots[i].type = "run_program";
            config.slots[i].config_details = {
                {"path", "C:\\Windows\\System32\\notepad.exe"},
                {"args", ""},
                {"workdir", ""},
                {"run_as_admin", false},
                {"single_instance", false}
            };
        } else if (i == 1) {
            config.slots[i].label = "Google";
            config.slots[i].type = "open_url";
            config.slots[i].config_details = {
                {"url", "https://www.google.com"},
                {"browser", "default"},
                {"new_tab", true}
            };
        } else {
            config.slots[i].label = "Unassigned";
            config.slots[i].type = "run_program";
            config.slots[i].config_details = {
                {"path", ""},
                {"args", ""},
                {"workdir", ""},
                {"run_as_admin", false},
                {"single_instance", false}
            };
        }
    }
    return config;
}

bool ConfigStore::Load(const std::wstring& path) {
    std::unique_lock<std::shared_mutex> lock(m_mutex);

    if (!std::filesystem::exists(path)) {
        m_config = CreateDefaultConfig();
        lock.unlock();
        return Save(path);
    }

    try {
        std::ifstream file(path);
        if (!file.is_open()) {
            m_config = CreateDefaultConfig();
            lock.unlock();
            return Save(path);
        }

        nlohmann::json j;
        file >> j;

        AppConfig loaded;
        if (j.contains("global")) {
            from_json(j["global"], loaded.global);
        } else {
            loaded.global = CreateDefaultConfig().global;
        }

        loaded.slots.resize(8);
        AppConfig defaults = CreateDefaultConfig();
        for (int i = 0; i < 8; ++i) {
            loaded.slots[i] = defaults.slots[i];
        }

        if (j.contains("slots") && j["slots"].is_array()) {
            for (const auto& s_json : j["slots"]) {
                int idx = s_json.value("index", -1);
                if (idx >= 0 && idx < 8) {
                    from_json(s_json, loaded.slots[idx]);
                }
            }
        }

        m_config = loaded;
        return true;
    } catch (...) {
        // Backup corrupted file
        try {
            std::filesystem::rename(path, path + L".bad");
        } catch (...) {}

        m_config = CreateDefaultConfig();
        lock.unlock();
        return Save(path);
    }
}

bool ConfigStore::Save(const std::wstring& path) {
    std::shared_lock<std::shared_mutex> lock(m_mutex);

    nlohmann::json j;
    to_json(j["global"], m_config.global);

    nlohmann::json slots_arr = nlohmann::json::array();
    for (const auto& s : m_config.slots) {
        nlohmann::json s_json;
        to_json(s_json, s);
        slots_arr.push_back(s_json);
    }
    j["slots"] = slots_arr;

    try {
        std::filesystem::path fs_path(path);
        std::filesystem::create_directories(fs_path.parent_path());

        std::wstring temp_path = path + L".tmp";
        std::ofstream file(temp_path);
        if (!file.is_open()) return false;

        file << j.dump(4);
        file.close();

        std::filesystem::rename(temp_path, path);
        return true;
    } catch (...) {
        return false;
    }
}

AppConfig ConfigStore::GetConfig() const {
    std::shared_lock<std::shared_mutex> lock(m_mutex);
    return m_config;
}

void ConfigStore::SetConfig(const AppConfig& config) {
    std::unique_lock<std::shared_mutex> lock(m_mutex);
    m_config = config;
}

} // namespace KnobLaunch
```

### 4.5 Win32 Entry Point (`src/main.cpp` structure)
```cpp
#include <windows.h>
#include <shellapi.h>
#include <shlwapi.h>
#include <string>
#include <filesystem>
#include "config_store.h"

#define WM_TRAYICON (WM_USER + 1)
#define ID_TRAY_OPEN_CONFIG 2001
#define ID_TRAY_RELOAD_CONFIG 2002
#define ID_TRAY_EXIT 2003

KnobLaunch::ConfigStore g_configStore;
std::wstring g_configPath;

std::wstring GetExecutableDirectory() {
    wchar_t buffer[MAX_PATH];
    GetModuleFileNameW(nullptr, buffer, MAX_PATH);
    std::wstring path(buffer);
    size_t pos = path.find_last_of(L"\\/");
    return (pos == std::wstring::npos) ? L"" : path.substr(0, pos);
}

void OpenConfigInEditor() {
    // Generate config if it doesn't exist
    if (!std::filesystem::exists(g_configPath)) {
        g_configStore.Load(g_configPath);
    }
    ShellExecuteW(nullptr, L"open", g_configPath.c_str(), nullptr, nullptr, SW_SHOWNORMAL);
}

LRESULT CALLBACK WndProc(HWND hWnd, UINT message, WPARAM wParam, LPARAM lParam) {
    switch (message) {
    case WM_TRAYICON:
        if (lParam == WM_RBUTTONUP) {
            POINT curPoint;
            GetCursorPos(&curPoint);
            
            SetForegroundWindow(hWnd); // Prevent focus issues
            
            HMENU hMenu = CreatePopupMenu();
            if (hMenu) {
                AppendMenuW(hMenu, MF_STRING, ID_TRAY_OPEN_CONFIG, L"Open Config");
                AppendMenuW(hMenu, MF_STRING, ID_TRAY_RELOAD_CONFIG, L"Reload Config");
                AppendMenuW(hMenu, MF_SEPARATOR, 0, nullptr);
                AppendMenuW(hMenu, MF_STRING, ID_TRAY_EXIT, L"Exit");
                
                TrackPopupMenu(hMenu, TPM_RIGHTBUTTON, curPoint.x, curPoint.y, 0, hWnd, nullptr);
                DestroyMenu(hMenu);
            }
        }
        break;
        
    case WM_COMMAND:
        switch (LOWORD(wParam)) {
        case ID_TRAY_OPEN_CONFIG:
            OpenConfigInEditor();
            break;
        case ID_TRAY_RELOAD_CONFIG:
            if (g_configStore.Load(g_configPath)) {
                MessageBoxW(hWnd, L"Configuration reloaded successfully.", L"KnobLaunch", MB_OK | MB_ICONINFORMATION);
            } else {
                MessageBoxW(hWnd, L"Failed to reload configuration.", L"KnobLaunch", MB_OK | MB_ICONERROR);
            }
            break;
        case ID_TRAY_EXIT:
            DestroyWindow(hWnd);
            break;
        }
        break;
        
    case WM_DESTROY:
        NOTIFYICONDATAW nid = {};
        nid.cbSize = sizeof(NOTIFYICONDATAW);
        nid.hWnd = hWnd;
        nid.uID = 1;
        Shell_NotifyIconW(NIM_DELETE, &nid);
        
        PostQuitMessage(0);
        break;
        
    default:
        return DefWindowProc(hWnd, message, wParam, lParam);
    }
    return 0;
}

int WINAPI wWinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPWSTR lpCmdLine, int nCmdShow) {
    std::wstring exeDir = GetExecutableDirectory();
    g_configPath = exeDir + L"\\..\\config\\config.json";
    
    g_configStore.Load(g_configPath);
    
    const wchar_t CLASS_NAME[] = L"KnobLaunchTrayWindow";
    WNDCLASSW wc = {};
    wc.lpfnWndProc = WndProc;
    wc.hInstance = hInstance;
    wc.lpszClassName = CLASS_NAME;
    RegisterClassW(&wc);
    
    HWND hWnd = CreateWindowExW(
        0, CLASS_NAME, L"KnobLaunch Daemon", WS_OVERLAPPEDWINDOW,
        CW_USEDEFAULT, CW_USEDEFAULT, CW_USEDEFAULT, CW_USEDEFAULT,
        nullptr, nullptr, hInstance, nullptr
    );
    if (!hWnd) return 0;
    
    NOTIFYICONDATAW nid = {};
    nid.cbSize = sizeof(NOTIFYICONDATAW);
    nid.hWnd = hWnd;
    nid.uID = 1;
    nid.uFlags = NIF_MESSAGE | NIF_ICON | NIF_TIP;
    nid.uCallbackMessage = WM_TRAYICON;
    nid.hIcon = LoadIconW(nullptr, IDI_APPLICATION); // Standard application icon
    wcscpy_s(nid.szTip, L"KnobLaunch");
    
    Shell_NotifyIconW(NIM_ADD, &nid);
    
    MSG msg = {};
    while (GetMessageW(&msg, nullptr, 0, 0)) {
        TranslateMessage(&msg);
        DispatchMessageW(&msg);
    }
    
    return static_cast<int>(msg.wParam);
}
```

---

## 5. Verification Method

Once implemented, the files can be compiled and validated as follows:

### 5.1 Build Command
From the repository root on Windows (with MSVC and CMake installed):
```cmd
cmake -B build -G "Visual Studio 17 2022" -A x64
cmake --build build --config Release
```
This should compile without warnings or errors (with strict warnings `/W4 /WX` enabled) and generate `bin/knoblaunch.exe`.

### 5.2 Verification Actions
1. **First-run Generation**: Delete `config/` directory. Run `bin/knoblaunch.exe`. Verify that `config/config.json` is automatically generated with default values.
2. **Invalid Config Recoverability**: Modify `config/config.json` to have invalid JSON syntax (e.g. remove a closing brace). Run the application. Verify that the app renames the invalid config to `config.json.bad` and creates a fresh `config.json`.
3. **Tray Interaction**: Run the application. Check the Windows System Tray for the application icon. Right-click the icon to verify the menu is shown with the expected items.
4. **Open Config**: Click "Open Config" in the tray menu. Verify that `config.json` opens in Notepad or the default JSON editor.
5. **Reload Config**: Click "Reload Config" in the tray menu. Verify the message box confirms successful reloading.
6. **Exit**: Click "Exit" in the tray menu. Verify the application process terminates and the tray icon is removed.
