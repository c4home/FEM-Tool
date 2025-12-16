import re
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

selected_file_path = None

def extract_grid_points(f06_path):
    grid_points = []
    pattern = r"GRID POINT\s+(\d+)\s+COMPONENT\s+1 ILLEGALLY DEFINED"
    with open(f06_path, "r") as file:
        for line in file:
            match = re.search(pattern, line)
            if match:
                grid_points.append(match.group(1))
    return grid_points

def extract_elements_with_curvature_issue(f06_path):
    elements = []
    pattern = r"ELEMENT\s+(\d+)\s+HAS TOO MUCH CURVATURE"
    with open(f06_path, "r") as file:
        for line in file:
            match = re.search(pattern, line)
            if match:
                elements.append(match.group(1))
    return elements

def copy_to_clipboard(data_list):
    root.clipboard_clear()
    root.clipboard_append(", ".join(data_list))
    root.update()

def select_f06_file():
    global selected_file_path
    filepath = filedialog.askopenfilename(title="Select F06 file", filetypes=[("F06 files", "*.f06"), ("All files", "*.*")])
    if filepath:
        selected_file_path = filepath
        label_selected_file.config(text=f"Selected file: {filepath}")
        update_all_results()

def extract_user_fatal_2101_grid_points(f06_path):
    grid_points = []
    pattern_error_start = r"\*\*\* USER FATAL MESSAGE 2101"
    pattern_grid_point_id = r"GRID POINT\s+(\d+)\s+COMPONENT"
    with open(f06_path, "r") as file:
        lines = file.readlines()
        for i, line in enumerate(lines):
            if re.search(pattern_error_start, line):
                # Usually the grid point id is on the same line or a few lines below
                match = re.search(pattern_grid_point_id, line)
                if match:
                    grid_points.append(match.group(1))
                else:
                    for j in range(i+1, min(i+5, len(lines))):
                        match = re.search(pattern_grid_point_id, lines[j])
                        if match:
                            grid_points.append(match.group(1))
                            break
    return grid_points

def extract_user_fatal_7546_ids(f06_path):
    element_ids = []
    pattern_error_start = r"\*\*\* USER FATAL MESSAGE 7546"
    pattern_element_id = r"THE SHID1 \(OR SHID2\)=\s+(\d+)"
    with open(f06_path, "r") as file:
        lines = file.readlines()
        for i, line in enumerate(lines):
            if re.search(pattern_error_start, line):
                # The element ID is usually a couple of lines below error start
                # Scan next few lines for the SHID1 or SHID2 ID
                for j in range(i+1, min(i+5, len(lines))):
                    match = re.search(pattern_element_id, lines[j])
                    if match:
                        element_ids.append(match.group(1))
                        break
    return element_ids

def extract_user_fatal_7549_ids(f06_path):
    element_ids = []
    pattern_error_start = r"\*\*\* USER FATAL MESSAGE 7549"
    pattern_element_id = r"CFAST ELEMENT ID=(\d+)"
    with open(f06_path, "r") as file:
        lines = file.readlines()
        for i, line in enumerate(lines):
            if re.search(pattern_error_start, line):
                # The element ID is usually on the same line or next line
                match = re.search(pattern_element_id, line)
                if match:
                    element_ids.append(match.group(1))
                else:
                    # Search next few lines if needed
                    for j in range(i+1, min(i+5, len(lines))):
                        match = re.search(pattern_element_id, lines[j])
                        if match:
                            element_ids.append(match.group(1))
                            break
    return element_ids

def parse_totals_line(line_parts):
    values = []
    for v in line_parts:
        try:
            values.append(float(v))
        except ValueError:
            values.append(0.0)
    return values

def sum_totals(values):
    return sum(values)

def compare_totals(v1, v2):
    return abs(sum_totals(v1) - sum_totals(v2)) < 1e-12

