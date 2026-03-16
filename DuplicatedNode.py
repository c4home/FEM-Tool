import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import os
import re
from collections import defaultdict


def parse_include_files(main_dat_path):
    main_dir = os.path.dirname(main_dat_path)
    include_files = []
    with open(main_dat_path, 'r', errors='replace') as f:
        for line in f:
            match = re.match(r"^\s*INCLUDE\s+'?([^'\n]+)'?\s*$", line.strip(), re.IGNORECASE)
            if match:
                inc_path = match.group(1).strip().strip("'")
                if not os.path.isabs(inc_path):
                    inc_path = os.path.join(main_dir, inc_path)
                include_files.append(inc_path)
    return include_files


def extract_grids_from_file(filepath):
    grids = []
    if not os.path.exists(filepath):
        return grids
    with open(filepath, 'r', errors='replace') as f:
        for lineno, line in enumerate(f, 1):
            if line.startswith('$'):
                continue
            stripped = line.rstrip()
            if re.match(r'^GRID\s*\*?\s', stripped, re.IGNORECASE):
                parts = stripped.split()
                if len(parts) >= 2:
                    try:
                        gid = int(parts[1])
                        grids.append((gid, lineno))
                    except ValueError:
                        pass
    return grids


def analyze_duplicates(main_path):
    include_files = parse_include_files(main_path)
    all_files = [main_path] + include_files
    duplicates_per_file = {}
    all_grids = defaultdict(list)
    for fpath in all_files:
        grids = extract_grids_from_file(fpath)
        seen = defaultdict(list)
        for gid, lineno in grids:
            seen[gid].append(lineno)
            all_grids[gid].append((fpath, lineno))
        file_dups = {gid: lines for gid, lines in seen.items() if len(lines) > 1}
        if file_dups:
            duplicates_per_file[fpath] = file_dups
    global_duplicates = {gid: locs for gid, locs in all_grids.items()
                         if len(set(f for f, _ in locs)) > 1}
    return include_files, duplicates_per_file, global_duplicates, all_grids


