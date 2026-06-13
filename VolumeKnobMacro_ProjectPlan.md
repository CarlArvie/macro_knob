# Volume Knob Macro Tool — Full Project Plan

**Codename:** `KnobLaunch`
**Stack:** C++ (core daemon) + AutoHotkey v2 (macro engine) + Win32 API (GUI)
**Target OS:** Windows 10/11 (64-bit)
**Goal:** Lightweight, sub-5MB RAM footprint, instant response

---

## 1. Project Overview

A volume knob interceptor that opens a GTA 5-style radial circle menu on press,
allowing the user to assign and trigger macros per slice. The daemon runs in the
system tray, intercepts multimedia key events before the OS volume handler, and
spawns/destroys the overlay GUI on demand.

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   KnobLaunch System                     │
│                                                         │
│  ┌────────────┐     IPC Pipe     ┌───────────────────┐  │
│  │ C++ Daemon │◄────────────────►│  AHK Script Host  │  │
│  │  (knob.exe)│                  │ (macro_engine.ahk)│  │
│  └─────┬──────┘                  └───────────────────┘  │
│        │ Win32 Hook                                      │
│        ▼                                                 │
│  ┌─────────────┐     ┌───────────────────────────────┐  │
│  │  Input Hook │     │  Radial GUI (Win32 GDI+)      │  │
│  │  (WH_KB_LL) │────►│  GTA5-style overlay window    │  │
│  └─────────────┘     └───────────────────────────────┘  │
│        │                                                 │
│        ▼                                                 │
│  ┌─────────────┐     ┌───────────────────────────────┐  │
│  │  Config UI  │     │  JSON Config Store            │  │
│  │  (Settings) │────►│  config.json (per-slot data)  │  │
│  └─────────────┘     └───────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## 3. Technology Decisions

| Component | Technology | Reason |
|---|---|---|
| Core daemon | C++ (MSVC/MinGW) | Lowest RAM, fast hooks, system tray |
| Macro engine | AutoHotkey v2 (embedded) | Proven scripting, AHK DLL via COM |
| GUI renderer | Win32 GDI+ / Direct2D | No Electron, no Qt — pure Win32 |
| IPC | Named Pipe (`\\.\pipe\knoblaunch`) | Microsecond latency, zero overhead |
| Config store | JSON (`config.json`) | Human-readable, lightweight (nlohmann/json) |
| Installer | NSIS or simple xcopy | No heavy framework |
| Build system | CMake + MSVC | Standard, portable |

---

## 4. Feature Breakdown

### 4.1 Radial Circle Menu (GTA5-style)

- Triggered by: volume knob press (or configurable hotkey)
- Stays open while key is held; confirms selection on release
- 8 slice positions (N, NE, E, SE, S, SW, W, NW)
- Center slice: reserved for "pass-through / cancel"
- Mouse cursor auto-warps to center of overlay on open
- Slice highlight follows cursor angle from center
- Smooth fade-in (~80ms) / fade-out (~60ms) animation using alpha layering
- Overlay is a layered `WS_EX_LAYERED | WS_EX_TOPMOST` window (no taskbar entry)
- Custom slice icons: PNG/SVG per slot (rendered via GDI+)
- Slice label: short name (max 12 chars), displayed along arc
- Each slice has a color theme (user-configurable, 6 presets)

### 4.2 Macro Types (per slice)

#### a) Run Program
- Full path to .exe
- Optional command-line arguments
- Optional working directory
- Run as admin toggle
- Single/multi-instance guard

#### b) Open Website
- URL input (validated on save)
- Browser: default, or specific path
- Opens in new tab vs new window

#### c) Multi-Step Macro
- Sequence of actions, each with optional delay (ms)
- Action types: SendKeys, MouseClick, MouseMove, Wait, RunProgram, TypeText
- Visual step builder in config UI (drag-to-reorder)
- Loop count (1-999 or infinite)
- Stop trigger: hotkey or timeout

