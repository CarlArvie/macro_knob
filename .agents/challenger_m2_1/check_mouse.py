import ctypes
import time

class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

pt = POINT()
ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
print(f"Original pos: {pt.x}, {pt.y}")

ret = ctypes.windll.user32.SetCursorPos(pt.x + 100, pt.y + 100)
print(f"SetCursorPos ret: {ret}, err: {ctypes.windll.kernel32.GetLastError()}")

pt2 = POINT()
ctypes.windll.user32.GetCursorPos(ctypes.byref(pt2))
print(f"New pos: {pt2.x}, {pt2.y}")
