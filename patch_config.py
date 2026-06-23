import os

file_path = "c:\\Users\\carla\\Desktop\\AHK\\Arvie Knob Macro\\src\\config_store.cpp"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

find_block = """static bool SanitizeSlots(nlohmann::json& s, int depth) {
    bool modified = false;
    if (depth > 10) return false;
    
    if (!s.is_array()) {
        s = nlohmann::json::array();
        modified = true;
    }

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
        nlohmann::json& item = existingSlots[i];"""

replace_block = """static bool SanitizeSlots(nlohmann::json& s, int depth) {
    bool modified = false;
    if (depth > 10) return false;
    
    if (!s.is_array()) {
        s = nlohmann::json::array();
        modified = true;
    }

    std::vector<nlohmann::json> existingSlots;
    for (auto& item : s) {
        if (item.is_object()) {
            existingSlots.push_back(item);
        }
    }
    
    // Fallback if empty root
    if (depth == 0 && existingSlots.empty()) {
        for (int i=0; i<8; i++) existingSlots.push_back(nlohmann::json::object());
        modified = true;
    }

    nlohmann::json sanitizedSlots = nlohmann::json::array();
    for (size_t i = 0; i < existingSlots.size(); ++i) {
        nlohmann::json& item = existingSlots[i];"""

content = content.replace(find_block, replace_block)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("config_store.cpp padded logic removed")
