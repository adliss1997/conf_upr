import tkinter as tk
from tkinter import scrolledtext
import sys
import os
import xml.etree.ElementTree as ET
import base64
from pathlib import Path
import time


class VFS:
    def __init__(self):
        self.root = {'type': 'directory', 'name': '', 'children': {}}
        self.current_path = Path('/')

    def load_from_xml(self, xml_path):
        """Загрузка VFS из XML файла"""
        try:
            if not os.path.exists(xml_path):
                return False, f"Файл не найден: {xml_path}"

            tree = ET.parse(xml_path)
            root_element = tree.getroot()

            if root_element.tag != 'vfs':
                return False, "Неверный формат XML: корневой элемент должен быть 'vfs'"

            self.root = {'type': 'directory', 'name': '', 'children': {}}

            self._parse_xml_element(root_element, self.root)

            return True, "VFS успешно загружена"

        except ET.ParseError as e:
            return False, f"Ошибка парсинга XML: {e}"
        except Exception as e:
            return False, f"Ошибка загрузки VFS: {e}"

    def _parse_xml_element(self, xml_element, current_node):
        for child in xml_element:
            if child.tag == 'directory':
                dir_name = child.get('name', '')
                new_dir = {'type': 'directory', 'name': dir_name, 'children': {}}
                current_node['children'][dir_name] = new_dir
                self._parse_xml_element(child, new_dir)

            elif child.tag == 'file':
                file_name = child.get('name', '')
                content = child.text or ''
                if child.get('encoding') == 'base64':
                    try:
                        content = base64.b64decode(content).decode('utf-8')
                    except:
                        content = f"[Binary data - decode error]"

                new_file = {
                    'type': 'file',
                    'name': file_name,
                    'content': content,
                    'size': len(content)
                }
                current_node['children'][file_name] = new_file

    def vfs_init(self):
        self.root = {
            'type': 'directory',
            'name': '',
            'children': {
                'home': {
                    'type': 'directory',
                    'name': 'home',
                    'children': {
                        'user': {
                            'type': 'directory',
                            'name': 'user',
                            'children': {
                                'documents': {
                                    'type': 'directory',
                                    'name': 'documents',
                                    'children': {
                                        'readme.txt': {
                                            'type': 'file',
                                            'name': 'readme.txt',
                                            'content': 'Добро пожаловать в VFS!\nЭто тестовый файл.',
                                            'size': 45
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                'etc': {
                    'type': 'directory',
                    'name': 'etc',
                    'children': {
                        'config.txt': {
                            'type': 'file',
                            'name': 'config.txt',
                            'content': 'version=1.0\nlanguage=ru',
                            'size': 22
                        }
                    }
                }
            }
        }
        self.current_path = Path('/')
        return "VFS инициализирована по умолчанию"

    def get_current_directory(self):
        current = self.root
        if self.current_path != Path('/'):
            for part in self.current_path.parts[1:]:
                if part in current['children'] and current['children'][part]['type'] == 'directory':
                    current = current['children'][part]
                else:
                    return None
        return current

    def ls(self, path=None):
        target = self.get_current_directory()
        if path:
            pass

        if not target:
            return "Ошибка: директория не найдена"

        result = []
        for name, item in target['children'].items():
            if item['type'] == 'directory':
                result.append(f"{name}/")
            else:
                result.append(name)

        return "\n".join(sorted(result))

    def cd(self, path):
        if path == '/':
            self.current_path = Path('/')
            return ""
        elif path == '..':
            if self.current_path != Path('/'):
                self.current_path = self.current_path.parent
            return ""
        else:
            return f"Ошибка: директория '{path}' не найдена"

class Terminal_Emulator:
    def __init__(self, root, vfs_path=None, prompt="$ ", script_path=None):
        self.root = root
        self.root.title("MyVFS Emulator")

        self.vfs_path = vfs_path
        self.custom_prompt = prompt
        self.script_path = script_path

        self.vfs = VFS()
        self.vfs_loaded = False

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

        if self.vfs_path:
            success, message = self.vfs.load_from_xml(self.vfs_path)
            if success:
                self.vfs_loaded = True
                self.print_output(f"VFS загружена: {message}\n")
            else:
                self.print_output(f"Ошибка загрузки VFS: {message}\n")

        else:
            message = self.vfs.vfs_init()
            self.vfs_loaded = True
            self.print_output(f"{message}\n")

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
            self.root.after(100, self.root.destroy)
        elif cmd == "ls":
            result = self.vfs.ls(args[0] if args else None)
            self.print_output(f"{result}\n")
        elif cmd == "cd":
            result = self.vfs.cd(args[0] if args else "")
            if result:
                self.print_output(f"{result}\n")
        elif cmd == "vfs-init":
            result = self.vfs.vfs_init()
            self.print_output(f"{result}\n")
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
            result = self.vfs.ls(args[0] if args else None)
            self.print_output(f"{result}\n")
        elif cmd == "cd":
            result = self.vfs.cd(args[0] if args else "")
            if result:
                self.print_output(f"{result}\n")
        elif cmd == "vfs-init":
            result = self.vfs.vfs_init()
            self.vfs_loaded = True
            self.print_output(f"{result}\n")
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