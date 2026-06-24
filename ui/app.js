let configData = null;
let activeSlotIndex = 0;
let currentPath = [];

const DOM = {
    isEnabled: document.getElementById('is_enabled'),
    enableHapticSound: document.getElementById('enable_haptic_sound'),
    toggleHotkey: document.getElementById('toggle_hotkey'),
    slotEnabled: document.getElementById('slot_enabled'),
    interactionMode: document.getElementById('interaction_mode'),
    hotkeyOverride: document.getElementById('hotkey_override'),
    rotaryNext: document.getElementById('rotary_next'),
    rotaryPrev: document.getElementById('rotary_prev'),
    holdThreshold: document.getElementById('hold_threshold_ms'),
    radialSize: document.getElementById('radial_size'),
      menuSpawnLocation: document.getElementById('menu_spawn_location'),
      autoHideTimerS: document.getElementById('auto_hide_timer_s'),
    showTrayIcon: document.getElementById('show_tray_icon'),
    debugLog: document.getElementById('debug_log'),
    
    svg: document.getElementById('pie-chart'),
    
    editorTitle: document.getElementById('editor-title'),
    slotLabel: document.getElementById('slot_label'),
    slotColor: document.getElementById('slot_color'),
    btnResetColor: document.getElementById('btn_reset_color'),
    slotColorPicker: document.getElementById('slot_color_picker'),
    slotType: document.getElementById('slot_type'),
    slotPath: document.getElementById('slot_path'),
    slotUrl: document.getElementById('slot_url'),
    
    groupPath: document.getElementById('group_path'),
    groupUrl: document.getElementById('group_url'),
    groupSubMenu: document.getElementById('group_sub_menu'),
    btnEnterSubMenu: document.getElementById('btn_enter_sub_menu'),
    btnAddSlice: document.getElementById('btn_add_slice'),
    btnDeleteSlice: document.getElementById('btn_delete_slice'),
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
            for(let j=0; j<4; j++) current[idx].slots.push({index: j, enabled: true, label: `Slot ${j}`, color: "0xFF777777", type: "run_program", config: {}});
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
    DOM.enableHapticSound.checked = g.enable_haptic_sound ?? true;
    DOM.toggleHotkey.value = g.toggle_hotkey || "F14";
    DOM.interactionMode.value = g.interaction_mode || "mouse_hold";
    DOM.hotkeyOverride.value = g.hotkey_override || "";
    DOM.rotaryNext.value = g.rotary_next || "";
    DOM.rotaryPrev.value = g.rotary_prev || "";
    DOM.holdThreshold.value = g.hold_threshold_ms || 150;
    DOM.radialSize.value = g.radial_size || "medium";
      DOM.menuSpawnLocation.value = g.menu_spawn_location || "cursor";
      DOM.autoHideTimerS.value = g.auto_hide_timer_s !== undefined ? g.auto_hide_timer_s : 10;
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
    const slotsArr = getSlotsAtPath(currentPath);
    const N = slotsArr.length;
    if (N === 0) return;
    
    if (N === 1) {
        const slot = slotsArr[0];
        const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
        circle.setAttribute("cx", "0");
        circle.setAttribute("cy", "0");
        circle.setAttribute("r", "90");
        circle.setAttribute("fill", `#${slot.color.replace('0xFF', '')}`);
        circle.setAttribute("stroke", "#2d2d2d");
        circle.setAttribute("stroke-width", "2");
        circle.style.cursor = "pointer";
        if (slot.enabled === false) circle.setAttribute("opacity", "0.15");
        circle.addEventListener('click', () => loadSlot(0));
        DOM.svg.appendChild(circle);
        
        const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
        text.setAttribute("x", "0");
        text.setAttribute("y", "0");
        text.setAttribute("text-anchor", "middle");
        text.setAttribute("dominant-baseline", "middle");
        text.setAttribute("fill", "#ffffff");
        text.setAttribute("font-size", "12px");
        text.setAttribute("font-weight", "600");
        text.style.pointerEvents = "none";
        text.textContent = slot.label || "Slot 1";
        if (slot.enabled === false) text.setAttribute("opacity", "0.15");
        DOM.svg.appendChild(text);
        return;
    }
    
    const sweepAngle = 360 / N;
    for (let i = 0; i < N; i++) {
        const slot = slotsArr[i];
        const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
        const startAngle = (i * sweepAngle) - 90 - (sweepAngle / 2);
        const endAngle = startAngle + sweepAngle;
        
        const x1 = 90 * Math.cos(startAngle * Math.PI / 180);
        const y1 = 90 * Math.sin(startAngle * Math.PI / 180);
        const x2 = 90 * Math.cos(endAngle * Math.PI / 180);
        const y2 = 90 * Math.sin(endAngle * Math.PI / 180);
        const largeArcFlag = sweepAngle > 180 ? 1 : 0;
        
        path.setAttribute("d", `M 0 0 L ${x1} ${y1} A 90 90 0 ${largeArcFlag} 1 ${x2} ${y2} Z`);
        path.setAttribute("fill", `#${slot.color.replace('0xFF', '')}`);
        path.setAttribute("stroke", "#2d2d2d");
        path.setAttribute("stroke-width", "2");
        path.style.cursor = "pointer";
        path.style.transition = "all 0.2s ease";
        if (slot.enabled === false) path.setAttribute("opacity", "0.15");
        DOM.svg.appendChild(path);

        const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
        const midAngle = startAngle + (sweepAngle / 2);
        const tx = 60 * Math.cos(midAngle * Math.PI / 180);
        const ty = 60 * Math.sin(midAngle * Math.PI / 180);
        
        text.setAttribute("x", tx);
        text.setAttribute("y", ty);
        text.setAttribute("text-anchor", "middle");
        text.setAttribute("dominant-baseline", "middle");
        text.setAttribute("fill", "#ffffff");
        text.setAttribute("font-size", "12px");
        text.setAttribute("font-weight", "600");
        text.style.pointerEvents = "none";
        
        let label = slot.label || `Slot ${i+1}`;
        if (label.length > 10) label = label.substring(0, 8) + '..';
        text.textContent = label;
        if (slot.enabled === false) text.setAttribute("opacity", "0.15");
        DOM.svg.appendChild(text);

        path.addEventListener('click', () => loadSlot(i));
        // Add visual highlighting on hover
        path.addEventListener('mouseover', () => {
            path.setAttribute("opacity", "0.8");
        });
        path.addEventListener('mouseout', () => {
            if (slot.enabled === false) path.setAttribute("opacity", "0.15");
            else path.setAttribute("opacity", "1");
        });
    }
}

