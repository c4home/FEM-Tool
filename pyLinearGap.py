import tkinter as tk
from tkinter import filedialog, messagebox
import os

def process_bdf_file(filepath, spc_count, spoint_start_id, dof):
    try:
        with open(filepath, 'r') as file:
            lines = file.readlines()

        new_lines = []
        cgap_replacement_blocks = []
        current_spoint_id = spoint_start_id

        # First pass: store lines, collect CGAP replacements
        for line in lines:
            if line.startswith('CGAP') or line.startswith('CBUSH'):
                cgap_val3 = line[24:32].strip()
                cgap_val4 = line[32:40].strip()

                spoint_id = current_spoint_id
                spoint_id_plus1 = current_spoint_id + 1

                comment_line = f"$Gap between grid {cgap_val3} dof {dof} and grid {cgap_val4} dof {dof} init open = 0.\n"
                spoint = f"{'SPOINT':<8}{spoint_id:>8}{spoint_id_plus1:>8}\n"
                suport = f"{'SUPORT':<8}{spoint_id:>8}{0:>8}\n"
                spc = f"{'SPC':<8}{spc_count:>8}{spoint_id_plus1:>8}{0:>8}{0:>8}\n"
                mpc_line1 = (f"{'MPC':<8}{spc_count:>8}{int(cgap_val3):>8}{dof:>8}"
                             f"{-1.0:>8.1f}{int(cgap_val4):>8}{dof:>8}{1.0:>8.1f}{'':8}{'+':<8}\n")
                mpc_line2 = (f"{'+':<8}{'':8}{spoint_id:>8}{0:>8}{1.0:>8.1f}"
                             f"{spoint_id_plus1:>8}{0:>8}{-1.0:>8.1f}\n")

                cgap_replacement_blocks.extend([comment_line,spoint, suport, spc, mpc_line1, mpc_line2])
                current_spoint_id += 2
            else:
                new_lines.append(line)

        base, ext = os.path.splitext(filepath)
        new_filepath = base + "_processed" + ext
        with open(new_filepath, 'w') as file:
            file.writelines(cgap_replacement_blocks)
        return new_filepath
    except Exception as e:
        messagebox.showerror("Error", f"Failed to process file:\n{str(e)}")
        return None

def select_and_process_file(spc_entry, spoint_entry, dof_entry):
    filepath = filedialog.askopenfilename(filetypes=[("BDF Files", "*.bdf"), ("All Files", "*.*")])
    if filepath:
        try:
            spc_count = int(spc_entry.get())
            spoint_start_id = int(spoint_entry.get())
            dof = int(dof_entry.get())
        except ValueError:
            messagebox.showerror("Input Error", "Please enter valid integers for SPC count, SPOINT start ID, and DOF.")
            return
        new_filepath = process_bdf_file(filepath, spc_count, spoint_start_id, dof)
        if new_filepath:
            messagebox.showinfo("Success", f"File processed successfully.\nSaved as:\n{new_filepath}")

def main():
    root = tk.Tk()
    root.title("BDF Nastran CGAP Replace Tool")
    root.geometry('400x280')

    tk.Label(root, text="Number of SPC:").pack(pady=(20, 0))
    spc_entry = tk.Entry(root)
    spc_entry.pack()
    spc_entry.insert(0, "4")

    tk.Label(root, text="SPOINT Start ID:").pack(pady=(10, 0))
    spoint_entry = tk.Entry(root)
    spoint_entry.pack()
    spoint_entry.insert(0, "2000000")

    tk.Label(root, text="DOF:").pack(pady=(10, 0))
    dof_entry = tk.Entry(root)
    dof_entry.pack()
    dof_entry.insert(0, "1")

    btn = tk.Button(root, text="Select BDF Nastran File", command=lambda: select_and_process_file(spc_entry, spoint_entry, dof_entry), width=30, height=2)
    btn.pack(pady=20)

    root.mainloop()

if __name__ == '__main__':
    main()
