let configData = null;
let activeSlotIndex = 0;
let currentPath = [];

const DOM = {
    isEnabled: document.getElementById('is_enabled'),
    toggleHotkey: document.getElementById('toggle_hotkey'),
    slotEnabled: document.getElementById('slot_enabled'),
    interactionMode: document.getElementById('interaction_mode'),
    hotkeyOverride: document.getElementById('hotkey_override'),
    rotaryNext: document.getElementById('rotary_next'),
    rotaryPrev: document.getElementById('rotary_prev'),
    holdThreshold: document.getElementById('hold_threshold_ms'),
    radialSize: document.getElementById('radial_size'),
    showTrayIcon: document.getElementById('show_tray_icon'),
    debugLog: document.getElementById('debug_log'),
    
    svg: document.getElementById('pie-chart'),
    
    editorTitle: document.getElementById('editor-title'),
    slotLabel: document.getElementById('slot_label'),
    slotColor: document.getElementById('slot_color'),
    slotColorPicker: document.getElementById('slot_color_picker'),
    slotType: document.getElementById('slot_type'),
    slotPath: document.getElementById('slot_path'),
    slotUrl: document.getElementById('slot_url'),
    
    groupPath: document.getElementById('group_path'),
    groupUrl: document.getElementById('group_url'),
    groupSubMenu: document.getElementById('group_sub_menu'),
    btnEnterSubMenu: document.getElementById('btn_enter_sub_menu'),
    breadcrumb: document.getElementById('breadcrumb'),
    
    saveBtn: document.getElementById('save-btn'),
    toast: document.getElementById('toast')
};

async function init() {
    try {
        const res = await fetch('/api/config');
        configData = await res.json();
        populateGlobalSettings();
        renderPieChart();
        updateBreadcrumb();
        loadSlot(0);
        attachEventListeners();
    } catch (e) {
        console.error("Failed to load config", e);
    }
}

