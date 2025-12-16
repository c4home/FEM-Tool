import tkinter as tk
from tkinter import filedialog, messagebox
import os


class FileSearcherApp:
    def __init__(self, root):
        self.root = root
        self.root.title('File Content Searcher')
        self.root.geometry('800x400')

        self.file_type = tk.StringVar(value='.sub')

        # Folder selection
        self.folder_path = tk.StringVar()
        tk.Label(root, text='Selected Folder:').pack(pady=5)
        tk.Entry(root, textvariable=self.folder_path, width=80).pack()
        tk.Button(root, text='Select Folder', command=self.select_folder).pack(pady=5)

        # File type selection
        tk.Label(root, text='Select file type to search in:').pack(pady=5)
        tk.Radiobutton(root, text='.sub files', variable=self.file_type, value='.sub').pack()
        tk.Radiobutton(root, text='.dat files', variable=self.file_type, value='.dat').pack()

        # Search term entry
        tk.Label(root, text='Enter content to search for (e.g., a number, text):').pack(pady=5)
        self.search_term_entry = tk.Entry(root, width=40)
        self.search_term_entry.pack()

        # Search button
        tk.Button(root, text='Search', command=self.search_files).pack(pady=10)

        # Text areas frame
        text_frame = tk.Frame(root)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Text for files searched
        left_frame = tk.Frame(text_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        tk.Label(left_frame, text='Files Checked:').pack()
        self.files_checked_text = tk.Text(left_frame, height=15, width=50)
        self.files_checked_text.pack(fill=tk.BOTH, expand=True)

        # Text for search results
        right_frame = tk.Frame(text_frame)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        tk.Label(right_frame, text='Search Results:').pack()
        self.results_text = tk.Text(right_frame, height=15, width=50)
        self.results_text.pack(fill=tk.BOTH, expand=True)

    def select_folder(self):
        selected_folder = filedialog.askdirectory()
        if selected_folder:
            self.folder_path.set(selected_folder)
            self.files_checked_text.delete(1.0, tk.END)
            self.results_text.delete(1.0, tk.END)

    def search_files(self):
        folder = self.folder_path.get()
        if not folder:
            messagebox.showwarning('Warning', 'Please select a folder first.')
            return

        search_term = self.search_term_entry.get()
        if not search_term:
            messagebox.showwarning('Warning', 'Please enter a search term.')
            return

        file_ext = self.file_type.get()
        found = []

        self.files_checked_text.delete(1.0, tk.END)
        self.results_text.delete(1.0, tk.END)

        self.results_text.insert(tk.END, f'Searching for "{search_term}" in *{file_ext} files under {folder}...\n')

        for root_dir, dirs, files in os.walk(folder):
            for file in files:
                if file.endswith(file_ext):
                    file_path = os.path.join(root_dir, file)
                    self.files_checked_text.insert(tk.END, f'{file_path}\n')
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            if search_term in content:
                                found.append(file_path)
                    except Exception as e:
                        self.files_checked_text.insert(tk.END, f'Could not read file {file_path}: {e}\n')

        if found:
            self.results_text.insert(tk.END, f'\nFound {len(found)} file(s) containing "{search_term}":\n')
            for fpath in found:
                self.results_text.insert(tk.END, f'{fpath}\n')
        else:
            self.results_text.insert(tk.END, f'\nNo {file_ext} files containing "{search_term}" were found.')


if __name__ == '__main__':
    root = tk.Tk()
    app = FileSearcherApp(root)
    root.mainloop()
