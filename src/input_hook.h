#pragma once
#include <windows.h>

#define TIMER_ID_HOLD 1
#define WM_HOLD_TIMER (WM_USER + 2)

bool StartInputHook(HWND hDaemonWnd);
void StopInputHook();
void UpdateHookConfig();
void EnableInputHook(bool enable);
bool IsInputHookEnabled();
void HandleHoldTimer(WPARAM wParam);
