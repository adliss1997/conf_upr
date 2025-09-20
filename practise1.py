import tkinter as tk
from tkinter import scrolledtext


class Terminal_Emulator:
    def __init__(self, root):
        self.root = root
        self.root.title("MyVFS Emulator")

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

        self.prompt_label = tk.Label(input_frame, text="$ ")
        self.prompt_label.pack(side=tk.LEFT)

        self.input_entry = tk.Entry(input_frame)
        self.input_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(5, 5))
        self.input_entry.bind("<Return>", self.process_command)

        self.run_button = tk.Button(input_frame, text="Run", command=self.process_command)
        self.run_button.pack(side=tk.RIGHT)

        self.print_output("Добро пожаловать в эмулятор терминала!\nВведите 'exit' для выхода.\n")

    def print_output(self, text):
        self.output_area.configure(state='normal')
        self.output_area.insert(tk.END, text)
        self.output_area.see(tk.END)
        self.output_area.configure(state='disabled')

    def process_command(self, event=None):
        command = self.input_entry.get().strip()
        if not command:
            return

        self.print_output(f"$ {command}\n")

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

def main():
    root = tk.Tk()
    app = Terminal_Emulator(root)
    root.mainloop()


if __name__ == "__main__":
    main()