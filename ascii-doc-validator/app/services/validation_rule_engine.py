# app/services/validation_rule_engine.py
"""
Описание программного модуля:
-----------------------------
Данный модуль содержит класс `ValidationRuleEngine`, который отвечает за выполнение 
валидации документации на основе набора правил. Класс использует модели из модулей 
`validation_report` и `validation_rule` для создания отчетов о валидации.

Функциональное назначение:
---------------------------
Модуль предназначен для автоматизации процесса проверки документации. Он позволяет 
применять правила валидации к распарсенной документации, генерировать отчеты о найденных 
проблемах и их исправлениях, а также определять общий статус валидации.
"""

# Импорты стандартной библиотеки Python
import uuid
from datetime import datetime

# Импорты внутренних моделей
from models.validation_report import (
    ValidationIssue,
    ValidationReport,
    ValidationStatus,
    ValidationSummary,
    IssueType
)  # Модели для отчетов о валидации
from models.validation_rule import ValidationRule
from .validators.syntax_validator import SyntaxValidator

# Импорты сторонних библиотек
from typing import Dict, Any, List, Optional


class ValidationRuleEngine:
    """
    Description:
    ---------------
        Класс для выполнения валидации документации на основе набора правил.

    Args:
    ---------------
        rules: Список правил валидации (опционально).
    """

    def __init__(self, rules: Optional[List[ValidationRule]] = None):
        """
        Description:
        ---------------
            Инициализирует движок валидации.

        Args:
        ---------------
            rules: Список правил валидации (опционально).
        """
        self.rules = rules or []
        self.syntax_validator = SyntaxValidator()

    def set_rules(self, rules: List[ValidationRule]) -> None:
        """
        Description:
        ---------------
            Устанавливает правила валидации.

        Args:
        ---------------
            rules: Список правил валидации.
        """
        self.rules = rules

    def validate(self, parsed_doc: Dict[str, Any], source_path: str) -> ValidationReport:
        """
        Description:
        ---------------
            Валидирует документацию на основе набора правил.

        Args:
        ---------------
            parsed_doc: Распарсенная документация.
            source_path: Путь к исходному файлу документации.

        Returns:
        ---------------
            ValidationReport: Отчет о валидации.
        """
        # Получаем исходный текст документа из parsed_doc, если доступен
        original_content = self._extract_original_content(parsed_doc)
        
        # Выполняем синтаксическую валидацию
        syntax_issues = []
        if original_content:
            syntax_issues = self.syntax_validator.validate(original_content, source_path)
        
        # Выполняем другие типы валидации (в будущих версиях)
        # semantic_issues = self._validate_semantic(parsed_doc, source_path)
        # completeness_issues = self._validate_completeness(parsed_doc, source_path)
        # quality_issues = self._validate_quality(parsed_doc, source_path)
        
        # Объединяем все проблемы
        all_issues = syntax_issues  # + semantic_issues + completeness_issues + quality_issues
        
        # Отделяем исправления от проблем
        issues = []
        corrections = []
        
        for issue in all_issues:
            if issue.corrected_content:
                corrections.append(issue)
            else:
                issues.append(issue)
        
        # Создаем сводные данные
        summary = ValidationSummary(
            total_issues=len(all_issues),
            corrected_issues=len(corrections),
            skipped_issues=0,
        )
        
        # Определяем статус валидации
        if not all_issues:
            status = ValidationStatus.VALID
        elif all(issue.type != IssueType.SYNTAX for issue in issues):
            status = ValidationStatus.VALID_WITH_WARNINGS
        elif len(corrections) == len(all_issues):
            status = ValidationStatus.FULLY_CORRECTED
        elif corrections:
            status = ValidationStatus.PARTIALLY_CORRECTED
        else:
            status = ValidationStatus.INVALID
        
        # Создаем отчет
        report = ValidationReport(
            validation_id=str(uuid.uuid4()),
            documentation_source=source_path,
            timestamp=datetime.now(),
            issues=issues,
            corrections=corrections,
            summary=summary,
            status=status,
        )
        
        return report
    
    def _extract_original_content(self, parsed_doc: Dict[str, Any]) -> Optional[str]:
        """
        Description:
        ---------------
            Извлекает исходный текст документа из parsed_doc.

        Args:
        ---------------
            parsed_doc: Распарсенная документация.

        Returns:
        ---------------
            Optional[str]: Исходный текст документа или None, если не удалось извлечь.
        """
        # Проверяем наличие секций
        if not parsed_doc.get("sections"):
            return None
        
        # Создаем список всех строк
        all_lines = []
        
        # Добавляем заголовок документа, если есть
        if parsed_doc.get("meta", {}).get("title"):
            all_lines.append(f"= {parsed_doc['meta']['title']}")
            all_lines.append("")  # Пустая строка после заголовка
        
        # Добавляем секции
        for section in parsed_doc["sections"]:
            # Добавляем заголовок секции
            level = section.get("level", 1)
            title = section.get("title", "")
            all_lines.append(f"{'=' * level} {title}")
            
            # Добавляем содержимое секции
            if isinstance(section.get("content"), list):
                all_lines.extend(section["content"])
            elif isinstance(section.get("content"), str):
                all_lines.extend(section["content"].splitlines())
        
        # Объединяем все строки в один текст
        return "\n".join(all_lines)