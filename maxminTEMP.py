import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import os
import glob

def parse_temp_line(line):
    """
    Parse a TEMP line, handling both standard and merged fixed-width formats.
    
    Supported formats:
    1. Standard: TEMP  579  96007025  74.58570  (4 parts)
    2. Merged A: TEMP  579  9600702574.58570    (3 parts, Node+Temp merged)
    3. Merged B: TEMP  59592000000  -39.403     (3 parts, FileID+Node merged)
    """
    line = line.strip()
    if not line.startswith("TEMP"):
        return None, None, None
        
    parts = line.split()
    # parts[0] is always "TEMP"
    
    file_id = None
    node_id = None
    temp_val = None

    try:
        # Case 1: Standard spaced format (4 columns)
        if len(parts) == 4:
            file_id = parts[1]
            node_id = parts[2]
            temp_val = float(parts[3])
            
        # Case 2: Merged/Stuck columns (3 columns detected)
        elif len(parts) == 3:
            # Check for Merged Node + Temp (e.g., "9600702574.58570")
            # Logic: If the 3rd part is long (>8 chars) and has a decimal, it's likely Node+Temp.
            if len(parts[2]) > 8 and '.' in parts[2] and len(parts[1]) <= 8:
                file_id = parts[1]
                merged_part = parts[2]
                # NASTRAN fixed format usually gives 8 chars for Node ID
                node_id = merged_part[:8]      # First 8 digits
                temp_val = float(merged_part[8:]) # The rest is temperature
                
            # Check for Merged FileID + Node (Old code logic, e.g., "59592000000")
            else:
                merged_part = parts[1]
                temp_val = float(parts[2])
                # Old logic: First 3 are FileID, rest is NodeID
                file_id = merged_part[:3]
                node_id = merged_part[3:]
                
    except (IndexError, ValueError):
        return None, None, None
        
    return file_id, node_id, temp_val

def scan_folder():
    folder = filedialog.askdirectory(title="Select folder with .dat files")
    if not folder:
        return

    temps = []  # list of (temp_value, filepath)

    pattern = os.path.join(folder, "*.dat")
    for filepath in glob.glob(pattern):
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                file_id, node_id, temp_val = parse_temp_line(line)
                if temp_val is None:
                    continue
                temps.append((temp_val, filepath))

    if not temps:
        messagebox.showinfo("Result", "No TEMP values found in .dat files.")
        return

    min_value, min_file = min(temps, key=lambda x: x[0])
    max_value, max_file = max(temps, key=lambda x: x[0])

    min_label_var.set(f"Min TEMP: {min_value:.3f} in {os.path.basename(min_file)}")
    max_label_var.set(f"Max TEMP: {max_value:.3f} in {os.path.basename(max_file)}")

def scan_node_min_max():
    folder = filedialog.askdirectory(title="Select folder with .dat files")
    if not folder:
        return

    node_query = simpledialog.askstring("Node ID", "Enter node ID (e.g., 92000000):")
    if not node_query:
        return
    node_query = node_query.strip()

    node_temps = []  # (temp_value, filepath)

    pattern = os.path.join(folder, "*.dat")
    for filepath in glob.glob(pattern):
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                file_id, node_id, temp_val = parse_temp_line(line)
                if temp_val is None:
                    continue
                if node_id == node_query:
                    node_temps.append((temp_val, filepath))

    if not node_temps:
        messagebox.showinfo("Result", f"No TEMP values found for node {node_query}.")
        return

    min_node, min_file = min(node_temps, key=lambda x: x[0])
    max_node, max_file = max(node_temps, key=lambda x: x[0])

    node_label_var.set(
        f"Node {node_query} - Min: {min_node:.3f} in {os.path.basename(min_file)}, "
        f"Max: {max_node:.3f} in {os.path.basename(max_file)}"
    )

# --- Tkinter UI ---
root = tk.Tk()
root.title("DAT Temperature Scanner")

frame = tk.Frame(root, padx=10, pady=10)
frame.pack()

btn = tk.Button(frame, text="Select folder and scan", command=scan_folder)
btn.pack(pady=5)

min_label_var = tk.StringVar(value="Min TEMP: -")
max_label_var = tk.StringVar(value="Max TEMP: -")

min_label = tk.Label(frame, textvariable=min_label_var)
max_label = tk.Label(frame, textvariable=max_label_var)

node_btn = tk.Button(frame, text="Scan specific node min/max", command=scan_node_min_max)
node_btn.pack(pady=5)

node_label_var = tk.StringVar(value="Node TEMP: -")
node_label = tk.Label(frame, textvariable=node_label_var)
node_label.pack(pady=2)

min_label.pack(pady=2)
max_label.pack(pady=2)

root.mainloop()
