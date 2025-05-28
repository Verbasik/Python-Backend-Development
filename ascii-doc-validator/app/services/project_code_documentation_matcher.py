# app/services/project_code_documentation_matcher.py
"""
Описание программного модуля:
-----------------------------
Данный модуль содержит класс `ProjectCodeDocumentationMatcher`, который отвечает 
за сопоставление исходного кода проекта с документацией. Класс предоставляет методы 
для анализа множества файлов кода и документации, их сопоставления и выявления 
несоответствий.

Функциональное назначение:
---------------------------
Модуль предназначен для автоматического сопоставления структуры проекта 
с документацией и выявления недокументированных или устаревших элементов.
"""

import os
import re
import uuid
from datetime import datetime
from typing import List, Dict, Set, Tuple, Optional, Any

from app.models.code_structure import LanguageType
from app.models.code_structure import CodeStructure
from app.models.validation_report import (
    ValidationIssue, ValidationReport, ValidationStatus, ValidationSummary, IssueType, IssueLocation
)
from app.services.source_code_analyzer import SourceCodeAnalyzer
from app.services.code_documentation_matcher import CodeDocumentationMatcher


class ProjectCodeDocumentationMatcher:
    """
    Description:
    ---------------
        Класс для сопоставления исходного кода проекта с документацией.

    Attributes:
    ---------------
        source_code_analyzer: Анализатор исходного кода.
        code_doc_matcher: Сопоставитель кода и документации.

    Methods:
    ---------------
        match_project: Сопоставляет структуру проекта с документацией.
        match_file: Сопоставляет файл кода с документацией.
    """

    def __init__(self, source_code_analyzer: Optional[SourceCodeAnalyzer] = None):
        """
        Description:
        ---------------
            Инициализирует сопоставитель кода проекта и документации.

        Args:
        ---------------
            source_code_analyzer: Анализатор исходного кода (опционально).
        """
        self.source_code_analyzer = source_code_analyzer or SourceCodeAnalyzer()
        self.code_doc_matcher = CodeDocumentationMatcher(self.source_code_analyzer)

    def match_project(
        self, code_structures: Dict[str, CodeStructure], doc_structures: Dict[str, Any]
    ) -> ValidationReport:
        """
        Description:
        ---------------
            Сопоставляет структуру проекта с документацией.

        Args:
        ---------------
            code_structures: Словарь структур кода (путь_к_файлу -> структура_кода).
            doc_structures: Словарь структур документации (путь_к_файлу -> структура_документации).

        Returns:
        ---------------
            ValidationReport: Отчет о валидации проекта.
        """
        # Создаем отчет
        validation_id = str(uuid.uuid4())
        issues = []
        corrections = []
        
        # Сопоставляем каждый файл кода с соответствующей документацией
        for code_path, code_structure in code_structures.items():
            # Определяем имя класса
            class_name = self._get_primary_class_name(code_structure)
            
            # Находим соответствующую документацию
            doc_path, doc_structure = self._find_matching_doc(code_path, class_name, doc_structures)
            
            if doc_structure:
                # Выполняем сопоставление кода и документации
                file_issues = self._match_file(code_structure, doc_structure, code_path, doc_path)
                issues.extend(file_issues)
            else:
                # Если документация не найдена, добавляем проблему
                issues.append(ValidationIssue(
                    id=f"COMPLETENESS-FILE-001-{len(issues)+1}",
                    type=IssueType.COMPLETENESS,
                    location=IssueLocation(),
                    issue=f"Файл кода '{code_path}' не имеет соответствующей документации"
                ))
        
        # Проверяем наличие документации без соответствующего кода
        for doc_path, doc_structure in doc_structures.items():
            class_name = self._extract_class_name(doc_structure)
            if class_name and not self._has_matching_code(class_name, code_structures):
                issues.append(ValidationIssue(
                    id=f"SEMANTIC-FILE-001-{len(issues)+1}",
                    type=IssueType.SEMANTIC,
                    location=IssueLocation(),
                    issue=f"Документация '{doc_path}' описывает класс '{class_name}', который отсутствует в коде проекта"
                ))
        
        # Создаем сводку
        summary = ValidationSummary(
            total_issues=len(issues),
            corrected_issues=len(corrections),
            skipped_issues=0,
        )
        
        # Определяем статус валидации
        if not issues:
            status = ValidationStatus.VALID
        elif all(issue.type != IssueType.COMPLETENESS and issue.type != IssueType.SEMANTIC for issue in issues):
            status = ValidationStatus.VALID_WITH_WARNINGS
        else:
            status = ValidationStatus.INVALID
        
        # Создаем отчет
        report = ValidationReport(
            validation_id=validation_id,
            documentation_source="project",
            timestamp=datetime.now(),
            issues=issues,
            corrections=corrections,
            summary=summary,
            status=status,
        )
        
        return report

    def _match_file(
        self, code_structure: CodeStructure, doc_structure: Dict[str, Any],
        code_path: str, doc_path: str
    ) -> List[ValidationIssue]:
        """
        Description:
        ---------------
            Сопоставляет файл кода с документацией.

        Args:
        ---------------
            code_structure: Структура кода.
            doc_structure: Структура документации.
            code_path: Путь к файлу кода.
            doc_path: Путь к файлу документации.

        Returns:
        ---------------
            List[ValidationIssue]: Список проблем валидации.
        """
        issues = []
        
        # Проверяем API-эндпоинты
        api_issues = self.code_doc_matcher.match_api_endpoints(code_structure, doc_structure)
        issues.extend(self._add_file_paths_to_issues(api_issues, code_path, doc_path))
        
        # Проверяем недокументированные методы
        undocumented_issues = self.code_doc_matcher.find_undocumented_methods(code_structure, doc_structure)
        issues.extend(self._add_file_paths_to_issues(undocumented_issues, code_path, doc_path))
        
        # Проверяем отсутствующие в коде методы
        missing_methods_issues = self.code_doc_matcher.find_documented_but_missing_methods(code_structure, doc_structure)
        issues.extend(self._add_file_paths_to_issues(missing_methods_issues, code_path, doc_path))
        
        return issues

    def _add_file_paths_to_issues(
        self, issues: List[ValidationIssue], code_path: str, doc_path: str
    ) -> List[ValidationIssue]:
        """
        Description:
        ---------------
            Добавляет пути к файлам в проблемы валидации.

        Args:
        ---------------
            issues: Список проблем валидации.
            code_path: Путь к файлу кода.
            doc_path: Путь к файлу документации.

        Returns:
        ---------------
            List[ValidationIssue]: Список проблем валидации с добавленными путями.
        """
        for issue in issues:
            # Добавляем информацию о файлах в описание проблемы
            issue.issue = f"[{os.path.basename(code_path)} | {os.path.basename(doc_path)}] {issue.issue}"
        
        return issues

    def _get_primary_class_name(self, code_structure: CodeStructure) -> Optional[str]:
        """
        Description:
        ---------------
            Получает имя основного класса из структуры кода.

        Args:
        ---------------
            code_structure: Структура кода.

        Returns:
        ---------------
            Optional[str]: Имя класса или None, если классы отсутствуют.
        """
        if code_structure.classes:
            return code_structure.classes[0].name
        return None

    # Поиск соответствующей документации для файла кода
    def _find_matching_doc(
        self, 
        code_path: str, 
        class_name: Optional[str], 
        doc_structures: Dict[str, Any]
    ) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        """
        Description:
        ---------------
            Находит соответствующую документацию для указанного файла кода.
            Поиск производится по трем этапам: по имени класса, по имени файла 
            и по анализу содержимого.

        Args:
        ---------------
            code_path: Путь к файлу исходного кода
            class_name: Имя класса для поиска (может быть None)
            doc_structures: Словарь структур документации

        Returns:
        ---------------
            Кортеж из пути к найденной документации и её структуры,
            или (None, None) если документация не найдена

        Raises:
        ---------------
            Exception: При ошибках анализа структуры кода

        Examples:
        ---------------
            >>> doc_path, doc_struct = self._find_matching_doc(
            ...     "src/MyClass.java", "MyClass", doc_structures
            ... )
            >>> print(doc_path)  # "docs/MyClass_documentation.md"
        """
        from services.analyzers.analyzer_factory import detect_language_from_file
        
        # Вспомогательная функция для красивого логирования процесса поиска
        def log(message: str, level: str = "INFO", indent: int = 0) -> None:
            """
            Description:
            ---------------
                Выводит красиво отформатированные логи с эмодзи и цветовым кодированием.

            Args:
            ---------------
                message: Текст сообщения для вывода
                level: Уровень логирования (INFO, ERROR, FOUND, etc.)
                indent: Уровень отступа для вложенности

            Returns:
            ---------------
                None

            Examples:
            ---------------
                >>> log("Начинаем поиск", "START", 0)
                🔍 Начинаем поиск
            """
            # Словарь иконок для различных типов сообщений
            icons = {
                "START": "🔍",
                "INFO": "ℹ️ ",
                "SEARCH": "🔎",
                "FOUND": "✅",
                "NOT_FOUND": "❌",
                "LANG": "🌐",
                "FILE": "📄",
                "CLASS": "🏷️ ",
                "MATCH": "🎯",
                "ERROR": "⚠️ ",
                "STEP": "👉",
                "RESULT": "📋"
            }
            
            # Цветовые коды ANSI для терминала
            colors = {
                "START": "\033[95m",     # Фиолетовый
                "INFO": "\033[94m",      # Синий
                "SEARCH": "\033[96m",    # Голубой
                "FOUND": "\033[92m",     # Зеленый
                "NOT_FOUND": "\033[91m", # Красный
                "LANG": "\033[93m",      # Желтый
                "FILE": "\033[94m",      # Синий
                "CLASS": "\033[95m",     # Фиолетовый
                "MATCH": "\033[92m",     # Зеленый
                "ERROR": "\033[91m",     # Красный
                "STEP": "\033[96m",      # Голубой
                "RESULT": "\033[92m"     # Зеленый
            }
            
            # Код сброса цвета
            reset = "\033[0m"
            icon = icons.get(level, "  ")
            color = colors.get(level, "")
            prefix = "  " * indent
            
            print(f"{prefix}{color}{icon} {message}{reset}")

        # Начинаем процесс поиска с подробным логированием
        log("=" * 60, "INFO")
        log("ПОИСК ДОКУМЕНТАЦИИ", "START")
        log("=" * 60, "INFO")
        log(f"Файл кода: {code_path}", "FILE", 1)
        log(f"Имя класса: {class_name or 'Не указано'}", "CLASS", 1)
        
        # Определяем язык программирования исходного кода
        code_language = detect_language_from_file(code_path)
        log(f"Определен язык кода: {code_language or 'Неизвестен'}", "LANG", 1)
        
        # Этап 1: Поиск документации по имени класса с учетом языка
        if class_name:
            log("", "INFO")
            log("ЭТАП 1: Поиск по имени класса", "STEP")
            log("-" * 40, "INFO", 1)
            log(f"Ищем класс: {class_name}", "SEARCH", 1)
            
            # Перебираем все доступные документы
            for doc_path, doc_structure in doc_structures.items():
                doc_class_name = self._extract_class_name(doc_structure)
                if doc_class_name:
                    log(f"Проверяем: {os.path.basename(doc_path)}", "INFO", 2)
                    log(f"Класс в документе: {doc_class_name}", "CLASS", 3)
                    
                    # Проверяем точное совпадение имени класса
                    if doc_class_name == class_name:
                        # Проверяем совместимость языков программирования
                        is_compatible = self._is_language_compatible(
                            code_path, doc_path, doc_structure
                        )
                        if is_compatible:
                            log(f"Найдено соответствие!", "FOUND", 3)
                            log(f"Документация: {doc_path}", "RESULT", 2)
                            log("=" * 60, "INFO")
                            return doc_path, doc_structure
                        else:
                            log("Несовместимые языки", "NOT_FOUND", 3)
            
            log("Не найдено по имени класса", "NOT_FOUND", 1)
        
        # Этап 2: Поиск документации по имени файла с учетом языка
        log("", "INFO")
        log("ЭТАП 2: Поиск по имени файла", "STEP")
        log("-" * 40, "INFO", 1)
        
        # Получаем базовое имя файла без расширения
        code_base_name = os.path.splitext(os.path.basename(code_path))[0]
        log(f"Базовое имя файла: {code_base_name}", "FILE", 1)
        
        # Собираем список совместимых документов
        compatible_docs = []
        for doc_path, doc_structure in doc_structures.items():
            # Проверяем совместимость языков
            is_compatible = self._is_language_compatible(
                code_path, doc_path, doc_structure
            )
            
            if is_compatible:
                # Получаем очищенное имя документа
                doc_base_name = os.path.splitext(os.path.basename(doc_path))[0]
                clean_doc_name = self._clean_filename_prefix(doc_base_name)
                
                log(f"Проверяем: {os.path.basename(doc_path)}", "INFO", 2)
                log(f"Очищенное имя: {clean_doc_name}", "INFO", 3)
                
                # Сравниваем имена файлов (без учета регистра)
                if clean_doc_name.lower() == code_base_name.lower():
                    log("Совпадение по имени!", "MATCH", 3)
                    compatible_docs.append((doc_path, doc_structure))
        
        # Если найдены совместимые документы, возвращаем первый
        if compatible_docs:
            result_doc_path, result_doc_structure = compatible_docs[0]
            log(f"Найдена документация: {result_doc_path}", "FOUND", 1)
            log("=" * 60, "INFO")
            return result_doc_path, result_doc_structure
        
        log("Не найдено по имени файла", "NOT_FOUND", 1)
        
        # Этап 3: Поиск документации по анализу содержимого и структуры
        if code_language:
            log("", "INFO")
            log("ЭТАП 3: Поиск по содержимому", "STEP")
            log("-" * 40, "INFO", 1)
            
            try:
                log("Анализируем структуру кода...", "SEARCH", 1)
                # Анализируем структуру исходного кода
                code_structure = self.source_code_analyzer.analyze_file(code_path)
                log("Ищем схожую документацию...", "SEARCH", 1)
                
                # Ищем документацию по структурному сходству
                result = self._find_doc_by_content_similarity(
                    code_structure, doc_structures, code_language
                )
                if result[0]:
                    log(f"Найдена документация: {result[0]}", "FOUND", 1)
                else:
                    log("Не найдено подходящей документации", "NOT_FOUND", 1)
                
                log("=" * 60, "INFO")
                return result
                
            except Exception as e:
                log(f"Ошибка при анализе: {str(e)}", "ERROR", 1)
        
        # Если ничего не найдено на всех этапах
        log("", "INFO")
        log("Документация не найдена", "NOT_FOUND")
        log("=" * 60, "INFO")
        return None, None

    # Проверка совместимости языков программирования кода и документации
    def _is_language_compatible(
        self, 
        code_path: str, 
        doc_path: str, 
        doc_structure: Dict[str, Any]
    ) -> bool:
        """
        Description:
        ---------------
            Проверяет совместимость языков программирования кода и документации.
            Сравнивает язык исходного кода с языком, указанным в документации.

        Args:
        ---------------
            code_path: Путь к файлу исходного кода
            doc_path: Путь к файлу документации
            doc_structure: Структура документации для анализа

        Returns:
        ---------------
            True если языки совместимы или не определены, False в противном случае

        Raises:
        ---------------
            None

        Examples:
        ---------------
            >>> is_compatible = self._is_language_compatible(
            ...     "src/Main.java", "docs/java_guide.md", doc_struct
            ... )
            >>> print(is_compatible)  # True
        """
        from services.analyzers.analyzer_factory import detect_language_from_file

        # Вспомогательная функция для логирования совместимости языков
        def log_compat(message: str, result: bool = None) -> None:
            """
            Description:
            ---------------
                Выводит сообщения о проверке совместимости языков.

            Args:
            ---------------
                message: Текст сообщения
                result: Результат проверки (True/False/None)

            Returns:
            ---------------
                None
            """
            if result is not None:
                icon = "✅" if result else "❌"
                color = "\033[92m" if result else "\033[91m"
                print(f"            {color}{icon} {message}\033[0m")
            else:
                print(f"            🔍 {message}")
        
        # Начало проверки совместимости
        log_compat(f"Начинаем проверку совместимости языков для {code_path} и {doc_path}")
        
        # Определяем язык исходного кода
        log_compat("Определяем язык исходного кода...")
        code_language = detect_language_from_file(code_path)
        
        if code_language:
            log_compat(f"Обнаружен язык кода: {code_language}")
        else:
            log_compat("Язык кода не определен, считаем совместимым", True)
            return True
        
        # Определяем язык документации из её структуры
        log_compat("Определяем язык документации...")
        doc_language = self._detect_doc_language_from_structure(
            doc_path, doc_structure
        )
        
        if doc_language:
            log_compat(f"Обнаружен язык документации: {doc_language}")
        else:
            log_compat("Язык документации не определен, считаем совместимым", True)
            return True
        
        # Сравниваем языки программирования
        log_compat(f"Сравниваем языки: {code_language} vs {doc_language}")
        result = code_language == doc_language
        
        # Финальный результат
        if result:
            log_compat(f"Языки совместимы: {code_language} == {doc_language}", True)
        else:
            log_compat(f"Языки НЕ совместимы: {code_language} != {doc_language}", False)
        
        return result

    # Очистка имени файла от языковых префиксов и постфиксов
    def _clean_filename_prefix(self, filename: str) -> str:
        """
        Description:
        ---------------
            Удаляет языковые префиксы и постфиксы из имени файла для 
            более точного сопоставления с исходным кодом.

        Args:
        ---------------
            filename: Исходное имя файла для очистки

        Returns:
        ---------------
            Очищенное имя файла без префиксов и постфиксов

        Raises:
        ---------------
            None

        Examples:
        ---------------
            >>> clean_name = self._clean_filename_prefix("java_MyClass_doc")
            >>> print(clean_name)  # "MyClass"
        """
        # Расширенный список префиксов для удаления
        prefixes = [
            'java_', 'py_', 'python_', 'js_', 'javascript_', 
            'ts_', 'typescript_', 'cs_', 'csharp_',
            'module_', 'class_', 'api_'
        ]
        
        # Список постфиксов для удаления
        suffixes = [
            '_doc', '_docs', '_documentation', '_api', '_spec'
        ]
        
        filename_lower = filename.lower()
        
        # Удаляем префиксы в начале имени файла
        for prefix in prefixes:
            if filename_lower.startswith(prefix):
                filename = filename[len(prefix):]
                filename_lower = filename.lower()
                break
        
        # Удаляем постфиксы в конце имени файла
        for suffix in suffixes:
            if filename_lower.endswith(suffix):
                filename = filename[:-len(suffix)]
                break
        
        return filename

    # Определение языка программирования из структуры документации
    def _detect_doc_language_from_structure(
        self, 
        doc_path: str, 
        doc_structure: Dict[str, Any]
    ) -> Optional['LanguageType']:
        """
        Description:
        ---------------
            Определяет язык программирования документации на основе её структуры,
            содержимого и имени файла. Анализирует префиксы, блоки кода и ключевые слова.

        Args:
        ---------------
            doc_path: Путь к файлу документации
            doc_structure: Словарь со структурой документации

        Returns:
        ---------------
            Тип языка программирования или None если не определен

        Raises:
        ---------------
            ValueError: При неизвестном типе языка

        Examples:
        ---------------
            >>> lang = self._detect_doc_language_from_structure(
            ...     "docs/java_guide.md", doc_struct
            ... )
            >>> print(lang)  # LanguageType.JAVA
        """
        # 1. Проверяем уже определенный язык в структуре документа
        detected_lang = doc_structure.get('detected_language')
        if detected_lang:
            try:
                return LanguageType(detected_lang)
            except ValueError:
                pass
        
        # 2. Анализ префикса имени файла (более гибкий подход)
        filename = os.path.basename(doc_path).lower()
        
        # Паттерны для определения Java
        if any(pattern in filename for pattern in ['java_', '_java', 'java-']):
            return LanguageType.JAVA
        
        # Паттерны для определения Python
        if any(pattern in filename for pattern in [
            'py_', '_py', 'python_', '_python', 'py-'
        ]):
            return LanguageType.PYTHON
        
        # Паттерны для определения JavaScript
        if any(pattern in filename for pattern in [
            'js_', '_js', 'javascript_', '_javascript', 'js-'
        ]):
            return LanguageType.JAVASCRIPT
        
        # 3. Анализ содержимого блоков кода в документации
        for section in doc_structure.get("sections", []):
            content = section.get("content", "")
            
            # Поиск маркеров Java в блоках кода
            if ("```java" in content or 
                "[source,java]" in content or 
                "language=\"java\"" in content):
                return LanguageType.JAVA
            
            # Поиск маркеров Python в блоках кода
            elif any(marker in content for marker in [
                "```python", "[source,python]", "```py", "language=\"python\""
            ]):
                return LanguageType.PYTHON
            
            # Поиск маркеров JavaScript в блоках кода
            elif any(marker in content for marker in [
                "```javascript", "[source,javascript]", 
                "```js", "language=\"javascript\""
            ]):
                return LanguageType.JAVASCRIPT
        
        # 4. Анализ ключевых слов в содержимом документации (более точный)
        all_content = " ".join([
            s.get("content", "") for s in doc_structure.get("sections", [])
        ])
        
        # Паттерны для определения Java по ключевым словам
        java_patterns = [
            r'\bpublic\s+class\b', r'\bprivate\s+\w+\b', 
            r'\bstatic\s+void\s+main\b', r'\bimport\s+java\.',
            r'\@Override\b', r'\bString\[\]\s+args\b'
        ]
        if any(re.search(pattern, all_content) for pattern in java_patterns):
            return LanguageType.JAVA
        
        # Паттерны для определения Python по ключевым словам
        python_patterns = [
            r'\bdef\s+\w+\(', r'\bclass\s+\w+:', r'\bimport\s+\w+',
            r'\bfrom\s+\w+\s+import\b', r'__init__\s*\(', r'self\s*\.'
        ]
        if any(re.search(pattern, all_content) for pattern in python_patterns):
            return LanguageType.PYTHON
        
        # Паттерны для определения JavaScript по ключевым словам
        js_patterns = [
            r'\bfunction\s+\w+\(', r'\bconst\s+\w+\s*=', 
            r'\bvar\s+\w+\s*=', r'\blet\s+\w+\s*=',
            r'=>\s*{', r'\bconsole\.log\('
        ]
        if any(re.search(pattern, all_content) for pattern in js_patterns):
            return LanguageType.JAVASCRIPT
        
        # Если ничего не найдено, возвращаем None
        return None

    # Поиск документации по структурному сходству содержимого
    def _find_doc_by_content_similarity(
        self, 
        code_structure: 'CodeStructure', 
        doc_structures: Dict[str, Any], 
        code_language: 'LanguageType'
    ) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        """
        Description:
        ---------------
            Находит документацию по анализу содержимого (имена классов, методов).
            Сравнивает идентификаторы из кода с идентификаторами из документации.

        Args:
        ---------------
            code_structure: Структура анализируемого кода
            doc_structures: Словарь структур доступной документации
            code_language: Язык программирования исходного кода

        Returns:
        ---------------
            Кортеж из пути к наиболее подходящей документации и её структуры,
            или (None, None) если подходящая документация не найдена

        Raises:
        ---------------
            None

        Examples:
        ---------------
            >>> doc_path, doc_struct = self._find_doc_by_content_similarity(
            ...     code_struct, doc_structures, LanguageType.JAVA
            ... )
            >>> print(doc_path)  # "docs/matching_class.md"
        """
        # Извлекаем идентификаторы (имена классов, методов) из кода
        code_identifiers = set()
        
        # Добавляем имена классов из структуры кода
        for cls in code_structure.classes:
            code_identifiers.add(cls.name.lower())
            # Добавляем имена методов каждого класса
            for method in cls.methods:
                code_identifiers.add(method.name.lower())
        
        # Добавляем имена функций верхнего уровня
        for func in code_structure.functions:
            code_identifiers.add(func.name.lower())
        
        print(f"[DEBUG] Идентификаторы из кода: {code_identifiers}")
        
        # Ищем документы с максимальным пересечением идентификаторов
        best_match = None
        best_score = 0
        
        # Перебираем все доступные документы
        for doc_path, doc_structure in doc_structures.items():
            # Проверяем совместимость языков программирования
            doc_language = self._detect_doc_language_from_structure(
                doc_path, doc_structure
            )
            if doc_language and doc_language != code_language:
                continue
            
            # Извлекаем идентификаторы из документации
            doc_identifiers = self._extract_identifiers_from_doc(doc_structure)
            
            # Вычисляем пересечение множеств идентификаторов
            intersection = code_identifiers.intersection(doc_identifiers)
            score = len(intersection)
            
            print(f"[DEBUG] Документ {doc_path}: идентификаторы {doc_identifiers}, "
                f"пересечение {intersection}, счет {score}")
            
            # Обновляем лучшее совпадение если найдено более высокое сходство
            if score > best_score and score > 0:  # Минимум одно совпадение
                best_score = score
                best_match = (doc_path, doc_structure)
        
        return best_match if best_match else (None, None)

    # Извлечение идентификаторов из структуры документации
    def _extract_identifiers_from_doc(self, doc_structure: Dict[str, Any]) -> Set[str]:
        """
        Description:
        ---------------
            Извлекает идентификаторы (имена классов, методов) из структуры документации.
            Анализирует заголовки, секции и блоки кода для поиска идентификаторов.

        Args:
        ---------------
            doc_structure: Словарь со структурой документации

        Returns:
        ---------------
            Множество найденных идентификаторов в нижнем регистре

        Raises:
        ---------------
            None

        Examples:
        ---------------
            >>> identifiers = self._extract_identifiers_from_doc(doc_struct)
            >>> print(identifiers)  # {'myclass', 'mymethod', 'calculate'}
        """
        identifiers = set()
        
        # Извлекаем идентификаторы из заголовка документа
        title = doc_structure.get("meta", {}).get("title", "")
        class_match = re.search(
            r"(?:класса|class|модуля|module)\s+['`\"]?(\w+)['`\"]?", 
            title, 
            re.IGNORECASE
        )
        if class_match:
            identifiers.add(class_match.group(1).lower())
        
        # Извлекаем идентификаторы из секций документации
        for section in doc_structure.get("sections", []):
            section_title = section.get("title", "")
            content = section.get("content", "")
            
            # Поиск методов в заголовках секций
            method_match = re.search(
                r"Метод\s+(\w+)|Method\s+(\w+)|^(\w+)$", 
                section_title, 
                re.IGNORECASE
            )
            if method_match:
                method_name = (method_match.group(1) or 
                            method_match.group(2) or 
                            method_match.group(3))
                # Исключаем служебные слова
                if (method_name and 
                    method_name.lower() not in ['метод', 'method', 'введение', 'introduction']):
                    identifiers.add(method_name.lower())
            
            # Извлечение идентификаторов из блоков кода
            code_blocks = re.findall(r'```\w*\s*(.*?)```', content, re.DOTALL)
            for block in code_blocks:
                # Ищем определения функций и методов
                func_matches = re.findall(
                    r'(?:def|function|public|private|protected)?\s*(\w+)\s*\(', 
                    block
                )
                for match in func_matches:
                    # Исключаем слишком короткие совпадения
                    if len(match) > 2:
                        identifiers.add(match.lower())
                
                # Ищем определения классов в блоках кода
                class_matches = re.findall(r'class\s+(\w+)', block, re.IGNORECASE)
                for match in class_matches:
                    identifiers.add(match.lower())
        
        return identifiers

    def _extract_class_name(self, doc_structure: Dict[str, Any]) -> Optional[str]:
        """
        Description:
        ---------------
            Извлекает имя класса из структуры документации.

        Args:
        ---------------
            doc_structure: Структура документации.

        Returns:
        ---------------
            Optional[str]: Имя класса или None, если не удалось извлечь.
        """
        import re
        
        # Проверяем заголовок документа
        title = doc_structure.get("meta", {}).get("title", "")
        class_match = re.search(r"(?:класса|class|модуля|module)\s+['`\"]?(\w+)['`\"]?", title, re.IGNORECASE)
        if class_match:
            return class_match.group(1)
        
        # Если имя класса не найдено в заголовке, пробуем найти в содержимом
        for section in doc_structure.get("sections", []):
            content = section.get("content", "")
            class_match = re.search(r"(?:класс|class)\s+['`\"]?(\w+)['`\"]?", content, re.IGNORECASE)
            if class_match:
                return class_match.group(1)
            
            # Поиск в блоках кода
            code_block_match = re.search(r"```\w*\s*(?:public\s+)?class\s+(\w+)", content, re.IGNORECASE)
            if code_block_match:
                return code_block_match.group(1)
        
        return None

    def _has_matching_code(self, class_name: str, code_structures: Dict[str, CodeStructure]) -> bool:
        """
        Description:
        ---------------
            Проверяет наличие соответствующего класса в коде проекта.

        Args:
        ---------------
            class_name: Имя класса.
            code_structures: Словарь структур кода.

        Returns:
        ---------------
            bool: True, если класс найден, иначе False.
        """
        for code_structure in code_structures.values():
            for cls in code_structure.classes:
                if cls.name == class_name:
                    return True
        return False
    