function getSlotsAtPath(path) {
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

function populateGlobalSettings() {
    const g = configData.global;
    DOM.isEnabled.checked = g.is_enabled ?? true;
    DOM.toggleHotkey.value = g.toggle_hotkey || "F14";
    DOM.interactionMode.value = g.interaction_mode || "mouse_hold";
    DOM.hotkeyOverride.value = g.hotkey_override || "";
    DOM.rotaryNext.value = g.rotary_next || "";
    DOM.rotaryPrev.value = g.rotary_prev || "";
    DOM.holdThreshold.value = g.hold_threshold_ms || 150;
    DOM.radialSize.value = g.radial_size || "medium";
    DOM.showTrayIcon.checked = g.show_tray_icon ?? true;
    DOM.debugLog.checked = g.debug_log ?? false;
}

function extractHexFromARGB(argb) {
    if (!argb) return "#777777";
    // argb is like 0xFF555555
    if (argb.length === 10 && argb.startsWith("0x")) {
        return "#" + argb.substring(4);
    }
    return "#777777";
}

function convertHexToARGB(hex) {
    // hex is like #555555
    if (hex.startsWith("#")) hex = hex.substring(1);
    return "0xFF" + hex.toUpperCase();
}

function renderPieChart() {
    DOM.svg.innerHTML = '';
    const numSlices = 8;
    
    // Draw slices
    for (let i = 0; i < numSlices; i++) {
        const slotsArr = getSlotsAtPath(currentPath);
        const slot = slotsArr[i];
        const hexColor = extractHexFromARGB(slot.color);
        
        // Math for 8 slices (45 degrees each). Start at top (-90 deg), shifted back by 22.5 deg so slice 0 is perfectly top-centered.
        const startAngle = (i * 45) - 90 - 22.5;
        const endAngle = startAngle + 45;
        
        const startRad = startAngle * Math.PI / 180;
        const endRad = endAngle * Math.PI / 180;
        
        const r = 90;
        const x1 = Math.cos(startRad) * r;
        const y1 = Math.sin(startRad) * r;
        const x2 = Math.cos(endRad) * r;
        const y2 = Math.sin(endRad) * r;
        
        const pathData = [
            `M 0 0`,
            `L ${x1} ${y1}`,
            `A ${r} ${r} 0 0 1 ${x2} ${y2}`,
            `Z`
        ].join(' ');
        
        const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
        path.setAttribute("d", pathData);
        path.setAttribute("fill", hexColor);
        path.setAttribute("class", i === activeSlotIndex ? "slice active" : "slice");
        path.addEventListener("click", () => loadSlot(i));
        if (slot.enabled === false) path.setAttribute("opacity", "0.15");
        DOM.svg.appendChild(path);
        
        // Add Text
        const midRad = (startAngle + 22.5) * Math.PI / 180;
        const textR = 60; // position text along the slice radius
        const tx = Math.cos(midRad) * textR;
        const ty = Math.sin(midRad) * textR;
        
        const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
        text.setAttribute("x", tx);
        text.setAttribute("y", ty);
        text.setAttribute("class", "slice-text");
        
        let label = slot.label || `Slot ${i+1}`;
        if (label.length > 10) label = label.substring(0, 8) + "..";
        text.textContent = label;
        if (slot.enabled === false) text.setAttribute("opacity", "0.15");
        DOM.svg.appendChild(text);
    }
}

function loadSlot(index) {
    activeSlotIndex = index;
    const slotsArr = getSlotsAtPath(currentPath);
    const slot = slotsArr[index];
    
    DOM.editorTitle.textContent = `Edit Slot ${index + 1}`;
    DOM.slotEnabled.checked = slot.enabled ?? true;
    DOM.slotLabel.value = slot.label || "";
    
    const hex = extractHexFromARGB(slot.color);
    DOM.slotColorPicker.value = hex;
    DOM.slotColor.value = slot.color || "";
    
    DOM.slotType.value = slot.type || "run_program";
    
    DOM.groupPath.style.display = "none";
    DOM.groupUrl.style.display = "none";
    DOM.groupSubMenu.style.display = "none";

    if (slot.type === "open_url") {
        DOM.groupUrl.style.display = "block";
        DOM.slotUrl.value = slot.config.url || "";
        DOM.slotPath.value = "";
    } else if (slot.type === "sub_menu") {
        DOM.groupSubMenu.style.display = "block";
    } else if (slot.type === "back") {
        // Nothing to configure
    } else {
        DOM.groupPath.style.display = "block";
        DOM.slotPath.value = slot.config.path || "";
        DOM.slotUrl.value = "";
    }
    
    renderPieChart();
}

function attachEventListeners() {
    // Type change
    DOM.slotType.addEventListener('change', (e) => {
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
    });
    
    // Auto update on input
    const inputs = [DOM.slotLabel, DOM.slotPath, DOM.slotUrl];
    DOM.slotEnabled.addEventListener('change', updateCurrentSlot);
    inputs.forEach(input => {
        input.addEventListener('input', updateCurrentSlot);
    });
    
    // Color picker sync
    DOM.slotColorPicker.addEventListener('input', (e) => {
        DOM.slotColor.value = convertHexToARGB(e.target.value);
        updateCurrentSlot();
    });
    
    DOM.slotColor.addEventListener('input', (e) => {
        DOM.slotColorPicker.value = extractHexFromARGB(e.target.value);
        updateCurrentSlot();
    });

    // Save
    DOM.saveBtn.addEventListener('click', saveConfig);
}

function updateCurrentSlot() {
    const slotsArr = getSlotsAtPath(currentPath);
    const slot = slotsArr[activeSlotIndex];
    slot.enabled = DOM.slotEnabled.checked;
    slot.label = DOM.slotLabel.value;
    slot.color = DOM.slotColor.value;
    slot.type = DOM.slotType.value;
    
    if (slot.type === "open_url") {
        slot.config = { url: DOM.slotUrl.value };
    } else {
        slot.config = { path: DOM.slotPath.value };
    }
    
    renderPieChart();
}

async function saveConfig() {
    // Update global settings
    configData.global.is_enabled = DOM.isEnabled.checked;
    configData.global.toggle_hotkey = DOM.toggleHotkey.value;
    configData.global.interaction_mode = DOM.interactionMode.value;
    configData.global.hotkey_override = DOM.hotkeyOverride.value;
    configData.global.rotary_next = DOM.rotaryNext.value;
    configData.global.rotary_prev = DOM.rotaryPrev.value;
    configData.global.hold_threshold_ms = parseInt(DOM.holdThreshold.value) || 150;
    configData.global.radial_size = DOM.radialSize.value;
    configData.global.show_tray_icon = DOM.showTrayIcon.checked;
    configData.global.debug_log = DOM.debugLog.checked;
    
    DOM.saveBtn.textContent = "Saving...";
    DOM.saveBtn.disabled = true;
    
    try {
        await fetch('/api/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(configData)
        });
        
        showToast();
        setTimeout(() => {
            window.close();
            // Fallback if window.close() is blocked
            document.body.innerHTML = "<div class='glass-container' style='text-align: center; margin-top: 100px;'><h2>Settings Saved!</h2><p>You can close this tab now. The config server has been safely shut down.</p></div>";
        }, 1500);
    } catch (e) {
        console.error("Save failed", e);
        DOM.saveBtn.textContent = "Error!";
    }
}

function showToast() {
    DOM.toast.classList.add('show');
    setTimeout(() => {
        DOM.toast.classList.remove('show');
    }, 3000);
}

// Start
init();
