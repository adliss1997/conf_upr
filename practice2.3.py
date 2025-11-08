# stage_3.py
import os
import json
from typing import Dict, List, Set, Optional
from collections import defaultdict
import configparser


class DependencyGraphStage3:
    def __init__(self):
        self.graph: Dict[str, List[str]] = defaultdict(list)
        self.visited: Set[str] = set()
        self.recursion_stack: Set[str] = set()
        self.cycles: List[List[str]] = []
        self.max_depth_reached = False

    def add_dependency(self, package: str, dependency: str):
        """Добавляет зависимость в граф"""
        self.graph[package].append(dependency)

    def build_graph_from_repository(self, start_package: str, version: str,
                                    repo_path: str, max_depth: int, current_depth: int = 0):
        """
        Рекурсивно строит граф зависимостей с помощью DFS
        """
        if current_depth > max_depth:
            self.max_depth_reached = True
            return

        # Обнаружение циклических зависимостей
        if start_package in self.recursion_stack:
            cycle_path = list(self.recursion_stack)
            cycle_path.append(start_package)
            self.cycles.append(cycle_path)
            print(f"Обнаружен цикл: {' -> '.join(cycle_path)}")
            return

        if start_package in self.visited:
            return

        print(f"Обрабатываем пакет: {start_package} (глубина: {current_depth})")
        self.visited.add(start_package)
        self.recursion_stack.add(start_package)

        try:
            # Получаем зависимости для текущего пакета
            dependencies = self.get_package_dependencies(start_package, version, repo_path)

            for dep in dependencies:
                self.add_dependency(start_package, dep)
                # Рекурсивно строим граф для зависимостей
                self.build_graph_from_repository(dep, version, repo_path, max_depth, current_depth + 1)

        except Exception as e:
            print(f"Ошибка при обработке пакета {start_package}: {e}")
        finally:
            self.recursion_stack.remove(start_package)

    def get_package_dependencies(self, package: str, version: str, repo_path: str) -> List[str]:
        """
        Получает зависимости пакета из репозитория или тестового файла
        """
        # Режим тестирования - читаем из файла
        if os.path.isfile(repo_path):
            return self.get_dependencies_from_test_file(package, repo_path)
        else:
            # Реальный репозиторий (упрощенная реализация)
            return self.get_dependencies_from_crates_io(package, version)

    def get_dependencies_from_test_file(self, package: str, test_file_path: str) -> List[str]:
        """
        Получает зависимости из тестового файла
        Формат файла: JSON с структурой { "A": ["B", "C"], "B": ["C", "D"] }
        """
        try:
            with open(test_file_path, 'r') as f:
                test_data = json.load(f)

            dependencies = test_data.get(package, [])
            print(f"  Зависимости {package}: {dependencies}")
            return dependencies
        except Exception as e:
            print(f"Ошибка чтения тестового файла: {e}")
            return []

    def get_dependencies_from_crates_io(self, package: str, version: str) -> List[str]:
        """
        Получает зависимости из crates.io (упрощенная демонстрация)
        """
        # Демонстрационные данные для реальных пакетов
        demo_dependencies = {
            "serde": ["serde_derive"],
            "serde_derive": ["proc-macro2", "quote", "syn"],
            "tokio": ["futures", "mio", "num_cpus"],
            "reqwest": ["tokio", "serde", "hyper"],
            "hyper": ["http", "tokio"],
            "actix-web": ["actix-rt", "serde", "tokio"]
        }

        dependencies = demo_dependencies.get(package, [])
        print(f"  Зависимости {package}: {dependencies}")
        return dependencies

    def print_ascii_tree(self, start_package: str, max_depth: int = None):
        """
        Выводит дерево зависимостей в ASCII формате
        """
        print(f"\nДерево зависимостей для {start_package}:")
        self._print_tree_recursive(start_package, "", set(), 0, max_depth or 10)

    def _print_tree_recursive(self, package: str, prefix: str, visited: Set[str],
                              depth: int, max_depth: int):
        """Рекурсивно печатает дерево зависимостей"""
        if depth > max_depth or package in visited:
            marker = ""
            if package in visited:
                marker = " (цикл)"
            elif depth > max_depth:
                marker = " (макс. глубина)"
            print(prefix + "└── " + package + marker)
            return

        visited.add(package)

        dependencies = self.graph.get(package, [])
        if not dependencies:
            print(prefix + "└── " + package)
            return

        print(prefix + "├── " + package)

        for i, dep in enumerate(dependencies):
            is_last = i == len(dependencies) - 1
            connector = "└── " if is_last else "├── "
            next_prefix = prefix + ("    " if is_last else "│   ")

            print(prefix + "│   " + connector + dep)
            self._print_tree_recursive(dep, next_prefix, visited.copy(), depth + 1, max_depth)

    def get_cycles_info(self) -> str:
        """Возвращает информацию о циклических зависимостях"""
        if not self.cycles:
            return "Циклические зависимости не обнаружены"

        result = "\nОбнаружены циклические зависимости:\n"
        for i, cycle in enumerate(self.cycles, 1):
            result += f"Цикл {i}: {' -> '.join(cycle)}\n"

        return result

    def get_statistics(self) -> str:
        """Возвращает статистику по графу"""
        total_packages = len(self.visited)
        total_dependencies = sum(len(deps) for deps in self.graph.values())

        stats = f"\nСтатистика графа:\n"
        stats += f"  Всего пакетов: {total_packages}\n"
        stats += f"  Всего зависимостей: {total_dependencies}\n"
        stats += f"  Циклических зависимостей: {len(self.cycles)}\n"
        stats += f"  Достигнута максимальная глубина: {'Да' if self.max_depth_reached else 'Нет'}\n"

        return stats


