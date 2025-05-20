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
import uuid
from datetime import datetime
from typing import List, Dict, Tuple, Optional, Any

from models.code_structure import CodeStructure
from models.validation_report import (
    ValidationIssue, ValidationReport, ValidationStatus, ValidationSummary, IssueType, IssueLocation
)
from services.source_code_analyzer import SourceCodeAnalyzer
from services.code_documentation_matcher import CodeDocumentationMatcher


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

    def _find_matching_doc(
        self, code_path: str, class_name: Optional[str], doc_structures: Dict[str, Any]
    ) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        """
        Description:
        ---------------
            Находит соответствующую документацию для файла кода.

        Args:
        ---------------
            code_path: Путь к файлу кода.
            class_name: Имя класса.
            doc_structures: Словарь структур документации.

        Returns:
        ---------------
            Tuple[Optional[str], Optional[Dict[str, Any]]]: 
            Путь к файлу документации и структура документации или (None, None), если документация не найдена.
        """
        # Сначала пробуем найти по имени класса
        if class_name:
            for doc_path, doc_structure in doc_structures.items():
                doc_class_name = self._extract_class_name(doc_structure)
                if doc_class_name and doc_class_name == class_name:
                    return doc_path, doc_structure
        
        # Затем пробуем найти по имени файла
        code_base_name = os.path.splitext(os.path.basename(code_path))[0]
        
        for doc_path, doc_structure in doc_structures.items():
            doc_base_name = os.path.splitext(os.path.basename(doc_path))[0]
            
            # Проверяем совпадение имен файлов (игнорируя регистр)
            if doc_base_name.lower() == code_base_name.lower():
                return doc_path, doc_structure
        
        return None, None

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