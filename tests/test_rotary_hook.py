import ctypes
import os
import time
import subprocess
import json
import shutil
import sys

# --- Ctypes structures for Keyboard Simulation ---

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", ctypes.c_long),
        ("dy", ctypes.c_long),
        ("mouseData", ctypes.c_ulong),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ctypes.c_void_p)
    ]

class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", ctypes.c_ushort),
        ("wScan", ctypes.c_ushort),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ctypes.c_void_p)
    ]

class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", ctypes.c_ulong),
        ("wParamL", ctypes.c_ushort),
        ("wParamH", ctypes.c_ushort)
    ]

class INPUT_UNION(ctypes.Union):
    _fields_ = [
        ("mi", MOUSEINPUT),
        ("ki", KEYBDINPUT),
        ("hi", HARDWAREINPUT)
    ]

class INPUT(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.c_ulong),
        ("union", INPUT_UNION)
    ]

User32 = ctypes.windll.user32
User32.SendInput.argtypes = [ctypes.c_uint, ctypes.POINTER(INPUT), ctypes.c_int]
User32.SendInput.restype = ctypes.c_uint

User32.MapVirtualKeyW.argtypes = [ctypes.c_uint, ctypes.c_uint]
User32.MapVirtualKeyW.restype = ctypes.c_uint

User32.FindWindowW.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p]
User32.FindWindowW.restype = ctypes.c_void_p

User32.IsWindowVisible.argtypes = [ctypes.c_void_p]
User32.IsWindowVisible.restype = ctypes.c_int

INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_EXTENDEDKEY = 0x0001

VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF
VK_PRIOR = 0x21  # PgUp

def send_key(vk, is_down):
    scan_code = User32.MapVirtualKeyW(vk, 0)
    if scan_code == 0:
        if vk == VK_VOLUME_DOWN:
            scan_code = 0x30
        elif vk == VK_VOLUME_UP:
            scan_code = 0x30
        elif vk == VK_PRIOR:
            scan_code = 0x49
    
    dwFlags = 0
    if not is_down:
        dwFlags |= KEYEVENTF_KEYUP
    if vk in [VK_VOLUME_DOWN, VK_VOLUME_UP]:
        dwFlags |= KEYEVENTF_EXTENDEDKEY
        
    ki = KEYBDINPUT(
        wVk=vk,
        wScan=scan_code,
        dwFlags=dwFlags,
        time=0,
        dwExtraInfo=None
    )
    inp = INPUT(
        type=INPUT_KEYBOARD,
        union=INPUT_UNION(ki=ki)
    )
    ret = User32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))
    if ret == 0:
        print(f"SendInput FAILED for vk: {vk}, error: {ctypes.windll.kernel32.GetLastError()}")

def press_and_release_key(vk):
    send_key(vk, is_down=True)
    time.sleep(0.05)
    send_key(vk, is_down=False)
    time.sleep(0.05)

def get_system_volume(workspace_dir):
    query_exe = os.path.join(workspace_dir, "bin", "query_volume.exe")
    if not os.path.exists(query_exe):
        raise FileNotFoundError(f"query_volume.exe not found at {query_exe}")
    result = subprocess.run([query_exe], capture_output=True, text=True, check=True)
    return float(result.stdout.strip())

