@echo off
set "WindowsSdkDir=C:\Program Files (x86)\Windows Kits\10"
set "WindowsSDKVersion=10.0.26100.0"
call "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvarsall.bat" x64
bin\knoblaunch.exe
echo Exit code is %errorlevel%
