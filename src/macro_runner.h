#pragma once
#include <string>

bool RunProgram(const std::string& path, const std::string& args = "", bool runAsAdmin = false);
bool OpenURL(const std::string& url);
bool RunAHKScript(const std::string& scriptPath);
