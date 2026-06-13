#include "config_store.h"
#include <windows.h>
#include <shlobj.h>
#include <fstream>
#include <iostream>
#include <algorithm>

// Custom load/save helper functions
static void LoadFromJson(const nlohmann::json& j, GlobalConfig& g, std::vector<SlotConfig>& sVec) {
    auto& gj = j["global"];
    g.hold_threshold_ms = gj["hold_threshold_ms"].get<int>();
    g.radial_size = gj["radial_size"].get<std::string>();
    g.hotkey_override = gj["hotkey_override"].get<std::string>();
    g.show_tray_icon = gj["show_tray_icon"].get<bool>();
    g.debug_log = gj["debug_log"].get<bool>();

    sVec.clear();
    auto& sj = j["slots"];
    for (auto& item : sj) {
        SlotConfig sc;
        sc.index = item["index"].get<int>();
        sc.label = item["label"].get<std::string>();
        sc.icon = item["icon"].get<std::string>();
        sc.color = item["color"].get<std::string>();
        sc.type = item["type"].get<std::string>();
        sc.config_data = item["config"];
        sVec.push_back(sc);
    }
}

static nlohmann::json SaveToJson(const GlobalConfig& g, const std::vector<SlotConfig>& sVec) {
    nlohmann::json j;
    j["global"]["hold_threshold_ms"] = g.hold_threshold_ms;
    j["global"]["radial_size"] = g.radial_size;
    j["global"]["hotkey_override"] = g.hotkey_override;
    j["global"]["show_tray_icon"] = g.show_tray_icon;
    j["global"]["debug_log"] = g.debug_log;

    j["slots"] = nlohmann::json::array();
    for (const auto& sc : sVec) {
        nlohmann::json item;
        item["index"] = sc.index;
        item["label"] = sc.label;
        item["icon"] = sc.icon;
        item["color"] = sc.color;
        item["type"] = sc.type;
        item["config"] = sc.config_data;
        j["slots"].push_back(item);
    }
    return j;
}

ConfigStore::ConfigStore() {
    resolvedPath = ResolveConfigPath();
}

std::wstring ConfigStore::ResolveConfigPath() const {
    wchar_t exePath[MAX_PATH];
    if (GetModuleFileNameW(NULL, exePath, MAX_PATH) == 0) {
        return L"config.json"; // fallback
    }
    std::wstring pathStr(exePath);
    size_t lastSlash = pathStr.find_last_of(L"\\/");
    if (lastSlash == std::wstring::npos) {
        return L"config.json";
    }
    std::wstring exeDir = pathStr.substr(0, lastSlash);

    // Candidates:
    // 1. (exe_dir)/config/config.json
    std::wstring cand1 = exeDir + L"\\config\\config.json";
    // 2. (exe_dir)/../config/config.json
    std::wstring cand2 = exeDir + L"\\..\\config\\config.json";
    // 3. (exe_dir)/config.json
    std::wstring cand3 = exeDir + L"\\config.json";

    if (GetFileAttributesW(cand1.c_str()) != INVALID_FILE_ATTRIBUTES) {
        return cand1;
    }
    if (GetFileAttributesW(cand2.c_str()) != INVALID_FILE_ATTRIBUTES) {
        return cand2;
    }
    if (GetFileAttributesW(cand3.c_str()) != INVALID_FILE_ATTRIBUTES) {
        return cand3;
    }

    // Determine where to create
    bool isBin = false;
    if (exeDir.length() >= 3) {
        std::wstring last3 = exeDir.substr(exeDir.length() - 3);
        if (_wcsicmp(last3.c_str(), L"bin") == 0 || 
            (exeDir.length() >= 4 && _wcsicmp(exeDir.substr(exeDir.length() - 4).c_str(), L"bin\\") == 0) ||
            (exeDir.length() >= 4 && _wcsicmp(exeDir.substr(exeDir.length() - 4).c_str(), L"bin/") == 0)) {
            isBin = true;
        }
    }

    if (isBin) {
        return cand2;
    } else {
        return cand1;
    }
}

