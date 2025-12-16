import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import re
import numpy as np

# -------------------- Tab 1: Remove Missing Temperatures --------------------
class TemperatureFixerTab:
    def __init__(self, frame):
        self.frame = frame
        self.f06_path = ""
        self.dat_folder = ""

        tk.Label(frame, text="Select .f06 File:").pack(anchor='w', padx=10, pady=(10, 0))
        self.f06_entry = tk.Entry(frame, state="readonly", relief="sunken")
        self.f06_entry.pack(fill='x', padx=10, pady=2)
        tk.Button(frame, text="Browse", command=self.select_f06).pack(padx=10)

        tk.Label(frame, text="Select Folder with temperature Files:").pack(anchor='w', padx=10, pady=(15, 0))
        self.folder_entry = tk.Entry(frame, state="readonly", relief="sunken")
        self.folder_entry.pack(fill='x', padx=10, pady=2)
        tk.Button(frame, text="Browse", command=self.select_dat_folder).pack(padx=10)

        tk.Button(frame, text="Run Processing", command=self.process_files, bg="#4CAF50", fg="white").pack(padx=10, pady=15)

    def select_f06(self):
        path = filedialog.askopenfilename(filetypes=[("F06 Files", "*.f06")])
        if path:
            self.f06_path = path
            self.f06_entry.config(state='normal')
            self.f06_entry.delete(0, tk.END)
            self.f06_entry.insert(0, path)
            self.f06_entry.config(state='readonly')

    def select_dat_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.dat_folder = path
            self.folder_entry.config(state='normal')
            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, path)
            self.folder_entry.config(state='readonly')

    def extract_missing_ids(self):
        missing_ids = set()
        pattern = re.compile(r"TEMPERATURE SET \d+ REFERENCES UNDEFINED GRID POINT (\d+)")
        with open(self.f06_path, 'r') as f:
            for line in f:
                match = pattern.search(line)
                if match:
                    missing_ids.add(match.group(1))
        return missing_ids

    def process_files(self):
        if not self.f06_path or not self.dat_folder:
            messagebox.showerror("Error", "Please select both .f06 file and .dat folder.")
            return

        missing_ids = self.extract_missing_ids()
        if not missing_ids:
            messagebox.showinfo("No IDs Found", "No missing temperature IDs found in the .f06 file.")
            return

        output_folder = os.path.join(self.dat_folder, "modified_dat_files")
        os.makedirs(output_folder, exist_ok=True)

        for filename in os.listdir(self.dat_folder):
            if filename.endswith(".dat"):
                input_path = os.path.join(self.dat_folder, filename)
                output_path = os.path.join(output_folder, filename)
                with open(input_path, 'r') as infile:
                        lines = infile.readlines()

                with open(output_path, 'w') as outfile:
                        for line in lines:
                                stripped_line = line.strip()
                                if stripped_line.startswith("TEMP") and not stripped_line.startswith("$"):
                                        if any(grid_id in line for grid_id in missing_ids):
                                                line = "$" + line
                                outfile.write(line)
        messagebox.showinfo("Done", f"All files processed.\nModified files saved in:\n{output_folder}")

