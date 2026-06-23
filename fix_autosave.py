import os

js_path = r"c:\Users\carla\Desktop\AHK\Arvie Knob Macro\ui\app.js"
with open(js_path, "r", encoding="utf-8") as f:
    js = f.read()

find_add = """        slotsArr.push({index: newIdx, enabled: true, label: `Slot ${newIdx}`, color: "0xFF777777", type: "run_program", config: {}});
        renderPieChart();
        saveConfig();
    });"""
replace_add = """        slotsArr.push({index: newIdx, enabled: true, label: `Slot ${newIdx}`, color: "0xFF777777", type: "run_program", config: {}});
        renderPieChart();
    });"""

find_delete = """            } else {
                DOM.slotEditor.style.display = 'none';
            }
            renderPieChart();
            saveConfig();
        }
    });"""
replace_delete = """            } else {
                DOM.slotEditor.style.display = 'none';
            }
            renderPieChart();
        }
    });"""

js = js.replace(find_add, replace_add)
js = js.replace(find_delete, replace_delete)

with open(js_path, "w", encoding="utf-8") as f:
    f.write(js)
print("Removed saveConfig from add/delete slice!")
