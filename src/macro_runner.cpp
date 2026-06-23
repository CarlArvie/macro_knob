#include "macro_runner.h"
#include <windows.h>
#include <shellapi.h>
#include <string>
#include <thread>
#include <mutex>
#include <fstream>
#include <ctime>
#include <algorithm>

static HANDLE g_hJob = NULL;
static std::mutex g_jobMtx;

static void LogMessage(const std::string& msg) {
    std::ofstream ofs("tests/daemon.log", std::ios::app);
    if (ofs.is_open()) {
        std::time_t t = std::time(nullptr);
        char timestamp[30];
        struct tm timeinfo;
        localtime_s(&timeinfo, &t);
        std::strftime(timestamp, sizeof(timestamp), "%Y-%m-%d %H:%M:%S", &timeinfo);
        ofs << "[" << timestamp << "] [PID:" << GetCurrentProcessId() << "] " << msg << std::endl;
    }
}

static void EnsureJobInitialized() {
    std::lock_guard<std::mutex> lock(g_jobMtx);
    if (g_hJob == NULL) {
        g_hJob = CreateJobObjectW(NULL, NULL);
        if (g_hJob != NULL) {
            JOBOBJECT_EXTENDED_LIMIT_INFORMATION jeli = {};
            jeli.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;
            SetInformationJobObject(g_hJob, JobObjectExtendedLimitInformation, &jeli, sizeof(jeli));
        }
    }
}

static std::wstring Utf8ToUtf16(const std::string& utf8Str) {
    if (utf8Str.empty()) return std::wstring();
    int sizeNeeded = MultiByteToWideChar(CP_UTF8, 0, utf8Str.c_str(), (int)utf8Str.size(), NULL, 0);
    std::wstring wstr(sizeNeeded, 0);
    MultiByteToWideChar(CP_UTF8, 0, utf8Str.c_str(), (int)utf8Str.size(), &wstr[0], sizeNeeded);
    return wstr;
}

static std::wstring GetWorkspaceRoot() {
    wchar_t exePath[MAX_PATH];
    if (GetModuleFileNameW(NULL, exePath, MAX_PATH) == 0) {
        return L"";
    }
    std::wstring pathStr(exePath);
    size_t lastSlash = pathStr.find_last_of(L"\\/");
    if (lastSlash == std::wstring::npos) {
        return L"";
    }
    std::wstring exeDir = pathStr.substr(0, lastSlash);
    
    if (exeDir.length() >= 3 && _wcsicmp(exeDir.substr(exeDir.length() - 3).c_str(), L"bin") == 0) {
        return exeDir.substr(0, exeDir.length() - 3);
    }
    if (exeDir.length() >= 4 && (_wcsicmp(exeDir.substr(exeDir.length() - 4).c_str(), L"bin\\") == 0 ||
                                 _wcsicmp(exeDir.substr(exeDir.length() - 4).c_str(), L"bin/") == 0)) {
        return exeDir.substr(0, exeDir.length() - 4);
    }
    size_t buildDebugIdx = exeDir.rfind(L"\\build\\Debug");
    if (buildDebugIdx != std::wstring::npos) {
        return exeDir.substr(0, buildDebugIdx);
    }
    size_t buildIdx = exeDir.rfind(L"\\build");
    if (buildIdx != std::wstring::npos) {
        return exeDir.substr(0, buildIdx);
    }
    return exeDir + L"\\";
}

static bool IsAbsolutePath(const std::wstring& path) {
    if (path.length() >= 2 && iswalpha(path[0]) && path[1] == L':') {
        return true;
    }
    if (path.length() >= 2 && path[0] == L'\\' && path[1] == L'\\') {
        return true;
    }
    return false;
}

static bool ShouldPrependWorkspaceRoot(const std::wstring& path) {
    if (IsAbsolutePath(path)) return false;
    if (path.find(L'\\') == std::wstring::npos && path.find(L'/') == std::wstring::npos) {
        return false;
    }
    return true;
}

static std::wstring ResolvePath(const std::string& pathUtf8) {
    std::wstring wpath = Utf8ToUtf16(pathUtf8);
    if (!ShouldPrependWorkspaceRoot(wpath)) {
        return wpath;
    }
    std::wstring root = GetWorkspaceRoot();
    if (root.empty()) return wpath;
    
    if (root.back() != L'\\' && root.back() != L'/') {
        root += L'\\';
    }
    size_t start = 0;
    while (start < wpath.length() && (wpath[start] == L'\\' || wpath[start] == L'/')) {
        start++;
    }
    return root + wpath.substr(start);
}

static std::wstring FindAutoHotkeyExe() {
    wchar_t exePath[MAX_PATH];
    if (GetModuleFileNameW(NULL, exePath, MAX_PATH) == 0) {
        return L"";
    }
    std::wstring pathStr(exePath);
    size_t lastSlash = pathStr.find_last_of(L"\\/");
    if (lastSlash == std::wstring::npos) {
        return L"";
    }
    std::wstring exeDir = pathStr.substr(0, lastSlash);

    std::wstring cand1 = exeDir + L"\\AutoHotkey64.exe";
    if (GetFileAttributesW(cand1.c_str()) != INVALID_FILE_ATTRIBUTES) {
        return cand1;
    }
    
    std::wstring cand2 = exeDir + L"\\bin\\AutoHotkey64.exe";
    if (GetFileAttributesW(cand2.c_str()) != INVALID_FILE_ATTRIBUTES) {
        return cand2;
    }

    std::wstring cand3 = exeDir + L"\\..\\..\\bin\\AutoHotkey64.exe";
    if (GetFileAttributesW(cand3.c_str()) != INVALID_FILE_ATTRIBUTES) {
        return cand3;
    }

    return L"bin\\AutoHotkey64.exe";
}

