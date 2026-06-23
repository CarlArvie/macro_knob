import os

file_path = "c:\\Users\\carla\\Desktop\\AHK\\Arvie Knob Macro\\src\\input_hook.cpp"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace(
    "static UINT g_toggleHotkeyVk = 0;",
    "#include <vector>\nstatic std::vector<UINT> g_toggleHotkeys;"
)

content = content.replace(
    'g_toggleHotkeyVk = ParseHotkeyStringToVk(cfg.toggle_hotkey);',
    'g_toggleHotkeys.clear();\n    std::string s = cfg.toggle_hotkey;\n    size_t pos = 0;\n    while ((pos = s.find(\'+\')) != std::string::npos) {\n        std::string t = s.substr(0, pos);\n        t.erase(0, t.find_first_not_of(" \\t"));\n        t.erase(t.find_last_not_of(" \\t") + 1);\n        if(!t.empty()) g_toggleHotkeys.push_back(ParseHotkeyStringToVk(t));\n        s.erase(0, pos + 1);\n    }\n    s.erase(0, s.find_first_not_of(" \\t"));\n    s.erase(s.find_last_not_of(" \\t") + 1);\n    if(!s.empty()) g_toggleHotkeys.push_back(ParseHotkeyStringToVk(s));'
)

block_find = """        if (pKeyInfo->vkCode == g_toggleHotkeyVk) {
            bool isDown = (wParam == WM_KEYDOWN || wParam == WM_SYSKEYDOWN);
            if (isDown) {
                g_appEnabled = !g_appEnabled;
                GlobalConfig cfg = g_configStore.GetGlobal();
                cfg.is_enabled = g_appEnabled;
                g_configStore.UpdateGlobal(cfg);
                g_configStore.Save();
                PostMessageW(g_hDaemonWnd, 0x0111, 40003, 0); // WM_COMMAND, ID_TRAY_RELOAD
            }
            return 1;
        }"""

block_replace = """        bool isToggleHotkey = false;
        if (!g_toggleHotkeys.empty()) {
            isToggleHotkey = true;
            bool foundCurrent = false;
            for (UINT vk : g_toggleHotkeys) {
                if (pKeyInfo->vkCode == vk) {
                    foundCurrent = true;
                    continue;
                }
                if ((GetAsyncKeyState(vk) & 0x8000) == 0) {
                    isToggleHotkey = false;
                    break;
                }
            }
            if (!foundCurrent) isToggleHotkey = false;
        }

        if (isToggleHotkey) {
            bool isDown = (wParam == WM_KEYDOWN || wParam == WM_SYSKEYDOWN);
            if (isDown) {
                static ULONGLONG lastToggleTime = 0;
                ULONGLONG now = GetTickCount64();
                if (now - lastToggleTime > 500) {
                    lastToggleTime = now;
                    g_appEnabled = !g_appEnabled;
                    GlobalConfig cfg = g_configStore.GetGlobal();
                    cfg.is_enabled = g_appEnabled;
                    g_configStore.UpdateGlobal(cfg);
                    g_configStore.Save();
                    PostMessageW(g_hDaemonWnd, 0x0111, 40003, 0); // WM_COMMAND, ID_TRAY_RELOAD
                }
            }
            return 1;
        }"""

content = content.replace(block_find, block_replace)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("input_hook.cpp patched for multi-key")
