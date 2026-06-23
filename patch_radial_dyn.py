import os

file_path = "c:\\Users\\carla\\Desktop\\AHK\\Arvie Knob Macro\\src\\radial_menu.cpp"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

redraw_find = """        std::vector<SlotConfig> slots = g_configStore.GetSlotsAtPath(GetCurrentMenuPath());

        for (int k = 0; k < 8; ++k) {
            bool isHovered = (k == hoveredSector);"""
redraw_replace = """        std::vector<SlotConfig> slots = g_configStore.GetSlotsAtPath(GetCurrentMenuPath());
        int N = (int)slots.size();
        if (N == 0) {
            // clear dc and return
        } else {
        double sweep_angle = 360.0 / N;
        for (int k = 0; k < N; ++k) {
            bool isHovered = (k == hoveredSector);"""
content = content.replace(redraw_find, redraw_replace)

content = content.replace(
    'double start_angle = k * 45.0 - 112.5;',
    'double start_angle = k * sweep_angle - 90.0 - (sweep_angle / 2.0);'
)

content = content.replace(
    'path.AddArc(cx - R_outer, cy - R_outer, 2.0f * R_outer, 2.0f * R_outer, (float)start_angle, 45.0f);',
    'path.AddArc(cx - R_outer, cy - R_outer, 2.0f * R_outer, 2.0f * R_outer, (float)start_angle, (float)sweep_angle);'
)

content = content.replace(
    'path.AddArc(cx - R_inner, cy - R_inner, 2.0f * R_inner, 2.0f * R_inner, (float)start_angle + 45.0f, -45.0f);',
    'path.AddArc(cx - R_inner, cy - R_inner, 2.0f * R_inner, 2.0f * R_inner, (float)start_angle + (float)sweep_angle, -(float)sweep_angle);'
)

content = content.replace(
    'double theta_deg = k * 45.0;',
    'double theta_deg = k * sweep_angle;'
)

content = content.replace(
    '''            }
        }
    }

    POINT ptDest = { rect.left, rect.top };''',
    '''            }
        }
        }
    }

    POINT ptDest = { rect.left, rect.top };'''
)

proc_find = """                double dist = std::sqrt(dx * dx + dy * dy);
                int hovered = -1;
                if (dist >= 60.0) {
                    double angle = std::atan2(dx, dy);
                    double deg = angle * 180.0 / 3.14159265358979323846;
                    if (deg < 0) deg += 360.0;
                    hovered = (int)std::floor((deg + 22.5) / 45.0) % 8;
                }"""
proc_replace = """                double dist = std::sqrt(dx * dx + dy * dy);
                int hovered = -1;
                if (dist >= 60.0) {
                    std::vector<SlotConfig> slots = g_configStore.GetSlotsAtPath(GetCurrentMenuPath());
                    int N = (int)slots.size();
                    if (N > 0) {
                        double sweep = 360.0 / N;
                        double angle = std::atan2(dx, dy);
                        double deg = angle * 180.0 / 3.14159265358979323846;
                        if (deg < 0) deg += 360.0;
                        hovered = (int)std::floor((deg + sweep / 2.0) / sweep) % N;
                    }
                }"""
content = content.replace(proc_find, proc_replace)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("radial_menu.cpp patched")
