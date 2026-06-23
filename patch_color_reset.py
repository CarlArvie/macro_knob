import os

# 1. Update index.html
html_path = r"c:\Users\carla\Desktop\AHK\Arvie Knob Macro\ui\index.html"
with open(html_path, "r", encoding="utf-8") as f:
    html = f.read()

find_html = """                        <div class="color-picker-row">
                            <input type="color" id="slot_color_picker">
                            <input type="text" id="slot_color" placeholder="0xFF555555">
                        </div>"""

replace_html = """                        <div class="color-picker-row" style="display: flex; gap: 0.5rem; align-items: center;">
                            <input type="color" id="slot_color_picker" style="flex: 0 0 40px;">
                            <input type="text" id="slot_color" placeholder="0xFF555555" style="flex: 1;">
                            <button id="btn_reset_color" class="primary-btn" style="flex: 0 0 auto; padding: 0.4rem 0.6rem; font-size: 0.75rem; background: #64748b;">Reset</button>
                        </div>"""

html = html.replace(find_html, replace_html)

with open(html_path, "w", encoding="utf-8") as f:
    f.write(html)

# 2. Update app.js
js_path = r"c:\Users\carla\Desktop\AHK\Arvie Knob Macro\ui\app.js"
with open(js_path, "r", encoding="utf-8") as f:
    js = f.read()

js = js.replace(
    "    slotColor: document.getElementById('slot_color'),",
    "    slotColor: document.getElementById('slot_color'),\n    btnResetColor: document.getElementById('btn_reset_color'),"
)

listeners_addition = """    DOM.btnResetColor.addEventListener('click', () => {
        DOM.slotColor.value = "0xFF777777";
        DOM.slotColorPicker.value = extractHexFromARGB("0xFF777777");
        updateCurrentSlot();
    });"""

js = js.replace(
    "    DOM.slotColor.addEventListener('input', (e) => {\n        DOM.slotColorPicker.value = extractHexFromARGB(e.target.value);\n        updateCurrentSlot();\n    });",
    "    DOM.slotColor.addEventListener('input', (e) => {\n        DOM.slotColorPicker.value = extractHexFromARGB(e.target.value);\n        updateCurrentSlot();\n    });\n\n" + listeners_addition
)

with open(js_path, "w", encoding="utf-8") as f:
    f.write(js)

print("Color reset button added!")
