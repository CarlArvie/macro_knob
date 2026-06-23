import os

js_path = "c:\\Users\\carla\\Desktop\\AHK\\Arvie Knob Macro\\ui\\app.js"
with open(js_path, "r", encoding="utf-8") as f:
    js = f.read()

js = js.replace('circle.setAttribute("cx", "150");', 'circle.setAttribute("cx", "0");')
js = js.replace('circle.setAttribute("cy", "150");', 'circle.setAttribute("cy", "0");')
js = js.replace('circle.setAttribute("r", "130");', 'circle.setAttribute("r", "90");')

js = js.replace('text.setAttribute("x", "150");', 'text.setAttribute("x", "0");')
js = js.replace('text.setAttribute("y", "150");', 'text.setAttribute("y", "0");')

js = js.replace('const x1 = 150 + 130 * Math.cos(startAngle * Math.PI / 180);', 'const x1 = 90 * Math.cos(startAngle * Math.PI / 180);')
js = js.replace('const y1 = 150 + 130 * Math.sin(startAngle * Math.PI / 180);', 'const y1 = 90 * Math.sin(startAngle * Math.PI / 180);')
js = js.replace('const x2 = 150 + 130 * Math.cos(endAngle * Math.PI / 180);', 'const x2 = 90 * Math.cos(endAngle * Math.PI / 180);')
js = js.replace('const y2 = 150 + 130 * Math.sin(endAngle * Math.PI / 180);', 'const y2 = 90 * Math.sin(endAngle * Math.PI / 180);')

js = js.replace('path.setAttribute("d", `M 150 150 L ${x1} ${y1} A 130 130 0 ${largeArcFlag} 1 ${x2} ${y2} Z`);', 'path.setAttribute("d", `M 0 0 L ${x1} ${y1} A 90 90 0 ${largeArcFlag} 1 ${x2} ${y2} Z`);')

js = js.replace('const tx = 150 + 80 * Math.cos(midAngle * Math.PI / 180);', 'const tx = 60 * Math.cos(midAngle * Math.PI / 180);')
js = js.replace('const ty = 150 + 80 * Math.sin(midAngle * Math.PI / 180);', 'const ty = 60 * Math.sin(midAngle * Math.PI / 180);')

with open(js_path, "w", encoding="utf-8") as f:
    f.write(js)
print("app.js fixed")
