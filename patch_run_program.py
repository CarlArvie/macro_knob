import os

cpp_path = r"c:\Users\carla\Desktop\AHK\Arvie Knob Macro\src\macro_runner.cpp"
with open(cpp_path, "r", encoding="utf-8") as f:
    cpp = f.read()

find_rp = """bool RunProgram(const std::string& path, const std::string& args, bool runAsAdmin) {
    LogMessage("Running program: " + path + " with args: " + args);
    
    std::wstring wpath = Utf8ToUtf16(path);"""

replace_rp = """bool RunProgram(const std::string& path, const std::string& args, bool runAsAdmin) {
    LogMessage("Running program: " + path + " with args: " + args);
    
    std::wstring wpath = Utf8ToUtf16(path);
    
    // Check if path is a directory or an existing file that should be opened by default handler
    DWORD dwAttrib = GetFileAttributesW(wpath.c_str());
    if (dwAttrib != INVALID_FILE_ATTRIBUTES && (dwAttrib & FILE_ATTRIBUTE_DIRECTORY)) {
        LogMessage("Path is a directory, using ShellExecuteW instead.");
        HINSTANCE hInst = ShellExecuteW(NULL, L"open", wpath.c_str(), NULL, NULL, SW_SHOWNORMAL);
        return ((intptr_t)hInst > 32);
    }
    """

if find_rp in cpp:
    cpp = cpp.replace(find_rp, replace_rp)
    with open(cpp_path, "w", encoding="utf-8") as f:
        f.write(cpp)
    print("Patched RunProgram to handle directories!")
else:
    print("Could not find RunProgram in macro_runner.cpp")
