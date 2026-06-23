import ctypes

def enum_windows():
    hwnds = []
    def callback(hwnd, param):
        hwnds.append(hwnd)
        return True
    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))
    ctypes.windll.user32.EnumWindows(EnumWindowsProc(callback), 0)
    
    for hwnd in hwnds:
        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        buff = ctypes.create_unicode_buffer(length + 1)
        ctypes.windll.user32.GetWindowTextW(hwnd, buff, length + 1)
        if "Knob" in buff.value:
            print("Found:", buff.value, hwnd)
            ctypes.windll.user32.PostMessageW(hwnd, 0x0111, 40003, 0)
            print("Message sent")

enum_windows()
