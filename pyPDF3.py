import os
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import subprocess
import sys
from pypdf import PdfReader
import logging
import warnings

logging.getLogger("pypdf").setLevel(logging.ERROR)
warnings.filterwarnings("ignore")

file_paths = {}

def select_folder():
    folder = filedialog.askdirectory()
    if folder:
        folder_path.set(folder)

def search_keyword():
    global file_paths
    folders  = list(folder_listbox.get(0, tk.END))
    aircraft = aircraft_entry.get().lower()
    keyword  = keyword_entry.get().lower()

    if not folders or not keyword:
        messagebox.showwarning("Warning", "Please add at least one folder and enter a keyword.")
        return

    result_box.config(state=tk.NORMAL)
    result_box.delete(1.0, tk.END)
    file_paths.clear()

    results  = {}
    tag_counter = 0

    for folder in folders:
        for root_dir, dirs, files in os.walk(folder):
            for file in files:
                if not file.lower().endswith(".pdf"):
                    continue
                pdf_path = os.path.join(root_dir, file)
                
                # Show current file being scanned
                status_var.set(f"🔍 Scanning: {pdf_path}")
                root.update_idletasks()   # forces the label to refresh immediately
                
                try:
                    reader = PdfReader(pdf_path)
                    # checks all pages
                    if aircraft:
                        full_text = " ".join(
                            (page.extract_text() or "") for page in reader.pages
                        )
                        if aircraft not in full_text.lower():
                            continue

                    pages_found = []
                    for i, page in enumerate(reader.pages):
                        text = page.extract_text()
                        if text and keyword in text.lower():
                            pages_found.append(i + 1)

                    if pages_found:
                        rel_folder = os.path.relpath(root_dir, os.path.dirname(folder))
                        rel_folder = rel_folder.replace("\\", "/")
                        if rel_folder not in results:
                            results[rel_folder] = {}
                        results[rel_folder][file] = {
                            "path": pdf_path,
                            "pages": sorted(set(pages_found))
                        }
                except Exception:
                    continue

    if not results:
        result_box.insert(tk.END, "No matches found.\n")
        return

    printed_folders = set()

    for rel_folder, files in sorted(results.items()):
        parts = rel_folder.split("/")

        # Print folder hierarchy with indentation
        cumulative = ""
        for depth, part in enumerate(parts):
            cumulative = f"{cumulative}/{part}" if cumulative else part
            if cumulative not in printed_folders:
                indent = "    " * depth
                result_box.insert(tk.END, f"{indent}📁 {part}\n")
                printed_folders.add(cumulative)

        # Print each file with inline clickable pages
        file_indent = "    " * len(parts)
        for filename, data in sorted(files.items()):
            file_paths[filename] = data["path"]
            result_box.insert(tk.END, f"{file_indent}📄 {filename}  (Pages: ")

            for idx, page in enumerate(data["pages"]):
                tag_name = f"page_link_{tag_counter}"
                tag_counter += 1

                result_box.insert(tk.END, str(page), tag_name)
                result_box.tag_config(tag_name, foreground="blue", underline=True)
                result_box.tag_bind(tag_name, "<Button-1>", lambda e, f=filename, p=page: open_pdf(file_paths[f], p))
                result_box.tag_bind(tag_name, "<Enter>",    lambda e: result_box.config(cursor="hand2"))
                result_box.tag_bind(tag_name, "<Leave>",    lambda e: result_box.config(cursor=""))

                if idx < len(data["pages"]) - 1:
                    result_box.insert(tk.END, ", ")

            result_box.insert(tk.END, ")\n")


def open_pdf(file_path, page):
    try:
        if sys.platform.startswith("win"):
            acrobat_path = r"C:\Program Files\Adobe\Acrobat DC\Acrobat\Acrobat.exe"
            subprocess.Popen([acrobat_path, "/A", f"page={page}", file_path])
        elif sys.platform.startswith("darwin"):
            subprocess.run(["open", file_path])
        else:
            subprocess.run(["xdg-open", file_path])
    except Exception as e:
        messagebox.showerror("Error", f"Could not open PDF:\n{e}")

def add_folder():
    folder = filedialog.askdirectory()
    if folder and folder not in folder_listbox.get(0, tk.END):
        folder_listbox.insert(tk.END, folder)

def remove_folder():
    selected = folder_listbox.curselection()
    if selected:
        folder_listbox.delete(selected[0])

# --- UI ---
root = tk.Tk()
root.title("PDF Keyword Search")
root.geometry("1200x600")

folder_path = tk.StringVar()
# root.rowconfigure(4, weight=1)
root.columnconfigure(0, weight=1)

# Row 0 — Folder list
frame_top = tk.Frame(root)
frame_top.grid(row=0, column=0, padx=6, pady=5, sticky="ew")
frame_top.columnconfigure(0, weight=1)

folder_listbox = tk.Listbox(frame_top, height=8, selectmode=tk.SINGLE)
folder_listbox.grid(row=0, column=0, columnspan=2, sticky="ew", padx=(0,5))

btn_frame = tk.Frame(frame_top)
btn_frame.grid(row=1, column=0, sticky="w", pady=2)
tk.Button(btn_frame, text="➕ Add Folder",    command=add_folder).pack(side=tk.LEFT, padx=2)
tk.Button(btn_frame, text="➖ Remove Selected", command=remove_folder).pack(side=tk.LEFT, padx=2)

# Row 1 — Aircraft Support
frame_aircraft = tk.Frame(root)
frame_aircraft.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
tk.Label(frame_aircraft, text="Aircraft Support:").pack(side=tk.LEFT)
aircraft_entry = tk.Entry(frame_aircraft, width=30)
aircraft_entry.insert(0, "A320")
aircraft_entry.pack(side=tk.LEFT, padx=5)

# Row 2 — Keyword
frame_mid = tk.Frame(root)
frame_mid.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
tk.Label(frame_mid, text="Keyword:").pack(side=tk.LEFT)
keyword_entry = tk.Entry(frame_mid, width=30)
keyword_entry.insert(0, "Upward")
keyword_entry.pack(side=tk.LEFT, padx=5)

# Row 3 — Search button + Status label (same frame, button stays fixed)
frame_search = tk.Frame(root)
frame_search.grid(row=3, column=0, padx=10, pady=5, sticky="ew")
frame_search.columnconfigure(1, weight=1)   # status label expands, button stays left

tk.Button(frame_search, text="Search", command=search_keyword).grid(row=0, column=0, padx=(0, 10))

status_var = tk.StringVar(value="")
status_label = tk.Label(frame_search, textvariable=status_var, fg="gray", anchor="w",
                        wraplength=550, justify="left")
status_label.grid(row=0, column=1, sticky="ew")

# Row 5 — Results  (update rowconfigure too)
result_box = scrolledtext.ScrolledText(root, wrap=tk.WORD)
result_box.grid(row=5, column=0, sticky="nsew", padx=10, pady=10)
root.rowconfigure(5, weight=1)

root.mainloop()