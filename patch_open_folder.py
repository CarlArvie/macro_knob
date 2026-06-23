import os

# 1. Update index.html
html_path = r"c:\Users\carla\Desktop\AHK\Arvie Knob Macro\ui\index.html"
with open(html_path, "r", encoding="utf-8") as f:
    html = f.read()

find_select = """                          <option value="open_url">Open URL in Browser</option>"""
replace_select = """                          <option value="open_url">Open URL in Browser</option>
                          <option value="open_folder">Open File / Folder</option>"""
html = html.replace(find_select, replace_select)

with open(html_path, "w", encoding="utf-8") as f:
    f.write(html)

# 2. Update app.js
js_path = r"c:\Users\carla\Desktop\AHK\Arvie Knob Macro\ui\app.js"
with open(js_path, "r", encoding="utf-8") as f:
    js = f.read()

js = js.replace('        } else {\n            DOM.groupPath.style.display = "block";\n        }', '        } else {\n            DOM.groupPath.style.display = "block";\n        }')

js = js.replace('    } else {\n        DOM.groupPath.style.display = "block";\n        DOM.slotPath.value = slot.config.path || "";\n        DOM.slotUrl.value = "";\n    }', '    } else {\n        DOM.groupPath.style.display = "block";\n        DOM.slotPath.value = slot.config.path || "";\n        DOM.slotUrl.value = "";\n    }')

# Actually, the logic in app.js for fallback is `} else { DOM.groupPath.style.display = "block"; ... }`
# Which naturally covers `open_folder`! Because it's not "open_url", "sub_menu", or "back".
# So app.js literally requires NO changes! The fallback logic handles it perfectly by showing the Path box and saving it to slot.config.path.

# 3. Update input_hook.cpp
ih_path = r"c:\Users\carla\Desktop\AHK\Arvie Knob Macro\src\input_hook.cpp"
with open(ih_path, "r", encoding="utf-8") as f:
    ih = f.read()

ih_find = """    } else if (slot.type == "open_url") {
        if (!slot.config["url"].is_null()) {
            std::string url = slot.config["url"];
            OpenURL(url);
        }
    }"""
ih_replace = """    } else if (slot.type == "open_url") {
        if (!slot.config["url"].is_null()) {
            std::string url = slot.config["url"];
            OpenURL(url);
        }
    } else if (slot.type == "open_folder" || slot.type == "open_file") {
        if (!slot.config["path"].is_null()) {
            std::string path = slot.config["path"];
            OpenURL(path);
        }
    }"""
ih = ih.replace(ih_find, ih_replace)

with open(ih_path, "w", encoding="utf-8") as f:
    f.write(ih)

print("Added Open Folder action type!")
