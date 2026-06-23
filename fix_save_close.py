import os

js_path = r"c:\Users\carla\Desktop\AHK\Arvie Knob Macro\ui\app.js"
with open(js_path, "r", encoding="utf-8") as f:
    js = f.read()

find_save = """        showToast();
        setTimeout(() => {
            window.close();
            // Fallback if window.close() blocked
            document.body.innerHTML = "<h2 style='color:white; text-align:center; margin-top:20vh;'>Configuration Saved.<br>You can safely close this window.</h2>";
        }, 1500);"""

replace_save = """        showToast();
        setTimeout(() => {
            DOM.saveBtn.textContent = "Save Changes";
            DOM.saveBtn.disabled = false;
        }, 1500);"""

if find_save in js:
    js = js.replace(find_save, replace_save)
    with open(js_path, "w", encoding="utf-8") as f:
        f.write(js)
    print("Fixed saveConfig to not close window!")
else:
    print("Could not find the window.close block.")
