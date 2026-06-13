# KnobLaunch Milestone 1: Scaffold & Config Proposal

This document outlines the design strategy, folder layout, build configuration, and code declarations for Milestone 1 of the KnobLaunch project.

---

## 1. Directory Layout
The project directory structure follows the layout specified in `PROJECT.md`. Because the root of the user's workspace contains general macro planning files, all project files for KnobLaunch will be organized under the root directory as follows:

```
KnobLaunch/
├── CMakeLists.txt                 # CMake configuration for MSVC builds
├── src/
│   ├── main.cpp                   # Win32 Application entry point & tray menu
│   ├── config_store.h             # Configuration management header
│   ├── config_store.cpp           # JSON load, save, default generation, and self-healing
│   ├── input_hook.h               # Low-level keyboard hook header (Stub in M1)
│   ├── input_hook.cpp             # Hook management (Stub in M1)
│   ├── radial_menu.h              # Radial Menu overlay window header (Stub in M1)
│   ├── radial_menu.cpp            # GDI+ drawing, window proc (Stub in M1)
│   ├── macro_runner.h             # Macro executor header (Stub in M1)
│   └── macro_runner.cpp           # Spawning programs, URLs, AHK scripts (Stub in M1)
├── include/
│   └── nlohmann/
│       └── json.hpp               # nlohmann/json header-only library
├── resources/
│   └── icons/                     # Pre-packaged icons for slices (default.png, etc.)
├── bin/
│   ├── AutoHotkey64.exe           # AutoHotkey v2 executable bundled for scripts
│   └── (knoblaunch.exe)           # Built executable output target
├── tests/
│   ├── test_runner.py             # E2E test runner
│   └── test_cases/                # E2E test cases
└── README.md                      # Basic readme
```

---

## 2. CMake Configuration (`CMakeLists.txt`)
The build configuration targets MSVC with C++17 to ensure modern language features (like `<filesystem>` and `std::shared_mutex`) are available while keeping compatibility high. It builds a Windows GUI application (no console popup window) and links the necessary Win32 libraries.

### Proposed `CMakeLists.txt`
```cmake
cmake_minimum_required(VERSION 3.20)
project(KnobLaunch LANGUAGES CXX)

# Require C++17
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# MSVC Compiler Warning Options & Strict Settings
if(MSVC)
    add_compile_options(
        /W4          # Warning Level 4
        /WX          # Treat warnings as errors
        /permissive- # Standard conformance mode
        /EHsc        # C++ exception handling model
    )
    # Expose classic Windows functions by not minimizing windows.h inclusion
    add_compile_definitions(NOMINMAX WIN32_LEAN_AND_MEAN)
endif()

# Direct binary output to the bin/ directory
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}/bin)

# Setup include search paths
include_directories(
    ${CMAKE_SOURCE_DIR}/include
    ${CMAKE_SOURCE_DIR}/src
)

# Source files list (stubs are compiled so they can be integrated later)
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

# Win32 Windows Executable (No command-prompt pop-up on start)
add_executable(knoblaunch WIN32 ${SOURCES})

# Link libraries
# - user32: windows message loops, hooks
# - shell32: tray notifications (Shell_NotifyIconW), ShellExecuteW
# - gdi32 / gdiplus: 2D rendering for radial menus
# - shlwapi: Win32 shell path utility functions (fallback / fallback checks)
target_link_libraries(knoblaunch PRIVATE
    user32
    shell32
    gdi32
    gdiplus
    shlwapi
)

# Post-build step to copy or verify config directory structure
add_custom_command(TARGET knoblaunch POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E make_directory $<TARGET_FILE_DIR:knoblaunch>/../config
    COMMENT "Ensuring config output directory exists"
)
```

---

## 3. nlohmann/json Integration Strategy
We will use version `3.11.x` of the header-only `nlohmann/json` library. 
- **Method**: Download the single header file `json.hpp` from the official repository releases page and save it at `include/nlohmann/json.hpp`.
- **Packaging**: Since it is a header-only library, no library compilation is required, and there are no runtime dependencies.

---

## 4. ConfigStore Module Design

