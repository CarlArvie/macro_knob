#include "radial_menu.h"
#include "config_store.h"
#include "input_hook.h"
#include <mmsystem.h>
#pragma comment(lib, "winmm.lib")
#include <gdiplus.h>
#include <cmath>
#include <string>
#include <vector>
#include <algorithm>

extern ConfigStore g_configStore;

static Gdiplus::Color ParseColorString(const std::string& colorStr, bool isHovered) {
    Gdiplus::Color baseColor(180, 80, 80, 80); // default semi-transparent dark gray
    
    std::string s = colorStr;
    std::transform(s.begin(), s.end(), s.begin(), [](unsigned char c) {
        return (char)std::tolower(c);
    });
    
    if (s == "blue") {
        baseColor = Gdiplus::Color(200, 30, 144, 255);
    } else if (s == "red") {
        baseColor = Gdiplus::Color(200, 220, 20, 60);
    } else if (s == "green") {
        baseColor = Gdiplus::Color(200, 34, 139, 34);
    } else if (s == "gray" || s == "grey") {
        baseColor = Gdiplus::Color(200, 100, 100, 100);
    } else if (s == "white") {
        baseColor = Gdiplus::Color(200, 240, 240, 240);
    } else if (s == "black") {
        baseColor = Gdiplus::Color(200, 10, 10, 10);
    } else {
        size_t startOffset = 0;
        if (s.rfind("0x", 0) == 0 || s.rfind("0X", 0) == 0) {
            startOffset = 2;
        } else if (s.rfind("#", 0) == 0) {
            startOffset = 1;
        }
        std::string hexPart = s.substr(startOffset);
        if (!hexPart.empty()) {
            try {
                unsigned long val = std::stoul(hexPart, nullptr, 16);
                if (hexPart.length() <= 6) {
                    BYTE r = (val >> 16) & 0xFF;
                    BYTE g = (val >> 8) & 0xFF;
                    BYTE b = val & 0xFF;
                    baseColor = Gdiplus::Color(200, r, g, b);
                } else {
                    BYTE a = (val >> 24) & 0xFF;
                    BYTE r = (val >> 16) & 0xFF;
                    BYTE g = (val >> 8) & 0xFF;
                    BYTE b = val & 0xFF;
                    baseColor = Gdiplus::Color(a, r, g, b);
                }
            } catch (...) {
                // keep default
            }
        }
    }
    
    if (isHovered) {
        int a = baseColor.GetA() + 30; if (a > 255) a = 255;
        int r = baseColor.GetR() + 60; if (r > 255) r = 255;
        int g = baseColor.GetG() + 60; if (g > 255) g = 255;
        int b = baseColor.GetB() + 60; if (b > 255) b = 255;
        return Gdiplus::Color((BYTE)a, (BYTE)r, (BYTE)g, (BYTE)b);
    }
    
    return baseColor;
}

