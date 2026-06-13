@echo off
set "WindowsSdkDir=C:\Program Files (x86)\Windows Kits\10"
set "WindowsSDKVersion=10.0.26100.0"
call "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvarsall.bat" x64
if %errorlevel% neq 0 (
    echo Failed to initialize vcvarsall.bat
    exit /b 1
)
cmake --build build --config Debug
if %errorlevel% neq 0 (
    echo CMake build failed
    exit /b %errorlevel%
)
echo CMake build successful
exit /b 0