The `ConfigStore` must load and save JSON configurations, ensure thread safety for concurrent accesses (e.g. macro runner, GUI updates, or tray menu reloading), and gracefully handle malformed, missing, or partial configuration files.

### 4.1 Header Declaration: `src/config_store.h`
```cpp
#pragma once

#include <string>
#include <vector>
#include <filesystem>
#include <shared_mutex>
#include <nlohmann/json.hpp>

namespace KnobLaunch {

struct GlobalConfig {
    int hold_threshold_ms = 150;
    std::string radial_size = "medium";
    std::string hotkey_override = "";
    bool show_tray_icon = true;
    bool debug_log = false;
};

struct SlotConfig {
    struct ConfigDetails {
        // run_program
        std::string path = "";
        std::string args = "";
        std::string workdir = "";
        bool run_as_admin = false;
        bool single_instance = false;

        // open_url
        std::string url = "";
        std::string browser = "default";
        bool new_tab = true;

        // ahk_script
        std::string script_file = "";
    };

    int index = 0;
    std::string label = "";
    std::string icon = "";
    std::string color = "blue";
    std::string type = "run_program";
    ConfigDetails config;
};

struct AppConfig {
    GlobalConfig global;
    std::vector<SlotConfig> slots;
};

class ConfigStore {
public:
    // Constructor accepts the direct path to the target config.json
    explicit ConfigStore(std::filesystem::path configPath);

    // Loads config from disk. If missing or invalid, generates defaults, saves, and loads.
    bool Load();

    // Saves the provided configuration to disk atomically.
    bool Save(const AppConfig& config);

    // Thread-safe getter for the current configuration
    AppConfig GetConfig() const;

    // Returns a hardcoded default configuration structure
    AppConfig GetDefaultConfig() const;

private:
    // Validates JSON structure, fills in default values for missing/invalid keys
    void ValidateAndRepair(nlohmann::json& j) const;

    // Writes content to a temp file, then performs an atomic swap on Windows
    bool WriteAtomic(const std::string& content) const;

    std::filesystem::path m_configPath;
    AppConfig m_config;
    mutable std::shared_mutex m_mutex;
};

} // namespace KnobLaunch
```

### 4.2 Implementation Details: `src/config_store.cpp`
To implement the schema contracts, serialization functions are written in `config_store.cpp`:

