#!/usr/bin/env python3


import configparser
import os
import sys
import json
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional
from urllib.parse import urljoin


class DependencyGraphConfig:
    """Класс для работы с конфигурацией приложения"""

    def __init__(self):
        self.default_config = {
            'package': {
                'name': 'serde',
                'version': '1.0.0',
            },
            'repository': {
                'url': 'https://crates.io/api/v1/crates/',
                'test_mode': 'false',
                'test_repo_path': './test-repo',
            },
            'output': {
                'graph_filename': 'dependency_graph.png',
                'ascii_tree_mode': 'false',
                'max_depth': '3'
            }
        }

        self.config = configparser.ConfigParser()
        self.config.read_dict(self.default_config)

    def load_config(self, config_path: str = 'config.ini') -> bool:
        """Загрузка конфигурации из файла"""
        try:
            if not os.path.exists(config_path):
                self._create_default_config(config_path)
                print(f"Создан файл конфигурации по умолчанию: {config_path}")
                return False

            self.config.read(config_path)
            return True

        except Exception as e:
            raise ConfigError(f"Ошибка загрузки конфигурации: {str(e)}")

    def _create_default_config(self, config_path: str):
        """Создание конфигурационного файла по умолчанию"""
        with open(config_path, 'w', encoding='utf-8') as f:
            self.config.write(f)

    def validate_config(self):
        """Валидация параметров конфигурации"""
        errors = []

        # Проверка имени пакета
        package_name = self.get_package_name()
        if not package_name or not isinstance(package_name, str):
            errors.append("Имя пакета должно быть непустой строкой")

        # Проверка версии
        version = self.get_package_version()
        if not version or not isinstance(version, str):
            errors.append("Версия пакета должна быть непустой строкой")

        # Проверка URL репозитория
        repo_url = self.get_repository_url()
        if repo_url and not isinstance(repo_url, str):
            errors.append("URL репозитория должен быть строкой")

        # Проверка пути к тестовому репозиторию
        test_repo_path = self.get_test_repo_path()
        if test_repo_path and not isinstance(test_repo_path, str):
            errors.append("Путь к тестовому репозиторию должен быть строкой")

        # Проверка режима тестового репозитория
        try:
            test_mode = self.get_test_mode()
            if not isinstance(test_mode, bool):
                errors.append("Режим тестового репозитория должен быть true/false")
        except ValueError as e:
            errors.append(str(e))

        # Проверка имени файла графа
        graph_filename = self.get_graph_filename()
        if not graph_filename or not isinstance(graph_filename, str):
            errors.append("Имя файла графа должно быть непустой строкой")

        # Проверка режима ASCII-дерева
        try:
            ascii_mode = self.get_ascii_tree_mode()
            if not isinstance(ascii_mode, bool):
                errors.append("Режим ASCII-дерева должен быть true/false")
        except ValueError as e:
            errors.append(str(e))

        # Проверка максимальной глубины
        try:
            max_depth = self.get_max_depth()
            if not isinstance(max_depth, int) or max_depth < 1:
                errors.append("Максимальная глубина должна быть положительным целым числом")
        except ValueError as e:
            errors.append(str(e))

        if errors:
            raise ConfigError("Ошибки валидации конфигурации:\n- " + "\n- ".join(errors))

    def get_package_name(self) -> str:
        return self.config.get('package', 'name', fallback='')

    def get_package_version(self) -> str:
        return self.config.get('package', 'version', fallback='')

    def get_repository_url(self) -> str:
        return self.config.get('repository', 'url', fallback='')

    def get_test_mode(self) -> bool:
        return self.config.getboolean('repository', 'test_mode', fallback=False)

    def get_test_repo_path(self) -> str:
        return self.config.get('repository', 'test_repo_path', fallback='')

    def get_graph_filename(self) -> str:
        return self.config.get('output', 'graph_filename', fallback='')

    def get_ascii_tree_mode(self) -> bool:
        return self.config.getboolean('output', 'ascii_tree_mode', fallback=False)

    def get_max_depth(self) -> int:
        return self.config.getint('output', 'max_depth', fallback=3)