def process_file(filename):
    with open(filename, 'r') as f:
        lines = f.readlines()

    section = None
    subcase = None
    oload_totals = {}
    spcforce_totals = {}
    mpcforce_totals = {}

    i = 0
    while i < len(lines):
        line = lines[i]
        line_strip = line.strip()

        if "OLOAD    RESULTANT" in line:
            section = "OLOAD"
            i += 1
            continue
        elif "SPCFORCE RESULTANT" in line:
            section = "SPCFORCE"
            i += 1
            continue
        elif "MPCFORCE RESULTANT" in line:
            section = "MPCFORCE"
            i += 1
            continue

        if section and line_strip == "":
            section = None
            i += 1
            continue

        subcase_match = re.match(r'0\s+(\d+)\s+', line)
        if subcase_match:
            subcase = int(subcase_match.group(1))
            i += 1
            continue

        if section and line_strip.startswith("TOTALS"):
            total_strs = line_strip.split()[1:]
            j = i + 1
            while len(total_strs) < 6 and j < len(lines):
                next_line = lines[j].strip()
                if next_line == "" or next_line.startswith("TOTALS") or re.match(r'0\s+\d+\s+', next_line):
                    break
                total_strs.extend(next_line.split())
                j += 1

            totals_values = parse_totals_line(total_strs)
            if section == "OLOAD":
                oload_totals[subcase] = totals_values
            elif section == "SPCFORCE":
                spcforce_totals[subcase] = totals_values
            elif section == "MPCFORCE":
                mpcforce_totals[subcase] = totals_values

            i = j
            continue
        i += 1

    results = []
    all_subcases = set(oload_totals.keys()) | set(spcforce_totals.keys()) | set(mpcforce_totals.keys())

    for sc in sorted(all_subcases):
        ovals = oload_totals.get(sc)
        svals = spcforce_totals.get(sc)
        mvals = mpcforce_totals.get(sc)
        if not ovals or not svals or not mvals:
            results.append((sc, "Missing data", "black"))
            continue
        if (compare_totals(ovals, svals) and compare_totals(ovals, mvals)):
            results.append((sc, "OK", "green"))
        else:
            results.append((sc, "not OK", "red"))
    return results, oload_totals, spcforce_totals, mpcforce_totals

def display_results(results, oload_totals, spcforce_totals, mpcforce_totals):
    col_width = 18
    sep = "|"
    def fmt_val(v): return f"{v:.6e}"

    def draw_separator(text_widget):
        total = "+" + "+".join(["-" * col_width] * 8) + "+\n"
        text_widget.insert(tk.END, total)

    text_area_loads.config(state='normal')
    text_area_loads.delete('1.0', tk.END)
    for sc, _, _ in results:
        ovals = oload_totals.get(sc)
        svals = spcforce_totals.get(sc)
        mvals = mpcforce_totals.get(sc)
        text_area_loads.insert(tk.END, f"Subcase {sc}:\n")
        draw_separator(text_area_loads)
        header_type = f"{'Type':^{col_width}}"
        col_titles = ["T1", "T2", "T3", "R1", "R2", "R3"]
        header_cols = "".join(f"{col:^{col_width}}" for col in col_titles)
        text_area_loads.insert(tk.END, sep + header_type + header_cols + sep + "\n")
        draw_separator(text_area_loads)

        # OLOAD
        if ovals:
            oload_line = f"{'OLOAD':^{col_width}}"
            oload_line += "".join(f"{fmt_val(v):>{col_width}}" for v in ovals)
        else:
            oload_line = f"{'OLOAD':^{col_width}}" + f"{'Missing':^{col_width * 6}}"
        text_area_loads.insert(tk.END, sep + oload_line + sep + "\n")

        # SPCFORCE
        if svals:
            spcforce_line = f"{'SPCFORCE':^{col_width}}"
            spcforce_line += "".join(f"{fmt_val(v):>{col_width}}" for v in svals)
        else:
            spcforce_line = f"{'SPCFORCE':^{col_width}}" + f"{'Missing':^{col_width * 6}}"
        text_area_loads.insert(tk.END, sep + spcforce_line + sep + "\n")

        # MPCFORCE
        if mvals:
            mpcforce_line = f"{'MPCFORCE':^{col_width}}"
            mpcforce_line += "".join(f"{fmt_val(v):>{col_width}}" for v in mvals)
        else:
            mpcforce_line = f"{'MPCFORCE':^{col_width}}" + f"{'Missing':^{col_width * 6}}"
        text_area_loads.insert(tk.END, sep + mpcforce_line + sep + "\n")

        # Status
        text_area_loads.insert(tk.END, sep)
        text_area_loads.insert(tk.END, f"{'Status':^{col_width}}")
        for o, s, m in zip(ovals if ovals else [], svals if svals else [], mvals if mvals else []):
            diff_osp = o + s