```cpp
#include "config_store.h"
#include <fstream>
#include <windows.h>

namespace KnobLaunch {

// --- JSON Serialization Mappings ---

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
    j.at("hold_threshold_ms").get_to(c.hold_threshold_ms);
    j.at("radial_size").get_to(c.radial_size);
    j.at("hotkey_override").get_to(c.hotkey_override);
    j.at("show_tray_icon").get_to(c.show_tray_icon);
    j.at("debug_log").get_to(c.debug_log);
}

void to_json(nlohmann::json& j, const SlotConfig& c) {
    j = nlohmann::json{
        {"index", c.index},
        {"label", c.label},
        {"icon", c.icon},
        {"color", c.color},
        {"type", c.type}
    };
    
    nlohmann::json cfg = nlohmann::json::object();
    if (c.type == "run_program") {
        cfg["path"] = c.config.path;
        cfg["args"] = c.config.args;
        cfg["workdir"] = c.config.workdir;
        cfg["run_as_admin"] = c.config.run_as_admin;
        cfg["single_instance"] = c.config.single_instance;
    } else if (c.type == "open_url") {
        cfg["url"] = c.config.url;
        cfg["browser"] = c.config.browser;
        cfg["new_tab"] = c.config.new_tab;
    } else if (c.type == "ahk_script") {
        cfg["script_file"] = c.config.script_file;
    }
    j["config"] = cfg;
}

void from_json(const nlohmann::json& j, SlotConfig& c) {
    j.at("index").get_to(c.index);
    j.at("label").get_to(c.label);
    j.at("icon").get_to(c.icon);
    j.at("color").get_to(c.color);
    j.at("type").get_to(c.type);
    
    const auto& cfg = j.at("config");
    if (c.type == "run_program") {
        if (cfg.contains("path")) cfg.at("path").get_to(c.config.path);
        if (cfg.contains("args")) cfg.at("args").get_to(c.config.args);
        if (cfg.contains("workdir")) cfg.at("workdir").get_to(c.config.workdir);
        if (cfg.contains("run_as_admin")) cfg.at("run_as_admin").get_to(c.config.run_as_admin);
        if (cfg.contains("single_instance")) cfg.at("single_instance").get_to(c.config.single_instance);
    } else if (c.type == "open_url") {
        if (cfg.contains("url")) cfg.at("url").get_to(c.config.url);
        if (cfg.contains("browser")) cfg.at("browser").get_to(c.config.browser);
        if (cfg.contains("new_tab")) cfg.at("new_tab").get_to(c.config.new_tab);
    } else if (c.type == "ahk_script") {
        if (cfg.contains("script_file")) cfg.at("script_file").get_to(c.config.script_file);
    }
}

void to_json(nlohmann::json& j, const AppConfig& c) {
    j = nlohmann::json{
        {"global", c.global},
        {"slots", c.slots}
    };
}

void from_json(const nlohmann::json& j, AppConfig& c) {
    j.at("global").get_to(c.global);
    j.at("slots").get_to(c.slots);
}

// --- ConfigStore Methods ---

ConfigStore::ConfigStore(std::filesystem::path configPath)
    : m_configPath(std::move(configPath)) {}

AppConfig ConfigStore::GetConfig() const {
    std::shared_lock<std::shared_mutex> lock(m_mutex);
    return m_config;
}

AppConfig ConfigStore::GetDefaultConfig() const {
    AppConfig cfg;
    cfg.global.hold_threshold_ms = 150;
    cfg.global.radial_size = "medium";
    cfg.global.hotkey_override = "";
    cfg.global.show_tray_icon = true;
    cfg.global.debug_log = false;

    cfg.slots.resize(8);
    for (int i = 0; i < 8; ++i) {
        cfg.slots[i].index = i;
        cfg.slots[i].color = "blue";
        cfg.slots[i].type = "run_program";
        
        if (i == 0) {
            cfg.slots[i].label = "Notepad";
            cfg.slots[i].icon = "resources/icons/notepad.png";
            cfg.slots[i].config.path = "C:\\Windows\\System32\\notepad.exe";
        } else if (i == 1) {
            cfg.slots[i].label = "GitHub";
            cfg.slots[i].icon = "resources/icons/github.png";
            cfg.slots[i].type = "open_url";
            cfg.slots[i].config.url = "https://github.com";
        } else {
            cfg.slots[i].label = "Slot " + std::to_string(i + 1);
            cfg.slots[i].icon = "resources/icons/default.png";
            cfg.slots[i].config.path = "";
        }
    }
    return cfg;
}

bool ConfigStore::WriteAtomic(const std::string& content) const {
    std::filesystem::path tmpPath = m_configPath;
    tmpPath.replace_extension(".tmp");

    try {
        // Ensure config's parent directories exist
        std::filesystem::create_directories(m_configPath.parent_path());

        // Write temp file
        std::ofstream out(tmpPath, std::ios::out | std::ios::binary | std::ios::trunc);
        if (!out.is_open()) return false;
        out << content;
        out.close();

        // Perform an atomic swap using Win32 MoveFileEx
        BOOL success = MoveFileExW(
            tmpPath.c_str(),
            m_configPath.c_str(),
            MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH
        );
        return success != 0;
    } catch (...) {
        return false;
    }
}

bool ConfigStore::Save(const AppConfig& config) {
    std::unique_lock<std::shared_mutex> lock(m_mutex);
    nlohmann::json j = config;
    if (WriteAtomic(j.dump(4))) {
        m_config = config;
        return true;
    }
    return false;
}

bool ConfigStore::Load() {
    std::unique_lock<std::shared_mutex> lock(m_mutex);

    if (!std::filesystem::exists(m_configPath)) {
        m_config = GetDefaultConfig();
        nlohmann::json j = m_config;
        WriteAtomic(j.dump(4));
        return true;
    }

    try {
        std::ifstream in(m_configPath, std::ios::in | std::ios::binary);
        if (!in.is_open()) {
            m_config = GetDefaultConfig();
            return false;
        }

        nlohmann::json j;
        in >> j;
        in.close();

        // Perform validations and heal structure
        ValidateAndRepair(j);

        // Map repaired JSON to variables
        m_config = j.get<AppConfig>();

        // Re-save healed structure to disk
        WriteAtomic(j.dump(4));
        return true;
    } catch (...) {
        // Fallback for json syntax errors
        m_config = GetDefaultConfig();
        nlohmann::json j = m_config;
        WriteAtomic(j.dump(4));
        return false;
    }
}

void ConfigStore::ValidateAndRepair(nlohmann::json& j) const {
    if (!j.contains("global") || !j["global"].is_object()) {
        j["global"] = nlohmann::json::object();
    }
    auto& g = j["global"];
    if (!g.contains("hold_threshold_ms") || !g["hold_threshold_ms"].is_number_integer()) {
        g["hold_threshold_ms"] = 150;
    }
    if (!g.contains("radial_size") || !g["radial_size"].is_string()) {
        g["radial_size"] = "medium";
    } else {
        std::string size = g["radial_size"];
        if (size != "small" && size != "medium" && size != "large") {
            g["radial_size"] = "medium";
        }
    }
    if (!g.contains("hotkey_override") || !g["hotkey_override"].is_string()) {
        g["hotkey_override"] = "";
    }
    if (!g.contains("show_tray_icon") || !g["show_tray_icon"].is_boolean()) {
        g["show_tray_icon"] = true;
    }
    if (!g.contains("debug_log") || !g["debug_log"].is_boolean()) {
        g["debug_log"] = false;
    }

    if (!j.contains("slots") || !j["slots"].is_array()) {
        j["slots"] = nlohmann::json::array();
    }
    auto& s = j["slots"];

    std::vector<nlohmann::json> validatedSlots(8);
    for (auto& item : s) {
        if (item.is_object() && item.contains("index") && item["index"].is_number_integer()) {
            int idx = item["index"].get<int>();
            if (idx >= 0 && idx < 8) {
                validatedSlots[idx] = item;
            }
        }
    }

    for (int i = 0; i < 8; ++i) {
        auto& item = validatedSlots[i];
        if (item.is_null() || !item.is_object()) {
            item = nlohmann::json::object();
        }
        item["index"] = i;
        
        if (!item.contains("label") || !item["label"].is_string()) {
            item["label"] = "Slot " + std::to_string(i + 1);
        }
        if (!item.contains("icon") || !item["icon"].is_string()) {
            item["icon"] = "resources/icons/default.png";
        }
        if (!item.contains("color") || !item["color"].is_string()) {
            item["color"] = "blue";
        }
        if (!item.contains("type") || !item["type"].is_string()) {
            item["type"] = "run_program";
        }
        
        std::string type = item["type"];
        if (type != "run_program" && type != "open_url" && type != "ahk_script") {
            item["type"] = "run_program";
            type = "run_program";
        }

        if (!item.contains("config") || !item["config"].is_object()) {
            item["config"] = nlohmann::json::object();
        }
        auto& cfg = item["config"];
        if (type == "run_program") {
            if (!cfg.contains("path") || !cfg["path"].is_string()) cfg["path"] = "";
            if (!cfg.contains("args") || !cfg["args"].is_string()) cfg["args"] = "";
            if (!cfg.contains("workdir") || !cfg["workdir"].is_string()) cfg["workdir"] = "";
            if (!cfg.contains("run_as_admin") || !cfg["run_as_admin"].is_boolean()) cfg["run_as_admin"] = false;
            if (!cfg.contains("single_instance") || !cfg["single_instance"].is_boolean()) cfg["single_instance"] = false;
        } else if (type == "open_url") {
            if (!cfg.contains("url") || !cfg["url"].is_string()) cfg["url"] = "";
            if (!cfg.contains("browser") || !cfg["browser"].is_string()) cfg["browser"] = "default";
            if (!cfg.contains("new_tab") || !cfg["new_tab"].is_boolean()) cfg["new_tab"] = true;
        } else if (type == "ahk_script") {
            if (!cfg.contains("script_file") || !cfg["script_file"].is_string()) {
                cfg["script_file"] = "scripts/user_script_slot" + std::to_string(i) + ".ahk";
            }
        }
    }
    s = validatedSlots;
}

} // namespace KnobLaunch
```

