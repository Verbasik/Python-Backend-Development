# app/models/project_structure.py
"""
Описание программного модуля:
-----------------------------
Данный модуль содержит класс `ProjectStructure` для представления структуры проекта,
включая исходный код и документацию.

Функциональное назначение:
---------------------------
Модуль предназначен для создания унифицированного представления структуры проекта,
которое может быть использовано для валидации и сопоставления кода с документацией.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

from app.models.code_structure import CodeStructure


class FileMapping(BaseModel):
    """
    Description:
    ---------------
        Модель сопоставления файлов кода и документации.

    Args:
    ---------------
        code_file: Путь к файлу кода.
        doc_file: Путь к файлу документации (опционально).
        class_name: Имя класса (опционально).
    """
    code_file: str
    doc_file: Optional[str] = None
    class_name: Optional[str] = None


class ProjectStructure(BaseModel):
    """
    Description:
    ---------------
        Модель структуры проекта.

    Args:
    ---------------
        code_dir: Путь к директории с кодом.
        docs_dir: Путь к директории с документацией.
        code_structures: Словарь структур кода.
        doc_structures: Словарь структур документации.
        file_mappings: Список сопоставлений файлов.
    """
    code_dir: str
    docs_dir: str
    code_structures: Dict[str, CodeStructure] = Field(default_factory=dict)
    doc_structures: Dict[str, Any] = Field(default_factory=dict)
    file_mappings: List[FileMapping] = Field(default_factory=list)

    def add_code_structure(self, file_path: str, structure: CodeStructure) -> None:
        """
        Description:
        ---------------
            Добавляет структуру кода.

        Args:
        ---------------
            file_path: Путь к файлу кода.
            structure: Структура кода.
        """
        self.code_structures[file_path] = structure

    def add_doc_structure(self, file_path: str, structure: Dict[str, Any]) -> None:
        """
        Description:
        ---------------
            Добавляет структуру документации.

        Args:
        ---------------
            file_path: Путь к файлу документации.
            structure: Структура документации.
        """
        self.doc_structures[file_path] = structure

    def add_file_mapping(self, code_file: str, doc_file: Optional[str], class_name: Optional[str] = None) -> None:
        """
        Description:
        ---------------
            Добавляет сопоставление файлов.

        Args:
        ---------------
            code_file: Путь к файлу кода.
            doc_file: Путь к файлу документации (опционально).
            class_name: Имя класса (опционально).
        """
        self.file_mappings.append(FileMapping(
            code_file=code_file,
            doc_file=doc_file,
            class_name=class_name
        ))

    def to_dict(self) -> Dict[str, Any]:
        """
        Description:
        ---------------
            Преобразует структуру проекта в словарь.

        Returns:
        ---------------
            Dict[str, Any]: Структура проекта в виде словаря.
        """
        return self.model_dump()

    def to_json(self) -> str:
        """
        Description:
        ---------------
            Преобразует структуру проекта в JSON-строку.

        Returns:
        ---------------
            str: Структура проекта в виде JSON-строки.
        """
        import json
        return json.dumps(self.to_dict(), indent=2)