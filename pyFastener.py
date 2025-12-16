import os
import tkinter as tk
from tkinter import filedialog, messagebox

def scan_blt_files(folder):
    cfast_data = {}
    for filename in os.listdir(folder):
        if filename.endswith(".blt"):
            filepath = os.path.join(folder, filename)
            with open(filepath, 'r') as f:
                lines = f.readlines()

            last_hmtag = None
            for i, line in enumerate(lines):
                line = line.strip()
                if line.startswith("$HMTAG"):
                    start_quote = line.find('"')
                    end_quote = line.rfind('"')
                    if start_quote != -1 and end_quote != -1 and end_quote > start_quote:
                        full_tag = line[start_quote + 1:end_quote]
                        parts = full_tag.split()
                        meaningful_tag = None
                        for part in parts:
                            if part.startswith("EN") or part.startswith("ABS"):
                                meaningful_tag = part
                                break
                        last_hmtag = meaningful_tag if meaningful_tag else full_tag
                
                elif line.startswith("CFAST"):
                    parts = line.split()
                    if len(parts) > 1:
                        cfast_full_id = parts[1]
                        cfast_id = cfast_full_id[:8]

                        diameter = None
                        # Look ahead for PFAST line with matching ID
                        for j in range(i + 1, min(i + 5, len(lines))):
                            next_line = lines[j].strip()
                            if next_line.startswith("PFAST"):
                                pfast_parts = next_line.split()
                                if len(pfast_parts) > 2 and pfast_parts[1] == cfast_id:
                                    diameter = pfast_parts[2]
                                    break
                        
                        if last_hmtag is not None:
                            cfast_data[cfast_id] = (last_hmtag, diameter)
    return cfast_data

def browse_folder():
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        cfast_mapping = scan_blt_files(folder_selected)
        if cfast_mapping:
            result_text.delete(1.0, tk.END)
            for cfast_id, (hmtag, diameter) in cfast_mapping.items():
                diameter_str = diameter if diameter is not None else "N/A"
                result_text.insert(tk.END, f"{cfast_id} {hmtag} {diameter_str}\n")
        else:
            messagebox.showinfo("Result", "No CFAST and HMTAG pairs found in .blt files.")

def copy_to_clipboard():
    text = result_text.get(1.0, tk.END)
    root.clipboard_clear()
    root.clipboard_append(text)
    messagebox.showinfo("Copied", "Results copied to clipboard!")

# GUI setup
root = tk.Tk()
root.title("BLT File Scanner")

frame = tk.Frame(root, padx=10, pady=10)
frame.pack(fill=tk.BOTH, expand=True)

label = tk.Label(frame, text="Select folder containing .blt files:")
label.pack()

browse_btn = tk.Button(frame, text="Browse Folder", command=browse_folder)
browse_btn.pack(pady=5)

result_text = tk.Text(frame, height=20, width=70)
result_text.pack()

copy_btn = tk.Button(frame, text="Copy to Clipboard", command=copy_to_clipboard)
copy_btn.pack(pady=5)

root.mainloop()

