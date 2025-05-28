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
from app.models.validation_report import ValidationIssue, IssueType, ValidationReport

# Импорты сторонних библиотек
from typing import List, Dict, Any


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

    def generate_project_json(self, report: ValidationReport) -> str:
        """
        Description:
        ---------------
            Генерирует JSON-отчет о валидации проекта.

        Args:
        ---------------
            report: Отчет о валидации.

        Returns:
        ---------------
            str: JSON-строка с отчетом.
        """
        # Группируем проблемы по файлам
        issues_by_file = self._group_issues_by_file(report.issues)
        
        # Создаем структуру отчета
        project_report = {
            "validation_id": report.validation_id,
            "project_validation": True,
            "timestamp": report.timestamp.isoformat(),
            "summary": {
                "total_issues": report.summary.total_issues,
                "corrected_issues": report.summary.corrected_issues,
                "skipped_issues": report.summary.skipped_issues,
                "status": report.status,
                "total_files": len(issues_by_file)
            },
            "files": []
        }
        
        # Добавляем информацию о файлах и их проблемах
        for file_info, file_issues in issues_by_file.items():
            file_report = {
                "file_path": file_info,
                "issues_count": len(file_issues),
                "issues": [issue.model_dump() for issue in file_issues]
            }
            project_report["files"].append(file_report)
        
        return json.dumps(project_report, indent=2)

    def generate_project_summary(self, report: ValidationReport) -> Dict[str, Any]:
        """
        Description:
        ---------------
            Генерирует краткую сводку о валидации проекта.

        Args:
        ---------------
            report: Отчет о валидации.

        Returns:
        ---------------
            Dict[str, Any]: Краткая сводка с основной информацией.
        """
        # Группируем проблемы по файлам и типам
        issues_by_file = self._group_issues_by_file(report.issues)
        issues_by_type = self._group_issues_by_type(report.issues)
        
        # Создаем сводку
        summary = {
            "status": report.status,
            "total_issues": report.summary.total_issues,
            "is_valid": report.status in ["VALID", "VALID_WITH_WARNINGS", "FULLY_CORRECTED"],
            "files_with_issues": len(issues_by_file),
            "issues_by_type": {
                issue_type.value: len(issues) for issue_type, issues in issues_by_type.items()
            }
        }
        
        return summary

    def _group_issues_by_file(self, issues: List[ValidationIssue]) -> Dict[str, List[ValidationIssue]]:
        """
        Description:
        ---------------
            Группирует проблемы по файлам.

        Args:
        ---------------
            issues: Список проблем валидации.

        Returns:
        ---------------
            Dict[str, List[ValidationIssue]]: Словарь, где ключ - путь к файлу,
                                         значение - список проблем.
        """
        import re
        
        issues_by_file = {}
        
        for issue in issues:
            # Извлекаем имя файла из описания проблемы
            file_match = re.search(r"\[(.*?)\s*\|\s*(.*?)\]", issue.issue)
            
            if file_match:
                file_info = f"{file_match.group(1)} | {file_match.group(2)}"
                if file_info not in issues_by_file:
                    issues_by_file[file_info] = []
                issues_by_file[file_info].append(issue)
            else:
                # Если формат не соответствует, добавляем в категорию "Общие проблемы"
                if "General" not in issues_by_file:
                    issues_by_file["General"] = []
                issues_by_file["General"].append(issue)
        
        return issues_by_file

    def _group_issues_by_type(self, issues: List[ValidationIssue]) -> Dict[IssueType, List[ValidationIssue]]:
        """
        Description:
        ---------------
            Группирует проблемы по типу.

        Args:
        ---------------
            issues: Список проблем валидации.

        Returns:
        ---------------
            Dict[IssueType, List[ValidationIssue]]: Словарь, где ключ - тип проблемы,
                                                  значение - список проблем.
        """
        issues_by_type = {}
        
        for issue in issues:
            if issue.type not in issues_by_type:
                issues_by_type[issue.type] = []
            issues_by_type[issue.type].append(issue)
        
        return issues_by_type