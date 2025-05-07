# app/services/analyzers/language_specific_analyzer.py
"""
Описание программного модуля:
-----------------------------
Данный модуль содержит интерфейс `LanguageSpecificAnalyzer` для языково-специфичных
анализаторов исходного кода. Интерфейс расширяет базовый интерфейс `CodeAnalyzer`
и добавляет методы для работы с конкретным языком программирования.

Функциональное назначение:
---------------------------
Модуль предназначен для создания специализированных анализаторов для конкретных
языков программирования. Это позволяет учитывать особенности синтаксиса и семантики
каждого языка при анализе исходного кода.
"""

# Импорты стандартной библиотеки Python
from typing import Dict, List, Optional, Any

# Импорты внутренних модулей
from services.analyzers.code_analyzer import CodeAnalyzer
from models.code_structure import LanguageType


class LanguageSpecificAnalyzer(CodeAnalyzer):
    """
    Description:
    ---------------
        Интерфейс для языково-специфичных анализаторов исходного кода.

    Attributes:
    ---------------
        language_type: Тип языка программирования.
        file_extensions: Список поддерживаемых расширений файлов.

    Methods:
    ---------------
        get_language_type: Возвращает тип языка программирования.
        get_file_extensions: Возвращает список поддерживаемых расширений файлов.
        is_supported_file: Проверяет, поддерживается ли файл.

    Examples:
    ---------------
        >>> analyzer = JavaAnalyzer()
        >>> analyzer.get_language_type()
        LanguageType.JAVA
    """

    def __init__(self, language_type: LanguageType, file_extensions: List[str]):
        """
        Description:
        ---------------
            Инициализирует анализатор языка.

        Args:
        ---------------
            language_type: Тип языка программирования.
            file_extensions: Список поддерживаемых расширений файлов.
        """
        self.language_type = language_type
        self.file_extensions = file_extensions

    def get_language_type(self) -> LanguageType:
        """
        Description:
        ---------------
            Возвращает тип языка программирования.

        Returns:
        ---------------
            LanguageType: Тип языка программирования.
        """
        return self.language_type

    def get_file_extensions(self) -> List[str]:
        """
        Description:
        ---------------
            Возвращает список поддерживаемых расширений файлов.

        Returns:
        ---------------
            List[str]: Список поддерживаемых расширений файлов.
        """
        return self.file_extensions

    def is_supported_file(self, file_path: str) -> bool:
        """
        Description:
        ---------------
            Проверяет, поддерживается ли файл.

        Args:
        ---------------
            file_path: Путь к файлу.

        Returns:
        ---------------
            bool: True, если файл поддерживается, иначе False.
        """
        import os
        ext = os.path.splitext(file_path)[1].lower().lstrip(".")
        return ext in self.file_extensions

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
        try:
            lang_type = LanguageType(language.upper())
            return lang_type == self.language_type
        except ValueError:
            return False

    def get_supported_languages(self) -> List[str]:
        """
        Description:
        ---------------
            Возвращает список поддерживаемых языков программирования.

        Returns:
        ---------------
            List[str]: Список поддерживаемых языков.
        """
        return [self.language_type.value]

    def analyze_directory(
        self, dir_path: str, recursive: bool = True
    ) -> Dict[str, Any]:
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
        import os
        from pathlib import Path

        if not os.path.isdir(dir_path):
            raise FileNotFoundError(f"Директория не найдена: {dir_path}")

        result = {}
        
        if recursive:
            for root, _, files in os.walk(dir_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    if self.is_supported_file(file_path):
                        try:
                            result[file_path] = self.analyze_file(file_path)
                        except Exception as e:
                            # Логирование ошибки и продолжение анализа
                            print(f"Ошибка при анализе файла {file_path}: {str(e)}")
        else:
            for file in os.listdir(dir_path):
                file_path = os.path.join(dir_path, file)
                if os.path.isfile(file_path) and self.is_supported_file(file_path):
                    try:
                        result[file_path] = self.analyze_file(file_path)
                    except Exception as e:
                        # Логирование ошибки и продолжение анализа
                        print(f"Ошибка при анализе файла {file_path}: {str(e)}")

        return result