#            diff_omp = abs(o - m)
            if diff_osp < 1e-01:
                ok_text = "OK"
                pad_left = (col_width - len(ok_text)) // 2
                pad_right = col_width - pad_left - len(ok_text)
                text_area_loads.insert(tk.END, " " * pad_left)
                insert_index = text_area_loads.index(tk.END)
                text_area_loads.insert(tk.END, ok_text)
                end_index = text_area_loads.index(tk.END)
                text_area_loads.tag_add("green", insert_index, end_index)
                text_area_loads.insert(tk.END, " " * pad_right)
            else:
                not_ok_text = "not OK"
                pad_left = (col_width - len(not_ok_text)) // 2
                pad_right = col_width - pad_left - len(not_ok_text)
                text_area_loads.insert(tk.END, " " * pad_left)
                insert_index = text_area_loads.index(tk.END)
                text_area_loads.insert(tk.END, not_ok_text)
                end_index = text_area_loads.index(tk.END)
                text_area_loads.tag_add("red", insert_index, end_index)
                text_area_loads.insert(tk.END, " " * pad_right)

        text_area_loads.insert(tk.END, sep + "\n")
        draw_separator(text_area_loads)
        text_area_loads.insert(tk.END, "\n")
    text_area_loads.config(state='disabled')

def update_all_results():
    if not selected_file_path:
        messagebox.showwarning("Warning", "Please select an F06 file first.")
        return

    # Existing extraction calls
    grid_points = extract_grid_points(selected_file_path)
    text_area_grid.config(state='normal')
    text_area_grid.delete("1.0", tk.END)
    if grid_points:
        text_area_grid.insert(tk.END, f"Found {len(grid_points)} grid points:\n" + ", ".join(grid_points))
    else:
        text_area_grid.insert(tk.END, "No grid points found.")
    text_area_grid.config(state='disabled')

    elements = extract_elements_with_curvature_issue(selected_file_path)
    text_area_elements.config(state='normal')
    text_area_elements.delete("1.0", tk.END)
    if elements:
        text_area_elements.insert(tk.END, f"Found {len(elements)} elements with curvature issues:\n" + ", ".join(elements))
    else:
        text_area_elements.insert(tk.END, "No elements with curvature issues found.")
    text_area_elements.config(state='disabled')

    fatal_ids_7546 = extract_user_fatal_7546_ids(selected_file_path)
    text_area_fatal_ids.config(state='normal')
    text_area_fatal_ids.delete("1.0", tk.END)
    if fatal_ids_7546:
        text_area_fatal_ids.insert(tk.END, f"Found {len(fatal_ids_7546)} element IDs in USER FATAL MESSAGE 7546:\n" + ", ".join(fatal_ids_7546))
    else:
        text_area_fatal_ids.insert(tk.END, "No USER FATAL MESSAGE 7546 element IDs found.")
    text_area_fatal_ids.config(state='disabled')

    fatal_ids_7549 = extract_user_fatal_7549_ids(selected_file_path)
    text_area_fatal_7549_ids.config(state='normal')
    text_area_fatal_7549_ids.delete("1.0", tk.END)
    if fatal_ids_7549:
        text_area_fatal_7549_ids.insert(tk.END, f"Found {len(fatal_ids_7549)} element IDs in USER FATAL MESSAGE 7549:\n" + ", ".join(fatal_ids_7549))
    else:
        text_area_fatal_7549_ids.insert(tk.END, "No USER FATAL MESSAGE 7549 element IDs found.")
    text_area_fatal_7549_ids.config(state='disabled')

    fatal_grid_points_2101 = extract_user_fatal_2101_grid_points(selected_file_path)
    text_area_fatal_2101_grid_points.config(state='normal')
    text_area_fatal_2101_grid_points.delete("1.0", tk.END)
    if fatal_grid_points_2101:
        text_area_fatal_2101_grid_points.insert(tk.END, f"Found {len(fatal_grid_points_2101)} GRID POINT IDs in USER FATAL MESSAGE 2101:\n" + ", ".join(fatal_grid_points_2101))
    else:
        text_area_fatal_2101_grid_points.insert(tk.END, "No USER FATAL MESSAGE 2101 GRID POINT IDs found.")
    text_area_fatal_2101_grid_points.config(state='disabled')


    results, oload_totals, spcforce_totals, mpcforce_totals = process_file(selected_file_path)
    display_results(results, oload_totals, spcforce_totals, mpcforce_totals)

