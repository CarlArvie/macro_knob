import os

html_path = r"c:\Users\carla\Desktop\AHK\Arvie Knob Macro\ui\index.html"
with open(html_path, "r", encoding="utf-8") as f:
    html = f.read()

find_select = """                            <option value="open_url">Open URL</option>"""
replace_select = """                            <option value="open_url">Open URL</option>
                            <option value="open_folder">Open File / Folder</option>"""

if find_select in html:
    html = html.replace(find_select, replace_select)
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    print("Added Open File / Folder successfully!")
else:
    print("Could not find the string to replace.")
