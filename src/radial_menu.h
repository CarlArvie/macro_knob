#pragma once
#include <windows.h>

// Registers the KnobLaunchRadialMenu window class
bool RegisterRadialMenuClass(HINSTANCE hInstance);

// Creates and displays the radial menu centered on mouse cursor
HWND CreateRadialMenu(HWND hParentWnd);
