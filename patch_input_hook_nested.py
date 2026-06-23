import os

file_path = "c:\\Users\\carla\\Desktop\\AHK\\Arvie Knob Macro\\src\\input_hook.cpp"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace(
    'static int g_rotaryHovered = 0;',
    'static int g_rotaryHovered = 0;\nstatic std::vector<int> g_menuPath;'
)

content = content.replace(
    'static void SetMenuVisible(bool visible) {',
    'static void UpdateSlotEnabledCache() {\n    for (int i=0; i<8; i++) {\n        g_slotEnabled[i] = g_configStore.GetSlotAtPath(g_menuPath, i).enabled;\n    }\n}\n\nstatic void SetMenuVisible(bool visible) {'
)

content = content.replace(
    '    for(int i=0; i<8; i++) g_slotEnabled[i] = g_configStore.GetSlot(i).enabled;',
    '    UpdateSlotEnabledCache();'
)

content = content.replace(
    'void TriggerSlotMacro(int sector) {\n    SlotConfig slot = g_configStore.GetSlot(sector);',
    'void TriggerSlotMacro(int sector) {\n    SlotConfig slot = g_configStore.GetSlotAtPath(g_menuPath, sector);'
)

# Mouse mode trigger logic replacement
mouse_trigger_find = """                        if (dist >= 60.0) {
                            double angle = atan2(dx, dy);
                            double deg = angle * 180.0 / 3.14159265358979323846;
                            if (deg < 0) deg += 360.0;
                            int sector = (int)floor((deg + 22.5) / 45.0) % 8;
                            DebugLog("LowLevelKeyboardProc: Triggering sector " + std::to_string(sector));
                            PostMessageW(g_hDaemonWnd, WM_TRIGGER_MACRO, (WPARAM)sector, 0);
                        }

                        if (g_hRadialMenuWnd) {
                            DestroyWindow(g_hRadialMenuWnd);
                            g_hRadialMenuWnd = NULL;
                        }
                    } else {
                        DebugLog("LowLevelKeyboardProc: Menu not visible, sending simulated tap.");
                        SendSimulatedTap((WORD)g_targetVk);
                    }
                    return 1;"""

mouse_trigger_replace = """                        if (dist >= 60.0) {
                            double angle = atan2(dx, dy);
                            double deg = angle * 180.0 / 3.14159265358979323846;
                            if (deg < 0) deg += 360.0;
                            int sector = (int)floor((deg + 22.5) / 45.0) % 8;
                            SlotConfig slot = g_configStore.GetSlotAtPath(g_menuPath, sector);
                            if (slot.type == "sub_menu") {
                                g_menuPath.push_back(sector);
                                UpdateSlotEnabledCache();
                                g_isHotkeyHeld = false; // require re-press, but keep menu open
                                return 1;
                            } else if (slot.type == "back") {
                                if (!g_menuPath.empty()) g_menuPath.pop_back();
                                UpdateSlotEnabledCache();
                                g_isHotkeyHeld = false;
                                return 1;
                            } else {
                                PostMessageW(g_hDaemonWnd, WM_TRIGGER_MACRO, (WPARAM)sector, 0);
                            }
                        }

                        if (g_hRadialMenuWnd) {
                            DestroyWindow(g_hRadialMenuWnd);
                            g_hRadialMenuWnd = NULL;
                        }
                    } else {
                        SendSimulatedTap((WORD)g_targetVk);
                    }
                    return 1;"""
content = content.replace(mouse_trigger_find, mouse_trigger_replace)

# Rotary mode trigger logic replacement
rotary_trigger_find = """            } else if (pKeyInfo->vkCode == g_targetVk) {
                if (isDown && g_menuVisible) {
                    PostMessageW(g_hDaemonWnd, WM_TRIGGER_MACRO, (WPARAM)g_rotaryHovered, 0);
                    if (g_hRadialMenuWnd) {
                        DestroyWindow(g_hRadialMenuWnd);
                        g_hRadialMenuWnd = NULL;
                    }
                    SetMenuVisible(false);
                    if (g_hRotaryTimer) {
                        DeleteTimerQueueTimer(NULL, g_hRotaryTimer, NULL);
                        g_hRotaryTimer = NULL;
                    }
                    g_swallowTargetUp = true;
                    return 1;
                } else if (isUp) {"""

rotary_trigger_replace = """            } else if (pKeyInfo->vkCode == g_targetVk) {
                if (isDown && g_menuVisible) {
                    SlotConfig slot = g_configStore.GetSlotAtPath(g_menuPath, g_rotaryHovered);
                    if (slot.type == "sub_menu") {
                        g_menuPath.push_back(g_rotaryHovered);
                        g_rotaryHovered = 0;
                        UpdateSlotEnabledCache();
                        RadialMenuSetHovered(g_hRadialMenuWnd, g_rotaryHovered);
                        if (g_hRotaryTimer) { DeleteTimerQueueTimer(NULL, g_hRotaryTimer, NULL); g_hRotaryTimer = NULL; }
                        CreateTimerQueueTimer(&g_hRotaryTimer, NULL, RotaryTimerCallback, NULL, 10000, 0, WT_EXECUTEONLYONCE);
                        g_swallowTargetUp = true;
                        return 1;
                    } else if (slot.type == "back") {
                        if (!g_menuPath.empty()) g_menuPath.pop_back();
                        g_rotaryHovered = 0;
                        UpdateSlotEnabledCache();
                        RadialMenuSetHovered(g_hRadialMenuWnd, g_rotaryHovered);
                        if (g_hRotaryTimer) { DeleteTimerQueueTimer(NULL, g_hRotaryTimer, NULL); g_hRotaryTimer = NULL; }
                        CreateTimerQueueTimer(&g_hRotaryTimer, NULL, RotaryTimerCallback, NULL, 10000, 0, WT_EXECUTEONLYONCE);
                        g_swallowTargetUp = true;
                        return 1;
                    }

                    PostMessageW(g_hDaemonWnd, WM_TRIGGER_MACRO, (WPARAM)g_rotaryHovered, 0);
                    if (g_hRadialMenuWnd) {
                        DestroyWindow(g_hRadialMenuWnd);
                        g_hRadialMenuWnd = NULL;
                    }
                    SetMenuVisible(false);
                    if (g_hRotaryTimer) {
                        DeleteTimerQueueTimer(NULL, g_hRotaryTimer, NULL);
                        g_hRotaryTimer = NULL;
                    }
                    g_swallowTargetUp = true;
                    return 1;
                } else if (isUp) {"""
content = content.replace(rotary_trigger_find, rotary_trigger_replace)

# Menu open logic replacement
content = content.replace(
    '                        SetMenuVisible(true);\n                        g_rotaryHovered = 0;',
    '                        g_menuPath.clear();\n                        UpdateSlotEnabledCache();\n                        SetMenuVisible(true);\n                        g_rotaryHovered = 0;'
)

content = content.replace(
    '        SetMenuVisible(true);\n        DebugLog("HandleHoldTimer: Creating radial menu.");',
    '        g_menuPath.clear();\n        UpdateSlotEnabledCache();\n        SetMenuVisible(true);\n        DebugLog("HandleHoldTimer: Creating radial menu.");'
)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("input_hook.cpp patched for sub-menus")