#### d) Autofill / Text Expansion
- Trigger: short abbreviation string (e.g. `.e1`, `;;addr`)
- Detection: low-level keyboard hook watches typed chars
- Match: checks last N typed chars against all triggers on every keypress
- On match: backspace-delete the trigger string, type the expansion
- Expansion supports: plain text, clipboard paste mode, multi-line
- Example entries:
  - `.e1` → `yourname@email.com`
  - `.ph` → `+63-912-345-6789`
  - `.sig` → full email signature block
- Triggers stored in `autofill.json` (separate from macro slots)
- Autofill runs globally (not just when radial is open)

#### e) Haptic Feedback
- Windows: triggers `PlaySound` + optional rumble via XInput (if controller present)
- Notification: tray balloon, or brief screen flash (configurable)
- Sound: built-in tones (5 presets) or custom .wav path
- Per-slot feedback: different sound per macro type

#### f) Raw AHK Script
- Each slot can contain a full AHK v2 script block
- Saved to temp `.ahk` file and executed via AHK runtime
- Script editor in config UI: monospace font, basic syntax highlighting
- "Test Run" button in editor
- Error capture: stderr piped back, shown in config UI

---

## 5. Configuration GUI

### 5.1 Main Config Window

- Win32 dialog-based window (no WPF, no Electron)
- Left panel: list of 8 slots (with icon preview and name)
- Right panel: slot editor (tabs per macro type)
- Top bar: global settings, import/export config
- Bottom bar: Save / Cancel / Apply buttons

### 5.2 Slot Editor Tabs

```
┌─ Slot 3 — "Dev Tools" ─────────────────────────────────┐
│  [Run Program] [Open URL] [Multi-Step] [Autofill] [AHK] │
│                                                         │
│  Icon: [browse PNG]  Label: [____________]              │
│  Color: [●Red][●Blue][●Green][●White][●Cyan][●Gold]     │
│                                                         │
│  ── Run Program ──                                      │
│  Path:    [C:\Windows\System32\notepad.exe    ] [Browse]│
│  Args:    [________________________________]            │
│  WorkDir: [________________________________]            │
│  [x] Run as admin   [ ] Single instance only            │
│                                                         │
│  ── Haptic Feedback ──                                  │
│  Sound: [○ None  ○ Click  ○ Whoosh  ○ Custom...]        │
│  Screen flash: [x]                                      │
│                                                         │
│                        [Test Now]  [Save]               │
└─────────────────────────────────────────────────────────┘
```

### 5.3 Autofill Manager

Separate panel (accessible from tray menu):
- Table view: Trigger | Expansion | Enabled checkbox
- Add / Edit / Delete buttons
- Import from CSV
- Enable/disable all toggle

### 5.4 Global Settings

- Startup with Windows (registry Run key)
- Knob press hold duration threshold (ms) before radial opens
- Radial menu size (small / medium / large)
- Radial open animation style (fade / zoom / instant)
- Primary hotkey override (in case knob press not detectable)
- Tray icon: show/hide
- Debug log: enable/disable (logs to `knoblaunch.log`)

---

## 6. File & Directory Structure

```
KnobLaunch/
├── bin/
│   ├── knoblaunch.exe          ← Main C++ daemon + GUI
│   ├── autohotkey.dll          ← AHK v2 COM-ready DLL (or bundled AHK64.exe)
│   └── resources/
│       ├── icons/              ← Default slice icons (PNG, 48x48)
│       ├── sounds/             ← Haptic .wav files
│       └── fonts/              ← Optional overlay font
├── config/
│   ├── config.json             ← Slot configs, global settings
│   └── autofill.json           ← Text expansion entries
├── scripts/
│   └── user_script_slotN.ahk   ← Per-slot AHK scripts (generated)
├── logs/
│   └── knoblaunch.log          ← Debug log (optional)
└── README.md
```

---

## 7. config.json Schema

