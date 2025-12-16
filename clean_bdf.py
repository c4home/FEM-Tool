import tkinter as tk
from tkinter import filedialog, messagebox
import re
import os

class BDFCleanerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Nastran BDF Node Cleaner")
        self.root.geometry("500x250")

        # Variables to store file paths
        self.txt_path = tk.StringVar()
        self.bdf_path = tk.StringVar()

        # --- UI Layout ---
        
        # Section 1: Warning TXT File
        tk.Label(root, text="Select Warning (.txt) File:", font=("Arial", 10, "bold")).pack(pady=(10, 5))
        frame_txt = tk.Frame(root)
        frame_txt.pack(fill="x", padx=20)
        
        self.entry_txt = tk.Entry(frame_txt, textvariable=self.txt_path, width=40)
        self.entry_txt.pack(side="left", padx=5)
        tk.Button(frame_txt, text="Browse", command=self.browse_txt).pack(side="left")

        # Section 2: Input BDF File
        tk.Label(root, text="Select Input (.bdf) File:", font=("Arial", 10, "bold")).pack(pady=(10, 5))
        frame_bdf = tk.Frame(root)
        frame_bdf.pack(fill="x", padx=20)
        
        self.entry_bdf = tk.Entry(frame_bdf, textvariable=self.bdf_path, width=40)
        self.entry_bdf.pack(side="left", padx=5)
        tk.Button(frame_bdf, text="Browse", command=self.browse_bdf).pack(side="left")

        # Section 3: Action Button
        tk.Button(root, text="Process and Save New BDF", command=self.process_files, 
                  bg="#4CAF50", fg="white", font=("Arial", 11, "bold")).pack(pady=20)

        # Status Label
        self.status_label = tk.Label(root, text="Ready", fg="gray")
        self.status_label.pack(side="bottom", pady=5)

    def browse_txt(self):
        filename = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
        if filename:
            self.txt_path.set(filename)

    def browse_bdf(self):
        filename = filedialog.askopenfilename(filetypes=[("BDF Files", "*.bdf"), ("DAT Files", "*.dat"), ("All Files", "*.*")])
        if filename:
            self.bdf_path.set(filename)

    def process_files(self):
        txt_file = self.txt_path.get()
        bdf_file = self.bdf_path.get()

        if not txt_file or not bdf_file:
            messagebox.showerror("Error", "Please select both the TXT and BDF files.")
            return

        try:
            # 1. Parse the TXT file to find node IDs to delete
            nodes_to_delete = set()
            
            # Regex pattern to match: "nodes id 12345" inside the line
            # It looks for "nodes id" followed by spaces, followed by digits
            pattern = re.compile(r"nodes id\s+(\d+)")

            with open(txt_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if "Warning" in line and "found more than once" in line:
                        match = pattern.search(line)
                        if match:
                            nodes_to_delete.add(match.group(1))

            if not nodes_to_delete:
                messagebox.showwarning("Warning", "No duplicate node warnings found in the TXT file.")
                return

            self.status_label.config(text=f"Found {len(nodes_to_delete)} nodes to remove. Processing...")
            self.root.update()

            # 2. Ask where to save the result
            output_file = filedialog.asksaveasfilename(
                defaultextension=".bdf",
                filetypes=[("BDF Files", "*.bdf"), ("All Files", "*.*")],
                title="Save Cleaned BDF As"
            )
            
            if not output_file:
                self.status_label.config(text="Cancelled.")
                return

            # 3. Read BDF, Filter, and Write
            deleted_count = 0
            with open(bdf_file, 'r', encoding='utf-8') as fin, open(output_file, 'w', encoding='utf-8') as fout:
                for line in fin:
                    # Strip whitespace to check content, but keep original line for writing
                    clean_line = line.strip()
                    
                    # Check if line is a GRID card
                    # We look for lines starting with GRID or GRID*
                    if clean_line.startswith("GRID"):
                        # Split by whitespace to get fields
                        parts = clean_line.split()
                        
                        # Safety check: ensure there is at least a GRID keyword and an ID
                        if len(parts) >= 2:
                            node_id = parts[1]
                            
                            # Nastran sometimes uses GRID* for large field format. 
                            # Usually the ID is still the second item if split by space.
                            # If the ID is in the "nodes_to_delete" set, we skip writing it.
                            if node_id in nodes_to_delete:
                                deleted_count += 1
                                continue # Skip writing this line

                    # Write the line if it wasn't skipped
                    fout.write(line)

            # 4. Done
            messagebox.showinfo("Success", f"Process Complete!\n\nRemoved {deleted_count} GRID lines.\nSaved to: {os.path.basename(output_file)}")
            self.status_label.config(text="Ready")

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred:\n{str(e)}")
            self.status_label.config(text="Error occurred")

if __name__ == "__main__":
    root = tk.Tk()
    app = BDFCleanerApp(root)
    root.mainloop()