def remove_cross_duplicates(main_path, global_duplicates, include_files):
    all_files_ordered = [main_path] + include_files
    file_order = {fpath: idx for idx, fpath in enumerate(all_files_ordered)}
    lines_to_delete = defaultdict(set)
    for gid, locs in global_duplicates.items():
        by_file = defaultdict(list)
        for fpath, lineno in locs:
            by_file[fpath].append(lineno)
        sorted_files = sorted(by_file.keys(), key=lambda f: file_order.get(f, 9999))
        for fpath in sorted_files[1:]:
            for lineno in by_file[fpath]:
                lines_to_delete[fpath].add(lineno)
    total_removed = 0
    for fpath, line_nums in lines_to_delete.items():
        if not os.path.exists(fpath):
            continue
        with open(fpath, 'r', errors='replace') as f:
            file_lines = f.readlines()
        new_lines = [line for idx, line in enumerate(file_lines, 1)
                     if not (idx in line_nums and not line.startswith('$'))]
        deleted = len(file_lines) - len(new_lines)
        if deleted > 0:
            cleaned_dir = os.path.join(os.path.dirname(fpath), 'cleaned')
            os.makedirs(cleaned_dir, exist_ok=True)
            out_path = os.path.join(cleaned_dir, os.path.basename(fpath))
            with open(out_path, 'w') as f:
                f.writelines(new_lines)
            total_removed += deleted
    return lines_to_delete, total_removed


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Nastran DAT - Duplicate GRID Checker')
        self.geometry('1050x700')
        self.configure(bg='#1e1e2e')
        self._last_include_files = []
        self._last_global_duplicates = {}
        self._last_main_path = ''
        self._build_ui()

    def _build_ui(self):
        top = tk.Frame(self, bg='#1e1e2e', pady=8)
        top.pack(fill=tk.X, padx=10)
        tk.Label(top, text='Main .dat File:', bg='#1e1e2e', fg='#cdd6f4',
                 font=('Segoe UI', 10)).pack(side=tk.LEFT)
        self.file_var = tk.StringVar()
        entry = tk.Entry(top, textvariable=self.file_var, width=70,
                         bg='#313244', fg='#cdd6f4', insertbackground='white',
                         font=('Segoe UI', 9), relief=tk.FLAT, bd=4)
        entry.pack(side=tk.LEFT, padx=6)
        tk.Button(top, text='Browse…', command=self._browse,
                  bg='#89b4fa', fg='#1e1e2e', font=('Segoe UI', 9, 'bold'),
                  relief=tk.FLAT, padx=8).pack(side=tk.LEFT)
        tk.Button(top, text='Analyze', command=self._analyze,
                  bg='#a6e3a1', fg='#1e1e2e', font=('Segoe UI', 9, 'bold'),
                  relief=tk.FLAT, padx=8).pack(side=tk.LEFT, padx=6)
        style = ttk.Style(self)
        style.theme_use('default')
        style.configure('TNotebook', background='#1e1e2e', borderwidth=0)
        style.configure('TNotebook.Tab', background='#313244', foreground='#cdd6f4',
                        padding=[10, 4], font=('Segoe UI', 9))
        style.map('TNotebook.Tab', background=[('selected', '#89b4fa')],
                  foreground=[('selected', '#1e1e2e')])
        nb = ttk.Notebook(self)
        nb.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)
        tab1 = tk.Frame(nb, bg='#181825')
        nb.add(tab1, text=' Included Files ')
        self._build_files_tab(tab1)
        tab2 = tk.Frame(nb, bg='#181825')
        nb.add(tab2, text=' Intra-file Duplicates ')
        self._build_intra_tab(tab2)
        tab3 = tk.Frame(nb, bg='#181825')
        nb.add(tab3, text=' Cross-file Duplicates ')
        self._build_cross_tab(tab3)
        self.status_var = tk.StringVar(value='Ready — select a .dat file to begin.')
        tk.Label(self, textvariable=self.status_var, bg='#313244', fg='#a6e3a1',
                 font=('Segoe UI', 9), anchor='w', padx=8).pack(fill=tk.X, side=tk.BOTTOM)

    def _build_files_tab(self, parent):
        cols = ('File', 'Status', 'Exists')
        self.tree_files = ttk.Treeview(parent, columns=cols, show='headings')
        self._style_tree(self.tree_files)
        for c, w in zip(cols, [680, 200, 80]):
            self.tree_files.heading(c, text=c)
            self.tree_files.column(c, width=w, anchor='w')
        sb = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.tree_files.yview)
        self.tree_files.configure(yscrollcommand=sb.set)
        self.tree_files.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

    def _build_intra_tab(self, parent):
        cols = ('File', 'GRID ID', 'Duplicate Lines')
        self.tree_intra = ttk.Treeview(parent, columns=cols, show='headings')
        self._style_tree(self.tree_intra)
        for c, w in zip(cols, [480, 100, 300]):
            self.tree_intra.heading(c, text=c)
            self.tree_intra.column(c, width=w, anchor='w')
        sb = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.tree_intra.yview)
        self.tree_intra.configure(yscrollcommand=sb.set)
        self.tree_intra.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

    def _build_cross_tab(self, parent):
        btn_frame = tk.Frame(parent, bg='#181825', pady=6)
        btn_frame.pack(fill=tk.X, padx=8)
        tk.Label(btn_frame,
                 text='Duplicates are kept in the file listed FIRST in the main include order.',
                 bg='#181825', fg='#cdd6f4', font=('Segoe UI', 9)).pack(side=tk.LEFT)
        self.btn_remove_cross = tk.Button(
            btn_frame,
            text='🗑 Remove Cross-file Duplicates',
            command=self._remove_cross_duplicates,
            bg='#f38ba8', fg='#1e1e2e', font=('Segoe UI', 9, 'bold'),
            relief=tk.FLAT, padx=10, pady=3,
            state=tk.DISABLED
        )
        self.btn_remove_cross.pack(side=tk.RIGHT)
        cols = ('GRID ID', 'File', 'Line', 'Action')
        self.tree_cross = ttk.Treeview(parent, columns=cols, show='headings')
        self._style_tree(self.tree_cross)
        for c, w in zip(cols, [90, 620, 80, 160]):
            self.tree_cross.heading(c, text=c)
            self.tree_cross.column(c, width=w, anchor='w')
        sb = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.tree_cross.yview)
        self.tree_cross.configure(yscrollcommand=sb.set)
        self.tree_cross.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

    def _style_tree(self, tree):
        style = ttk.Style()
        style.configure('Treeview', background='#1e1e2e', foreground='#cdd6f4',
                        fieldbackground='#1e1e2e', font=('Consolas', 9), rowheight=22)
        style.configure('Treeview.Heading', background='#313244', foreground='#89b4fa',
                        font=('Segoe UI', 9, 'bold'))
        style.map('Treeview', background=[('selected', '#45475a')])
        tree.tag_configure('ok',   background='#1e1e2e', foreground='#a6e3a1')
        tree.tag_configure('dup',  background='#2a1e2e', foreground='#f38ba8')
        tree.tag_configure('keep', background='#1e2a1e', foreground='#a6e3a1')
        tree.tag_configure('miss', background='#1e1e2e', foreground='#fab387')

    def _browse(self):
        path = filedialog.askopenfilename(
            title='Select main Nastran .dat file',
            filetypes=[('Nastran DAT files', '*.dat *.bdf'), ('All files', '*.*')])
        if path:
            self.file_var.set(path)

    def _analyze(self):
        main_path = self.file_var.get().strip()
        if not main_path or not os.path.exists(main_path):
            self.status_var.set('ERROR: File not found.')
            return
        self.status_var.set('Analyzing…')
        self.update()
        try:
            inc_files, dup_intra, dup_cross, all_grids = analyze_duplicates(main_path)
        except Exception as e:
            self.status_var.set(f'ERROR: {e}')
            return
        self._last_include_files = inc_files
        self._last_global_duplicates = dup_cross
        self._last_main_path = main_path
        for row in self.tree_files.get_children():
            self.tree_files.delete(row)
        all_files = [main_path] + inc_files
        for fpath in all_files:
            exists = os.path.exists(fpath)
            has_dup = fpath in dup_intra
            if has_dup:
                status = f'⚠ {len(dup_intra[fpath])} duplicate GRID ID(s)'
                tag = 'dup'
            elif not exists:
                status = '✗ File not found'
                tag = 'miss'
            else:
                status = '✓ OK'
                tag = 'ok'
            self.tree_files.insert('', tk.END,
                                   values=(os.path.basename(fpath), status, 'Yes' if exists else 'No'),
                                   tags=(tag,))
        for row in self.tree_intra.get_children():
            self.tree_intra.delete(row)
        for fpath, dups in sorted(dup_intra.items()):
            fname = os.path.basename(fpath)
            for gid, lines in sorted(dups.items()):
                self.tree_intra.insert('', tk.END,
                                       values=(fname, gid, ', '.join(f'L{l}' for l in lines)),
                                       tags=('dup',))
        self._fill_cross_tab(dup_cross, main_path, inc_files)
        n_intra = sum(len(v) for v in dup_intra.values())
        n_cross = len(dup_cross)
        self.status_var.set(
            f'Done — {len(inc_files)} INCLUDE file(s) found | '
            f'Intra-file duplicates: {n_intra} GRID ID(s) | '
            f'Cross-file duplicates: {n_cross} GRID ID(s)'
        )
        if n_cross > 0:
            self.btn_remove_cross.config(state=tk.NORMAL)
        else:
            self.btn_remove_cross.config(state=tk.DISABLED)

    def _fill_cross_tab(self, dup_cross, main_path, inc_files):
        for row in self.tree_cross.get_children():
            self.tree_cross.delete(row)
        if not dup_cross:
            return
        all_files_ordered = [main_path] + inc_files
        file_order = {fpath: idx for idx, fpath in enumerate(all_files_ordered)}
        for gid in sorted(dup_cross.keys()):
            locs = dup_cross[gid]
            sorted_locs = sorted(locs, key=lambda x: file_order.get(x[0], 9999))
            first = True
            for fpath, lineno in sorted_locs:
                if first:
                    action = '✔ KEEP'
                    tag = 'keep'
                else:
                    action = '✖ TO REMOVE'
                    tag = 'dup'
                self.tree_cross.insert('', tk.END,
                                       values=(gid if first else '',
                                               os.path.basename(fpath),
                                               lineno,
                                               action),
                                       tags=(tag,))
                first = False

    def _remove_cross_duplicates(self):
        main_path = self._last_main_path
        if not main_path:
            return
        n_cross = len(self._last_global_duplicates)
        confirm = messagebox.askyesno(
            'Confirm Removal',
            f'This will delete duplicate GRID lines for {n_cross} GRID ID(s)\n'
            f'from files loaded LATER in the main include order.\n\n'
            f'Original lines will be prefixed with:\n'
            f'  $ [REMOVED DUPLICATE]\n\n'
            f'Files will be modified in-place. Proceed?'
        )
        if not confirm:
            return
        try:
            lines_map, total = remove_cross_duplicates(
                main_path,
                self._last_global_duplicates,
                self._last_include_files
            )
        except Exception as e:
            messagebox.showerror('Error', str(e))
            return
        self._analyze()
        messagebox.showinfo(
            'Done',
            f'{total} GRID line(s) deleted across '
            f'{len(lines_map)} file(s).\n\nCleaned files saved in \'cleaned\' subfolder(s).\n\nRe-analysis complete.'
        )


if __name__ == '__main__':
    app = App()
    app.mainloop()