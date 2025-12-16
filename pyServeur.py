import tkinter as tk
from tkinter import scrolledtext
import threading
import paramiko

SERVER_IP = "your.server.ip"
USERNAME = "your_username"
PASSWORD = "your_password"

class AnalysisManagerSSHApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Analysis Manager with SSH (Paramiko)")

        tk.Label(root, text="Analysis Command:").pack()
        self.input_text = scrolledtext.ScrolledText(root, width=40, height=4)
        self.input_text.pack()
        tk.Button(root, text="Send to Server", command=self.run_command_threaded).pack(pady=10)

        self.status_box = scrolledtext.ScrolledText(root, width=40, height=12, state='disabled')
        self.status_box.pack()

    def run_command_threaded(self):
        command = self.input_text.get("1.0", tk.END).strip()
        if command:
            threading.Thread(target=self.send_analysis_command, args=(command,)).start()
            self.append_status(f"Sent: {command}\n")

    def send_analysis_command(self, command):
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(SERVER_IP, username=USERNAME, password=PASSWORD)
            stdin, stdout, stderr = ssh.exec_command(command)
            result = stdout.read().decode()
            error = stderr.read().decode()
            ssh.close()
            msg = f"Result:\n{result}\n" if result else ""
            msg += f"Error:\n{error}\n" if error else ""
            self.append_status(msg)
        except Exception as ex:
            self.append_status(f"Error: {ex}\n")

    def append_status(self, msg):
        self.status_box.config(state='normal')
        self.status_box.insert(tk.END, msg)
        self.status_box.config(state='disabled')
        self.status_box.see(tk.END)

root = tk.Tk()
app = AnalysisManagerSSHApp(root)
root.mainloop()