# --- GUI Setup ---

root = tk.Tk()
root.title("F06 Reader")

frame_top = tk.Frame(root, pady=10)
frame_top.pack(fill='x')

btn_select_file = tk.Button(frame_top, text="Select F06 File", command=select_f06_file)
btn_select_file.pack(side='left', padx=10)

label_selected_file = tk.Label(frame_top, text="No file selected")
label_selected_file.pack(side='left')

tab_control = ttk.Notebook(root)
tab_control.pack(expand=1, fill='both')

tab1 = ttk.Frame(tab_control)
tab_control.add(tab1, text='Extract Grid Points')
text_area_grid = scrolledtext.ScrolledText(tab1, width=170, height=15, font=("Consolas", 12))
text_area_grid.pack(fill='both', expand=True, padx=10, pady=10)
text_area_grid.config(state='disabled')

tab2 = ttk.Frame(tab_control)
tab_control.add(tab2, text='Extract Curvature Issues')
text_area_elements = scrolledtext.ScrolledText(tab2, width=170, height=15, font=("Consolas", 12))
text_area_elements.pack(fill='both', expand=True, padx=10, pady=10)
text_area_elements.config(state='disabled')

tab3 = ttk.Frame(tab_control)
tab_control.add(tab3, text='Show OLOAD, SPC, MPC Force Sum')
text_area_loads = scrolledtext.ScrolledText(tab3, width=170, height=25, font=("Consolas", 12))
text_area_loads.pack(fill='both', expand=True, padx=10, pady=10)
text_area_loads.config(state='disabled')

tab4 = ttk.Frame(tab_control)
tab_control.add(tab4, text='ERROR 7546 (MDG2SH) IS NOT A SHELL ELEMENT')
text_area_fatal_ids = scrolledtext.ScrolledText(tab4, width=170, height=15, font=("Consolas", 12))
text_area_fatal_ids.pack(fill='both', expand=True, padx=10, pady=10)
text_area_fatal_ids.config(state='disabled')

tab5 = ttk.Frame(tab_control)
tab_control.add(tab5, text='ERROR 7549 CFAST Element IDs')
text_area_fatal_7549_ids = scrolledtext.ScrolledText(tab5, width=170, height=15, font=("Consolas", 12))
text_area_fatal_7549_ids.pack(fill='both', expand=True, padx=10, pady=10)
text_area_fatal_7549_ids.config(state='disabled')

tab6 = ttk.Frame(tab_control)
tab_control.add(tab6, text='ERROR 2101 GRID POINTS')
text_area_fatal_2101_grid_points = scrolledtext.ScrolledText(tab6, width=170, height=15, font=("Consolas", 12))
text_area_fatal_2101_grid_points.pack(fill='both', expand=True, padx=10, pady=10)
text_area_fatal_2101_grid_points.config(state='disabled')

text_area_loads.tag_configure("green", foreground="green")
text_area_loads.tag_configure("red", foreground="red")
text_area_loads.tag_configure("black", foreground="black")

root.mainloop()
