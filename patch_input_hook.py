import os

file_path = "c:\\Users\\carla\\Desktop\\AHK\\Arvie Knob Macro\\src\\input_hook.cpp"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace(
    'static std::string g_hotkeyOverride = "F13";',
    'static std::string g_hotkeyOverride = "F13";\nstatic bool g_appEnabled = True;\nstatic UINT g_toggleHotkeyVk = 0;\nstatic bool g_slotEnabled[8] = {true, true, true, true, true, true, true, true};'
)

content = content.replace(
    'g_hotkeyOverride = cfg.hotkey_override;\n\n    g_holdThresholdMs = cfg.hold_threshold_ms;\n    g_targetVk = ParseHotkeyStringToVk(g_hotkeyOverride);\n    g_rotaryPrevVk = ParseHotkeyStringToVk(g_rotaryPrev);\n    g_rotaryNextVk = ParseHotkeyStringToVk(g_rotaryNext);',
    'g_hotkeyOverride = cfg.hotkey_override;\n    g_appEnabled = cfg.is_enabled;\n    g_toggleHotkeyVk = ParseHotkeyStringToVk(cfg.toggle_hotkey);\n    for(int i=0; i<8; i++) g_slotEnabled[i] = g_configStore.GetSlot(i).enabled;\n\n    g_holdThresholdMs = cfg.hold_threshold_ms;\n    g_targetVk = ParseHotkeyStringToVk(g_hotkeyOverride);\n    g_rotaryPrevVk = ParseHotkeyStringToVk(g_rotaryPrev);\n    g_rotaryNextVk = ParseHotkeyStringToVk(g_rotaryNext);'
)

block_find = """        if (pKeyInfo->dwExtraInfo == BYPASS_SIGNATURE) {
            DebugLog("LowLevelKeyboardProc: Bypassing signature event: vkCode=" + std::to_string(pKeyInfo->vkCode));
            return CallNextHookEx(g_hHook, nCode, wParam, lParam);
        }

        if (g_interactionMode == "rotary") {"""

block_replace = """        if (pKeyInfo->dwExtraInfo == BYPASS_SIGNATURE) {
            DebugLog("LowLevelKeyboardProc: Bypassing signature event: vkCode=" + std::to_string(pKeyInfo->vkCode));
            return CallNextHookEx(g_hHook, nCode, wParam, lParam);
        }

        if (pKeyInfo->vkCode == g_toggleHotkeyVk) {
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
        }

        if (!g_appEnabled) {
            return CallNextHookEx(g_hHook, nCode, wParam, lParam);
        }

        if (g_interactionMode == "rotary") {"""

content = content.replace(block_find, block_replace)

rotate_find = """                        if (pKeyInfo->vkCode == g_rotaryNextVk) {
                            g_rotaryHovered = (g_rotaryHovered + 1) % 8;
                        } else {
                            g_rotaryHovered = (g_rotaryHovered - 1 + 8) % 8;
                        }"""

rotate_replace = """                        if (pKeyInfo->vkCode == g_rotaryNextVk) {
                            int nextSlot = g_rotaryHovered;
                            do {
                                nextSlot = (nextSlot + 1) % 8;
                            } while (!g_slotEnabled[nextSlot] && nextSlot != g_rotaryHovered);
                            g_rotaryHovered = nextSlot;
                        } else {
                            int nextSlot = g_rotaryHovered;
                            do {
                                nextSlot = (nextSlot - 1 + 8) % 8;
                            } while (!g_slotEnabled[nextSlot] && nextSlot != g_rotaryHovered);
                            g_rotaryHovered = nextSlot;
                        }"""

content = content.replace(rotate_find, rotate_replace)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("input_hook.cpp patched")
