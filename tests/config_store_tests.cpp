#include <iostream>
#include <cassert>
#include <fstream>
#include <thread>
#include <vector>
#include <atomic>
#include <windows.h>
#include "config_store.h"

// Define helper macro for testing
#define TEST_ASSERT(cond) \
    do { \
        if (!(cond)) { \
            std::cerr << "Assertion failed at line " << __LINE__ << ": " << #cond << std::endl; \
            std::exit(1); \
        } \
    } while (0)

void CleanConfigFile(const std::wstring& path) {
    DeleteFileW(path.c_str());
    std::wstring backup = path + L".bak";
    DeleteFileW(backup.c_str());
    std::wstring tmp = path + L".tmp";
    DeleteFileW(tmp.c_str());
}

void WriteRawConfig(const std::wstring& path, const std::string& content) {
    std::ofstream ofs(path);
    TEST_ASSERT(ofs.is_open());
    ofs << content;
    ofs.close();
}

// Requirement 1: Default config generation when config.json is deleted
// Requirement 2: Verification of exactly 8 slots created and default entries loaded
void TestDefaultConfigGeneration(const std::wstring& configPath) {
    std::cout << "Running TestDefaultConfigGeneration..." << std::endl;
    CleanConfigFile(configPath);

    ConfigStore store;
    TEST_ASSERT(store.Load());

    // Check config.json exists
    DWORD attrib = GetFileAttributesW(configPath.c_str());
    TEST_ASSERT(attrib != INVALID_FILE_ATTRIBUTES);

    // Verify global settings
    GlobalConfig global = store.GetGlobal();
    TEST_ASSERT(global.hold_threshold_ms == 150);
    TEST_ASSERT(global.radial_size == "medium");
    TEST_ASSERT(global.hotkey_override == "F13");
    TEST_ASSERT(global.show_tray_icon == true);
    TEST_ASSERT(global.debug_log == false);

    // Verify slots settings
    std::vector<SlotConfig> slots = store.GetSlots();
    TEST_ASSERT(slots.size() == 8);

    // Verify default entries loaded
    TEST_ASSERT(slots[0].index == 0);
    TEST_ASSERT(slots[0].label == "Notepad");
    TEST_ASSERT(slots[0].type == "run_program");
    TEST_ASSERT(slots[0].config_data["path"] == "notepad.exe");

    TEST_ASSERT(slots[1].index == 1);
    TEST_ASSERT(slots[1].label == "GitHub");
    TEST_ASSERT(slots[1].type == "open_url");
    TEST_ASSERT(slots[1].config_data["url"] == "https://github.com");

    for (int i = 2; i < 8; ++i) {
        TEST_ASSERT(slots[i].index == i);
        TEST_ASSERT(slots[i].label == "Slot " + std::to_string(i));
        TEST_ASSERT(slots[i].type == "run_program");
        TEST_ASSERT(slots[i].config_data["path"] == "");
    }
    std::cout << "TestDefaultConfigGeneration passed." << std::endl;
}

// Requirement 3: Self-healing when config.json is missing fields, has invalid slots, or is malformed
void TestSelfHealingMalformed(const std::wstring& configPath) {
    std::cout << "Running TestSelfHealingMalformed..." << std::endl;
    CleanConfigFile(configPath);
    WriteRawConfig(configPath, "{ malformed json: [ invalid }");

    ConfigStore store;
    // Load should not crash, should return true and regenerate default config
    TEST_ASSERT(store.Load());

    std::vector<SlotConfig> slots = store.GetSlots();
    TEST_ASSERT(slots.size() == 8);
    TEST_ASSERT(slots[0].label == "Notepad");
    TEST_ASSERT(slots[1].label == "GitHub");

    std::cout << "TestSelfHealingMalformed passed." << std::endl;
}

void TestSelfHealingMissingFields(const std::wstring& configPath) {
    std::cout << "Running TestSelfHealingMissingFields..." << std::endl;
    CleanConfigFile(configPath);
    // Write partial JSON containing only hold_threshold_ms
    WriteRawConfig(configPath, R"({
        "global": {
            "hold_threshold_ms": 300
        }
    })");

    ConfigStore store;
    TEST_ASSERT(store.Load());

    // hold_threshold_ms should be respected, other fields healed to defaults
    GlobalConfig global = store.GetGlobal();
    TEST_ASSERT(global.hold_threshold_ms == 300);
    TEST_ASSERT(global.radial_size == "medium"); // default
    TEST_ASSERT(global.hotkey_override == "F13"); // default

    // slots should be healed to exactly 8 default slots
    std::vector<SlotConfig> slots = store.GetSlots();
    TEST_ASSERT(slots.size() == 8);
    TEST_ASSERT(slots[0].label == "Notepad");
    TEST_ASSERT(slots[1].label == "GitHub");

    std::cout << "TestSelfHealingMissingFields passed." << std::endl;
}

