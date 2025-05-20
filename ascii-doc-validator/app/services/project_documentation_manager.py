# app/services/project_documentation_manager.py
"""
Описание программного модуля:
-----------------------------
Данный модуль содержит класс `ProjectDocumentationManager`, который отвечает за 
управление документацией проекта в формате AsciiDoc. Класс предоставляет методы 
для сканирования директории с документацией, парсинга файлов и создания индекса 
для быстрого поиска.

Функциональное назначение:
---------------------------
Модуль предназначен для работы с множеством файлов документации в формате AsciiDoc, 
их организации и подготовки к сопоставлению с исходным кодом проекта.
"""

import os
from typing import Dict, List, Optional, Any
from pathlib import Path

from services.documentation_parser import DocumentationParser


class ProjectDocumentationManager:
    """
    Description:
    ---------------
        Менеджер документации проекта.

    Attributes:
    ---------------
        docs_dir_path: Путь к директории с документацией.
        doc_parser: Парсер документации.
        doc_structures: Словарь структур документации.

    Methods:
    ---------------
        parse_documentation_directory: Парсит директорию с документацией.
        find_doc_for_code_file: Находит документацию для файла кода.
        get_class_docs: Получает документацию для класса.
    """

    def __init__(self, docs_dir_path: str):
        """
        Description:
        ---------------
            Инициализирует менеджер документации проекта.

        Args:
        ---------------
            docs_dir_path: Путь к директории с документацией.
        """
        self.docs_dir_path = docs_dir_path
        self.doc_parser = DocumentationParser()
        self.doc_structures: Dict[str, Any] = {}
        self.class_to_doc_map: Dict[str, str] = {}  # Карта: имя_класса -> путь_к_файлу_документации

    def parse_documentation_directory(self) -> Dict[str, Any]:
        """
        Description:
        ---------------
            Парсит директорию с документацией.

        Returns:
        ---------------
            Dict[str, Any]: Словарь структур документации.
        """
        for root, _, files in os.walk(self.docs_dir_path):
            for file in files:
                if file.endswith((".adoc", ".asciidoc")):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Проверяем синтаксис
                        syntax_valid, errors = self.doc_parser.validate_syntax(content)
                        if not syntax_valid:
                            print(f"Ошибка синтаксиса в файле {file_path}: {errors}")
                            continue
                        
                        # Парсим документацию
                        parsed_doc = self.doc_parser.parse(content)
                        
                        # Сохраняем структуру
                        self.doc_structures[file_path] = parsed_doc
                        
                        # Извлекаем имя класса и создаем индекс
                        class_name = self._extract_class_name(parsed_doc)
                        if class_name:
                            self.class_to_doc_map[class_name] = file_path
                    
                    except Exception as e:
                        print(f"Ошибка при парсинге файла {file_path}: {str(e)}")
        
        return self.doc_structures

    def find_doc_for_code_file(self, code_file_path: str, class_name: Optional[str] = None) -> Optional[str]:
        """
        Description:
        ---------------
            Находит документацию для файла кода.

        Args:
        ---------------
            code_file_path: Путь к файлу кода.
            class_name: Имя класса (опционально).

        Returns:
        ---------------
            Optional[str]: Путь к файлу документации или None, если документация не найдена.
        """
        # Если указано имя класса, пробуем найти по нему
        if class_name and class_name in self.class_to_doc_map:
            return self.class_to_doc_map[class_name]
        
        # Иначе пробуем найти по имени файла
        base_name = os.path.splitext(os.path.basename(code_file_path))[0]
        
        for doc_path in self.doc_structures.keys():
            doc_base_name = os.path.splitext(os.path.basename(doc_path))[0]
            
            # Проверяем совпадение имен файлов (игнорируя регистр)
            if doc_base_name.lower() == base_name.lower():
                return doc_path
        
        return None

    def get_class_docs(self, class_name: str) -> Optional[Dict[str, Any]]:
        """
        Description:
        ---------------
            Получает документацию для класса.

        Args:
        ---------------
            class_name: Имя класса.

        Returns:
        ---------------
            Optional[Dict[str, Any]]: Структура документации или None, если документация не найдена.
        """
        doc_path = self.class_to_doc_map.get(class_name)
        if doc_path:
            return self.doc_structures.get(doc_path)
        return None

    def _extract_class_name(self, parsed_doc: Dict[str, Any]) -> Optional[str]:
        """
        Description:
        ---------------
            Извлекает имя класса из распарсенной документации.

        Args:
        ---------------
            parsed_doc: Распарсенная документация.

        Returns:
        ---------------
            Optional[str]: Имя класса или None, если не удалось извлечь.
        """
        import re
        
        # Проверяем заголовок документа
        title = parsed_doc.get("meta", {}).get("title", "")
        class_match = re.search(r"(?:класса|class|модуля|module)\s+['`\"]?(\w+)['`\"]?", title, re.IGNORECASE)
        if class_match:
            return class_match.group(1)
        
        # Если имя класса не найдено в заголовке, пробуем найти в содержимом
        for section in parsed_doc.get("sections", []):
            content = section.get("content", "")
            class_match = re.search(r"(?:класс|class)\s+['`\"]?(\w+)['`\"]?", content, re.IGNORECASE)
            if class_match:
                return class_match.group(1)
            
            # Поиск в блоках кода
            code_block_match = re.search(r"```\w*\s*(?:public\s+)?class\s+(\w+)", content, re.IGNORECASE)
            if code_block_match:
                return code_block_match.group(1)
        
        return None