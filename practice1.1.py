import tkinter as tk
from tkinter import scrolledtext
import sys
import os
import time


class Terminal_Emulator:
    def __init__(self, root, vfs_path=None, prompt="$ ", script_path=None):
        self.root = root
        self.root.title("MyVFS Emulator")

        self.vfs_path = vfs_path
        self.custom_prompt = prompt
        self.script_path = script_path

        self.debug_output()

        self.output_area = scrolledtext.ScrolledText(
            root,
            wrap=tk.WORD,
            state=tk.DISABLED,
            width=80,
            height=30
        )
        self.output_area.pack(padx=10, pady=10, expand=True, fill=tk.BOTH)

        input_frame = tk.Frame(root)
        input_frame.pack(padx=(0, 10), pady=(0, 10), fill=tk.X)

        self.prompt_label = tk.Label(input_frame, text=self.custom_prompt)
        self.prompt_label.pack(side=tk.LEFT)

        self.input_entry = tk.Entry(input_frame)
        self.input_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(5, 5))
        self.input_entry.bind("<Return>", self.process_command)

        self.run_button = tk.Button(input_frame, text="Run", command=self.process_command)
        self.run_button.pack(side=tk.RIGHT)

        self.print_output("Добро пожаловать в эмулятор терминала!\nВведите 'exit' для выхода.\n")

        if self.script_path:
            self.execute_script(self.script_path)

    def debug_output(self):
        debug_info = [
            "--- DEBUG OUTPUT ---",
            f"VFS Path: {self.vfs_path}",
            f"Prompt: '{self.custom_prompt}'",
            f"Script path: {self.script_path}",
            "-----------"
        ]
        print("\n".join(debug_info))

    def execute_script(self, script_path):
        try:
            if not os.path.exists(script_path):
                self.print_output(f"Ошибка: скрипт не найден: {script_path}\n")
                return

            with open(script_path, "r", encoding='utf-8') as f:
                lines = f.readlines()

            for line in lines:
                clean_line = line.strip()
                if not clean_line or clean_line.startswith("#"):
                    continue

                self.print_output(f"{self.custom_prompt}{clean_line}\n")
                self.process_script_command(clean_line)

        except Exception as e:
            self.print_output(f"Ошибка выполнения скрипта: {e}\n")

    def process_script_command(self, command):
        parts = command.split()
        cmd = parts[0].lower() if parts else ""
        args = parts[1:] if len(parts) > 1 else []

        if cmd == "exit":
            self.root.after(100, self.root.destroy)  # Задержка перед выходом
        elif cmd == "ls":
            self.print_output(f"Команда 'ls' вызвана с аргументами: {args}\n")
        elif cmd == "cd":
            self.print_output(f"Команда 'cd' вызвана с аргументами: {args}\n")
        else:
            self.print_output(f"Команда не найдена: {cmd}\n")

    def print_output(self, text):
        self.output_area.configure(state='normal')
        self.output_area.insert(tk.END, text)
        self.output_area.see(tk.END)
        self.output_area.configure(state='disabled')

    def process_command(self, event=None):
        command = self.input_entry.get().strip()
        if not command:
            return

        self.print_output(f"{self.custom_prompt}{command}\n")

        self.input_entry.delete(0, tk.END)

        parts = command.split()
        cmd = parts[0].lower() if parts else ""
        args = parts[1:] if len(parts) > 1 else []

        if cmd == "exit":
            self.root.destroy()
        elif cmd == "ls":
            self.print_output(f"Команда 'ls' вызвана с аргументами: {args}\n")
        elif cmd == "cd":
            self.print_output(f"Команда 'cd' вызвана с аргументами: {args}\n")
        else:
            self.print_output(f"Команда не найдена: {cmd}\n")

def parse_arguments():
    vfs_path = None
    prompt = "$ "
    script_path = None

    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == "--vfs" and i + 1 < len(sys.argv):
            vfs_path = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--prompt" and i + 1 < len(sys.argv):
            prompt = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--script" and i + 1 < len(sys.argv):
            script_path = sys.argv[i + 1]
            i += 2
        else:
            i += 1

    return vfs_path, prompt, script_path

def main():
    vfs_path, prompt, script_path = parse_arguments()

    root = tk.Tk()
    app = Terminal_Emulator(root, vfs_path, prompt, script_path)
    root.mainloop()


if __name__ == "__main__":
    main()