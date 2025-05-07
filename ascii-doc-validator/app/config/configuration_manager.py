# app/config/configuration_manager.py
"""
Описание программного модуля:
-----------------------------
Данный модуль содержит класс `ConfigurationManager`, который отвечает за загрузку, 
хранение и сохранение конфигурации приложения и правил валидации. Конфигурация 
читается из YAML-файлов и может быть сохранена обратно в файлы.

Функциональное назначение:
---------------------------
Модуль предназначен для управления конфигурационными данными приложения. Он позволяет 
загружать конфигурацию из файлов, предоставлять доступ к данным и сохранять изменения 
обратно в файлы.
"""

# Импорты стандартной библиотеки Python
import os
from pathlib import Path

# Импорты сторонних библиотек
import yaml
from typing import Dict, Any, Optional, List


class ConfigurationManager:
    """
    Description:
    ---------------
        Класс для управления конфигурацией приложения и правилами валидации.

    Args:
    ---------------
        config_path: Путь к директории с конфигурационными файлами (опционально).
                     Если не указан, используется значение из переменной окружения
                     CONFIG_PATH или путь по умолчанию.

    Examples:
    ---------------
        >>> config_manager = ConfigurationManager()
        >>> app_config = config_manager.get_app_config()
        >>> validation_rules = config_manager.get_validation_rules()
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Description:
        ---------------
            Инициализирует менеджер конфигурации.

        Args:
        ---------------
            config_path: Путь к директории с конфигурационными файлами (опционально).
                         Если не указан, используется значение из переменной окружения
                         CONFIG_PATH или путь по умолчанию.
        """
        self.config_path = (
            config_path
            or os.environ.get("CONFIG_PATH", str(Path(__file__).parent.parent.parent / "config"))
        )
        self.app_config: Dict[str, Any] = {}
        self.validation_rules: List[Dict[str, Any]] = []
        self.load_configuration()

    def load_configuration(self) -> None:
        """
        Description:
        ---------------
            Загружает конфигурацию приложения и правила валидации из YAML-файлов.

        Raises:
        ---------------
            FileNotFoundError: Если файлы конфигурации отсутствуют.
        """
        # Загрузка основной конфигурации приложения
        app_config_path = Path(self.config_path) / "app_config.yaml"
        if app_config_path.exists():
            with open(app_config_path, "r") as f:
                self.app_config = yaml.safe_load(f)
        else:
            raise FileNotFoundError(f"Файл конфигурации не найден: {app_config_path}")

        # Загрузка правил валидации
        rules_path = Path(self.config_path) / "validation_rules.yaml"
        if rules_path.exists():
            with open(rules_path, "r") as f:
                self.validation_rules = yaml.safe_load(f)
        else:
            raise FileNotFoundError(f"Файл правил валидации не найден: {rules_path}")

    def get_app_config(self) -> Dict[str, Any]:
        """
        Description:
        ---------------
            Возвращает текущую конфигурацию приложения.

        Returns:
        ---------------
            Словарь с конфигурацией приложения.
        """
        return self.app_config

    def get_validation_rules(self) -> List[Dict[str, Any]]:
        """
        Description:
        ---------------
            Возвращает текущие правила валидации.

        Returns:
        ---------------
            Список словарей с правилами валидации.
        """
        return self.validation_rules

    def save_configuration(self) -> None:
        """
        Description:
        ---------------
            Сохраняет текущую конфигурацию приложения и правила валидации в YAML-файлы.

        Raises:
        ---------------
            PermissionError: Если нет прав на запись в указанные файлы.
        """
        # Сохранение основной конфигурации приложения
        app_config_path = Path(self.config_path) / "app_config.yaml"
        with open(app_config_path, "w") as f:
            yaml.dump(self.app_config, f)

        # Сохранение правил валидации
        rules_path = Path(self.config_path) / "validation_rules.yaml"
        with open(rules_path, "w") as f:
            yaml.dump(self.validation_rules, f)