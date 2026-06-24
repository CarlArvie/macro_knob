import os

cpp_path = r"c:\Users\carla\Desktop\AHK\Arvie Knob Macro\src\macro_runner.cpp"
with open(cpp_path, "r", encoding="utf-8") as f:
    cpp = f.read()

find_func = """static void ForceForegroundRights() {
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
}"""

replace_func = """static void ForceForegroundRights() {
    // Simulate a dummy ALT keystroke. ALT is explicitly handled by Windows to release the foreground lock.
    INPUT inputs[2] = {};
    inputs[0].type = INPUT_KEYBOARD;
    inputs[0].ki.wVk = VK_MENU;
    inputs[1].type = INPUT_KEYBOARD;
    inputs[1].ki.wVk = VK_MENU;
    inputs[1].ki.dwFlags = KEYEVENTF_KEYUP;
    SendInput(2, inputs, sizeof(INPUT));

    HWND hForeground = GetForegroundWindow();
    if (hForeground) {
        DWORD fgThread = GetWindowThreadProcessId(hForeground, NULL);
        DWORD myThread = GetCurrentThreadId();
        if (fgThread != myThread) {
            AttachThreadInput(myThread, fgThread, TRUE);
            AllowSetForegroundWindow(ASFW_ANY);
            BringWindowToTop(hForeground); // Give it a nudge
            AttachThreadInput(myThread, fgThread, FALSE);
        }
    }
    AllowSetForegroundWindow(ASFW_ANY);
}"""

if find_func in cpp:
    cpp = cpp.replace(find_func, replace_func)
    with open(cpp_path, "w", encoding="utf-8") as f:
        f.write(cpp)
    print("Patched ForceForegroundRights with VK_MENU!")
else:
    print("Could not find ForceForegroundRights")