class DependencyVisualizerStage3:
    def __init__(self, config_file: str = "config.ini"):
        self.config = self.load_config(config_file)
        self.graph = DependencyGraphStage3()

    def load_config(self, config_file: str) -> configparser.ConfigParser:
        """Загружает конфигурацию из INI файла"""
        config = configparser.ConfigParser()
        if not config.read(config_file):
            print(f"Файл конфигурации {config_file} не найден. Используются значения по умолчанию.")
            config['DEFAULT'] = {
                'package_name': 'serde',
                'package_version': '1.0',
                'repository_url': '',
                'test_mode': 'true',
                'max_depth': '5'
            }
        return config

    def create_test_files(self):
        """Создает тестовые файлы для демонстрации"""
        test_cases = {
            "simple_deps.json": {
                "A": ["B", "C"],
                "B": ["D"],
                "C": ["D", "E"],
                "D": [],
                "E": []
            },
            "cyclic_deps.json": {
                "A": ["B"],
                "B": ["C"],
                "C": ["A"]  # Цикл A->B->C->A
            },
            "complex_deps.json": {
                "WebServer": ["HTTP", "Database", "Auth"],
                "HTTP": ["JSON", "Compression"],
                "Database": ["SQL", "ConnectionPool"],
                "Auth": ["Database", "JWT"],
                "JWT": ["Crypto"],
                "Crypto": ["Random"],
                "ConnectionPool": ["Database"],  # Цикл
                "JSON": [],
                "Compression": [],
                "SQL": [],
                "Random": []
            }
        }

        for filename, test_data in test_cases.items():
            with open(filename, 'w') as f:
                json.dump(test_data, f, indent=2)
            print(f"Создан тестовый файл: {filename}")

    def cleanup_test_files(self):
        """Удаляет тестовые файлы"""
        test_files = ["simple_deps.json", "cyclic_deps.json", "complex_deps.json"]
        for filename in test_files:
            if os.path.exists(filename):
                os.remove(filename)
                print(f"Удален тестовый файл: {filename}")

    def run_demo_cases(self):
        """Демонстрация различных случаев работы с тестовым репозиторием"""
        print("\n" + "=" * 50)
        print("ДЕМОНСТРАЦИЯ РАЗЛИЧНЫХ СЛУЧАЕВ")
        print("=" * 50)

        test_cases = [
            ("simple_deps.json", "A", "Простой граф без циклов"),
            ("cyclic_deps.json", "A", "Граф с циклическими зависимостями"),
            ("complex_deps.json", "WebServer", "Сложный граф с циклами")
        ]

        for test_file, start_package, description in test_cases:
            print(f"\n--- {description} ---")
            print(f"Файл: {test_file}, Стартовый пакет: {start_package}")

            demo_graph = DependencyGraphStage3()
            max_depth = self.config.getint('DEFAULT', 'max_depth', fallback=5)

            demo_graph.build_graph_from_repository(
                start_package,
                "1.0",
                test_file,
                max_depth
            )

            demo_graph.print_ascii_tree(start_package, max_depth)
            print(demo_graph.get_cycles_info())
            print(demo_graph.get_statistics())

    def run(self):
        """Основная логика этапа 3"""
        print("=" * 60)
        print("ЭТАП 3: Построение графа зависимостей (DFS с рекурсией)")
        print("=" * 60)

        # Чтение конфигурации
        package = self.config.get('DEFAULT', 'package_name', fallback='serde')
        version = self.config.get('DEFAULT', 'package_version', fallback='1.0')
        repo_path = self.config.get('DEFAULT', 'repository_url', fallback='')
        max_depth = self.config.getint('DEFAULT', 'max_depth', fallback=5)
        test_mode = self.config.getboolean('DEFAULT', 'test_mode', fallback=True)

        print(f"Конфигурация:")
        print(f"  Анализируемый пакет: {package}")
        print(f"  Версия: {version}")
        print(f"  Режим тестирования: {test_mode}")
        print(f"  Максимальная глубина: {max_depth}")
        print(f"  Путь к репозиторию: {repo_path if repo_path else 'не указан'}")

        # Создаем тестовые файлы если в режиме тестирования
        if test_mode and not repo_path:
            self.create_test_files()
            repo_path = "complex_deps.json"  # Используем сложный граф для демонстрации

        # Строим граф зависимостей
        print(f"\nПостроение графа зависимостей...")
        self.graph.build_graph_from_repository(package, version, repo_path, max_depth)

        # Выводим результаты
        print("\n" + "=" * 50)
        print("РЕЗУЛЬТАТЫ АНАЛИЗА")
        print("=" * 50)

        self.graph.print_ascii_tree(package, max_depth)
        print(self.graph.get_cycles_info())
        print(self.graph.get_statistics())

        # Демонстрация на различных тестовых случаях
        if test_mode:
            self.run_demo_cases()
            # Очистка тестовых файлов
            self.cleanup_test_files()


def main():
    """Главная функция для этапа 3"""
    visualizer = DependencyVisualizerStage3("config.ini")
    visualizer.run()


if __name__ == "__main__":
    main()
