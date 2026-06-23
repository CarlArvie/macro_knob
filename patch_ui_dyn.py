import os

html_path = "c:\\Users\\carla\\Desktop\\AHK\\Arvie Knob Macro\\ui\\index.html"
with open(html_path, "r", encoding="utf-8") as f:
    html = f.read()

html = html.replace(
    '<div class="visualizer">',
    '<div style="text-align: center; margin-bottom: 1rem;"><button id="btn_add_slice" class="primary-btn" style="padding: 0.25rem 0.5rem; font-size: 0.8rem; background: #10b981; color: white;">+ Add Slice</button></div>\n                <div class="visualizer">'
)

html = html.replace(
    '                    <div class="form-group" id="group_sub_menu" style="display: none; margin-top: 1rem;">\n                        <button id="btn_enter_sub_menu" class="primary-btn" style="width: 100%; background: #a78bfa; color: #000;">Open Folder &rarr;</button>\n                    </div>',
    '                    <div class="form-group" id="group_sub_menu" style="display: none; margin-top: 1rem;">\n                        <button id="btn_enter_sub_menu" class="primary-btn" style="width: 100%; background: #a78bfa; color: #000;">Open Folder &rarr;</button>\n                    </div>\n                    <div style="margin-top: 2rem;">\n                        <button id="btn_delete_slice" class="primary-btn" style="width: 100%; background: #ef4444; color: white;">Delete this Slice</button>\n                    </div>'
)

with open(html_path, "w", encoding="utf-8") as f:
    f.write(html)
print("index.html patched")

js_path = "c:\\Users\\carla\\Desktop\\AHK\\Arvie Knob Macro\\ui\\app.js"
with open(js_path, "r", encoding="utf-8") as f:
    js = f.read()

js = js.replace(
    "    btnEnterSubMenu: document.getElementById('btn_enter_sub_menu'),",
    "    btnEnterSubMenu: document.getElementById('btn_enter_sub_menu'),\n    btnAddSlice: document.getElementById('btn_add_slice'),\n    btnDeleteSlice: document.getElementById('btn_delete_slice'),"
)

# Replace getSlotsAtPath to not force 8
js = js.replace(
    '            for(let j=0; j<8; j++) current[idx].slots.push({index: j, enabled: true, label: `Slot ${j}`, color: "0xFF777777", type: "run_program", config: {}});',
    '            for(let j=0; j<4; j++) current[idx].slots.push({index: j, enabled: true, label: `Slot ${j}`, color: "0xFF777777", type: "run_program", config: {}});'
)

# SVG rendering logic
svg_find = """    for (let i = 0; i < 8; i++) {
        const slotsArr = getSlotsAtPath(currentPath);
        const slot = slotsArr[i];
        
        const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
        const startAngle = (i * 45) - 90;
        const endAngle = startAngle + 45;
        
        const x1 = 150 + 130 * Math.cos(startAngle * Math.PI / 180);
        const y1 = 150 + 130 * Math.sin(startAngle * Math.PI / 180);
        const x2 = 150 + 130 * Math.cos(endAngle * Math.PI / 180);
        const y2 = 150 + 130 * Math.sin(endAngle * Math.PI / 180);
        
        path.setAttribute("d", `M 150 150 L ${x1} ${y1} A 130 130 0 0 1 ${x2} ${y2} Z`);
        path.setAttribute("fill", `#${slot.color.replace('0xFF', '')}`);
        path.setAttribute("stroke", "#2d2d2d");
        path.setAttribute("stroke-width", "2");
        path.style.cursor = "pointer";
        path.style.transition = "all 0.2s ease";
        if (slot.enabled === false) path.setAttribute("opacity", "0.15");
        DOM.svg.appendChild(path);

        const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
        const midAngle = startAngle + 22.5;
        const tx = 150 + 80 * Math.cos(midAngle * Math.PI / 180);
        const ty = 150 + 80 * Math.sin(midAngle * Math.PI / 180);
        
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
        path.addEventListener('mouseover', () => {
            path.setAttribute("fill", lightenColor(`#${slot.color.replace('0xFF', '')}`, 20));
        });
        path.addEventListener('mouseout', () => {
            path.setAttribute("fill", `#${slot.color.replace('0xFF', '')}`);
        });
    }"""
