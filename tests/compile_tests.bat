@echo off
set "WindowsSdkDir=C:\Program Files (x86)\Windows Kits\10"
set "WindowsSDKVersion=10.0.26100.0"
call "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvarsall.bat" x64
if %errorlevel% neq 0 (
    echo Failed to initialize vcvarsall.bat
    exit /b 1
)
cl.exe /EHsc /std:c++17 tests/config_store_tests.cpp src/config_store.cpp /Iinclude /Isrc /link user32.lib shell32.lib shlwapi.lib /out:bin/config_store_tests.exe
if %errorlevel% neq 0 (
    echo Compilation of config_store_tests failed
    exit /b %errorlevel%
)
cl.exe /EHsc /std:c++17 tests/diagnostic.cpp /link user32.lib gdiplus.lib /out:bin/diagnostic.exe
if %errorlevel% neq 0 (
    echo Compilation of diagnostic failed
    exit /b %errorlevel%
)
echo Compilation successful
exit /b 0
