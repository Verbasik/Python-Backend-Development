# app/services/analyzers/code_analyzer.py
"""
Описание программного модуля:
-----------------------------
Данный модуль содержит базовый интерфейс `CodeAnalyzer` для анализаторов исходного кода.
Интерфейс определяет методы для анализа отдельных файлов и директорий с кодом, а также
проверки поддержки различных языков программирования.

Функциональное назначение:
---------------------------
Модуль предназначен для создания унифицированного API для анализаторов исходного кода
различных языков программирования. Это позволяет абстрагироваться от конкретной
реализации анализатора и использовать одинаковый интерфейс для всех поддерживаемых языков.
"""

# Импорты стандартной библиотеки Python
import os
from pathlib import Path
from typing import Dict, List, Set, Optional, Any
from abc import ABC, abstractmethod

# Импорты внутренних моделей
from app.models.code_structure import CodeStructure, LanguageType


class CodeAnalyzer(ABC):
    """
    Description:
    ---------------
        Базовый интерфейс для анализаторов исходного кода.

    Methods:
    ---------------
        analyze: Анализирует исходный код из строки.
        analyze_file: Анализирует исходный код из файла.
        analyze_directory: Анализирует исходный код из директории.
        supports_language: Проверяет поддержку языка программирования.
        get_supported_languages: Возвращает список поддерживаемых языков.

    Examples:
    ---------------
        >>> analyzer = JavaCodeAnalyzer()
        >>> structure = analyzer.analyze_file("path/to/file.java")
    """

    @abstractmethod
    def analyze(self, source_code: str, file_path: str) -> CodeStructure:
        """
        Description:
        ---------------
            Анализирует исходный код из строки.

        Args:
        ---------------
            source_code: Строка с исходным кодом.
            file_path: Путь к файлу (для метаданных).

        Returns:
        ---------------
            CodeStructure: Структурированное представление кода.
        """
        pass

    @abstractmethod
    def analyze_file(self, file_path: str) -> CodeStructure:
        """
        Description:
        ---------------
            Анализирует исходный код из файла.

        Args:
        ---------------
            file_path: Путь к файлу с исходным кодом.

        Returns:
        ---------------
            CodeStructure: Структурированное представление кода.

        Raises:
        ---------------
            FileNotFoundError: Если файл не найден.
            ValueError: Если формат файла не поддерживается.
        """
        pass

    @abstractmethod
    def analyze_directory(
        self, dir_path: str, recursive: bool = True
    ) -> Dict[str, CodeStructure]:
        """
        Description:
        ---------------
            Анализирует исходный код из директории.

        Args:
        ---------------
            dir_path: Путь к директории с исходным кодом.
            recursive: Флаг рекурсивного анализа поддиректорий.

        Returns:
        ---------------
            Dict[str, CodeStructure]: Словарь, где ключ - путь к файлу,
                                      значение - структурированное представление кода.

        Raises:
        ---------------
            FileNotFoundError: Если директория не найдена.
        """
        pass

    @abstractmethod
    def supports_language(self, language: str) -> bool:
        """
        Description:
        ---------------
            Проверяет поддержку языка программирования.

        Args:
        ---------------
            language: Название языка программирования.

        Returns:
        ---------------
            bool: True, если язык поддерживается, иначе False.
        """
        pass

    @abstractmethod
    def get_supported_languages(self) -> List[str]:
        """
        Description:
        ---------------
            Возвращает список поддерживаемых языков программирования.

        Returns:
        ---------------
            List[str]: Список поддерживаемых языков.
        """
        pass