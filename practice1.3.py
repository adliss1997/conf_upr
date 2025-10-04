import tkinter as tk
from tkinter import scrolledtext
import sys
import os
import xml.etree.ElementTree as ET
import base64
from pathlib import Path
import time
import re


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
                                            'content': 'Добро пожаловать в VFS!\nЭто тестовый файл.\nТретья строка.',
                                            'size': 67
                                        },
                                        'notes.txt': {
                                            'type': 'file',
                                            'name': 'notes.txt',
                                            'content': 'Заметки пользователя\nВторая строка заметок',
                                            'size': 49
                                        }
                                    }
                                },
                                'downloads': {
                                    'type': 'directory',
                                    'name': 'downloads',
                                    'children': {
                                        'archive.zip': {
                                            'type': 'file',
                                            'name': 'archive.zip',
                                            'content': 'binary data here',
                                            'size': 15
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
                            'content': 'version=1.0\nlanguage=ru\nmode=production',
                            'size': 41
                        },
                        'system.conf': {
                            'type': 'file',
                            'name': 'system.conf',
                            'content': '# System configuration\nhostname=localhost',
                            'size': 40
                        }
                    }
                },
                'var': {
                    'type': 'directory',
                    'name': 'var',
                    'children': {
                        'log': {
                            'type': 'directory',
                            'name': 'log',
                            'children': {
                                'app.log': {
                                    'type': 'file',
                                    'name': 'app.log',
                                    'content': 'INFO: Application started\nERROR: Connection failed\nWARN: Retrying...',
                                    'size': 72
                                }
                            }
                        }
                    }
                },
                'bin': {
                    'type': 'directory',
                    'name': 'bin',
                    'children': {
                        'script.sh': {
                            'type': 'file',
                            'name': 'script.sh',
                            'content': '#!/bin/bash\necho "Hello World"',
                            'size': 28
                        }
                    }
                }
            }
        }
        self.current_path = Path('/')
        return "VFS инициализирована по умолчанию"

    def get_node_by_path(self, path):
        """Получить узел по абсолютному или относительному пути"""
        if not path or path == '.':
            return self.get_current_directory()

        if path == '/':
            return self.root

        path_obj = Path(path)

        # Обработка абсолютного пути
        if path.startswith('/'):
            current = self.root
            for part in path_obj.parts[1:]:
                if part in current['children'] and current['children'][part]['type'] == 'directory':
                    current = current['children'][part]
                else:
                    return None
            return current

        # Обработка относительного пути
        current = self.get_current_directory()
        if not current:
            return None

        for part in path_obj.parts:
            if part == '..':
                # Для .. нужно подняться на уровень выше
                if self.current_path != Path('/'):
                    # Временно меняем путь и получаем новую текущую директорию
                    old_path = self.current_path
                    self.current_path = self.current_path.parent
                    current = self.get_current_directory()
                    self.current_path = old_path
            elif part != '.':
                if part in current['children'] and current['children'][part]['type'] == 'directory':
                    current = current['children'][part]
                else:
                    return None
        return current

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
        if path:
            target = self.get_node_by_path(path)
        else:
            target = self.get_current_directory()

        if not target:
            return f"Ошибка: директория '{path}' не найдена"

        if target['type'] != 'directory':
            return f"Ошибка: '{path}' не является директорией"

        result = []
        for name, item in target['children'].items():
            if item['type'] == 'directory':
                result.append(f"{name}/")
            else:
                result.append(name)

        return "\n".join(sorted(result))

    def cd(self, path):
        if not path:
            return ""

        if path == '/':
            self.current_path = Path('/')
            return ""
        elif path == '..':
            if self.current_path != Path('/'):
                self.current_path = self.current_path.parent
            return ""
        else:
            target = self.get_node_by_path(path)
            if target and target['type'] == 'directory':
                # Обновляем current_path
                if path.startswith('/'):
                    self.current_path = Path(path)
                else:
                    self.current_path = self.current_path / path
                # Нормализуем путь
                self.current_path = self.current_path.resolve()
                return ""
            else:
                return f"Ошибка: директория '{path}' не найдена"

    def pwd(self):
        """Показать текущий рабочий каталог"""
        return str(self.current_path)

    def wc(self, args):
        """Подсчет строк, слов и символов в файлах"""
        if not args:
            return "Ошибка: укажите файл(ы) для анализа"

        results = []
        total_lines, total_words, total_chars = 0, 0, 0
        multiple_files = len(args) > 1

        for filename in args:
            file_node = self.get_node_by_path(filename)

            if not file_node:
                results.append(f"Ошибка: файл '{filename}' не найден")
                continue

            if file_node['type'] != 'file':
                results.append(f"Ошибка: '{filename}' не является файлом")
                continue

            content = file_node['content']
            lines = content.count('\n') + (1 if content else 0)
            words = len(re.findall(r'\S+', content))
            chars = len(content)

            results.append(f"  {lines}  {words}  {chars} {filename}")

            if multiple_files:
                total_lines += lines
                total_words += words
                total_chars += chars

        if multiple_files and results:
            results.append(f"  {total_lines}  {total_words}  {total_chars} total")

        return "\n".join(results) if results else "Нет файлов для анализа"

    def find(self, args):
        """Поиск файлов и директорий"""
        if not args:
            return "Ошибка: укажите параметры поиска"

        # Парсинг аргументов
        search_path = "."
        pattern = None
        name_pattern = None
        type_filter = None

        i = 0
        while i < len(args):
            if args[i] == '-name' and i + 1 < len(args):
                name_pattern = args[i + 1]
                i += 2
            elif args[i] == '-type' and i + 1 < len(args):
                type_filter = args[i + 1]
                i += 2
            elif not pattern and not args[i].startswith('-'):
                pattern = args[i]
                i += 1
            else:
                i += 1

        # Если не указан явно путь, используем первый не-опционный аргумент как путь
        if pattern and not search_path:
            search_path = pattern
            pattern = None

        start_node = self.get_node_by_path(search_path)
        if not start_node:
            return f"Ошибка: путь '{search_path}' не найден"

        results = []
        self._find_recursive(start_node, search_path, name_pattern, type_filter, results)

        return "\n".join(results) if results else "Файлы не найдены"

    def _find_recursive(self, node, current_path, name_pattern, type_filter, results):
        """Рекурсивный поиск файлов"""
        if node['type'] == 'directory':
            if (not type_filter or type_filter == 'd') and \
                    (not name_pattern or self._match_pattern(node['name'], name_pattern)):
                results.append(current_path)

            for name, child in node['children'].items():
                child_path = f"{current_path}/{name}" if current_path != '/' else f"/{name}"
                self._find_recursive(child, child_path, name_pattern, type_filter, results)

        elif node['type'] == 'file':
            if (not type_filter or type_filter == 'f') and \
                    (not name_pattern or self._match_pattern(node['name'], name_pattern)):
                results.append(current_path)

    def _match_pattern(self, name, pattern):
        """Простое сопоставление с шаблоном (поддержка * и ?)"""
        # Экранируем специальные символы regex кроме * и ?
        pattern_re = re.escape(pattern).replace(r'\*', '.*').replace(r'\?', '.')
        return re.match(f'^{pattern_re}$', name) is not None


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
        elif cmd == "pwd":
            result = self.vfs.pwd()
            self.print_output(f"{result}\n")
        elif cmd == "wc":
            result = self.vfs.wc(args)
            self.print_output(f"{result}\n")
        elif cmd == "find":
            result = self.vfs.find(args)
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
        elif cmd == "pwd":
            result = self.vfs.pwd()
            self.print_output(f"{result}\n")
        elif cmd == "wc":
            result = self.vfs.wc(args)
            self.print_output(f"{result}\n")
        elif cmd == "find":
            result = self.vfs.find(args)
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