```json
{
  "version": 1,
  "global": {
    "startup_with_windows": true,
    "hold_threshold_ms": 150,
    "radial_size": "medium",
    "radial_animation": "fade",
    "hotkey_override": "F13",
    "show_tray_icon": true,
    "debug_log": false
  },
  "slots": [
    {
      "index": 0,
      "label": "Notepad",
      "icon": "resources/icons/notepad.png",
      "color": "blue",
      "type": "run_program",
      "config": {
        "path": "C:\\Windows\\System32\\notepad.exe",
        "args": "",
        "workdir": "",
        "run_as_admin": false,
        "single_instance": false
      },
      "haptic": {
        "sound": "click",
        "screen_flash": false
      }
    },
    {
      "index": 1,
      "label": "GitHub",
      "icon": "resources/icons/github.png",
      "color": "white",
      "type": "open_url",
      "config": {
        "url": "https://github.com",
        "browser": "default",
        "new_tab": true
      },
      "haptic": {
        "sound": "whoosh",
        "screen_flash": false
      }
    },
    {
      "index": 2,
      "label": "My Script",
      "icon": "resources/icons/script.png",
      "color": "gold",
      "type": "ahk_script",
      "config": {
        "script_file": "scripts/user_script_slot2.ahk"
      },
      "haptic": {
        "sound": "none",
        "screen_flash": true
      }
    }
  ]
}
```

---

## 8. C++ Daemon — Key Modules

### 8.1 InputHook (knob_hook.cpp)
```
- SetWindowsHookEx(WH_KEYBOARD_LL, ...)
- Filter VK_VOLUME_MUTE or configurable VK
- Track press/release duration
- If hold >= threshold: fire RadialMenu::Show()
- If short tap: pass-through to system volume
```

### 8.2 RadialMenu (radial_menu.cpp)
```
- CreateWindowEx with WS_EX_LAYERED | WS_EX_TOPMOST | WS_EX_NOACTIVATE
- GDI+ DrawArc for each of 8 slices
- Track mouse angle from center: atan2(dy, dx)
- Highlight active slice with brighter fill
- On key release: fire selected slot action
- UpdateLayeredWindow for alpha blending (no flicker)
```

### 8.3 MacroRunner (macro_runner.cpp)
```
- Dispatch by slot type:
  - run_program → CreateProcess
  - open_url    → ShellExecuteEx with URL
  - multi_step  → sequential execution with Sleep(delay)
  - ahk_script  → write temp .ahk, launch AHK or call DLL
- Runs on worker thread, non-blocking
```

### 8.4 AutofillWatcher (autofill_watcher.cpp)
```
- Separate WH_KEYBOARD_LL hook (or same hook, branched)
- Maintain circular buffer of last 32 typed chars
- On each keypress: check buffer tail against all triggers
- On match: PostMessage sequence of VK_BACK × trigger.length
  then SendInput for expansion text
- Load triggers from autofill.json at startup
- File watcher: reload autofill.json on change (no restart needed)
```

### 8.5 HapticFeedback (haptic.cpp)
```
- PlaySound(wav_path, NULL, SND_ASYNC | SND_FILENAME)
- XInput rumble: XInputSetState (if gamepad present, silently skip if not)
- Screen flash: brief full-screen WS_EX_LAYERED window, alpha 0→60→0
```

### 8.6 ConfigStore (config_store.cpp)
```
- Load/save config.json using nlohmann/json (header-only)
- Validate schema on load; apply defaults for missing keys
- Thread-safe read (mutex-protected)
- Write is atomic: write to config.json.tmp, then rename
```

### 8.7 TrayIcon (tray.cpp)
```
- Shell_NotifyIcon with NIM_ADD
- Right-click context menu: Open Config, Autofill Manager,
  Enable/Disable, Reload Config, Exit
- Double-click: open config window
```

### 8.8 IPC Bridge (ipc_bridge.cpp)
```
- Named pipe server: \\.\pipe\knoblaunch
- JSON message protocol:
  { "cmd": "exec_slot", "slot": 3 }
  { "cmd": "reload_config" }
  { "cmd": "status" }
- AHK side uses FileOpen / DllCall to write to pipe
```