static void RedrawRadialMenu(HWND hWnd, int hoveredSector) {
    RECT rect;
    GetWindowRect(hWnd, &rect);
    int width = rect.right - rect.left;
    int height = rect.bottom - rect.top;

    HDC hdcScreen = GetDC(NULL);
    HDC hdcMem = CreateCompatibleDC(hdcScreen);

    BITMAPINFO bmi = {};
    bmi.bmiHeader.biSize = sizeof(BITMAPINFOHEADER);
    bmi.bmiHeader.biWidth = width;
    bmi.bmiHeader.biHeight = -height; // Top-down
    bmi.bmiHeader.biPlanes = 1;
    bmi.bmiHeader.biBitCount = 32;
    bmi.bmiHeader.biCompression = BI_RGB;

    void* pvBits = nullptr;
    HBITMAP hBitmap = CreateDIBSection(NULL, &bmi, DIB_RGB_COLORS, &pvBits, NULL, 0);
    HBITMAP hOldBitmap = (HBITMAP)SelectObject(hdcMem, hBitmap);

    {
        Gdiplus::Graphics graphics(hdcMem);
        graphics.SetSmoothingMode(Gdiplus::SmoothingModeAntiAlias);
        graphics.SetTextRenderingHint(Gdiplus::TextRenderingHintAntiAliasGridFit);

        graphics.Clear(Gdiplus::Color(0, 0, 0, 0));

        float cx = width / 2.0f;
        float cy = height / 2.0f;
        float R_outer = (width / 2.0f) - 10.0f;
        float R_inner = 60.0f;

        std::vector<SlotConfig> slots = g_configStore.GetSlotsAtPath(GetCurrentMenuPath());
        int N = (int)slots.size();
        if (N == 0) {
            // clear dc and return
        } else {
        double sweep_angle = 360.0 / N;
        for (int k = 0; k < N; ++k) {
            bool isHovered = (k == hoveredSector);
            std::string colorStr = "gray";
            std::string labelStr = "";
            bool isEnabled = true;
            if (k < (int)slots.size()) {
                colorStr = slots[k].color;
                labelStr = slots[k].label;
                isEnabled = slots[k].enabled;
            }

            Gdiplus::Color sliceColor = ParseColorString(colorStr, isHovered);
            if (!isEnabled) {
                sliceColor = Gdiplus::Color(25, sliceColor.GetR(), sliceColor.GetG(), sliceColor.GetB());
            }
            Gdiplus::SolidBrush brush(sliceColor);

            double start_angle = k * sweep_angle - 90.0 - (sweep_angle / 2.0);

            Gdiplus::GraphicsPath path;
            path.AddArc(cx - R_outer, cy - R_outer, 2.0f * R_outer, 2.0f * R_outer, (float)start_angle, (float)sweep_angle);
            path.AddArc(cx - R_inner, cy - R_inner, 2.0f * R_inner, 2.0f * R_inner, (float)start_angle + (float)sweep_angle, -(float)sweep_angle);
            path.CloseFigure();

            graphics.FillPath(&brush, &path);

            // Draw thin outline
            Gdiplus::Pen pen(Gdiplus::Color(255, 40, 40, 40), 1.5f);
            graphics.DrawPath(&pen, &path);

            if (!labelStr.empty()) {
                double theta_deg = k * sweep_angle;
                double theta_rad = theta_deg * 3.14159265358979323846 / 180.0;
                float R_text = (R_outer + R_inner) / 2.0f;
                float tx = cx + R_text * (float)std::sin(theta_rad);
                float ty = cy - R_text * (float)std::cos(theta_rad);

                Gdiplus::StringFormat format;
                format.SetAlignment(Gdiplus::StringAlignmentCenter);
                format.SetLineAlignment(Gdiplus::StringAlignmentCenter);

                Gdiplus::Font font(L"Segoe UI", 11.0f, Gdiplus::FontStyleBold);
                Gdiplus::SolidBrush textBrush(Gdiplus::Color(255, 255, 255, 255));

                std::wstring wlabel;
                wlabel.assign(labelStr.begin(), labelStr.end());

                Gdiplus::PointF point(tx, ty);
                graphics.DrawString(wlabel.c_str(), -1, &font, point, &format, &textBrush);
            }
        }
        }
    }

    POINT ptDest = { rect.left, rect.top };
    SIZE size = { width, height };
    POINT ptSrc = { 0, 0 };
    BLENDFUNCTION blend = {};
    blend.BlendOp = AC_SRC_OVER;
    blend.AlphaFormat = AC_SRC_ALPHA;
    blend.SourceConstantAlpha = 255;

    UpdateLayeredWindow(hWnd, hdcScreen, &ptDest, &size, hdcMem, &ptSrc, 0, &blend, ULW_ALPHA);

    SelectObject(hdcMem, hOldBitmap);
    DeleteObject(hBitmap);
    DeleteDC(hdcMem);
    ReleaseDC(NULL, hdcScreen);
}