void ConfigStore::GenerateDefaultConfig() {
    globalSettings = GlobalConfig();
    slotsSettings.clear();
    for (int i = 0; i < 8; ++i) {
        SlotConfig sc;
        sc.index = i;
        if (i == 0) {
            sc.label = "Notepad";
            sc.icon = "resources/icons/notepad.png";
            sc.color = "0xFF555555";
            sc.type = "run_program";
            sc.config_data["path"] = "notepad.exe";
        } else if (i == 1) {
            sc.label = "GitHub";
            sc.icon = "resources/icons/github.png";
            sc.color = "0xFF333333";
            sc.type = "open_url";
            sc.config_data["url"] = "https://github.com";
        } else {
            sc.label = "Slot " + std::to_string(i);
            sc.icon = "resources/icons/default.png";
            sc.color = "0xFF777777";
            sc.type = "run_program";
            sc.config_data["path"] = "";
        }
        slotsSettings.push_back(sc);
    }

    nlohmann::json j = SaveToJson(globalSettings, slotsSettings);
    std::wstring tmpPath = resolvedPath + L".tmp";
    size_t lastSlash = resolvedPath.find_last_of(L"\\/");
    if (lastSlash != std::wstring::npos) {
        std::wstring dirPath = resolvedPath.substr(0, lastSlash);
        SHCreateDirectoryExW(NULL, dirPath.c_str(), NULL);
    }

    std::ofstream ofs(tmpPath);
    if (ofs.is_open()) {
        ofs << j.dump(4) << std::endl;
        ofs.close();
        MoveFileExW(tmpPath.c_str(), resolvedPath.c_str(), MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH);
    }
}

bool ConfigStore::ValidateAndSanitize(nlohmann::json& j) {
    bool modified = false;

    if (!j.is_object()) {
        j = nlohmann::json::object();
        modified = true;
    }

    if (!j.contains("global") || !j["global"].is_object()) {
        j["global"] = nlohmann::json::object();
        modified = true;
    }

    auto& g = j["global"];
    
    if (!g.contains("hold_threshold_ms") || !g["hold_threshold_ms"].is_number_integer()) {
        g["hold_threshold_ms"] = 150;
        modified = true;
    }
    if (!g.contains("radial_size") || !g["radial_size"].is_string()) {
        g["radial_size"] = "medium";
        modified = true;
    } else {
        std::string sz = g["radial_size"];
        if (sz != "small" && sz != "medium" && sz != "large") {
            g["radial_size"] = "medium";
            modified = true;
        }
    }
    if (!g.contains("hotkey_override") || !g["hotkey_override"].is_string()) {
        g["hotkey_override"] = "F13";
        modified = true;
    }
    if (!g.contains("show_tray_icon") || !g["show_tray_icon"].is_boolean()) {
        g["show_tray_icon"] = true;
        modified = true;
    }
    if (!g.contains("debug_log") || !g["debug_log"].is_boolean()) {
        g["debug_log"] = false;
        modified = true;
    }

    if (!j.contains("slots") || !j["slots"].is_array()) {
        j["slots"] = nlohmann::json::array();
        modified = true;
    }

    auto& s = j["slots"];
    std::vector<nlohmann::json> existingSlots(8, nlohmann::json());
    
    for (auto& item : s) {
        if (item.is_object() && item.contains("index") && item["index"].is_number_integer()) {
            int idx = item["index"].get<int>();
            if (idx >= 0 && idx < 8) {
                existingSlots[idx] = item;
            }
        }
    }

    nlohmann::json sanitizedSlots = nlohmann::json::array();
    for (int i = 0; i < 8; ++i) {
        nlohmann::json& item = existingSlots[i];
        bool itemModified = false;
        
        if (item.is_null()) {
            item = nlohmann::json::object();
            item["index"] = i;
            itemModified = true;
        }

        if (!item.contains("index") || item["index"] != i) {
            item["index"] = i;
            itemModified = true;
        }

        if (!item.contains("label") || !item["label"].is_string()) {
            if (i == 0) item["label"] = "Notepad";
            else if (i == 1) item["label"] = "GitHub";
            else item["label"] = "Slot " + std::to_string(i);
            itemModified = true;
        }

        if (!item.contains("icon") || !item["icon"].is_string()) {
            if (i == 0) item["icon"] = "resources/icons/notepad.png";
            else if (i == 1) item["icon"] = "resources/icons/github.png";
            else item["icon"] = "resources/icons/default.png";
            itemModified = true;
        }

        if (!item.contains("color") || !item["color"].is_string()) {
            if (i == 0) item["color"] = "0xFF555555";
            else if (i == 1) item["color"] = "0xFF333333";
            else item["color"] = "0xFF777777";
            itemModified = true;
        }

        if (!item.contains("type") || !item["type"].is_string()) {
            if (i == 0) item["type"] = "run_program";
            else if (i == 1) item["type"] = "open_url";
            else item["type"] = "run_program";
            itemModified = true;
        } else {
            std::string t = item["type"];
            if (t != "run_program" && t != "open_url" && t != "ahk_script") {
                item["type"] = "run_program";
                itemModified = true;
            }
        }

        if (!item.contains("config") || !item["config"].is_object()) {
            item["config"] = nlohmann::json::object();
            itemModified = true;
        }

        auto& c = item["config"];
        std::string t = item["type"];
        if (t == "run_program") {
            if (!c.contains("path") || !c["path"].is_string()) {
                if (i == 0) c["path"] = "notepad.exe";
                else c["path"] = "";
                itemModified = true;
            }
        } else if (t == "open_url") {
            if (!c.contains("url") || !c["url"].is_string()) {
                if (i == 1) c["url"] = "https://github.com";
                else c["url"] = "";
                itemModified = true;
            }
        } else if (t == "ahk_script") {
            if (!c.contains("script_file") || !c["script_file"].is_string()) {
                c["script_file"] = "";
                itemModified = true;
            }
        }

        sanitizedSlots.push_back(item);
        if (itemModified) {
            modified = true;
        }
    }

    if (s != sanitizedSlots) {
        s = sanitizedSlots;
        modified = true;
    }

    return modified;
}

