import os

html_path = "c:\\Users\\carla\\Desktop\\AHK\\Arvie Knob Macro\\ui\\index.html"
with open(html_path, "r", encoding="utf-8") as f:
    html = f.read()

html = html.replace(
    '<option value="open_url">Open URL</option>',
    '<option value="open_url">Open URL</option>\n                            <option value="sub_menu">Sub-Menu (Folder)</option>\n                            <option value="back">Back to Parent</option>'
)

html = html.replace(
    '<div class="visualizer">',
    '<div id="breadcrumb" style="font-weight: 600; color: #a78bfa; margin-bottom: -1rem; text-align: center;">&#x1F3E0; Home</div>\n                <div class="visualizer">'
)

html = html.replace(
    '                    <div class="form-group" id="group_url" style="display: none;">\n                        <label for="slot_url">Website URL</label>\n                        <input type="text" id="slot_url" placeholder="https://github.com">\n                    </div>',
    '                    <div class="form-group" id="group_url" style="display: none;">\n                        <label for="slot_url">Website URL</label>\n                        <input type="text" id="slot_url" placeholder="https://github.com">\n                    </div>\n                    <div class="form-group" id="group_sub_menu" style="display: none; margin-top: 1rem;">\n                        <button id="btn_enter_sub_menu" class="primary-btn" style="width: 100%; background: #a78bfa; color: #000;">Open Folder &rarr;</button>\n                    </div>'
)

with open(html_path, "w", encoding="utf-8") as f:
    f.write(html)
print("index.html patched")

js_path = "c:\\Users\\carla\\Desktop\\AHK\\Arvie Knob Macro\\ui\\app.js"
with open(js_path, "r", encoding="utf-8") as f:
    js = f.read()

js = js.replace(
    'let activeSlotIndex = 0;',
    'let activeSlotIndex = 0;\nlet currentPath = [];'
)

js = js.replace(
    "    groupUrl: document.getElementById('group_url'),",
    "    groupUrl: document.getElementById('group_url'),\n    groupSubMenu: document.getElementById('group_sub_menu'),\n    btnEnterSubMenu: document.getElementById('btn_enter_sub_menu'),\n    breadcrumb: document.getElementById('breadcrumb'),"
)

# Replace get slot references
js = js.replace(
    'const slot = configData.slots[i];',
    'const slotsArr = getSlotsAtPath(currentPath);\n        const slot = slotsArr[i];'
)

js = js.replace(
    'const slot = configData.slots[index];',
    'const slotsArr = getSlotsAtPath(currentPath);\n    const slot = slotsArr[index];'
)

js = js.replace(
    'const slot = configData.slots[activeSlotIndex];',
    'const slotsArr = getSlotsAtPath(currentPath);\n    const slot = slotsArr[activeSlotIndex];'
)

# Add getSlotsAtPath and breadcrumb update
helper_funcs = """function getSlotsAtPath(path) {
    let current = configData.slots;
    for (let i = 0; i < path.length; i++) {
        const idx = path[i];
        if (!current[idx].slots) {
            current[idx].slots = [];
            for(let j=0; j<8; j++) current[idx].slots.push({index: j, enabled: true, label: `Slot ${j}`, color: "0xFF777777", type: "run_program", config: {}});
        }
        current = current[idx].slots;
    }
    return current;
}

function updateBreadcrumb() {
    if (currentPath.length === 0) {
        DOM.breadcrumb.innerHTML = '&#x1F3E0; Home';
    } else {
        let text = '<span style="cursor:pointer;" onclick="goHome()">&#x1F3E0; Home</span>';
        let cur = configData.slots;
        for (let i = 0; i < currentPath.length; i++) {
            const idx = currentPath[i];
            const name = cur[idx].label || `Slot ${idx}`;
            text += ` &gt; ${name}`;
            cur = cur[idx].slots;
        }
        DOM.breadcrumb.innerHTML = text;
    }
}

window.goHome = function() {
    currentPath = [];
    updateBreadcrumb();
    loadSlot(0);
};
"""

js = js.replace(
    'function populateGlobalSettings() {',
    helper_funcs + '\nfunction populateGlobalSettings() {'
)

js = js.replace(
    'loadSlot(0);\n        attachEventListeners();',
    'updateBreadcrumb();\n        loadSlot(0);\n        attachEventListeners();'
)

# Update Type change logic
js = js.replace(
    '    if (slot.type === "open_url") {\n        DOM.groupPath.style.display = "none";\n        DOM.groupUrl.style.display = "block";',
    '    DOM.groupPath.style.display = "none";\n    DOM.groupUrl.style.display = "none";\n    DOM.groupSubMenu.style.display = "none";\n\n    if (slot.type === "open_url") {\n        DOM.groupUrl.style.display = "block";'
)

js = js.replace(
    '    } else {\n        DOM.groupUrl.style.display = "none";\n        DOM.groupPath.style.display = "block";\n        DOM.slotPath.value = slot.config.path || "";\n        DOM.slotUrl.value = "";\n    }',
    '    } else if (slot.type === "sub_menu") {\n        DOM.groupSubMenu.style.display = "block";\n    } else if (slot.type === "back") {\n        // Nothing to configure\n    } else {\n        DOM.groupPath.style.display = "block";\n        DOM.slotPath.value = slot.config.path || "";\n        DOM.slotUrl.value = "";\n    }'
)

js = js.replace(
    '    DOM.slotType.addEventListener(\'change\', (e) => {\n        if (e.target.value === "open_url") {\n            DOM.groupPath.style.display = "none";\n            DOM.groupUrl.style.display = "block";\n        } else {\n            DOM.groupUrl.style.display = "none";\n            DOM.groupPath.style.display = "block";\n        }\n        updateCurrentSlot();\n    });',
    '''    DOM.slotType.addEventListener('change', (e) => {
        DOM.groupPath.style.display = "none";
        DOM.groupUrl.style.display = "none";
        DOM.groupSubMenu.style.display = "none";
        if (e.target.value === "open_url") {
            DOM.groupUrl.style.display = "block";
        } else if (e.target.value === "sub_menu") {
            DOM.groupSubMenu.style.display = "block";
        } else if (e.target.value === "back") {
            // Nothing
        } else {
            DOM.groupPath.style.display = "block";
        }
        updateCurrentSlot();
    });
    
    DOM.btnEnterSubMenu.addEventListener('click', () => {
        currentPath.push(activeSlotIndex);
        updateBreadcrumb();
        loadSlot(0);
    });'''
)

with open(js_path, "w", encoding="utf-8") as f:
    f.write(js)
print("app.js patched")