void TestSelfHealingInvalidSlots(const std::wstring& configPath) {
    std::cout << "Running TestSelfHealingInvalidSlots..." << std::endl;
    CleanConfigFile(configPath);
    // Write config with:
    // - slots is not an array (should heal all slots to default)
    WriteRawConfig(configPath, R"({
        "global": {
            "hold_threshold_ms": 150
        },
        "slots": {}
    })");

    ConfigStore store;
    TEST_ASSERT(store.Load());

    std::vector<SlotConfig> slots = store.GetSlots();
    TEST_ASSERT(slots.size() == 8);
    TEST_ASSERT(slots[0].label == "Notepad");

    // Test invalid slot types and colors
    CleanConfigFile(configPath);
    WriteRawConfig(configPath, R"({
        "global": {},
        "slots": [
            {
                "index": 0,
                "label": "Custom Notepad",
                "type": "invalid_type",
                "color": "0xFF123456",
                "config": {
                    "path": "custom_notepad.exe"
                }
            }
        ]
    })");

    TEST_ASSERT(store.Load());
    slots = store.GetSlots();
    TEST_ASSERT(slots.size() == 8);
    // Index 0 type should heal from "invalid_type" to "run_program"
    TEST_ASSERT(slots[0].type == "run_program");
    // Other properties should be preserved if valid or healed if missing
    TEST_ASSERT(slots[0].label == "Custom Notepad");
    TEST_ASSERT(slots[0].color == "0xFF123456");
    TEST_ASSERT(slots[0].config_data["path"] == "custom_notepad.exe");

    // Index 1 should heal to default GitHub slot
    TEST_ASSERT(slots[1].index == 1);
    TEST_ASSERT(slots[1].label == "GitHub");
    TEST_ASSERT(slots[1].type == "open_url");

    std::cout << "TestSelfHealingInvalidSlots passed." << std::endl;
}

// Requirement 5: Thread-safety checks (concurrently query ConfigStore config from multiple threads)
void TestThreadSafety() {
    std::cout << "Running TestThreadSafety..." << std::endl;
    ConfigStore store;
    store.Load();

    std::atomic<bool> start_flag(false);
    std::atomic<bool> stop_flag(false);

    const int num_threads = 16;
    std::vector<std::thread> threads;

    for (int i = 0; i < num_threads; ++i) {
        threads.emplace_back([&store, &start_flag, &stop_flag, i]() {
            while (!start_flag) {
                std::this_thread::yield();
            }

            int iterations = 5000;
            for (int k = 0; k < iterations; ++k) {
                if (stop_flag) break;

                // Alternate between reading and writing
                if (k % 20 == 0) {
                    // Write Global Config
                    GlobalConfig g = store.GetGlobal();
                    g.hold_threshold_ms = 100 + (k % 1000);
                    store.UpdateGlobal(g);
                } else if (k % 20 == 1) {
                    // Write Slot Config
                    int slotIdx = (i + k) % 8;
                    SlotConfig sc = store.GetSlot(slotIdx);
                    sc.label = "ThreadSlot_" + std::to_string(i) + "_" + std::to_string(k);
                    store.UpdateSlot(slotIdx, sc);
                } else {
                    // Read operations (majority)
                    GlobalConfig g = store.GetGlobal();
                    (void)g.hold_threshold_ms;

                    std::vector<SlotConfig> slots = store.GetSlots();
                    (void)slots.size();

                    int slotIdx = (i + k) % 8;
                    SlotConfig sc = store.GetSlot(slotIdx);
                    (void)sc.index;
                }
            }
        });
    }

    // Release threads simultaneously
    start_flag = true;

    // Wait for all threads to complete
    for (auto& t : threads) {
        if (t.joinable()) {
            t.join();
        }
    }

    std::cout << "TestThreadSafety passed." << std::endl;
}

