# stage_4.py
import os
import json
from typing import Dict, List, Set
from collections import defaultdict
import configparser


class DependencyGraphStage4:
    def __init__(self):
        self.graph: Dict[str, List[str]] = defaultdict(list)
        self.reverse_graph: Dict[str, List[str]] = defaultdict(list)
        self.visited: Set[str] = set()

    def build_graph_from_file(self, test_file_path: str):
        """
        Строит граф из тестового файла (для этапа 4)
        """
        try:
            with open(test_file_path, 'r') as f:
                test_data = json.load(f)

            for package, dependencies in test_data.items():
                for dep in dependencies:
                    self.add_dependency(package, dep)

            print(f"Граф построен из файла {test_file_path}")
            print(f"Пакеты в графе: {list(self.graph.keys())}")

        except Exception as e:
            print(f"Ошибка чтения тестового файла: {e}")

    def add_dependency(self, package: str, dependency: str):
        """Добавляет зависимость в граф и обратный граф"""
        self.graph[package].append(dependency)
        self.reverse_graph[dependency].append(package)

    def find_reverse_dependencies(self, target_package: str) -> List[str]:
        """
        Находит обратные зависимости - пакеты, которые зависят от целевого пакета
        Использует DFS для обхода обратного графа
        """
        reverse_deps = []
        visited = set()

        def dfs_reverse(current_package: str):
            if current_package in visited:
                return

            visited.add(current_package)

            # Ищем пакеты, которые зависят от текущего пакета
            for dependent in self.reverse_graph.get(current_package, []):
                if dependent not in reverse_deps and dependent != target_package:
                    reverse_deps.append(dependent)
                # Рекурсивно ищем зависимости этих пакетов
                dfs_reverse(dependent)

        # Начинаем обход с целевого пакета
        dfs_reverse(target_package)
        return reverse_deps

    def find_all_reverse_dependencies(self, target_package: str) -> Dict[str, List[str]]:
        """
        Находит все обратные зависимости с информацией об уровнях
        """
        result = {
            'direct': [],  # Прямые обратные зависимости
            'indirect': [],  # Косвенные обратные зависимости
            'all': []  # Все обратные зависимости
        }

        # Прямые обратные зависимости
        result['direct'] = self.reverse_graph.get(target_package, [])

        # Все обратные зависимости (включая косвенные)
        all_reverse = self.find_reverse_dependencies(target_package)
        result['all'] = all_reverse

        # Косвенные обратные зависимости (все кроме прямых)
        result['indirect'] = [pkg for pkg in all_reverse if pkg not in result['direct']]

        return result

    def print_reverse_dependencies_tree(self, target_package: str):
        """
        Выводит дерево обратных зависимостей в ASCII формате
        """
        print(f"\nДерево обратных зависимостей для '{target_package}':")

        if target_package not in self.reverse_graph and not any(
                target_package in deps for deps in self.graph.values()
        ):
            print("  Обратные зависимости не найдены")
            return

        self._print_reverse_tree_recursive(target_package, "", set())

    def _print_reverse_tree_recursive(self, package: str, prefix: str, visited: Set[str]):
        """Рекурсивно печатает дерево обратных зависимостей"""
        if package in visited:
            print(prefix + "└── " + package + " (уже посещен)")
            return

        visited.add(package)

        reverse_deps = self.reverse_graph.get(package, [])
        if not reverse_deps:
            print(prefix + "└── " + package)
            return

        print(prefix + "├── " + package + " ←")

        for i, dep in enumerate(reverse_deps):
            is_last = i == len(reverse_deps) - 1
            connector = "└── " if is_last else "├── "
            next_prefix = prefix + ("    " if is_last else "│   ")

            print(prefix + "│   " + connector + dep)
            self._print_reverse_tree_recursive(dep, next_prefix, visited.copy())

    def get_graph_info(self) -> str:
        """Возвращает информацию о графе"""
        total_packages = len(self.graph)
        total_dependencies = sum(len(deps) for deps in self.graph.values())

        info = f"Информация о графе:\n"
        info += f"  Всего пакетов: {total_packages}\n"
        info += f"  Всего зависимостей: {total_dependencies}\n"
        info += f"  Пакеты: {', '.join(sorted(self.graph.keys()))}\n"

        return info


