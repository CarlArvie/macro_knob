import ctypes
import time

class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", ctypes.c_ushort),
        ("wScan", ctypes.c_ushort),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ctypes.c_void_p)
    ]

class INPUT_UNION(ctypes.Union):
    _fields_ = [
        ("ki", KEYBDINPUT)
    ]

class INPUT(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.c_ulong),
        ("union", INPUT_UNION)
    ]

User32 = ctypes.windll.user32
User32.SendInput.argtypes = [ctypes.c_uint, ctypes.POINTER(INPUT), ctypes.c_int]
User32.SendInput.restype = ctypes.c_uint

ki = KEYBDINPUT(wVk=0xAD, wScan=0, dwFlags=0, time=0, dwExtraInfo=None)
inp = INPUT(type=1, union=INPUT_UNION(ki=ki))

ret = User32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))
err = ctypes.windll.kernel32.GetLastError()
print(f"SendInput return value: {ret}, GetLastError: {err}")