// Requirement 4: Validation of tray icon menu interaction stubs
// verify that the window with class name `KnobLaunchTrayHelper` exists and can receive custom commands like ID_TRAY_RELOAD_CONFIG
void TestTrayIconWindow() {
    std::cout << "Running TestTrayIconWindow..." << std::endl;

    // Check if the window is already running
    HWND hwnd = FindWindowW(L"KnobLaunchDaemon", L"KnobLaunchDaemonWindow");
    bool spawned = false;

    if (!hwnd) {
        std::cout << "KnobLaunchTrayHelper window not found. Spawning knoblaunch.exe..." << std::endl;
        STARTUPINFOW si = { sizeof(si) };
        PROCESS_INFORMATION pi = {};
        
        // Try to spawn knoblaunch.exe from the workspace directory or bin directory
        wchar_t cmdLine[] = L"bin\\knoblaunch.exe";
        BOOL success = CreateProcessW(NULL, cmdLine, NULL, NULL, FALSE, 0, NULL, NULL, &si, &pi);
        if (!success) {
            // Try fallback to root
            wchar_t cmdLineFallback[] = L"knoblaunch.exe";
            success = CreateProcessW(NULL, cmdLineFallback, NULL, NULL, FALSE, 0, NULL, NULL, &si, &pi);
        }

        TEST_ASSERT(success);
        spawned = true;

        // Wait up to 5 seconds for window to be created
        for (int i = 0; i < 50; ++i) {
            hwnd = FindWindowW(L"KnobLaunchDaemon", L"KnobLaunchDaemonWindow");
            if (hwnd) break;
            Sleep(100);
        }

        if (hwnd == NULL) {
            DWORD exitCode = 0;
            if (GetExitCodeProcess(pi.hProcess, &exitCode)) {
                std::cout << "[DIAGNOSTIC] Spawned process exited with code: " << exitCode << std::endl;
            } else {
                std::cout << "[DIAGNOSTIC] Failed to get process exit code." << std::endl;
            }
        }

        TEST_ASSERT(hwnd != NULL);
        std::cout << "Spawned and successfully located KnobLaunchDaemon window." << std::endl;
        CloseHandle(pi.hProcess);
        CloseHandle(pi.hThread);
    } else {
        std::cout << "Found existing KnobLaunchDaemon window." << std::endl;
    }

    // Verify that the window is of class "KnobLaunchDaemon"
    wchar_t className[256];
    GetClassNameW(hwnd, className, 256);
    TEST_ASSERT(std::wstring(className) == L"KnobLaunchDaemon");

    // Send custom command ID_TRAY_RELOAD (40003)
    // SendMessageW is synchronous and will process the message in WndProc
    std::cout << "Sending ID_TRAY_RELOAD command..." << std::endl;
    LRESULT res = SendMessageW(hwnd, WM_COMMAND, 40003, 0);
    TEST_ASSERT(res == 0); // WndProc returns 0 for processed commands
    std::cout << "ID_TRAY_RELOAD sent and handled successfully." << std::endl;

    // If we spawned it, let's also close it using ID_TRAY_EXIT (40004)
    if (spawned) {
        std::cout << "Sending ID_TRAY_EXIT command to clean up spawned process..." << std::endl;
        SendMessageW(hwnd, WM_COMMAND, 40004, 0);
        
        // Wait for it to exit
        Sleep(500);
        hwnd = FindWindowW(L"KnobLaunchDaemon", L"KnobLaunchDaemonWindow");
        TEST_ASSERT(hwnd == NULL);
        std::cout << "Spawned process closed and cleaned up successfully." << std::endl;
    }

    std::cout << "TestTrayIconWindow passed." << std::endl;
}

void TestSelfHealingTopLevelArray(const std::wstring& configPath) {
    std::cout << "Running TestSelfHealingTopLevelArray..." << std::endl;
    CleanConfigFile(configPath);
    WriteRawConfig(configPath, "[]");

    ConfigStore store;
    // Load should not crash, should return true and regenerate default config
    TEST_ASSERT(store.Load());

    std::vector<SlotConfig> slots = store.GetSlots();
    TEST_ASSERT(slots.size() == 8);
    TEST_ASSERT(slots[0].label == "Notepad");

    std::cout << "TestSelfHealingTopLevelArray passed." << std::endl;
}

int main() {
    // Resolve configuration path dynamically via dummy config store
    ConfigStore dummy;
    std::wstring configPath = dummy.GetResolvedPath();
    std::wcout << L"Resolved configuration path: " << configPath << std::endl;

    // Save copy of existing config if present
    std::wstring backupPath = configPath + L".orig";
    bool hasOriginal = false;
    if (GetFileAttributesW(configPath.c_str()) != INVALID_FILE_ATTRIBUTES) {
        CopyFileW(configPath.c_str(), backupPath.c_str(), FALSE);
        hasOriginal = true;
    }

    try {
        TestDefaultConfigGeneration(configPath);
        TestSelfHealingMalformed(configPath);
        TestSelfHealingTopLevelArray(configPath);
        TestSelfHealingMissingFields(configPath);
        TestSelfHealingInvalidSlots(configPath);
        TestThreadSafety();
        TestTrayIconWindow();
        std::cout << "\nALL TESTS PASSED SUCCESSFULLY!" << std::endl;
    } catch (...) {
        std::cerr << "Exception occurred during testing!" << std::endl;
        // Restore config if backup exists
        if (hasOriginal) {
            CopyFileW(backupPath.c_str(), configPath.c_str(), FALSE);
            DeleteFileW(backupPath.c_str());
        }
        return 1;
    }

    // Restore config if backup exists
    if (hasOriginal) {
        CopyFileW(backupPath.c_str(), configPath.c_str(), FALSE);
        DeleteFileW(backupPath.c_str());
    }

    return 0;
}
