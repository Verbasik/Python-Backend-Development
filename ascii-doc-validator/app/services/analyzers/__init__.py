# app/services/analyzers/__init__.py
"""
Описание программного модуля:
-----------------------------
Данный модуль инициализирует фабрику анализаторов исходного кода и регистрирует
доступные анализаторы для различных языков программирования.

Функциональное назначение:
---------------------------
Модуль предназначен для централизованной инициализации анализаторов исходного кода
и предоставления единой точки доступа к ним через фабрику.
"""

# Импорты внутренних модулей
from models.code_structure import LanguageType
from services.analyzers.analyzer_factory import AnalyzerFactory
from services.analyzers.java_analyzer import JavaAnalyzer
from services.analyzers.python_analyzer import PythonAnalyzer

# Инициализация фабрики анализаторов
analyzer_factory = AnalyzerFactory()

# Регистрация анализаторов
analyzer_factory.register_analyzer(LanguageType.JAVA, JavaAnalyzer)
analyzer_factory.register_analyzer(LanguageType.PYTHON, PythonAnalyzer)