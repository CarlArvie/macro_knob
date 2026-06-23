import os
import re

# 1. Fix app.js
js_path = r"c:\Users\carla\Desktop\AHK\Arvie Knob Macro\ui\app.js"
with open(js_path, "r", encoding="utf-8") as f:
    js = f.read()

# Remove the second updateCurrentSlot definition completely
second_ucs_pattern = re.compile(r"function updateCurrentSlot\(\) \{[^{}]*const slotsArr = getSlotsAtPath\(currentPath\);.*?renderPieChart\(\);\n\}", re.DOTALL)
matches = second_ucs_pattern.findall(js)
if len(matches) == 2:
    # There are two, remove the second one
    js = js[:js.rfind(matches[1])] + js[js.rfind(matches[1])+len(matches[1]):]

# Fix saveConfig to not close window
save_pattern = r"""        showToast\(\);\n        setTimeout\(\(\) => \{\n            window\.close\(\);\n            // Fallback if window\.close\(\) is blocked\n            document\.body\.innerHTML = "<div class='glass-container' style='text-align: center; margin-top: 100px;'><h2>Settings Saved!</h2><p>You can close this tab now\. The config server has been safely shut down\.</p></div>";\n        \}, 1500\);"""
js = re.sub(save_pattern, """        showToast();\n        setTimeout(() => {\n            DOM.saveBtn.textContent = "Save Changes";\n            DOM.saveBtn.disabled = false;\n        }, 1500);""", js)

with open(js_path, "w", encoding="utf-8") as f:
    f.write(js)


# 2. Fix config_server.py
cs_path = r"c:\Users\carla\Desktop\AHK\Arvie Knob Macro\config_server.py"
with open(cs_path, "r", encoding="utf-8") as f:
    cs = f.read()

cs = cs.replace('print("Config saved. Shutting down server...")', 'print("Config saved. Restarting daemon...")')
cs = cs.replace('threading.Thread(target=self.server.shutdown).start()', 'import subprocess\n                try:\n                    subprocess.run(["taskkill", "/IM", "knoblaunch.exe", "/F"], capture_output=True)\n                    subprocess.Popen(["bin\\\\knoblaunch.exe"], cwd=os.path.dirname(os.path.abspath(__file__)), creationflags=subprocess.CREATE_NO_WINDOW)\n                except Exception as ex:\n                    print("Failed to restart daemon:", ex)')

with open(cs_path, "w", encoding="utf-8") as f:
    f.write(cs)

print("Fixed app.js and config_server.py!")
