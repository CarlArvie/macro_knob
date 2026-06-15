import ctypes

User32 = ctypes.windll.user32
hwnd = User32.GetForegroundWindow()
title = ctypes.create_unicode_buffer(512)
class_name = ctypes.create_unicode_buffer(512)

User32.GetWindowTextW(hwnd, title, 512)
User32.GetClassNameW(hwnd, class_name, 512)

print(f"Foreground Window HWND: {hwnd}")
print(f"Title: {title.value}")
print(f"Class Name: {class_name.value}")
