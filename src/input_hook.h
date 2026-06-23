#pragma once
#include <windows.h>

#define TIMER_ID_HOLD 1
#define WM_HOLD_TIMER (WM_USER + 2)
#define WM_ROTARY_TIMEOUT (WM_USER + 3)
#define WM_TRIGGER_MACRO (WM_USER + 10)

bool StartInputHook(HWND hDaemonWnd);
void StopInputHook();
void UpdateHookConfig();
void EnableInputHook(bool enable);
bool IsInputHookEnabled();
void HandleHoldTimer(WPARAM wParam);
void HandleRotaryTimeout();
void TriggerSlotMacro(int sector);

#include <vector>
std::vector<int> GetCurrentMenuPath();

