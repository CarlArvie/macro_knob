import os

file_path = "c:\\Users\\carla\\Desktop\\AHK\\Arvie Knob Macro\\src\\input_hook.cpp"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace(
    'static bool g_slotEnabled[8] = {true, true, true, true, true, true, true, true};',
    'static std::vector<bool> g_slotEnabled;'
)

content = content.replace(
    '''static void UpdateSlotEnabledCache() {
    for (int i=0; i<8; i++) {
        g_slotEnabled[i] = g_configStore.GetSlotAtPath(g_menuPath, i).enabled;
    }
}''',
    '''static void UpdateSlotEnabledCache() {
    std::vector<SlotConfig> slots = g_configStore.GetSlotsAtPath(g_menuPath);
    g_slotEnabled.clear();
    for (size_t i=0; i<slots.size(); i++) {
        g_slotEnabled.push_back(slots[i].enabled);
    }
}'''
)

rotary_find = """                        if (pKeyInfo->vkCode == g_rotaryNextVk) {
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
rotary_replace = """                        int N = (int)g_slotEnabled.size();
                        if (N > 0) {
                            if (pKeyInfo->vkCode == g_rotaryNextVk) {
                                int nextSlot = g_rotaryHovered;
                                do {
                                    nextSlot = (nextSlot + 1) % N;
                                } while (!g_slotEnabled[nextSlot] && nextSlot != g_rotaryHovered);
                                g_rotaryHovered = nextSlot;
                            } else {
                                int nextSlot = g_rotaryHovered;
                                do {
                                    nextSlot = (nextSlot - 1 + N) % N;
                                } while (!g_slotEnabled[nextSlot] && nextSlot != g_rotaryHovered);
                                g_rotaryHovered = nextSlot;
                            }
                        }"""
content = content.replace(rotary_find, rotary_replace)

mouse_find = """                            double angle = atan2(dx, dy);
                            double deg = angle * 180.0 / 3.14159265358979323846;
                            if (deg < 0) deg += 360.0;
                            int sector = (int)floor((deg + 22.5) / 45.0) % 8;"""

mouse_replace = """                            double angle = atan2(dx, dy);
                            double deg = angle * 180.0 / 3.14159265358979323846;
                            if (deg < 0) deg += 360.0;
                            int N = (int)g_slotEnabled.size();
                            if (N == 0) return 1;
                            double sweep = 360.0 / N;
                            int sector = (int)floor((deg + sweep / 2.0) / sweep) % N;"""
content = content.replace(mouse_find, mouse_replace)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("input_hook.cpp patched")