static void MonitorProcess(HANDLE hProcess, const std::string& processName) {
    std::thread t([hProcess, processName]() {
        WaitForSingleObject(hProcess, INFINITE);
        DWORD exitCode = 0;
        if (GetExitCodeProcess(hProcess, &exitCode)) {
            LogMessage("Process " + processName + " exited with code " + std::to_string(exitCode));
        } else {
            LogMessage("Failed to get exit code for process " + processName);
        }
        CloseHandle(hProcess);
    });
    t.detach();
}

bool RunProgram(const std::string& path, const std::string& args, bool runAsAdmin) {
    std::wstring wpath = ResolvePath(path);
    
    // Check if path is a directory, if so, open it with ShellExecute natively
    DWORD dwAttrib = GetFileAttributesW(wpath.c_str());
    if (dwAttrib != INVALID_FILE_ATTRIBUTES && (dwAttrib & FILE_ATTRIBUTE_DIRECTORY)) {
        LogMessage("RunProgram: Path is a directory, redirecting to ShellExecuteW natively.");
        HINSTANCE hInst = ShellExecuteW(NULL, L"open", wpath.c_str(), NULL, NULL, SW_SHOWNORMAL);
        return ((intptr_t)hInst > 32);
    }

    if (runAsAdmin) {
        SHELLEXECUTEINFOW sei = {};
        sei.cbSize = sizeof(sei);
        sei.fMask = SEE_MASK_NOCLOSEPROCESS | SEE_MASK_FLAG_NO_UI;
        sei.lpVerb = L"runas";
        sei.lpFile = wpath.c_str();
        std::wstring wargs = Utf8ToUtf16(args);
        if (!wargs.empty()) {
            sei.lpParameters = wargs.c_str();
        }
        sei.nShow = SW_SHOWNORMAL;
        
        if (ShellExecuteExW(&sei)) {
            if (sei.hProcess != NULL) {
                EnsureJobInitialized();
                if (g_hJob != NULL) {
                    AssignProcessToJobObject(g_hJob, sei.hProcess);
                }
                MonitorProcess(sei.hProcess, path);
            }
            return true;
        } else {
            DWORD err = GetLastError();
            LogMessage("ShellExecuteExW failed for " + path + " with error " + std::to_string(err));
            return false;
        }
    } else {
        STARTUPINFOW si = {};
        si.cb = sizeof(si);
        PROCESS_INFORMATION pi = {};
        
        std::wstring wargs = Utf8ToUtf16(args);
        
        std::wstring cmdLine = L"\"" + wpath + L"\"";
        if (!wargs.empty()) {
            cmdLine += L" " + wargs;
        }
        
        EnsureJobInitialized();
        
        if (CreateProcessW(
            NULL,
            &cmdLine[0],
            NULL, NULL, FALSE,
            0,
            NULL, NULL, &si, &pi
        )) {
            if (g_hJob != NULL) {
                AssignProcessToJobObject(g_hJob, pi.hProcess);
            }
            MonitorProcess(pi.hProcess, path);
            CloseHandle(pi.hThread);
            return true;
        } else {
            DWORD err = GetLastError();
            LogMessage("CreateProcessW failed for " + path + " with error " + std::to_string(err));
            return false;
        }
    }
}

bool OpenURL(const std::string& url) {
    LogMessage("Opening URL: " + url);
    std::wstring wurl = Utf8ToUtf16(url);
    HINSTANCE hInst = ShellExecuteW(NULL, L"open", wurl.c_str(), NULL, NULL, SW_SHOWNORMAL);
    if ((intptr_t)hInst > 32) {
        return true;
    } else {
        LogMessage("ShellExecuteW failed for URL: " + url + " with error " + std::to_string((intptr_t)hInst));
        return false;
    }
}

bool RunAHKScript(const std::string& scriptPath) {
    std::wstring ahkExe = FindAutoHotkeyExe();
    std::wstring resolvedScript = ResolvePath(scriptPath);
    
    if (GetFileAttributesW(resolvedScript.c_str()) == INVALID_FILE_ATTRIBUTES) {
        LogMessage("AHK script file not found: " + scriptPath);
        return false;
    }
    
    std::wstring cmdLine = L"\"" + ahkExe + L"\" \"" + resolvedScript + L"\"";
    
    STARTUPINFOW si = {};
    si.cb = sizeof(si);
    PROCESS_INFORMATION pi = {};
    
    EnsureJobInitialized();
    
    if (CreateProcessW(
        NULL,
        &cmdLine[0],
        NULL, NULL, FALSE,
        0,
        NULL, NULL, &si, &pi
    )) {
        if (g_hJob != NULL) {
            AssignProcessToJobObject(g_hJob, pi.hProcess);
        }
        
        std::thread t([hProcess = pi.hProcess, scriptPath]() {
            WaitForSingleObject(hProcess, INFINITE);
            DWORD exitCode = 0;
            if (GetExitCodeProcess(hProcess, &exitCode)) {
                if (exitCode != 0) {
                    LogMessage("AHK script " + scriptPath + " failed with exit code " + std::to_string(exitCode));
                } else {
                    LogMessage("AHK script " + scriptPath + " finished successfully");
                }
            } else {
                LogMessage("Failed to get exit code for AHK script " + scriptPath);
            }
            CloseHandle(hProcess);
        });
        t.detach();
        
        CloseHandle(pi.hThread);
        return true;
    } else {
        DWORD err = GetLastError();
        LogMessage("Failed to execute AHK script: " + scriptPath + " using AutoHotkey64.exe error: " + std::to_string(err));
        return false;
    }
}

