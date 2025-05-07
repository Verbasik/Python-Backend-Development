# app/models/validation_rule.py
"""
Описание программного модуля:
-----------------------------
Данный модуль содержит классы для определения правил валидации документации. 
Классы описывают различные типы правил, их параметры и конфигурацию. Модуль 
использует Pydantic для валидации данных и предоставляет строгую типизацию 
для всех полей.

Функциональное назначение:
---------------------------
Модуль предназначен для создания и управления правилами валидации документации. 
Он позволяет структурировать информацию о правилах, их типах, важности и 
конфигурации. Это упрощает процесс проверки документации и обеспечивает 
гибкость в настройке правил.
"""

# Импорты стандартной библиотеки Python
from enum import Enum

# Импорты сторонних библиотек
from pydantic import BaseModel
from typing import List, Optional, Dict, Any


# Типы правил валидации
class RuleType(str, Enum):
    """
    Description:
    ---------------
        Перечисление типов правил валидации.

    Args:
    ---------------
        SYNTAX: Правила, связанные с синтаксисом
        SEMANTIC: Правила, связанные с семантикой
        COMPLETENESS: Правила, связанные с полнотой данных
        QUALITY: Правила, связанные с качеством данных

    Examples:
    ---------------
        >>> rule_type = RuleType.SYNTAX
    """
    SYNTAX       = "SYNTAX"
    SEMANTIC     = "SEMANTIC"
    COMPLETENESS = "COMPLETENESS"
    QUALITY      = "QUALITY"


# Модель правила валидации
class ValidationRule(BaseModel):
    """
    Description:
    ---------------
        Модель для описания правила валидации документации.

    Args:
    ---------------
        id: Уникальный идентификатор правила
        name: Название правила
        description: Описание правила
        type: Тип правила (см. RuleType)
        severity: Важность правила ("ERROR", "WARNING", "INFO")
        config: Конфигурация правила (опционально)

    Examples:
    ---------------
        >>> rule = ValidationRule(
        ...     id="rule_001",
        ...     name="Check Syntax",
        ...     description="Ensure proper syntax in documentation",
        ...     type=RuleType.SYNTAX,
        ...     severity="ERROR",
        ...     config={"key": "value"}
        ... )
    """
    id: str
    name: str
    description: str
    type: RuleType
    severity: str
    config: Dict[str, Any] = {}

    class Config:
        """
        Description:
        ---------------
            Конфигурация модели для Pydantic.

        Args:
        ---------------
            arbitrary_types_allowed: Разрешение использования произвольных типов
        """
        arbitrary_types_allowed = True