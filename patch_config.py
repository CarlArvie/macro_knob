import os

file_path = "c:\\Users\\carla\\Desktop\\AHK\\Arvie Knob Macro\\src\\config_store.cpp"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace(
    'g.interaction_mode = gj.value("interaction_mode", "mouse_hold");\n    g.rotary_prev = gj.value("rotary_prev", "PgDn");\n    g.rotary_next = gj.value("rotary_next", "PgUp");',
    'g.interaction_mode = gj.value("interaction_mode", "mouse_hold");\n    g.rotary_prev = gj.value("rotary_prev", "PgDn");\n    g.rotary_next = gj.value("rotary_next", "PgUp");\n    g.is_enabled = gj.value("is_enabled", True);\n    g.toggle_hotkey = gj.value("toggle_hotkey", "F14");'
)

content = content.replace(
    'sc.index = item["index"].get<int>();\n        sc.label = item["label"].get<std::string>();',
    'sc.index = item["index"].get<int>();\n        sc.enabled = item.value("enabled", True);\n        sc.label = item["label"].get<std::string>();'
)

content = content.replace(
    'j["global"]["rotary_prev"] = g.rotary_prev;\n    j["global"]["rotary_next"] = g.rotary_next;',
    'j["global"]["rotary_prev"] = g.rotary_prev;\n    j["global"]["rotary_next"] = g.rotary_next;\n    j["global"]["is_enabled"] = g.is_enabled;\n    j["global"]["toggle_hotkey"] = g.toggle_hotkey;'
)

content = content.replace(
    'item["index"] = sc.index;\n        item["label"] = sc.label;',
    'item["index"] = sc.index;\n        item["enabled"] = sc.enabled;\n        item["label"] = sc.label;'
)

content = content.replace(
    'if (!g.contains("rotary_next") || !g["rotary_next"].is_string()) {\n        g["rotary_next"] = "PgUp";\n        modified = true;\n    }',
    'if (!g.contains("rotary_next") || !g["rotary_next"].is_string()) {\n        g["rotary_next"] = "PgUp";\n        modified = true;\n    }\n    if (!g.contains("is_enabled") || !g["is_enabled"].is_boolean()) {\n        g["is_enabled"] = true;\n        modified = true;\n    }\n    if (!g.contains("toggle_hotkey") || !g["toggle_hotkey"].is_string()) {\n        g["toggle_hotkey"] = "F14";\n        modified = true;\n    }'
)

content = content.replace(
    'if (!item.contains("index") || item["index"] != i) {\n            item["index"] = i;\n            itemModified = true;\n        }',
    'if (!item.contains("index") || item["index"] != i) {\n            item["index"] = i;\n            itemModified = true;\n        }\n\n        if (!item.contains("enabled") || !item["enabled"].is_boolean()) {\n            item["enabled"] = true;\n            itemModified = true;\n        }'
)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Patch applied to config_store.cpp")
