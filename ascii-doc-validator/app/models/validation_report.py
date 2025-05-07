# app/models/validation_report.py
"""
Описание программного модуля:
-----------------------------
Данный модуль содержит набор классов для создания и управления отчетами о валидации документации. 
Классы описывают различные аспекты отчета, такие как типы проблем, их расположение, подробности 
ошибок, сводные данные и общий статус валидации. Модуль использует Pydantic для валидации данных 
и предоставляет строгую типизацию для всех полей.

Функциональное назначение:
---------------------------
Модуль предназначен для автоматизации процесса создания отчетов о проверке документации. 
Он позволяет структурировать информацию о выявленных проблемах, предложенных исправлениях 
и общем результате валидации.
"""

# Импорты стандартной библиотеки Python
from datetime import datetime
from enum import Enum

# Импорты сторонних библиотек
from pydantic import BaseModel, Field, field_serializer
from typing import List, Optional, Dict, Any


# Типы проблем, которые могут быть выявлены при валидации
class IssueType(str, Enum):
    """
    Description:
    ---------------
        Перечисление типов проблем, которые могут быть выявлены при валидации.

    Args:
    ---------------
        SYNTAX: Проблемы, связанные с синтаксисом
        SEMANTIC: Проблемы, связанные с семантикой
        COMPLETENESS: Проблемы, связанные с полнотой данных
        QUALITY: Проблемы, связанные с качеством данных
    """
    SYNTAX       = "SYNTAX"
    SEMANTIC     = "SEMANTIC"
    COMPLETENESS = "COMPLETENESS"
    QUALITY      = "QUALITY"


# Расположение проблемы в документе
class IssueLocation(BaseModel):
    """
    Description:
    ---------------
        Модель для описания расположения проблемы в документе.

    Args:
    ---------------
        line: Номер строки (опционально)
        column: Номер столбца (опционально)
        section: Название раздела документа (опционально)

    Examples:
    ---------------
        >>> location = IssueLocation(line=10, column=5, section="Introduction")
    """
    line: Optional[int] = None
    column: Optional[int] = None
    section: Optional[str] = None


# Подробная информация о проблеме
class ValidationIssue(BaseModel):
    """
    Description:
    ---------------
        Модель для описания конкретной проблемы, выявленной при валидации.

    Args:
    ---------------
        id: Уникальный идентификатор проблемы
        type: Тип проблемы (см. IssueType)
        location: Расположение проблемы (см. IssueLocation)
        issue: Описание проблемы
        original_content: Исходное содержимое (опционально)
        corrected_content: Исправленное содержимое (опционально)
        rule_applied: Правило, которое было применено для исправления (опционально)

    Examples:
    ---------------
        >>> issue = ValidationIssue(
        ...     id="issue_001",
        ...     type=IssueType.SYNTAX,
        ...     location=IssueLocation(line=10),
        ...     issue="Missing closing tag"
        ... )
    """
    id: str
    type: IssueType
    location: IssueLocation
    issue: str
    original_content: Optional[str] = None
    corrected_content: Optional[str] = None
    rule_applied: Optional[str] = None


# Сводные данные о валидации
class ValidationSummary(BaseModel):
    """
    Description:
    ---------------
        Модель для описания сводных данных о результатах валидации.

    Args:
    ---------------
        total_issues: Общее количество выявленных проблем
        corrected_issues: Количество исправленных проблем
        skipped_issues: Количество пропущенных проблем

    Examples:
    ---------------
        >>> summary = ValidationSummary(total_issues=5, corrected_issues=3, skipped_issues=2)
    """
    total_issues: int = 0
    corrected_issues: int = 0
    skipped_issues: int = 0


# Статус валидации
class ValidationStatus(str, Enum):
    """
    Description:
    ---------------
        Перечисление возможных статусов валидации.

    Args:
    ---------------
        VALID: Документация полностью корректна
        VALID_WITH_WARNINGS: Документация корректна, но есть предупреждения
        INVALID: Документация некорректна
        PARTIALLY_CORRECTED: Часть проблем исправлена
        FULLY_CORRECTED: Все проблемы исправлены

    Examples:
    ---------------
        >>> status = ValidationStatus.VALID
    """
    VALID = "VALID"
    VALID_WITH_WARNINGS = "VALID_WITH_WARNINGS"
    INVALID = "INVALID"
    PARTIALLY_CORRECTED = "PARTIALLY_CORRECTED"
    FULLY_CORRECTED = "FULLY_CORRECTED"


# Основной отчет о валидации
class ValidationReport(BaseModel):
    """
    Description:
    ---------------
        Модель для описания полного отчета о валидации документации.

    Args:
    ---------------
        validation_id: Уникальный идентификатор валидации
        documentation_source: Источник документации
        timestamp: Временная метка создания отчета
        issues: Список выявленных проблем (см. ValidationIssue)
        corrections: Список исправленных проблем (см. ValidationIssue)
        summary: Сводные данные о валидации (см. ValidationSummary)
        status: Статус валидации (см. ValidationStatus)

    Examples:
    ---------------
        >>> report = ValidationReport(
        ...     validation_id="validation_001",
        ...     documentation_source="example.docx",
        ...     timestamp=datetime.now(),
        ...     issues=[],
        ...     corrections=[],
        ...     summary=ValidationSummary(),
        ...     status=ValidationStatus.VALID
        ... )
    """
    validation_id: str
    documentation_source: str
    timestamp: datetime
    issues: List[ValidationIssue] = []
    corrections: List[ValidationIssue] = []
    summary: ValidationSummary
    status: ValidationStatus
    
    # Сериализатор для datetime
    @field_serializer('timestamp')
    def serialize_dt(self, dt: datetime, _info):
        return dt.isoformat()