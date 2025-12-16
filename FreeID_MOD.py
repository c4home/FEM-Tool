import tkinter as tk
from tkinter import filedialog, messagebox, font as tkfont

def browse_file():
    filepath = filedialog.askopenfilename(filetypes=[("NASTRAN files", "*.bdf *.blk"), ("All files", "*.*")])
    if filepath:
        file_entry.delete(0, tk.END)
        file_entry.insert(0, filepath)

def extract_ids(lines, keywords):
    ids = []
    for line in lines:
        if line.startswith(keywords):
            try:
                id_str = line[8:16].strip()
                if id_str.isdigit():
                    ids.append(int(id_str))
            except IndexError:
                continue
    return sorted(set(ids))

def find_free_ranges(id_list):
    if not id_list:
        return []

    free_ranges = []
    prev = id_list[0]

    for eid in id_list[1:]:
        if eid > prev + 1:
            free_ranges.append((prev + 1, eid - 1))
        prev = eid
    return free_ranges

def get_largest_ranges(free_ranges, count=3):
    return sorted(free_ranges, key=lambda r: r[1] - r[0], reverse=True)[:count]

def display_largest_ranges(title, top_ranges):
    result_text.insert(tk.END, f"{title}:\n\n")
    if not top_ranges:
        result_text.insert(tk.END, "  No free ID ranges found.\n\n")
        return

    for fr in top_ranges:
        line = f"  {fr[0]} - {fr[1]}\n"
        start_idx = result_text.index(tk.INSERT)
        result_text.insert(tk.END, line)
        end_idx = result_text.index(tk.INSERT)
        result_text.tag_add("bold", start_idx, end_idx)
    result_text.insert(tk.END, "\n")

def process_file():
    filepath = file_entry.get()
    if not filepath:
        messagebox.showwarning("No File", "Please select a file first.")
        return

    try:
        with open(filepath, 'r') as file:
            lines = file.readlines()

        result_text.delete("1.0", tk.END)

        # Extract IDs
        element_ids = extract_ids(lines, ("CQUAD4", "CROD"))
        grid_ids = extract_ids(lines, ("GRID",))

        # Compute free ranges
        free_element = find_free_ranges(element_ids)
        free_grid = find_free_ranges(grid_ids)

        # Get 3 largest ranges
        top_free_element = get_largest_ranges(free_element)
        top_free_grid = get_largest_ranges(free_grid)

        # Display only top 3 free ranges per type
        display_largest_ranges("Top 3 Free ID Ranges for ELEMENTS (CQUAD4, CROD)", top_free_element)
        display_largest_ranges("Top 3 Free ID Ranges for GRIDs", top_free_grid)

    except Exception as e:
        messagebox.showerror("Error", f"Failed to process file:\n{e}")

# --- GUI Setup ---

root = tk.Tk()
root.title("NASTRAN Top Free ID Range Viewer")

frame = tk.Frame(root, padx=10, pady=10)
frame.pack()

tk.Label(frame, text="Select a .bdf or .blk file:").grid(row=0, column=0, sticky="w")

file_entry = tk.Entry(frame, width=50)
file_entry.grid(row=1, column=0, padx=(0, 10))

browse_button = tk.Button(frame, text="Browse", command=browse_file)
browse_button.grid(row=1, column=1)

process_button = tk.Button(frame, text="Process File", command=process_file)
process_button.grid(row=2, column=0, columnspan=2, pady=10)

# Styled Text widget for result display
result_text = tk.Text(root, wrap="word", width=80, height=25)
result_text.pack(padx=10, pady=10)

# Bold font style
bold_font = tkfont.Font(result_text, result_text.cget("font"))
bold_font.configure(weight="bold")
result_text.tag_configure("bold", font=bold_font)

root.mainloop()
