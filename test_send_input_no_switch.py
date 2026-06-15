import sys
sys.path.append("tests")
import ctypes
import time
import tkinter as tk
from test_cases.test_base import INPUT, KEYBDINPUT, INPUT_UNION, User32

# Create Tkinter window
root = tk.Tk()
root.title("Diagnostic Focus Window")
root.geometry("100x100")
root.update()

# Force foreground
hwnd = root.winfo_id()
fore_ret = User32.SetForegroundWindow(hwnd)
print(f"SetForegroundWindow return value: {fore_ret}")
time.sleep(0.5)

# Verify foreground window
fg_hwnd = User32.GetForegroundWindow()
title = ctypes.create_unicode_buffer(512)
User32.GetWindowTextW(fg_hwnd, title, 512)
print(f"Foreground Window HWND: {fg_hwnd} (Expected: {hwnd})")
print(f"Foreground Title: {title.value}")

# Send key event using imported INPUT
ki = KEYBDINPUT(wVk=0xAD, wScan=0, dwFlags=0, time=0, dwExtraInfo=None)
inp = INPUT(type=1, union=INPUT_UNION(ki=ki))

ret = User32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))
err = ctypes.windll.kernel32.GetLastError()
print(f"SendInput return value: {ret}, GetLastError: {err}")

root.destroy()
