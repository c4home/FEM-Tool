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
    folder = folder_path.get()
    keyword = keyword_entry.get().lower()

    if not folder or not keyword:
        messagebox.showwarning("Warning", "Please select a folder and enter a keyword.")
        return

    result_box.delete(1.0, tk.END)
    file_paths.clear()
    results = {}

    for root_dir, dirs, files in os.walk(folder):
        for file in files:
            if file.lower().endswith(".pdf"):
                pdf_path = os.path.join(root_dir, file)
                try:
                    reader = PdfReader(pdf_path)
                    for i, page in enumerate(reader.pages):
                        text = page.extract_text()
                        if text and keyword in text.lower():
                            if file not in results:
                                results[file] = {"path": pdf_path, "pages": []}
                            results[file]["pages"].append(i + 1)
                except Exception:
                    continue

    if results:
        tag_counter = 0  # ✅ safe unique counter
        for file, data in results.items():
            pages = sorted(set(data["pages"]))
            file_paths[file] = data["path"]
            result_box.insert(tk.END, f"{file} (Pages: ")

            for idx, page in enumerate(pages):
                tag_name = f"page_link_{tag_counter}"  # ✅ no special chars
                tag_counter += 1

                result_box.insert(tk.END, str(page), tag_name)
                result_box.tag_config(tag_name, foreground="blue", underline=True)
                result_box.tag_bind(tag_name, "<Button-1>", lambda e, f=file, p=page: open_pdf(file_paths[f], p))
                result_box.tag_bind(tag_name, "<Enter>",    lambda e: result_box.config(cursor="hand2"))
                result_box.tag_bind(tag_name, "<Leave>",    lambda e: result_box.config(cursor=""))

                if idx < len(pages) - 1:
                    result_box.insert(tk.END, ", ")

            result_box.insert(tk.END, ")\n")
    else:
        result_box.insert(tk.END, "No matches found.\n")

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

# --- UI ---
root = tk.Tk()
root.title("PDF Keyword Search")
root.geometry("800x600")

folder_path = tk.StringVar()
root.rowconfigure(3, weight=1)
root.columnconfigure(0, weight=1)

frame_top = tk.Frame(root)
frame_top.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
tk.Label(frame_top, text="Folder:").pack(side=tk.LEFT)
tk.Entry(frame_top, textvariable=folder_path, width=50).pack(side=tk.LEFT, padx=5)
tk.Button(frame_top, text="Browse", command=select_folder).pack(side=tk.LEFT)

frame_mid = tk.Frame(root)
frame_mid.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
tk.Label(frame_mid, text="Keyword:").pack(side=tk.LEFT)
keyword_entry = tk.Entry(frame_mid, width=30)
keyword_entry.insert(0, "Upward")
keyword_entry.pack(side=tk.LEFT, padx=5)

tk.Button(root, text="Search", command=search_keyword).grid(row=2, column=0, pady=10)

result_box = scrolledtext.ScrolledText(root, wrap=tk.WORD)
result_box.grid(row=3, column=0, sticky="nsew", padx=10, pady=10)

root.mainloop()