---

## 9. AutoHotkey Integration

### 9.1 Execution Model

Two options (choose at build time via config):

**Option A — Subprocess (simpler):**
- Write slot script to `scripts/user_script_slotN.ahk`
- Launch `AutoHotkey64.exe scripts/user_script_slotN.ahk` via CreateProcess
- Reuse existing AHK installation or bundle a minimal AHK64.exe (~1MB)

**Option B — AHK DLL (advanced, lower overhead):**
- Use `AutoHotkey.dll` (COM interface)
- Load once at daemon startup
- Execute script strings in-process: `ahk->ahktextdll(L"...")`
- Lower per-execution overhead (~0.2ms vs ~50ms for subprocess)

**Recommendation:** Start with Option A for simplicity; migrate to Option B in v2.

### 9.2 Sample User AHK Script (slot)

```autohotkey
; user_script_slot2.ahk — Example: type current timestamp
#Requires AutoHotkey v2.0
timestamp := FormatTime(, "yyyy-MM-dd HH:mm:ss")
Send(timestamp)
```

### 9.3 Autofill Engine (also AHK-compatible)

Users can write autofill logic directly in AHK script slots:
```autohotkey
; Advanced autofill via AHK
::.e1::yourname@email.com
::.addr::123 Rizal Street, Laguna, PH
```
This is separate from the built-in autofill watcher — for users who prefer raw AHK hotstrings.

---

## 10. Development Phases

### Phase 1 — Core (Weeks 1–2)
- [ ] Project scaffold: CMake, MSVC build, folder layout
- [ ] System tray icon + right-click menu
- [ ] Low-level keyboard hook: detect volume knob press
- [ ] JSON config load/save (nlohmann/json)
- [ ] Basic radial menu window (8 slices, no animation yet)

### Phase 2 — Macro Engine (Weeks 3–4)
- [ ] Run Program macro
- [ ] Open URL macro
- [ ] Multi-step macro builder (basic: SendKeys + Wait)
- [ ] AHK script runner (subprocess model)
- [ ] Haptic feedback: sound playback

### Phase 3 — Autofill + Polish (Weeks 5–6)
- [ ] Autofill keyboard watcher
- [ ] Autofill config manager (config UI panel)
- [ ] Screen flash haptic
- [ ] Radial menu animations (fade in/out, GDI+ alpha)
- [ ] Slice icon loading from PNG (GDI+)

### Phase 4 — Config GUI (Weeks 7–8)
- [ ] Full Win32 config window (slot editor, all tabs)
- [ ] Autofill table UI
- [ ] Global settings panel
- [ ] Import/export config (JSON file dialog)
- [ ] "Test Now" buttons for each macro type

### Phase 5 — Hardening (Week 9)
- [ ] Error handling (missing AHK, bad config, access denied)
- [ ] Debug log to file
- [ ] Memory profiling (target: <4MB RAM idle)
- [ ] Auto-reload config on external file change
- [ ] Startup with Windows (registry key)

### Phase 6 — Packaging (Week 10)
- [ ] Bundle: knoblaunch.exe + autohotkey64.exe + default config
- [ ] NSIS installer (optional)
- [ ] README + quick-start guide
- [ ] Version stamping (version.h generated by CMake)

---

## 11. Memory & Performance Targets

| Metric | Target |
|---|---|
| Idle RAM | < 4 MB |
| Peak RAM (radial open) | < 8 MB |
| Radial open latency | < 30 ms |
| Autofill detection latency | < 5 ms |
| AHK script launch (subprocess) | < 80 ms |
| Config load time | < 10 ms |
| CPU idle | < 0.1% |

**Techniques to stay lightweight:**
- No STL containers in hot paths (use fixed-size arrays for autofill buffer)
- GDI+ context created once and reused
- AHK subprocess kept alive via `Persistent` flag if slot is used frequently
- nlohmann/json used only at load/save time, not in runtime loop
- No background threads except: input hook thread, macro worker thread, pipe server thread (3 threads total idle)

