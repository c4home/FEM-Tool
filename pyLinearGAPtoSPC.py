import os
import tkinter as tk
from tkinter import filedialog, messagebox


def format_nastran_spc(fields, dof):
    node = fields[0]
    cid = fields[2]
    return '{:<8}{:>8}{:>8}{:>8}{:>8}'.format(
        'SPC', cid, node, dof, '0.0'
    )


def load_and_convert():
    filepath = filedialog.askopenfilename(
        title="Select CSV file",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
    )
    if not filepath:
        return

    dof = dof_entry.get()
    if not dof:
        messagebox.showinfo("Info", "DOF is empty, using default value 1")
        dof = "1"

    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()

        results = []
        start_reading = False  # Flag to start reading after "Nodes"

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check for the trigger line to start reading
            if not start_reading:
                if line.startswith("Nodes"):
                    start_reading = True
                continue  # Skip until the start reading line is found

            parts = line.split(',')
            if len(parts) < 5:
                messagebox.showerror("Error", f"Invalid line: {line}")
                return
            try:
                mag_value = float(parts[4])
            except ValueError:
                messagebox.showerror("Error", f"Invalid magnitude value: {parts[4]} in line: {line}")
                return

            if mag_value > 0:
                results.append(format_nastran_spc(parts, dof))

        if not results:
            messagebox.showinfo("Info", "No valid data with magnitude > 0 found.")
            return

        output_text.delete('1.0', tk.END)
        output_text.insert(tk.END, '\n'.join(results))

        base, ext = os.path.splitext(filepath)
        save_path = base + "_convert.bdf"
        with open(save_path, 'w') as f_out:
            f_out.write('\n'.join(results))

        messagebox.showinfo("Success", f"File saved as {save_path}")

    except Exception as e:
        messagebox.showerror("Error", str(e))



root = tk.Tk()
root.title("CSV to Nastran SPC Converter")

frame = tk.Frame(root, padx=10, pady=10)
frame.pack()

btn_load = tk.Button(frame, text="Load CSV and Convert", command=load_and_convert)
btn_load.pack()

dof_label = tk.Label(frame, text="Degree Of Freedom (DOF):")
dof_label.pack(pady=(10, 0))

dof_entry = tk.Entry(frame)
dof_entry.pack()
dof_entry.insert(0, "1")  # default value

output_text = tk.Text(frame, width=80, height=20)
output_text.pack()

root.mainloop()