class ReverseDependencyAnalyzer:
    def __init__(self, config_file: str = "config.ini"):
        self.config = self.load_config(config_file)
        self.graph = DependencyGraphStage4()

    def load_config(self, config_file: str) -> configparser.ConfigParser:
        """Загружает конфигурацию из INI файла"""
        config = configparser.ConfigParser()
        if not config.read(config_file):
            print(f"Файл конфигурации {config_file} не найден. Используются значения по умолчанию.")
            config['DEFAULT'] = {
                'package_name': 'C',
                'test_mode': 'true',
                'repository_url': ''
            }
        return config

    def create_test_files_stage4(self):
        """Создает тестовые файлы для этапа 4"""
        test_cases = {
            "reverse_deps_simple.json": {
                "A": ["B"],
                "B": ["C"],
                "D": ["C"],
                "E": ["B"],
                "F": ["A"]
            },
            "reverse_deps_complex.json": {
                "Core": ["Utils"],
                "Network": ["Core", "Security"],
                "Database": ["Core", "Network"],
                "Security": ["Crypto"],
                "Crypto": ["Math"],
                "Utils": [],
                "Math": [],
                "WebApp": ["Network", "Database", "Security"],
                "MobileApp": ["Network", "Security"],
                "CLI": ["Core", "Utils"]
            },
            "reverse_deps_cyclic.json": {
                "A": ["B"],
                "B": ["C"],
                "C": ["A", "D"],
                "D": ["E"],
                "E": ["B"]
            }
        }

        for filename, test_data in test_cases.items():
            with open(filename, 'w') as f:
                json.dump(test_data, f, indent=2)
            print(f"Создан тестовый файл: {filename}")

    def cleanup_test_files(self):
        """Удаляет тестовые файлы"""
        test_files = ["reverse_deps_simple.json", "reverse_deps_complex.json", "reverse_deps_cyclic.json"]
        for filename in test_files:
            if os.path.exists(filename):
                os.remove(filename)
                print(f"Удален тестовый файл: {filename}")

    def demonstrate_reverse_dependencies(self, test_file: str, target_packages: List[str]):
        """Демонстрирует поиск обратных зависимостей"""
        print(f"\nАнализ файла: {test_file}")
        print("-" * 50)

        # Строим граф из тестового файла
        self.graph.build_graph_from_file(test_file)
        print(self.graph.get_graph_info())

        # Анализируем обратные зависимости для каждого целевого пакета
        for target_package in target_packages:
            print(f"\nАнализ обратных зависимостей для '{target_package}':")

            # Получаем все типы обратных зависимостей
            reverse_deps = self.graph.find_all_reverse_dependencies(target_package)

            print(f"  Прямые обратные зависимости: {reverse_deps['direct']}")
            print(f"  Косвенные обратные зависимости: {reverse_deps['indirect']}")
            print(f"  Все обратные зависимости: {reverse_deps['all']}")

            # Выводим дерево обратных зависимостей
            self.graph.print_reverse_dependencies_tree(target_package)

    def run_demo_cases(self):
        """Демонстрация различных случаев работы с обратными зависимостями"""
        print("\n" + "=" * 60)
        print("ДЕМОНСТРАЦИЯ ОБРАТНЫХ ЗАВИСИМОСТЕЙ")
        print("=" * 60)

        demo_cases = [
            ("reverse_deps_simple.json", ["C", "B", "A"], "Простой граф"),
            ("reverse_deps_complex.json", ["Core", "Security", "Utils"], "Сложный граф"),
            ("reverse_deps_cyclic.json", ["A", "B", "D"], "Граф с циклами")
        ]

        for test_file, target_packages, description in demo_cases:
            print(f"\n{description}:")
            print("-" * 40)
            self.demonstrate_reverse_dependencies(test_file, target_packages)

    def run(self):
        """Основная логика этапа 4"""
        print("=" * 60)
        print("ЭТАП 4: Обратные зависимости")
        print("=" * 60)

        # Чтение конфигурации
        package = self.config.get('DEFAULT', 'package_name', fallback='C')
        test_mode = self.config.getboolean('DEFAULT', 'test_mode', fallback=True)
        repo_path = self.config.get('DEFAULT', 'repository_url', fallback='')

        print(f"Конфигурация:")
        print(f"  Целевой пакет: {package}")
        print(f"  Режим тестирования: {test_mode}")
        print(f"  Путь к репозиторию: {repo_path if repo_path else 'не указан'}")

        # Создаем тестовые файлы если в режиме тестирования
        if test_mode and not repo_path:
            self.create_test_files_stage4()
            repo_path = "reverse_deps_complex.json"

        if repo_path and os.path.exists(repo_path):
            # Анализ указанного в конфигурации пакета
            print(f"\nАнализ пакета '{package}' из файла {repo_path}:")
            self.graph.build_graph_from_file(repo_path)

            reverse_deps = self.graph.find_all_reverse_dependencies(package)

            print(f"\nРезультаты для пакета '{package}':")
            print(f"  Прямые обратные зависимости: {reverse_deps['direct']}")
            print(f"  Косвенные обратные зависимости: {reverse_deps['indirect']}")
            print(f"  Все обратные зависимости: {reverse_deps['all']}")

            self.graph.print_reverse_dependencies_tree(package)

        else:
            print(f"Файл {repo_path} не найден!")

        # Демонстрация на различных тестовых случаях
        if test_mode:
            self.run_demo_cases()
            # Очистка тестовых файлов
            self.cleanup_test_files()

        print("\n" + "=" * 60)
        print("ЭТАП 4 ЗАВЕРШЕН")
        print("=" * 60)


def main():
    """Главная функция для этапа 4"""
    analyzer = ReverseDependencyAnalyzer("config.ini")
    analyzer.run()


if __name__ == "__main__":
    main()
