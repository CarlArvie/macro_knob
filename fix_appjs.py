import os, re

js_path = "c:\\Users\\carla\\Desktop\\AHK\\Arvie Knob Macro\\ui\\app.js"
with open(js_path, "r", encoding="utf-8") as f:
    js = f.read()

# Replace the entire renderPieChart function
start_str = "function renderPieChart() {"
end_str = "function loadSlot(index) {"

start_idx = js.find(start_str)
end_idx = js.find(end_str)

if start_idx != -1 and end_idx != -1:
    new_render = """function renderPieChart() {
    DOM.svg.innerHTML = '';
    const slotsArr = getSlotsAtPath(currentPath);
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

"""
    js = js[:start_idx] + new_render + js[end_idx:]
    with open(js_path, "w", encoding="utf-8") as f:
        f.write(js)
    print("Fixed renderPieChart")
else:
    print("Could not find renderPieChart bounds")