def create_test_script():
    """Создание тестового скрипта для демонстрации всех команд"""
    script_content = """# Тестовый скрипт для VFS Emulator
# Демонстрация всех команд этапа 4

echo "=== Тестирование команды pwd ==="
pwd

echo "=== Тестирование команды ls ==="
ls
ls /home
ls /etc

echo "=== Тестирование команды cd ==="
cd home
pwd
ls
cd user/documents
pwd
ls
cd ../..
pwd
cd /etc
pwd
ls
cd /

echo "=== Тестирование команды wc ==="
wc /home/user/documents/readme.txt
wc /etc/config.txt
wc /home/user/documents/readme.txt /etc/config.txt
wc nonexistent.txt

echo "=== Тестирование команды find ==="
find /home -name "*.txt"
find /etc -type f
find . -name "*.conf"
find /var -type d

echo "=== Тестирование обработки ошибок ==="
ls nonexistent
cd invalid_directory
wc /home
find /nonexistent -name "*.txt"

echo "=== Тестирование завершено ==="
"""

    with open("test_script.txt", "w", encoding="utf-8") as f:
        f.write(script_content)

    print("Тестовый скрипт создан: test_script.txt")


def main():
    vfs_path, prompt, script_path = parse_arguments()

    # Создаем тестовый скрипт если его нет
    if not os.path.exists("test_script.txt"):
        create_test_script()

    root = tk.Tk()
    app = Terminal_Emulator(root, vfs_path, prompt, script_path)
    root.mainloop()


if __name__ == "__main__":
    main()