LRESULT CALLBACK RadialMenuWndProc(HWND hWnd, UINT message, WPARAM wParam, LPARAM lParam) {
    switch (message) {
    case WM_CREATE: {
        SetWindowLongPtrW(hWnd, GWLP_USERDATA, (LONG_PTR)-1);
        SetTimer(hWnd, 1, 16, NULL);
        RedrawRadialMenu(hWnd, -1);
        break;
    }
    case WM_TIMER: {
        if (wParam == 1) {
            if (g_configStore.GetGlobal().interaction_mode == "rotary") {
                break;
            }
            POINT pt;
            if (GetCursorPos(&pt)) {
                RECT rect;
                GetWindowRect(hWnd, &rect);
                int cx = (rect.left + rect.right) / 2;
                int cy = (rect.top + rect.bottom) / 2;

                double dx = pt.x - cx;
                double dy = cy - pt.y;

                double dist = std::sqrt(dx * dx + dy * dy);
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
                }

                int currentHovered = (int)GetWindowLongPtrW(hWnd, GWLP_USERDATA);
                if (hovered != currentHovered) {
                    SetWindowLongPtrW(hWnd, GWLP_USERDATA, hovered);
                    RedrawRadialMenu(hWnd, hovered);
                    if (hovered != -1 && g_configStore.GetGlobal().enable_haptic_sound) {
                        PlaySoundW(L"resources\\sounds\\tick.wav", NULL, SND_FILENAME | SND_ASYNC | SND_NODEFAULT);
                    }
                }
            }
        }
        break;
    }
    case WM_DESTROY: {
        KillTimer(hWnd, 1);
        break;
    }
    default:
        return DefWindowProcW(hWnd, message, wParam, lParam);
    }
    return 0;
}

bool RegisterRadialMenuClass(HINSTANCE hInstance) {
    WNDCLASSEXW wcex = {};
    wcex.cbSize = sizeof(WNDCLASSEXW);
    wcex.style = CS_HREDRAW | CS_VREDRAW;
    wcex.lpfnWndProc = RadialMenuWndProc;
    wcex.hInstance = hInstance;
    wcex.hCursor = LoadCursorW(NULL, (LPCWSTR)IDC_ARROW);
    wcex.hbrBackground = NULL;
    wcex.lpszClassName = L"KnobLaunchRadialMenu";
    
    return RegisterClassExW(&wcex) != 0;
}

HWND CreateRadialMenu(HWND hParentWnd) {
    POINT pt;
    GetCursorPos(&pt);

    int width = 400;
    int height = 400;

    std::string sz = g_configStore.GetGlobal().radial_size;
    if (sz == "small") {
        width = height = 300;
    } else if (sz == "large") {
        width = height = 500;
    }

    int x = pt.x - width / 2;
    int y = pt.y - height / 2;

    HWND hWnd = CreateWindowExW(
        WS_EX_TOPMOST | WS_EX_LAYERED | WS_EX_NOACTIVATE,
        L"KnobLaunchRadialMenu",
        L"KnobLaunchRadialMenuWindow",
        WS_POPUP | WS_VISIBLE,
        x, y, width, height,
        hParentWnd, NULL, GetModuleHandle(NULL), NULL
    );

    if (!hWnd) {
        return NULL;
    }

    ShowWindow(hWnd, SW_SHOWNOACTIVATE);
    UpdateWindow(hWnd);

    RECT rect;
    if (GetWindowRect(hWnd, &rect)) {
        int cx = (rect.left + rect.right) / 2;
        int cy = (rect.top + rect.bottom) / 2;
        SetCursorPos(cx, cy);
    }

    return hWnd;
}

void RadialMenuSetHovered(HWND hWnd, int sector) {
    if (hWnd) {
        SetWindowLongPtrW(hWnd, GWLP_USERDATA, sector);
        RedrawRadialMenu(hWnd, sector);
    }
}