# -------------------- Tab 2: Spread Temperature --------------------
class TemperatureDiffuserTab:
    def __init__(self, frame):
        self.frame = frame

        tk.Label(frame, text="Select Temperature Folder:").pack()
        self.temp_entry = tk.Entry(frame, width=70)
        self.temp_entry.pack(pady=2)
        tk.Button(frame, text="Browse", command=self.select_temp_folder).pack()

        tk.Label(frame, text="Select Grid Folder (BDF/DAT files):").pack(pady=(10, 0))
        self.elem_entry = tk.Entry(frame, width=70)
        self.elem_entry.pack(pady=2)
        tk.Button(frame, text="Browse", command=self.select_grid_folder).pack()

        tk.Button(frame, text="Run Diffusion and Save", command=self.run_diffusion, bg="lightblue").pack(pady=15)

        self.status_label = tk.Label(frame, text="", fg="green", wraplength=580)
        self.status_label.pack()

    def update_status(self, message, color="black"):
        self.status_label.config(text=message, fg=color)

    def select_temp_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.temp_entry.delete(0, tk.END)
            self.temp_entry.insert(0, path)
            self.update_status("Temperature folder selected.")

    def select_grid_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.elem_entry.delete(0, tk.END)
            self.elem_entry.insert(0, path)
            self.update_status("Grid folder selected.")

    def load_temp_file(self, file_path):
        temp_data = {}
        sid_str = None
        with open(file_path, 'r') as f:
            for line in f:
                if line.startswith('TEMP'):
                    try:
                        if sid_str is None:
                            sid_str = line[8:16].strip()
                        node_str = line[16:24].strip()
                        temp_str = line[24:32].strip()
                        if sid_str and node_str and temp_str:
                            node_id = int(node_str)
                            temp = float(temp_str)
                            temp_data[node_id] = temp
                    except (ValueError, IndexError):
                        continue
        return sid_str, temp_data

    def load_grid_file(self, file_path):
        elements = {}
        with open(file_path, 'r') as f:
            for line in f:
                try:
                    if line.startswith('CQUAD4'):
                        elem_id = int(line[8:16].strip())
                        nodes = [int(line[24:32]), int(line[32:40]), int(line[40:48]), int(line[48:56])]
                        elements[elem_id] = nodes
                    elif line.startswith('CTRIA3'):
                        elem_id = int(line[8:16].strip())
                        nodes = [int(line[24:32]), int(line[32:40]), int(line[40:48])]
                        elements[elem_id] = nodes
                except (ValueError, IndexError):
                    continue
        return elements

    def propagate_temperature(self, temp_known, elements):
        temp_all = temp_known.copy()
        nodes_without_temp = {node for nodes in elements.values() for node in nodes if node not in temp_all}
        while nodes_without_temp:
            updated = False
            for nodes in elements.values():
                known = [temp_all[n] for n in nodes if n in temp_all]
                unknown = [n for n in nodes if n not in temp_all]
                if known and unknown and len(known) >= 1:
                    avg_temp = np.mean(known)
                    for node in unknown:
                        if node not in temp_all:
                            temp_all[node] = avg_temp
                            updated = True
            nodes_without_temp = {node for nodes in elements.values() for node in nodes if node not in temp_all}
            if not updated:
                break

        return temp_all

    def run_diffusion(self):
        temp_folder = self.temp_entry.get()
        grid_folder = self.elem_entry.get()

        if not temp_folder or not grid_folder:
            self.update_status("Please select both folders.", "red")
            return

        all_elements = {}
        for grid_file in os.listdir(grid_folder):
            if grid_file.lower().endswith(('.bdf', '.dat', '.blk')):
                elements = self.load_grid_file(os.path.join(grid_folder, grid_file))
                all_elements.update(elements)

        output_folder = os.path.join(temp_folder, "diffused_results")
        os.makedirs(output_folder, exist_ok=True)

        count = 0
        for temp_file in os.listdir(temp_folder):
            if temp_file.lower().endswith(".dat"):
                sid_str, temp_data = self.load_temp_file(os.path.join(temp_folder, temp_file))
                if not sid_str or not temp_data:
                    continue
                temp_all = self.propagate_temperature(temp_data, all_elements)
                existing_nodes = set(temp_data.keys())
                with open(os.path.join(temp_folder, temp_file), 'r') as f:
                    content = f.read()
                with open(os.path.join(output_folder, temp_file), 'w') as f:
                    f.write(content.strip() + '\n')
                    f.write("$$$ New node and its interpolated temperature $$$\n")
                    for node in sorted(temp_all):
                        if node not in existing_nodes:
                            f.write(f"{'TEMP':<8}{int(sid_str):8d}{node:8d}{temp_all[node]:8.3f}\n")
                count += 1

        self.update_status(f"✅ Diffusion complete! {count} files saved in {output_folder}", "green")


# -------------------- Main App --------------------
def main():
    root = tk.Tk()
    root.title("Temperature Tools")
    root.geometry("820x400")

    notebook = ttk.Notebook(root)

    # Tab 1
    tab1_frame = tk.Frame(notebook)
    TemperatureFixerTab(tab1_frame)
    notebook.add(tab1_frame, text="Remove Missing TEMP")

    # Tab 2
    tab2_frame = tk.Frame(notebook)
    TemperatureDiffuserTab(tab2_frame)
    notebook.add(tab2_frame, text="Spread TEMP to Missing Nodes")

    notebook.pack(fill='both', expand=True)
    root.mainloop()

if __name__ == "__main__":
    main()
