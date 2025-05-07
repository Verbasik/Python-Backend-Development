# app/services/report_generator.py
"""
Описание программного модуля:
-----------------------------
Данный модуль содержит класс `ReportGenerator`, который отвечает за генерацию 
отчетов о валидации документации. Класс предоставляет методы для создания JSON-отчетов 
и кратких сводок на основе данных из модели `ValidationReport`.

Функциональное назначение:
---------------------------
Модуль предназначен для автоматизации процесса формирования отчетов о валидации. 
Он позволяет преобразовывать данные в удобные для чтения и анализа форматы, такие как JSON, 
а также создавать краткие сводки для быстрого ознакомления с результатами проверки.
"""

# Импорты стандартной библиотеки Python
import json

# Импорты внутренних моделей
from models.validation_report import ValidationReport

# Импорты сторонних библиотек
from typing import Dict, Any


class ReportGenerator:
    """
    Description:
    ---------------
        Класс для генерации отчетов о валидации документации.
    """

    def __init__(self):
        """
        Description:
        ---------------
            Инициализирует генератор отчетов.

        Notes:
        ---------------
            В текущей версии инициализация не требует дополнительных параметров.
        """
        pass

    def generate_json(self, report: ValidationReport) -> str:
        """
        Description:
        ---------------
            Генерирует JSON-отчет о валидации.

        Args:
        ---------------
            report: Отчет о валидации.

        Returns:
        ---------------
            str: JSON-строка с отчетом.
        """
        # Преобразуем Pydantic модель в словарь, затем в JSON
        return json.dumps(report.model_dump(), indent=2)

    def generate_summary(self, report: ValidationReport) -> Dict[str, Any]:
        """
        Description:
        ---------------
            Генерирует краткую сводку на основе отчета.

        Args:
        ---------------
            report: Отчет о валидации.

        Returns:
        ---------------
            Dict[str, Any]: Краткая сводка с основной информацией.
        """
        return {
            "status": report.status,
            "total_issues": report.summary.total_issues,
            "is_valid": report.status
            in ["VALID", "VALID_WITH_WARNINGS", "FULLY_CORRECTED"],
        }