function loadSlot(index) {
    activeSlotIndex = index;
    const slotsArr = getSlotsAtPath(currentPath);
    if(slotsArr.length === 0) return;
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
    DOM.btnAddSlice.addEventListener('click', () => {
        const slotsArr = getSlotsAtPath(currentPath);
        const newIdx = slotsArr.length;
        slotsArr.push({index: newIdx, enabled: true, label: `Slot ${newIdx}`, color: "0xFF777777", type: "run_program", config: {}});
        renderPieChart();
    });

    DOM.btnDeleteSlice.addEventListener('click', () => {
        const slotsArr = getSlotsAtPath(currentPath);
        if (slotsArr.length > 0) {
            slotsArr.splice(activeSlotIndex, 1);
            for(let i=0; i<slotsArr.length; i++) slotsArr[i].index = i;
            activeSlotIndex = Math.max(0, activeSlotIndex - 1);
            if (slotsArr.length > 0) {
                loadSlot(activeSlotIndex);
            } else {
                DOM.slotEditor.style.display = 'none';
            }
            renderPieChart();
        }
    });
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

    DOM.btnResetColor.addEventListener('click', () => {
        DOM.slotColor.value = "0xFF777777";
        DOM.slotColorPicker.value = extractHexFromARGB("0xFF777777");
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
    configData.global.enable_haptic_sound = DOM.enableHapticSound.checked;
    configData.global.toggle_hotkey = DOM.toggleHotkey.value;
    configData.global.interaction_mode = DOM.interactionMode.value;
    configData.global.hotkey_override = DOM.hotkeyOverride.value;
    configData.global.rotary_next = DOM.rotaryNext.value;
    configData.global.rotary_prev = DOM.rotaryPrev.value;
    configData.global.hold_threshold_ms = parseInt(DOM.holdThreshold.value) || 150;
    configData.global.radial_size = DOM.radialSize.value;
    configData.global.menu_spawn_location = DOM.menuSpawnLocation.value;
    configData.global.auto_hide_timer_s = parseInt(DOM.autoHideTimerS.value, 10);
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
            DOM.saveBtn.textContent = "Save Changes";
            DOM.saveBtn.disabled = false;
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