---

## 5. Basic Win32 Application Entry Point (`main.cpp`)
The main file registers a hidden window class to host the tray icon, initializes GDI+, and launches the Win32 message loop.

### Proposed Structure: `src/main.cpp`
```cpp
#include <windows.h>
#include <gdiplus.h>
#include <shellapi.h>
#include <filesystem>
#include "config_store.h"

// Constants & Messages
#define WM_TRAY_ICON (WM_USER + 1)
#define ID_TRAY_OPEN_CONFIG 1001
#define ID_TRAY_RELOAD_CONFIG 1002
#define ID_TRAY_EXIT 1003

// Global Tray variables
NOTIFYICONDATAW g_nid = {};
std::filesystem::path g_configPath;
KnobLaunch::ConfigStore* g_configStore = nullptr;

// Helper to determine config file path relative to executable
std::filesystem::path GetConfigPath() {
    wchar_t buffer[MAX_PATH];
    GetModuleFileNameW(NULL, buffer, MAX_PATH);
    std::filesystem::path exePath(buffer);
    // Assuming binary is at <ProjectRoot>/bin/knoblaunch.exe
    std::filesystem::path rootDir = exePath.parent_path().parent_path();
    return rootDir / "config" / "config.json";
}

// Window Procedure
LRESULT CALLBACK WndProc(HWND hWnd, UINT message, WPARAM wParam, LPARAM lParam) {
    switch (message) {
        case WM_TRAY_ICON: {
            if (lParam == WM_RBUTTONUP) {
                // Display right-click context menu
                HMENU hMenu = CreatePopupMenu();
                AppendMenuW(hMenu, MF_STRING, ID_TRAY_OPEN_CONFIG, L"Open Config");
                AppendMenuW(hMenu, MF_STRING, ID_TRAY_RELOAD_CONFIG, L"Reload Config");
                AppendMenuW(hMenu, MF_SEPARATOR, 0, NULL);
                AppendMenuW(hMenu, MF_STRING, ID_TRAY_EXIT, L"Exit");

                POINT pt;
                GetCursorPos(&pt);
                SetForegroundWindow(hWnd);
                TrackPopupMenu(hMenu, TPM_RIGHTBUTTON | TPM_NOANIMATION, pt.x, pt.y, 0, hWnd, NULL);
                DestroyMenu(hMenu);
            } else if (lParam == WM_LBUTTONDBLCLK) {
                SendMessageW(hWnd, WM_COMMAND, ID_TRAY_OPEN_CONFIG, 0);
            }
            break;
        }

        case WM_COMMAND: {
            int wmId = LOWORD(wParam);
            switch (wmId) {
                case ID_TRAY_OPEN_CONFIG: {
                    // Open config.json in the system's default editor (e.g. Notepad)
                    ShellExecuteW(NULL, L"open", g_configPath.c_str(), NULL, NULL, SW_SHOWNORMAL);
                    break;
                }
                case ID_TRAY_RELOAD_CONFIG: {
                    if (g_configStore && g_configStore->Load()) {
                        // Show balloon confirmation tip
                        g_nid.uFlags |= NIF_INFO;
                        wcscpy_s(g_nid.szInfo, L"Configuration reloaded successfully.");
                        wcscpy_s(g_nid.szInfoTitle, L"KnobLaunch");
                        g_nid.dwInfoFlags = NIIF_INFO;
                        Shell_NotifyIconW(NIM_MODIFY, &g_nid);
                        g_nid.uFlags &= ~NIF_INFO; // Remove flag to prevent future re-triggers
                    } else {
                        MessageBoxW(hWnd, L"Failed to load or repair configuration.", L"Error", MB_OK | MB_ICONERROR);
                    }
                    break;
                }
                case ID_TRAY_EXIT: {
                    DestroyWindow(hWnd);
                    break;
                }
            }
            break;
        }

        case WM_DESTROY: {
            // Remove tray icon
            Shell_NotifyIconW(NIM_DELETE, &g_nid);
            PostQuitMessage(0);
            break;
        }

        default:
            return DefWindowProc(hWnd, message, wParam, lParam);
    }
    return 0;
}

// Win32 Main Entry
int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPSTR lpCmdLine, int nCmdShow) {
    UNREFERENCED_PARAMETER(hPrevInstance);
    UNREFERENCED_PARAMETER(lpCmdLine);
    UNREFERENCED_PARAMETER(nCmdShow);

    // Initialize GDI+
    Gdiplus::GdiplusStartupInput gdiplusStartupInput;
    ULONG_PTR gdiplusToken;
    Gdiplus::GdiplusStartup(&gdiplusToken, &gdiplusStartupInput, NULL);

    // Resolve Config path and initialize ConfigStore
    g_configPath = GetConfigPath();
    KnobLaunch::ConfigStore store(g_configPath);
    g_configStore = &store;
    g_configStore->Load(); // Auto-generates if missing

    // Register Tray Window Class
    const wchar_t szWindowClass[] = L"KnobLaunchTrayHelper";
    WNDCLASSEXW wcex = {};
    wcex.cbSize = sizeof(WNDCLASSEX);
    wcex.style = CS_HREDRAW | CS_VREDRAW;
    wcex.lpfnWndProc = WndProc;
    wcex.hInstance = hInstance;
    wcex.hIcon = LoadIconW(NULL, (LPCWSTR)IDI_APPLICATION);
    wcex.hCursor = LoadCursorW(NULL, (LPCWSTR)IDC_ARROW);
    wcex.hbrBackground = (HBRUSH)(COLOR_WINDOW + 1);
    wcex.lpszClassName = szWindowClass;
    RegisterClassExW(&wcex);

    // Create a hidden helper window (not message-only to ensure reliable Shell notifications)
    HWND hWnd = CreateWindowExW(
        0, szWindowClass, L"KnobLaunch Tray Helper",
        WS_OVERLAPPEDWINDOW, CW_USEDEFAULT, CW_USEDEFAULT, 0, 0,
        NULL, NULL, hInstance, NULL
    );

    if (!hWnd) {
        Gdiplus::GdiplusShutdown(gdiplusToken);
        return FALSE;
    }

    // Set up Tray Icon
    g_nid.cbSize = sizeof(NOTIFYICONDATAW);
    g_nid.hWnd = hWnd;
    g_nid.uID = 1;
    g_nid.uFlags = NIF_ICON | NIF_MESSAGE | NIF_TIP;
    g_nid.uCallbackMessage = WM_TRAY_ICON;
    g_nid.hIcon = LoadIconW(NULL, (LPCWSTR)IDI_APPLICATION); // Standard application icon for M1
    wcscpy_s(g_nid.szTip, L"KnobLaunch");
    Shell_NotifyIconW(NIM_ADD, &g_nid);

    // Standard Win32 Message Loop
    MSG msg;
    while (GetMessage(&msg, NULL, 0, 0)) {
        TranslateMessage(&msg);
        DispatchMessage(&msg);
    }

    // Clean up GDI+ before exit
    Gdiplus::GdiplusShutdown(gdiplusToken);

    return (int)msg.wParam;
}
```

---

## 6. Stubs for Remaining Modules (M1 Readiness)
To compile successfully under CMake, basic header/cpp stubs must be placed in `src/` for modules scheduled in subsequent Milestones (M2-M4):
- **`input_hook.h/cpp`**: Minimal class/functions for managing hooks (so compile and link won't break).
- **`radial_menu.h/cpp`**: Stub window creation and registry of class `KnobLaunchRadialMenu` (needed for test verification checking class existence).
- **`macro_runner.h/cpp`**: Stub executor interface.

These stub headers will expose empty or basic declarations that compile cleanly, allowing for continuous integration right from Milestone 1.
