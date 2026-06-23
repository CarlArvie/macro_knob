#pragma once

#include <string>
#include <vector>
#include <shared_mutex>
#include <nlohmann/json.hpp>

struct GlobalConfig {
    int hold_threshold_ms = 150;
    std::string radial_size = "medium";
    std::string hotkey_override = "F13";
    bool show_tray_icon = true;
    bool debug_log = false;
    std::string interaction_mode = "mouse_hold";
    std::string rotary_prev = "PgDn";
    std::string rotary_next = "PgUp";
    bool is_enabled = true;
    std::string toggle_hotkey = "F14";
    bool enable_haptic_sound = true;
};

struct SlotConfig {
    int index = 0;
    bool enabled = true;
    std::string label;
    std::string icon;
    std::string color;
    std::string type;
    nlohmann::json config_data;
    std::vector<SlotConfig> child_slots;
};

class ConfigStore {
public:
    ConfigStore();
    ~ConfigStore() = default;

    // Load from disk. Resolves configuration path, handles defaults and self-healing.
    bool Load();

    // Save current configuration to disk.
    bool Save();

    // Thread-safe accessors
    GlobalConfig GetGlobal() const;
    std::vector<SlotConfig> GetSlots() const;
    SlotConfig GetSlot(int index) const;
    std::vector<SlotConfig> GetSlotsAtPath(const std::vector<int>& path) const;
    SlotConfig GetSlotAtPath(const std::vector<int>& path, int index) const;

    // Thread-safe setters
    void UpdateGlobal(const GlobalConfig& newGlobal);
    void UpdateSlot(int index, const SlotConfig& newSlot);

    // Get the actual resolved configuration path
    std::wstring GetResolvedPath() const;

private:
    std::wstring ResolveConfigPath() const;
    void GenerateDefaultConfig();
    bool ValidateAndSanitize(nlohmann::json& j);

    mutable std::shared_mutex mtx;
    std::wstring resolvedPath;
    GlobalConfig globalSettings;
    std::vector<SlotConfig> slotsSettings; // Exactly 8 slots
};
