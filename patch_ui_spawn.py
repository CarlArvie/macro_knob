import os
import re

html_path = r"c:\Users\carla\Desktop\AHK\Arvie Knob Macro\ui\index.html"
with open(html_path, "r", encoding="utf-8") as f:
    html = f.read()

find_html = """                        <div class="form-group">
                            <label for="radial_size">Radial Menu Size</label>
                            <select id="radial_size">"""

replace_html = """                        <div class="form-group">
                            <label for="menu_spawn_location">Menu Spawn Location</label>
                            <select id="menu_spawn_location">
                                <option value="cursor">At Mouse Cursor (Default)</option>
                                <option value="center">Center of Screen</option>
                                <option value="top_left">Top Left</option>
                                <option value="top_right">Top Right</option>
                                <option value="bottom_left">Bottom Left</option>
                                <option value="bottom_right">Bottom Right</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label for="radial_size">Radial Menu Size</label>
                            <select id="radial_size">"""

if find_html in html:
    html = html.replace(find_html, replace_html)
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    print("Patched index.html!")
else:
    print("Could not find block in index.html")

js_path = r"c:\Users\carla\Desktop\AHK\Arvie Knob Macro\ui\app.js"
with open(js_path, "r", encoding="utf-8") as f:
    js = f.read()

js = js.replace("radialSize: document.getElementById('radial_size'),", "radialSize: document.getElementById('radial_size'),\n      menuSpawnLocation: document.getElementById('menu_spawn_location'),")
js = js.replace('DOM.radialSize.value = g.radial_size || "medium";', 'DOM.radialSize.value = g.radial_size || "medium";\n      DOM.menuSpawnLocation.value = g.menu_spawn_location || "cursor";')
js = js.replace('configData.global.radial_size = DOM.radialSize.value;', 'configData.global.radial_size = DOM.radialSize.value;\n    configData.global.menu_spawn_location = DOM.menuSpawnLocation.value;')

with open(js_path, "w", encoding="utf-8") as f:
    f.write(js)
print("Patched app.js!")
