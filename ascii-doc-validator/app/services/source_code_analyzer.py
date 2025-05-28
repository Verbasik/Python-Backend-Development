# app/services/source_code_analyzer.py
"""
Описание программного модуля:
-----------------------------
Данный модуль содержит класс `SourceCodeAnalyzer`, который предоставляет унифицированный
интерфейс для анализа исходного кода на различных языках программирования.
Класс использует соответствующие языково-специфичные анализаторы для каждого языка.

Функциональное назначение:
---------------------------
Модуль предназначен для абстрагирования от конкретных реализаций анализаторов
и предоставления единого интерфейса для анализа кода. Это упрощает интеграцию
с другими компонентами системы и обеспечивает расширяемость.
"""

# Импорты стандартной библиотеки Python
import os
from typing import Dict, List, Optional, Any

# Импорты внутренних модулей
from app.services.analyzers.analyzer_factory import AnalyzerFactory, detect_language_from_file
from app.services.analyzers import analyzer_factory
from app.models.code_structure import CodeStructure, LanguageType
from app.models.project_structure import ProjectStructure
from app.services.project_documentation_manager import ProjectDocumentationManager


class SourceCodeAnalyzer:
    """
    Description:
    ---------------
        Сервис для анализа исходного кода.

    Attributes:
    ---------------
        analyzer_factory: Фабрика анализаторов исходного кода.

    Methods:
    ---------------
        analyze_code: Анализирует исходный код из строки.
        analyze_file: Анализирует исходный код из файла.
        analyze_directory: Анализирует исходный код из директории.
        get_supported_languages: Возвращает список поддерживаемых языков.

    Examples:
    ---------------
        >>> analyzer = SourceCodeAnalyzer()
        >>> structure = analyzer.analyze_file("path/to/file.java")
    """

    def __init__(self, factory: Optional[AnalyzerFactory] = None):
        """
        Description:
        ---------------
            Инициализирует сервис анализа исходного кода.

        Args:
        ---------------
            factory: Фабрика анализаторов исходного кода (опционально).
        """
        self.analyzer_factory = factory or analyzer_factory

    def analyze_code(self, source_code: str, file_path: str, language_type: Optional[LanguageType] = None) -> CodeStructure:
        """
        Description:
        ---------------
            Анализирует исходный код из строки.

        Args:
        ---------------
            source_code: Строка с исходным кодом.
            file_path: Путь к файлу (для метаданных).
            language_type: Тип языка программирования (опционально).

        Returns:
        ---------------
            CodeStructure: Структурированное представление кода.

        Raises:
        ---------------
            ValueError: Если язык не поддерживается или произошла ошибка при парсинге.
        """
        # Если язык не указан, определяем его по расширению файла
        if language_type is None:
            language_type = detect_language_from_file(file_path)
            if language_type is None:
                raise ValueError(f"Не удалось определить язык программирования для файла: {file_path}")
        
        # Получаем соответствующий анализатор
        analyzer = self.analyzer_factory.get_analyzer(language_type)
        if analyzer is None:
            raise ValueError(f"Язык программирования не поддерживается: {language_type.value}")
        
        # Анализируем код
        return analyzer.analyze(source_code, file_path)

    def analyze_file(self, file_path: str, language_type: Optional[LanguageType] = None) -> CodeStructure:
        """
        Description:
        ---------------
            Анализирует исходный код из файла.

        Args:
        ---------------
            file_path: Путь к файлу с исходным кодом.
            language_type: Тип языка программирования (опционально).

        Returns:
        ---------------
            CodeStructure: Структурированное представление кода.

        Raises:
        ---------------
            FileNotFoundError: Если файл не найден.
            ValueError: Если язык не поддерживается или произошла ошибка при парсинге.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Файл не найден: {file_path}")
        
        # Если язык не указан, определяем его по расширению файла
        if language_type is None:
            language_type = detect_language_from_file(file_path)
            if language_type is None:
                raise ValueError(f"Не удалось определить язык программирования для файла: {file_path}")
        
        # Получаем соответствующий анализатор
        analyzer = self.analyzer_factory.get_analyzer(language_type)
        if analyzer is None:
            raise ValueError(f"Язык программирования не поддерживается: {language_type.value}")
        
        # Анализируем файл
        return analyzer.analyze_file(file_path)

    def analyze_directory(
        self, dir_path: str, recursive: bool = True, language_type: Optional[LanguageType] = None
    ) -> Dict[str, CodeStructure]:
        """
        Description:
        ---------------
            Анализирует исходный код из директории.

        Args:
        ---------------
            dir_path: Путь к директории с исходным кодом.
            recursive: Флаг рекурсивного анализа поддиректорий.
            language_type: Тип языка программирования (опционально).

        Returns:
        ---------------
            Dict[str, CodeStructure]: Словарь, где ключ - путь к файлу,
                                      значение - структурированное представление кода.

        Raises:
        ---------------
            FileNotFoundError: Если директория не найдена.
            ValueError: Если язык не поддерживается.
        """
        if not os.path.isdir(dir_path):
            raise FileNotFoundError(f"Директория не найдена: {dir_path}")
        
        result = {}
        
        # Если указан конкретный язык, используем соответствующий анализатор
        if language_type is not None:
            analyzer = self.analyzer_factory.get_analyzer(language_type)
            if analyzer is None:
                raise ValueError(f"Язык программирования не поддерживается: {language_type.value}")
            
            return analyzer.analyze_directory(dir_path, recursive)
        
        # Иначе анализируем все поддерживаемые файлы
        for root, _, files in os.walk(dir_path):
            if not recursive and root != dir_path:
                continue
            
            for file in files:
                file_path = os.path.join(root, file)
                language_type = detect_language_from_file(file_path)
                
                if language_type is not None:
                    analyzer = self.analyzer_factory.get_analyzer(language_type)
                    if analyzer is not None:
                        try:
                            result[file_path] = analyzer.analyze_file(file_path)
                        except Exception as e:
                            # Логирование ошибки и продолжение анализа
                            print(f"Ошибка при анализе файла {file_path}: {str(e)}")
        
        return result

    def get_supported_languages(self) -> List[str]:
        """
        Description:
        ---------------
            Возвращает список поддерживаемых языков программирования.

        Returns:
        ---------------
            List[str]: Список поддерживаемых языков.
        """
        return self.analyzer_factory.get_supported_languages()
    
    def analyze_project(self, code_dir: str, docs_dir: str) -> ProjectStructure:
        """
        Description:
        ---------------
            Анализирует структуру проекта, включая код и документацию.

        Args:
        ---------------
            code_dir: Путь к директории с кодом.
            docs_dir: Путь к директории с документацией.

        Returns:
        ---------------
            ProjectStructure: Структура проекта.

        Raises:
        ---------------
            FileNotFoundError: Если директории не существуют.
        """
        
        # Проверяем существование директорий
        if not os.path.isdir(code_dir):
            raise FileNotFoundError(f"Директория с кодом не найдена: {code_dir}")
        
        if not os.path.isdir(docs_dir):
            raise FileNotFoundError(f"Директория с документацией не найдена: {docs_dir}")
        
        # Создаем структуру проекта
        project = ProjectStructure(code_dir=code_dir, docs_dir=docs_dir)
        
        # Анализируем код
        code_structures = self.analyze_directory(code_dir, recursive=True)
        for file_path, structure in code_structures.items():
            project.add_code_structure(file_path, structure)
        
        # Анализируем документацию
        doc_manager = ProjectDocumentationManager(docs_dir)
        doc_structures = doc_manager.parse_documentation_directory()
        for file_path, structure in doc_structures.items():
            project.add_doc_structure(file_path, structure)
        
        # Создаем сопоставления файлов
        for code_path, code_structure in code_structures.items():
            # Определяем имя класса
            class_name = None
            if code_structure.classes:
                class_name = code_structure.classes[0].name
            
            # Ищем соответствующую документацию
            doc_path = doc_manager.find_doc_for_code_file(code_path, class_name)
            
            # Добавляем сопоставление
            project.add_file_mapping(code_path, doc_path, class_name)
        
        return project