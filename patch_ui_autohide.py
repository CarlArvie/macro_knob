import os

html_path = r"c:\Users\carla\Desktop\AHK\Arvie Knob Macro\ui\index.html"
with open(html_path, "r", encoding="utf-8") as f:
    html = f.read()

find_html = """                        <div class="form-group">
                            <label for="radial_size">Menu Size</label>
                            <select id="radial_size">"""

replace_html = """                        <div class="form-group">
                            <label for="auto_hide_timer_s">Auto-Hide Timer (Seconds)</label>
                            <input type="number" id="auto_hide_timer_s" min="0" max="300" step="1">
                            <small>Set to 0 to disable auto-hide.</small>
                        </div>
                        <div class="form-group">
                            <label for="radial_size">Menu Size</label>
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

js = js.replace("menuSpawnLocation: document.getElementById('menu_spawn_location'),", "menuSpawnLocation: document.getElementById('menu_spawn_location'),\n      autoHideTimerS: document.getElementById('auto_hide_timer_s'),")

js = js.replace('DOM.menuSpawnLocation.value = g.menu_spawn_location || "cursor";', 'DOM.menuSpawnLocation.value = g.menu_spawn_location || "cursor";\n      DOM.autoHideTimerS.value = g.auto_hide_timer_s !== undefined ? g.auto_hide_timer_s : 10;')

js = js.replace('configData.global.menu_spawn_location = DOM.menuSpawnLocation.value;', 'configData.global.menu_spawn_location = DOM.menuSpawnLocation.value;\n    configData.global.auto_hide_timer_s = parseInt(DOM.autoHideTimerS.value, 10);')

with open(js_path, "w", encoding="utf-8") as f:
    f.write(js)
print("Patched app.js!")
