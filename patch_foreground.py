import os

cpp_path = r"c:\Users\carla\Desktop\AHK\Arvie Knob Macro\src\macro_runner.cpp"
with open(cpp_path, "r", encoding="utf-8") as f:
    cpp = f.read()

force_func = """static void ForceForegroundRights() {
    // Simulate a dummy keystroke (F24) to trick Windows into treating this thread as the active input thread.
    // This allows AllowSetForegroundWindow to successfully grant foreground rights to spawned processes.
    INPUT input = {0};
    input.type = INPUT_KEYBOARD;
    input.ki.wVk = 0x87; // VK_F24
    SendInput(1, &input, sizeof(INPUT));
    input.ki.dwFlags = KEYEVENTF_KEYUP;
    SendInput(1, &input, sizeof(INPUT));

    // Also attempt thread attachment
    HWND hForeground = GetForegroundWindow();
    if (hForeground) {
        DWORD fgThread = GetWindowThreadProcessId(hForeground, NULL);
        DWORD myThread = GetCurrentThreadId();
        if (fgThread != myThread) {
            AttachThreadInput(myThread, fgThread, TRUE);
            AllowSetForegroundWindow(ASFW_ANY);
            AttachThreadInput(myThread, fgThread, FALSE);
            return;
        }
    }
    AllowSetForegroundWindow(ASFW_ANY);
}

static void MonitorProcess(HANDLE hProcess, const std::string& processName) {"""

cpp = cpp.replace("static void MonitorProcess(HANDLE hProcess, const std::string& processName) {", force_func)

cpp = cpp.replace("AllowSetForegroundWindow(ASFW_ANY);", "ForceForegroundRights();")

with open(cpp_path, "w", encoding="utf-8") as f:
    f.write(cpp)
print("Patched macro_runner.cpp with ForceForegroundRights!")
