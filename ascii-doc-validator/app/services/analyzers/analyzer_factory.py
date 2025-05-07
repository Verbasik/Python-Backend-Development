# app/services/analyzers/analyzer_factory.py
"""
Описание программного модуля:
-----------------------------
Данный модуль содержит класс `AnalyzerFactory` для создания экземпляров анализаторов
исходного кода в зависимости от языка программирования или расширения файла.

Функциональное назначение:
---------------------------
Модуль предназначен для автоматического выбора соответствующего анализатора
исходного кода на основе языка программирования или расширения файла. 
Это позволяет абстрагироваться от конкретной реализации анализатора и 
использовать единую точку входа для анализа кода на различных языках.
"""

# Импорты стандартной библиотеки Python
import os
from typing import Dict, Type, List, Optional

# Импорты внутренних модулей
from services.analyzers.code_analyzer import CodeAnalyzer
from services.analyzers.language_specific_analyzer import LanguageSpecificAnalyzer
from models.code_structure import LanguageType

# Словарь соответствия расширений файлов и языков программирования
LANGUAGE_EXTENSIONS = {
    LanguageType.JAVA: ["java"],
    LanguageType.PYTHON: ["py"],
    LanguageType.JAVASCRIPT: ["js"],
    LanguageType.TYPESCRIPT: ["ts"],
    LanguageType.CSHARP: ["cs"],
}


class AnalyzerFactory:
    """
    Description:
    ---------------
        Фабрика для создания анализаторов исходного кода.

    Attributes:
    ---------------
        registered_analyzers: Словарь зарегистрированных анализаторов по типу языка.

    Methods:
    ---------------
        register_analyzer: Регистрирует класс анализатора для языка программирования.
        get_analyzer: Возвращает экземпляр анализатора для указанного языка.
        get_analyzer_for_file: Возвращает экземпляр анализатора для указанного файла.
        get_supported_languages: Возвращает список поддерживаемых языков.

    Examples:
    ---------------
        >>> factory = AnalyzerFactory()
        >>> factory.register_analyzer(LanguageType.JAVA, JavaAnalyzer)
        >>> analyzer = factory.get_analyzer(LanguageType.JAVA)
    """

    _instance = None

    def __new__(cls):
        """
        Description:
        ---------------
            Создает экземпляр фабрики (реализация паттерна Singleton).

        Returns:
        ---------------
            AnalyzerFactory: Экземпляр фабрики.
        """
        if cls._instance is None:
            cls._instance = super(AnalyzerFactory, cls).__new__(cls)
            cls._instance.registered_analyzers = {}
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """
        Description:
        ---------------
            Инициализирует фабрику анализаторов, если она еще не инициализирована.
        """
        if not self._initialized:
            self.registered_analyzers: Dict[LanguageType, Type[LanguageSpecificAnalyzer]] = {}
            self._initialized = True

    def register_analyzer(
        self, language_type: LanguageType, analyzer_class: Type[LanguageSpecificAnalyzer]
    ) -> None:
        """
        Description:
        ---------------
            Регистрирует класс анализатора для языка программирования.

        Args:
        ---------------
            language_type: Тип языка программирования.
            analyzer_class: Класс анализатора.
        """
        self.registered_analyzers[language_type] = analyzer_class

    def get_analyzer(self, language_type: LanguageType) -> Optional[LanguageSpecificAnalyzer]:
        """
        Description:
        ---------------
            Возвращает экземпляр анализатора для указанного языка.

        Args:
        ---------------
            language_type: Тип языка программирования.

        Returns:
        ---------------
            Optional[LanguageSpecificAnalyzer]: Экземпляр анализатора или None, если язык не поддерживается.
        """
        analyzer_class = self.registered_analyzers.get(language_type)
        if analyzer_class:
            return analyzer_class()
        return None

    def get_analyzer_for_file(self, file_path: str) -> Optional[LanguageSpecificAnalyzer]:
        """
        Description:
        ---------------
            Возвращает экземпляр анализатора для указанного файла на основе его расширения.

        Args:
        ---------------
            file_path: Путь к файлу.

        Returns:
        ---------------
            Optional[LanguageSpecificAnalyzer]: Экземпляр анализатора или None, если формат файла не поддерживается.
        """
        ext = os.path.splitext(file_path)[1].lower().lstrip(".")
        
        for language_type, extensions in LANGUAGE_EXTENSIONS.items():
            if ext in extensions and language_type in self.registered_analyzers:
                return self.get_analyzer(language_type)
        
        return None

    def get_supported_languages(self) -> List[str]:
        """
        Description:
        ---------------
            Возвращает список поддерживаемых языков программирования.

        Returns:
        ---------------
            List[str]: Список поддерживаемых языков.
        """
        return [lang.value for lang in self.registered_analyzers.keys()]


def detect_language_from_file(file_path: str) -> Optional[LanguageType]:
    """
    Description:
    ---------------
        Определяет язык программирования на основе расширения файла.

    Args:
    ---------------
        file_path: Путь к файлу.

    Returns:
    ---------------
        Optional[LanguageType]: Тип языка программирования или None, если формат файла не поддерживается.
    """
    ext = os.path.splitext(file_path)[1].lower().lstrip('.')
    
    for language_type, extensions in LANGUAGE_EXTENSIONS.items():
        if ext in extensions:
            return language_type
    
    return None
