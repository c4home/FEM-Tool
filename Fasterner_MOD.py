import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import platform
import subprocess

# ----------- Function for PFAST Modification -----------
def update_pfast_lines(filename, element_ids, new_diameter, kt1, kt2, kt3):
    seen = set()
    unique_element_ids = []
    duplicates = []

    for eid in element_ids:
        if eid in seen:
            duplicates.append(eid)
        else:
            seen.add(eid)
            unique_element_ids.append(eid)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_filename = os.path.join(script_dir, "updated_" + os.path.basename(filename))
    found_ids = set()

    with open(filename, 'r') as infile, open(output_filename, 'w') as outfile:
        lines = infile.readlines()
        i = 0
        while i < len(lines):
            line = lines[i]
            if line.strip().startswith("PFAST"):
                field1 = line[0:8].strip()
                field2 = line[8:16].strip()
                element_id = field2

                if element_id in unique_element_ids:
                    new_line = f"{field1:<8}{element_id:>8}{str(new_diameter):^8}{line[24:32]:>8}       0{str(kt1):>8}{str(kt2):>8}{str(kt3):>8}    100.\n"
                    outfile.write(new_line)
                    i += 1
                    outfile.write(lines[i])
                    found_ids.add(element_id)
                else:
                    outfile.write(line)
            else:
                outfile.write(line)
            i += 1

    missing_ids = set(element_ids) - found_ids
    return os.path.abspath(output_filename), len(found_ids), missing_ids, duplicates

def browse_file(entry):
    path = filedialog.askopenfilename(title="Select .blt file", filetypes=[("BLT Files", "*.blt"), ("All Files", "*.*")])
    if path:
        entry.delete(0, tk.END)
        entry.insert(0, path)

def open_folder(path):
    folder = os.path.dirname(path)
    if platform.system() == "Windows":
        subprocess.Popen(f'explorer "{folder}"')
    elif platform.system() == "Darwin":
        subprocess.Popen(["open", folder])
    elif platform.system() == "Linux":
        subprocess.Popen(["xdg-open", folder])

def process_pfast(file_entry, elements_entry, diameter_entry, kt1_entry, kt2_entry, kt3_entry, result_label, duplicates_label, missing_label):
    try:
        filename = file_entry.get()
        element_ids = [eid.strip() for eid in elements_entry.get().split(",") if eid.strip()]
        diameter = diameter_entry.get().strip()
        kt1 = kt1_entry.get().strip()
        kt2 = kt2_entry.get().strip()
        kt3 = kt3_entry.get().strip()

        if not filename or not os.path.isfile(filename):
            raise ValueError("Invalid file selected.")

        output_path, found_ids, missing_ids, duplicates = update_pfast_lines(filename, element_ids, diameter, kt1, kt2, kt3)

        result_label.config(text=f"✅ File saved at:\n{output_path}\n {len(element_ids)} element ID(s) in your list \n 🔁 {found_ids} PFAST line(s) updated.", fg="green")
        duplicates_label.config(text=f"\n⚠️ {len(duplicates)} duplicated ID(s): {', '.join(sorted(duplicates))}" if duplicates else "", fg="red")
        missing_label.config(text=f"\n⚠️ {len(missing_ids)} ID(s) not found: {', '.join(sorted(missing_ids))}" if missing_ids else "", fg="red")
        open_folder(output_path)

    except Exception as e:
        messagebox.showerror("Error", str(e))

# ----------- Function for CFAST Disable -----------
def process_cfast(blt_entry, id_entry, status_label):
    path = blt_entry.get()
    if not path or not os.path.isfile(path):
        messagebox.showerror("Error", "Please select a .blt file.")
        return

    raw_ids = id_entry.get().replace(",", " ").split()
    try:
        element_ids = {str(int(eid)) for eid in raw_ids}
    except ValueError:
        messagebox.showerror("Invalid Input", "Please enter only numeric element IDs.")
        return

    output_path = os.path.join(os.path.dirname(path), "modified_" + os.path.basename(path))
    lines_modified = 0
    with open(path, 'r') as infile, open(output_path, 'w') as outfile:
        for line in infile:
            if line.startswith("CFAST") and any(eid in line for eid in element_ids):
                if not line.strip().startswith("$"):
                    line = "$" + line
                    lines_modified += 1
            outfile.write(line)

    status_label.config(
        text=f"✅ {lines_modified} CFAST line(s) modified.\nSaved to: {output_path}",
        fg="green"
    )
    open_folder(output_path)

# ----------- GUI Setup -----------
root = tk.Tk()
root.title("Fastener MOD")
root.geometry("820x640")

notebook = ttk.Notebook(root)
notebook.pack(fill='both', expand=True)

# ----------- Tab 1: PFAST Editor -----------
tab1 = ttk.Frame(notebook)
notebook.add(tab1, text="Modify PFAST Lines")

file_entry = tk.Entry(tab1, width=70)
elements_entry = tk.Entry(tab1, width=60)
diameter_entry = tk.Entry(tab1, width=20)
kt1_entry = tk.Entry(tab1, width=20)
kt2_entry = tk.Entry(tab1, width=20)
kt3_entry = tk.Entry(tab1, width=20)
result_label = tk.Label(tab1, text="", wraplength=600)
duplicates_label = tk.Label(tab1, text="", wraplength=600)
missing_label = tk.Label(tab1, text="", wraplength=600)

tk.Label(tab1, text="Select .blt file:").pack(pady=5)
file_entry.pack()
tk.Button(tab1, text="Browse", command=lambda: browse_file(file_entry)).pack()

tk.Label(tab1, text="List of element IDs (comma-separated):").pack()
elements_entry.pack()
tk.Label(tab1, text="New Diameter:").pack()
diameter_entry.pack()
tk.Label(tab1, text="KT 1:").pack()
kt1_entry.pack()
tk.Label(tab1, text="KT 2:").pack()
kt2_entry.pack()
tk.Label(tab1, text="KT 3:").pack()
kt3_entry.pack()

tk.Button(tab1, text="Process File", command=lambda: process_pfast(
    file_entry, elements_entry, diameter_entry, kt1_entry, kt2_entry, kt3_entry,
    result_label, duplicates_label, missing_label
), bg="#4CAF50", fg="white", padx=10, pady=5).pack(pady=10)

result_label.pack()
duplicates_label.pack()
missing_label.pack()

# ----------- Tab 2: CFAST Commenter -----------
tab2 = ttk.Frame(notebook)
notebook.add(tab2, text="Disable CFAST Lines")

tk.Label(tab2, text="Select .blt file:").pack(pady=10)
blt_entry = tk.Entry(tab2, width=70)
blt_entry.pack()
tk.Button(tab2, text="Browse", command=lambda: browse_file(blt_entry)).pack()

tk.Label(tab2, text="List of element IDs (comma separated):").pack(pady=10)
id_entry = tk.Entry(tab2, width=70)
id_entry.pack()

tk.Button(tab2, text="Process File", command=lambda: process_cfast(
    blt_entry, id_entry, cfast_status
), bg="#4CAF50", fg="white", padx=10, pady=5).pack(pady=20)

cfast_status = tk.Label(tab2, text="", wraplength=600)
cfast_status.pack()

# Run the app
root.mainloop()