def main():
    print("Starting Rotary Hook Standalone Test...")
    workspace_dir = r"c:\Users\carla\Desktop\AHK\Arvie Knob Macro"
    config_dir = os.path.join(workspace_dir, "config")
    config_path = os.path.join(config_dir, "config.json")
    backup_path = os.path.join(config_dir, "config.json.bak")
    macro_file = os.path.join(workspace_dir, "tests", "macro_fired.txt")

    # 1. Back up config
    if os.path.exists(config_path):
        shutil.copy2(config_path, backup_path)
        print("Backed up existing config.")

    # Clean up macro file if it exists
    if os.path.exists(macro_file):
        os.remove(macro_file)

    slots = []
    for i in range(8):
        slots.append({
            "index": i,
            "label": f"Slot {i}",
            "icon": "",
            "color": "blue",
            "type": "run_program",
            "config": {
                "path": "C:\\Windows\\System32\\cmd.exe",
                "args": f'/c echo fired > "{macro_file}"'
            }
        })
    test_config = {
        "global": {
            "hold_threshold_ms": 150,
            "radial_size": "medium",
            "hotkey_override": "PgUp",
            "show_tray_icon": True,
            "debug_log": True,
            "interaction_mode": "rotary",
            "rotary_prev": "Volume_Down",
            "rotary_next": "Volume_Up"
        },
        "slots": slots
    }

    os.makedirs(config_dir, exist_ok=True)
    with open(config_path, "w") as f:
        json.dump(test_config, f, indent=4)
    print("Wrote test config.json.")

    # 3. Kill existing daemon if running
    subprocess.run(["taskkill", "/F", "/IM", "knoblaunch.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(0.5)

    daemon_process = None
    log_file = None
    try:
        # Start daemon
        daemon_exe = os.path.join(workspace_dir, "knoblaunch.exe")
        if not os.path.exists(daemon_exe):
            daemon_exe = os.path.join(workspace_dir, "bin", "knoblaunch.exe")
        if not os.path.exists(daemon_exe):
            raise FileNotFoundError(f"Daemon executable not found at {daemon_exe}")

        print(f"Launching daemon: {daemon_exe}")
        log_file = open(os.path.join(workspace_dir, "tests", "daemon.log"), "a")
        log_file.write("\n=================== ROTARY HOOK INTERACTIVE TEST ===================\n")
        log_file.flush()

        daemon_process = subprocess.Popen([daemon_exe], cwd=workspace_dir, stdout=log_file, stderr=subprocess.STDOUT)
        time.sleep(1.0) # Wait for startup and hooks to register

        # Check if daemon process is still alive
        poll_res = daemon_process.poll()
        if poll_res is not None:
            raise AssertionError(f"Daemon process died immediately with code {poll_res}!")

        # Get volume before
        vol_before = get_system_volume(workspace_dir)
        print(f"System volume before keystrokes: {vol_before}")

        # 4. Simulate Volume Down to trigger menu
        print("Simulating Volume Down (rotary_prev) to open menu...")
        press_and_release_key(VK_VOLUME_DOWN)
        time.sleep(0.5)

        # Check menu is open
        hwnd = User32.FindWindowW("KnobLaunchRadialMenu", None)
        menu_visible = bool(User32.IsWindowVisible(hwnd))
        print(f"Radial menu window visible: {menu_visible}")
        if not menu_visible:
            raise AssertionError("Radial menu did not appear after simulating Volume Down!")

        # Simulate volume adjustments while menu is open to test swallowing
        print("Simulating further volume rotations while menu is open...")
        press_and_release_key(VK_VOLUME_UP)
        press_and_release_key(VK_VOLUME_DOWN)
        press_and_release_key(VK_VOLUME_UP)
        time.sleep(0.2)

        # Get volume after
        vol_after = get_system_volume(workspace_dir)
        print(f"System volume after simulated keystrokes: {vol_after}")
        if abs(vol_before - vol_after) > 0.001:
            raise AssertionError(f"System volume level changed! Before: {vol_before}, After: {vol_after}")

        # 5. Simulate PgUp (hotkey_override / targetVk) to trigger slot 0 macro
        print("Simulating PgUp to trigger macro and close menu...")
        press_and_release_key(VK_PRIOR)
        time.sleep(0.8) # Wait for macro execution & window destroy

        # Verify macro executed
        if not os.path.exists(macro_file):
            raise AssertionError("Macro did not execute (macro_fired.txt not found)!")
        print("Macro executed successfully!")

        # Verify menu closed
        hwnd_after = User32.FindWindowW("KnobLaunchRadialMenu", None)
        menu_visible_after = bool(User32.IsWindowVisible(hwnd_after)) if hwnd_after else False
        print(f"Radial menu window visible after execute: {menu_visible_after}")
        if menu_visible_after:
            raise AssertionError("Radial menu did not close after executing macro!")
        print("Radial menu closed cleanly!")

        print("\nALL TESTS PASSED SUCCESSFULLY!")

    finally:
        # Clean up daemon
        if daemon_process:
            print("Terminating daemon...")
            daemon_process.terminate()
            try:
                daemon_process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                daemon_process.kill()
        subprocess.run(["taskkill", "/F", "/IM", "knoblaunch.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        if log_file:
            log_file.close()

        # Clean up files
        if os.path.exists(macro_file):
            os.remove(macro_file)

        # Restore config
        if os.path.exists(backup_path):
            shutil.move(backup_path, config_path)
            print("Restored original config.")
        elif os.path.exists(config_path):
            os.remove(config_path)

if __name__ == "__main__":
    try:
        main()
        sys.exit(0)
    except Exception as e:
        print(f"\nTEST FAILED: {e}", file=sys.stderr)
        sys.exit(1)
