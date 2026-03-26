import os
import csv
import tkinter as tk
from tkinter import filedialog, messagebox
from collections import Counter
import re

class STPExporterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("STP to CSV Exporter")
        self.root.geometry("550x250")

        self.folder_path = tk.StringVar()
        self.csv_path = tk.StringVar()

        # UI Elements
        tk.Label(root, text="Target Folder:", font=("Arial", 10, "bold")).grid(row=0, column=0, padx=10, pady=20, sticky="e")
        tk.Entry(root, textvariable=self.folder_path, width=45, state="readonly").grid(row=0, column=1, padx=5, pady=20)
        tk.Button(root, text="Browse...", command=self.browse_folder).grid(row=0, column=2, padx=10, pady=20)

        tk.Label(root, text="Save CSV As:", font=("Arial", 10, "bold")).grid(row=1, column=0, padx=10, pady=10, sticky="e")
        tk.Entry(root, textvariable=self.csv_path, width=45, state="readonly").grid(row=1, column=1, padx=5, pady=10)
        tk.Button(root, text="Save As...", command=self.save_csv_file).grid(row=1, column=2, padx=10, pady=10)

        tk.Button(root, text="Analyze & Export to CSV", command=self.run_search, bg="#0052cc", fg="white", font=("Arial", 11, "bold"), width=25).grid(row=2, column=0, columnspan=3, pady=30)

    def browse_folder(self):
        folder = filedialog.askdirectory(title="Select Folder to Search")
        if folder:
            self.folder_path.set(folder)

    def save_csv_file(self):
        csv_file = filedialog.asksaveasfilename(
            title="Save CSV File",
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        if csv_file:
            self.csv_path.set(csv_file)

    def run_search(self):
        folder = self.folder_path.get()
        csv_export_path = self.csv_path.get()

        if not folder or not os.path.isdir(folder):
            messagebox.showerror("Error", "Please select a valid folder.")
            return

        if not csv_export_path:
            messagebox.showerror("Error", "Please define a save location.")
            return

        file_entries = []
        dimension_counts = Counter()

        # Walk through directory
        for root_dir, dirs, files in os.walk(folder):
            for filename in files:
                if filename.lower().endswith(('.stp', '.step')):
                    # Remove the extension
                    name_without_ext = os.path.splitext(filename)[0]

                    # Split the filename based on '_'
                    parts = name_without_ext.split('_')

                    # Default empty values in case the format doesn't match perfectly
                    pn = parts[0] if len(parts) > 0 else ""
                    load_case = parts[1] if len(parts) > 1 else ""
                    location = parts[2] if len(parts) > 2 else ""
                    struct_type = parts[3] if len(parts) > 3 else ""
                    
                    # Extract material as the 5th element
                    material = parts[4] if len(parts) > 4 else ""
                    
                    # Assume dimension tag is now the 6th element
                    dimension_tag = parts[5] if len(parts) > 5 else ""

                    # Handle trailing dots (e.g., .1, .2) in dimension tags
                    dimension_tag_clean = re.sub(r'\.\d+$', '', dimension_tag)

                    # Append the full filename as well, including the material
                    file_entries.append((pn, load_case, location, struct_type, material, dimension_tag_clean, filename))
                    dimension_counts[dimension_tag_clean] += 1

        if not file_entries:
            messagebox.showinfo("Result", "No .stp or .step files found.")
            return

        # Sort the entries by Dimension Tag (index 5) first, then P/N
        file_entries.sort(key=lambda x: (x[5], x[0]))

        # Write data to CSV
        try:
            with open(csv_export_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.writer(csvfile, delimiter=';')

                # Write header row with the new Material column
                writer.writerow(["P/N", "Load case", "Location", "Structure Type", "Material", "Dimension tag", "File Name", "Quantity"])

                seen_tags = set()
                # Unpack the 7 items including file_name
                for pn, load_case, location, struct_type, material, dim_tag, file_name in file_entries:
                    # Print count only for the first occurrence of each tag
                    if dim_tag not in seen_tags:
                        count_to_print = dimension_counts[dim_tag]
                        seen_tags.add(dim_tag)
                    else:
                        count_to_print = "" 

                    # Write the row including the material variable
                    writer.writerow([pn, load_case, location, struct_type, material, dim_tag, file_name, count_to_print])

            messagebox.showinfo("Success", f"Found {len(file_entries)} STP files!\nExported to:\n{csv_export_path}")

        except Exception as e:
            messagebox.showerror("Error", f"Could not write to CSV.\n\n{e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = STPExporterApp(root)
    root.mainloop()
