import os

cpp_path = r"c:\Users\carla\Desktop\AHK\Arvie Knob Macro\src\macro_runner.cpp"
with open(cpp_path, "r", encoding="utf-8") as f:
    cpp = f.read()

find_open = """bool OpenURL(const std::string& url) {
    LogMessage("Opening URL: " + url);
    std::wstring wurl = Utf8ToUtf16(url);
    HINSTANCE hInst = ShellExecuteW(NULL, L"open", wurl.c_str(), NULL, NULL, SW_SHOWNORMAL);"""

replace_open = """bool OpenURL(const std::string& url) {
    LogMessage("Opening URL: " + url);
    std::wstring wurl = Utf8ToUtf16(url);
    AllowSetForegroundWindow(ASFW_ANY);
    HINSTANCE hInst = ShellExecuteW(NULL, L"open", wurl.c_str(), NULL, NULL, SW_SHOWNORMAL);"""

if find_open in cpp:
    cpp = cpp.replace(find_open, replace_open)

find_run = """    if (dwAttrib != INVALID_FILE_ATTRIBUTES && (dwAttrib & FILE_ATTRIBUTE_DIRECTORY)) {
        LogMessage("RunProgram: Path is a directory, redirecting to ShellExecuteW natively.");
        HINSTANCE hInst = ShellExecuteW(NULL, L"open", wpath.c_str(), NULL, NULL, SW_SHOWNORMAL);"""

replace_run = """    if (dwAttrib != INVALID_FILE_ATTRIBUTES && (dwAttrib & FILE_ATTRIBUTE_DIRECTORY)) {
        LogMessage("RunProgram: Path is a directory, redirecting to ShellExecuteW natively.");
        AllowSetForegroundWindow(ASFW_ANY);
        HINSTANCE hInst = ShellExecuteW(NULL, L"open", wpath.c_str(), NULL, NULL, SW_SHOWNORMAL);"""

if find_run in cpp:
    cpp = cpp.replace(find_run, replace_run)

find_run2 = """    if (runAsAdmin) {
        SHELLEXECUTEINFOW sei = {};"""

replace_run2 = """    AllowSetForegroundWindow(ASFW_ANY);
    if (runAsAdmin) {
        SHELLEXECUTEINFOW sei = {};"""

if find_run2 in cpp:
    cpp = cpp.replace(find_run2, replace_run2)

with open(cpp_path, "w", encoding="utf-8") as f:
    f.write(cpp)
print("Patched macro_runner.cpp with ASFW_ANY!")