class DependencyFetcher:
    """Класс для получения информации о зависимостях пакетов Rust"""

    def __init__(self, config: DependencyGraphConfig):
        self.config = config
        self.crates_api_url = "https://crates.io/api/v1/crates/"

    def get_package_dependencies(self, package_name: str, version: str) -> List[Dict[str, str]]:
        """
        Получение прямых зависимостей пакета из crates.io API
        """
        try:
            # Формируем URL для запроса информации о пакете
            package_url = f"{self.crates_api_url}{package_name}/{version}/dependencies"

            print(f"Запрос данных из: {package_url}")

            # Создаем запрос с User-Agent (требование crates.io API)
            req = urllib.request.Request(
                package_url,
                headers={'User-Agent': 'DependencyGraphTool/1.0'}
            )

            # Выполняем запрос
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status != 200:
                    raise DependencyError(f"HTTP ошибка: {response.status}")

                data = json.loads(response.read().decode('utf-8'))

                # Извлекаем зависимости из ответа
                dependencies = []
                for dep in data.get('dependencies', []):
                    dependency_info = {
                        'name': dep.get('crate_id', ''),
                        'version': dep.get('req', ''),
                        'kind': dep.get('kind', 'normal')
                    }
                    dependencies.append(dependency_info)

                return dependencies

        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise DependencyError(f"Пакет {package_name} версии {version} не найден")
            else:
                raise DependencyError(f"HTTP ошибка при запросе: {e.code}")
        except urllib.error.URLError as e:
            raise DependencyError(f"Ошибка сети: {e.reason}")
        except json.JSONDecodeError as e:
            raise DependencyError(f"Ошибка парсинга JSON: {e}")
        except Exception as e:
            raise DependencyError(f"Неожиданная ошибка: {str(e)}")

    def display_dependencies(self, dependencies: List[Dict[str, str]]):
        """
        Вывод зависимостей на экран (требование этапа 2)
        """
        if not dependencies:
            print("Прямые зависимости не найдены")
            return

        print("\n" + "=" * 60)
        print("ПРЯМЫЕ ЗАВИСИМОСТИ ПАКЕТА")
        print("=" * 60)

        for i, dep in enumerate(dependencies, 1):
            kind = dep['kind']
            kind_display = "dev" if kind == "dev" else "build" if kind == "build" else "normal"

            print(f"{i:2d}. {dep['name']:30} {dep['version']:15} [{kind_display}]")

        print("=" * 60)
        print(f"Всего зависимостей: {len(dependencies)}")


class ConfigError(Exception):
    """Класс для ошибок конфигурации"""
    pass


class DependencyError(Exception):
    """Класс для ошибок получения зависимостей"""
    pass


def main():
    """Основная функция приложения"""
    try:
        # Инициализация конфигурации
        config_manager = DependencyGraphConfig()

        # Загрузка конфигурации
        config_loaded = config_manager.load_config()

        if not config_loaded:
            print("Пожалуйста, настройте config.ini и запустите приложение снова.")
            return

        # Валидация конфигурации
        config_manager.validate_config()

        # Вывод конфигурации
        print("=" * 50)
        print("ТЕКУЩАЯ КОНФИГУРАЦИЯ")
        print("=" * 50)

        for section in config_manager.config.sections():
            print(f"\n[{section}]")
            for key, value in config_manager.config.items(section):
                print(f"  {key} = {value}")

        print("\n" + "=" * 50)

        # Получение информации о зависимостях
        package_name = config_manager.get_package_name()
        package_version = config_manager.get_package_version()

        print(f"\nПолучение зависимостей для пакета: {package_name} {package_version}")

        fetcher = DependencyFetcher(config_manager)
        dependencies = fetcher.get_package_dependencies(package_name, package_version)

        # Вывод зависимостей (требование этапа 2)
        fetcher.display_dependencies(dependencies)

        print("\nЭтап 2 завершен успешно! Данные о зависимостях получены.")

    except ConfigError as e:
        print(f"Ошибка конфигурации: {e}")
        sys.exit(1)
    except DependencyError as e:
        print(f"Ошибка получения зависимостей: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