---

## 12. Dependencies

| Library | Version | License | Size |
|---|---|---|---|
| nlohmann/json | 3.11.x | MIT | Header-only (~1MB headers, 0 runtime) |
| AutoHotkey v2 | 2.0.x | GPL-2 | ~1.5MB (bundled exe) |
| Win32 GDI+ | Built-in | — | OS-provided |
| XInput | Built-in | — | OS-provided (optional rumble) |

No Boost. No Qt. No .NET. No Electron.

---

## 13. Radial Menu — Rendering Notes

### Slice Geometry
```
Center: screen center (or cursor position)
Radius inner: 60px (dead zone)
Radius outer: 160px
Slice angle: 360° / 8 = 45° per slice
Slice 0 (top/North): starts at -90° - 22.5°, ends at -90° + 22.5°
```

### GDI+ Draw Order (per frame)
1. Clear background (transparent)
2. Draw dark circle backdrop (alpha 180/255)
3. For each of 8 slices:
   a. Draw filled arc (normal: dark gray fill)
   b. If slice == hovered: draw with highlight color (brighter fill)
   c. Draw radial separator lines (thin, 1px)
   d. Draw icon (48x48 PNG, centered in slice midpoint)
   e. Draw label text (12pt, centered below icon)
4. Draw center circle (cancel zone, slightly lighter)
5. Call `UpdateLayeredWindow` once (no flicker double-buffer)

### Slice Midpoint Calculation (for icon/label placement)
```cpp
float midAngle = sliceStartAngle + 22.5f; // degrees
float r = (innerRadius + outerRadius) / 2.0f;
float iconX = centerX + r * cos(midAngle * PI / 180.0f);
float iconY = centerY + r * sin(midAngle * PI / 180.0f);
```

---

## 14. IPC Protocol (Named Pipe)

All messages are newline-terminated JSON strings.

### C++ → AHK
```json
{ "event": "slot_selected", "slot": 3, "label": "Dev Tools" }
{ "event": "config_reloaded" }
{ "event": "autofill_triggered", "trigger": ".e1" }
```

### AHK → C++
```json
{ "cmd": "exec_slot", "slot": 5 }
{ "cmd": "reload_config" }
{ "cmd": "set_autofill", "trigger": ".e1", "expansion": "user@email.com" }
```

---

## 15. Build Instructions (after implementation)

```batch
:: Prerequisites: MSVC (Visual Studio 2022), CMake 3.20+
git clone https://github.com/you/knoblaunch
cd knoblaunch
cmake -B build -G "Visual Studio 17 2022" -A x64
cmake --build build --config Release
:: Output: build/Release/knoblaunch.exe
```

---

## 16. Known Limitations & Future Work

| Item | Notes |
|---|---|
| Knob detection | Some keyboards use HID multimedia codes not exposed as VK_VOLUME_*. May need HID raw input fallback (`RegisterRawInputDevices`). |
| AHK GPL license | Bundling AHK exe is allowed under GPL. Source must be available. Or prompt user to install AHK separately. |
| Multi-monitor | Radial menu opens at cursor position; works on any monitor. |
| UAC elevation | For macros that need admin rights, knoblaunch itself may need elevation or a helper process. |
| Linux/macOS | Out of scope for v1. Would require full rewrite (evdev + X11/Wayland). |
| Hotstring conflicts | AHK autofill and built-in autofill could double-fire. Disable one per slot type. |

---

## 17. Quick-Start User Guide (after install)

1. Launch `knoblaunch.exe` → tray icon appears
2. Right-click tray → "Open Config"
3. Click any of the 8 slots to assign a macro
4. Press your volume knob (hold ~150ms) → radial menu appears
5. Move mouse toward desired slice → release knob → macro fires
6. To add autofill: right-click tray → "Autofill Manager" → Add entry
7. To write custom AHK: pick slot → AHK tab → paste script → Test Now

---

*Document version: 1.0 | Project: KnobLaunch | Generated for planning purposes*