bool ConfigStore::Load() {
    std::unique_lock<std::shared_mutex> lock(mtx);
    if (resolvedPath.empty()) {
        resolvedPath = ResolveConfigPath();
    }

    std::wstring tmpPath = resolvedPath + L".tmp";
    DWORD dwAttrib = GetFileAttributesW(tmpPath.c_str());
    if (dwAttrib != INVALID_FILE_ATTRIBUTES && !(dwAttrib & FILE_ATTRIBUTE_DIRECTORY)) {
        DeleteFileW(tmpPath.c_str());
    }

    std::ifstream ifs(resolvedPath);
    nlohmann::json j;
    bool needsWrite = false;

    if (!ifs.is_open()) {
        GenerateDefaultConfig();
        return true;
    }

    try {
        ifs >> j;
        ifs.close();
    } catch (...) {
        ifs.close();
        GenerateDefaultConfig();
        return true;
    }

    needsWrite = ValidateAndSanitize(j);
    LoadFromJson(j, globalSettings, slotsSettings);

    if (needsWrite) {
        size_t lastSlash = resolvedPath.find_last_of(L"\\/");
        if (lastSlash != std::wstring::npos) {
            std::wstring dirPath = resolvedPath.substr(0, lastSlash);
            SHCreateDirectoryExW(NULL, dirPath.c_str(), NULL);
        }
        std::ofstream ofs(tmpPath);
        if (ofs.is_open()) {
            ofs << j.dump(4) << std::endl;
            ofs.close();
            MoveFileExW(tmpPath.c_str(), resolvedPath.c_str(), MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH);
        }
    }

    return true;
}

bool ConfigStore::Save() {
    std::unique_lock<std::shared_mutex> lock(mtx);
    if (resolvedPath.empty()) {
        resolvedPath = ResolveConfigPath();
    }
    nlohmann::json j = SaveToJson(globalSettings, slotsSettings);
    std::wstring tmpPath = resolvedPath + L".tmp";
    size_t lastSlash = resolvedPath.find_last_of(L"\\/");
    if (lastSlash != std::wstring::npos) {
        std::wstring dirPath = resolvedPath.substr(0, lastSlash);
        SHCreateDirectoryExW(NULL, dirPath.c_str(), NULL);
    }
    std::ofstream ofs(tmpPath);
    if (!ofs.is_open()) {
        return false;
    }
    ofs << j.dump(4) << std::endl;
    ofs.close();
    if (!MoveFileExW(tmpPath.c_str(), resolvedPath.c_str(), MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH)) {
        return false;
    }
    return true;
}

GlobalConfig ConfigStore::GetGlobal() const {
    std::shared_lock<std::shared_mutex> lock(mtx);
    return globalSettings;
}

std::vector<SlotConfig> ConfigStore::GetSlots() const {
    std::shared_lock<std::shared_mutex> lock(mtx);
    return slotsSettings;
}

SlotConfig ConfigStore::GetSlot(int index) const {
    std::shared_lock<std::shared_mutex> lock(mtx);
    if (index >= 0 && index < (int)slotsSettings.size()) {
        return slotsSettings[index];
    }
    return SlotConfig();
}

void ConfigStore::UpdateGlobal(const GlobalConfig& newGlobal) {
    std::unique_lock<std::shared_mutex> lock(mtx);
    globalSettings = newGlobal;
}

void ConfigStore::UpdateSlot(int index, const SlotConfig& newSlot) {
    std::unique_lock<std::shared_mutex> lock(mtx);
    if (index >= 0 && index < (int)slotsSettings.size()) {
        slotsSettings[index] = newSlot;
    }
}

std::wstring ConfigStore::GetResolvedPath() const {
    std::shared_lock<std::shared_mutex> lock(mtx);
    return resolvedPath;
}