svg_replace = """    const slotsArr = getSlotsAtPath(currentPath);
    const N = slotsArr.length;
    if (N === 0) return;
    
    if (N === 1) {
        const slot = slotsArr[0];
        const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
        circle.setAttribute("cx", "150");
        circle.setAttribute("cy", "150");
        circle.setAttribute("r", "130");
        circle.setAttribute("fill", `#${slot.color.replace('0xFF', '')}`);
        circle.setAttribute("stroke", "#2d2d2d");
        circle.setAttribute("stroke-width", "2");
        circle.style.cursor = "pointer";
        if (slot.enabled === false) circle.setAttribute("opacity", "0.15");
        circle.addEventListener('click', () => loadSlot(0));
        DOM.svg.appendChild(circle);
        
        const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
        text.setAttribute("x", "150");
        text.setAttribute("y", "150");
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
        
        const x1 = 150 + 130 * Math.cos(startAngle * Math.PI / 180);
        const y1 = 150 + 130 * Math.sin(startAngle * Math.PI / 180);
        const x2 = 150 + 130 * Math.cos(endAngle * Math.PI / 180);
        const y2 = 150 + 130 * Math.sin(endAngle * Math.PI / 180);
        const largeArcFlag = sweepAngle > 180 ? 1 : 0;
        
        path.setAttribute("d", `M 150 150 L ${x1} ${y1} A 130 130 0 ${largeArcFlag} 1 ${x2} ${y2} Z`);
        path.setAttribute("fill", `#${slot.color.replace('0xFF', '')}`);
        path.setAttribute("stroke", "#2d2d2d");
        path.setAttribute("stroke-width", "2");
        path.style.cursor = "pointer";
        path.style.transition = "all 0.2s ease";
        if (slot.enabled === false) path.setAttribute("opacity", "0.15");
        DOM.svg.appendChild(path);

        const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
        const midAngle = startAngle + (sweepAngle / 2);
        const tx = 150 + 80 * Math.cos(midAngle * Math.PI / 180);
        const ty = 150 + 80 * Math.sin(midAngle * Math.PI / 180);
        
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
        path.addEventListener('mouseover', () => {
            path.setAttribute("fill", lightenColor(`#${slot.color.replace('0xFF', '')}`, 20));
        });
        path.addEventListener('mouseout', () => {
            path.setAttribute("fill", `#${slot.color.replace('0xFF', '')}`);
        });
    }"""
js = js.replace(svg_find, svg_replace)

# Add event listeners for add/delete
listeners = """    DOM.btnAddSlice.addEventListener('click', () => {
        const slotsArr = getSlotsAtPath(currentPath);
        const newIdx = slotsArr.length;
        slotsArr.push({index: newIdx, enabled: true, label: `Slot ${newIdx}`, color: "0xFF777777", type: "run_program", config: {}});
        renderPieChart();
        saveConfig();
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
            saveConfig();
        }
    });"""

js = js.replace(
    "    DOM.slotEnabled.addEventListener('change', updateCurrentSlot);",
    "    DOM.slotEnabled.addEventListener('change', updateCurrentSlot);\n" + listeners
)

js = js.replace(
    'const slotsArr = getSlotsAtPath(currentPath);\n    const slot = slotsArr[index];',
    'const slotsArr = getSlotsAtPath(currentPath);\n    if(slotsArr.length === 0) return;\n    const slot = slotsArr[index];'
)

with open(js_path, "w", encoding="utf-8") as f:
    f.write(js)
print("app.js patched")
