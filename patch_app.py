import os

file_path = "c:\\Users\\carla\\Desktop\\AHK\\Arvie Knob Macro\\ui\\app.js"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace(
    "    interactionMode: document.getElementById('interaction_mode'),",
    "    isEnabled: document.getElementById('is_enabled'),\n    toggleHotkey: document.getElementById('toggle_hotkey'),\n    slotEnabled: document.getElementById('slot_enabled'),\n    interactionMode: document.getElementById('interaction_mode'),"
)

content = content.replace(
    '    DOM.interactionMode.value = g.interaction_mode || "mouse_hold";',
    '    DOM.isEnabled.checked = g.is_enabled ?? true;\n    DOM.toggleHotkey.value = g.toggle_hotkey || "F14";\n    DOM.interactionMode.value = g.interaction_mode || "mouse_hold";'
)

content = content.replace(
    '        DOM.svg.appendChild(path);',
    '        if (slot.enabled === false) path.setAttribute("opacity", "0.15");\n        DOM.svg.appendChild(path);'
)

content = content.replace(
    '        text.textContent = label;\n        DOM.svg.appendChild(text);',
    '        text.textContent = label;\n        if (slot.enabled === false) text.setAttribute("opacity", "0.15");\n        DOM.svg.appendChild(text);'
)

content = content.replace(
    '    DOM.editorTitle.textContent = `Edit Slot ${index + 1}`;\n    DOM.slotLabel.value = slot.label || "";',
    '    DOM.editorTitle.textContent = `Edit Slot ${index + 1}`;\n    DOM.slotEnabled.checked = slot.enabled ?? true;\n    DOM.slotLabel.value = slot.label || "";'
)

content = content.replace(
    "    const inputs = [DOM.slotLabel, DOM.slotPath, DOM.slotUrl];",
    "    const inputs = [DOM.slotLabel, DOM.slotPath, DOM.slotUrl];\n    DOM.slotEnabled.addEventListener('change', updateCurrentSlot);"
)

content = content.replace(
    '    slot.label = DOM.slotLabel.value;',
    '    slot.enabled = DOM.slotEnabled.checked;\n    slot.label = DOM.slotLabel.value;'
)

content = content.replace(
    '    configData.global.interaction_mode = DOM.interactionMode.value;',
    '    configData.global.is_enabled = DOM.isEnabled.checked;\n    configData.global.toggle_hotkey = DOM.toggleHotkey.value;\n    configData.global.interaction_mode = DOM.interactionMode.value;'
)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("app.js patched")
