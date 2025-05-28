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
import re
from typing import Dict, List, Optional, Any
from pathlib import Path

from app.services.documentation_parser import DocumentationParser
from app.models.code_structure import LanguageType


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

    # Извлекает имя класса из распарсенной документации
    def _extract_class_name(self, parsed_doc: Dict[str, Any]) -> Optional[str]:
        """
        Description:
        ---------------
            Извлекает имя класса из распарсенной документации путём анализа 
            заголовков, содержимого секций и блоков кода.

        Args:
        ---------------
            parsed_doc: Словарь с распарсенной документацией, содержащий 
                       метаданные, секции и содержимое

        Returns:
        ---------------
            Имя класса если найдено, иначе None

        Raises:
        ---------------
            AttributeError: При ошибке доступа к атрибутам словаря
            
        Examples:
        ---------------
            >>> analyzer._extract_class_name({"meta": {"title": "class MyClass"}})
            'MyClass'
        """
        # 1. Проверяем заголовок документа (расширенный паттерн)
        title = parsed_doc.get("meta", {}).get("title", "")
        
        # Улучшенная регулярка с поддержкой "Документация для класса"
        class_patterns = [
            r"(?:Документация\s+для\s+класса|класса|class|модуля|module)"
            r"\s+['`\"]?(\w+)['`\"]?",
            r"Документация\s+для\s+['`\"]?(\w+)['`\"]?",
            r"^\s*(\w+)\s*$"  # Просто имя класса
        ]
        
        # Поиск по всем паттернам в заголовке
        for pattern in class_patterns:
            class_match = re.search(pattern, title, re.IGNORECASE)
            if class_match:
                return class_match.group(1)
        
        # 2. Если имя класса не найдено в заголовке, пробуем найти в 
        # содержимом секций
        for section in parsed_doc.get("sections", []):
            content = section.get("content", "")
            
            # Поиск в тексте секций
            for pattern in class_patterns:
                class_match = re.search(pattern, content, re.IGNORECASE)
                if class_match:
                    return class_match.group(1)
            
            # Поиск в блоках кода
            code_block_patterns = [
                r"```\w*\s*(?:public\s+)?class\s+(\w+)",
                r"class\s+(\w+):",          # Python стиль
                r"def\s+__init__\s*\(self"  # Python конструктор
            ]
            
            # Анализ блоков кода на предмет определения классов
            for pattern in code_block_patterns:
                code_block_match = re.search(pattern, content, re.IGNORECASE)
                if code_block_match:
                    return code_block_match.group(1)
        
        # 3. Fallback: попробовать извлечь из имени файла
        if 'meta' in parsed_doc:
            file_title = parsed_doc['meta'].get('title', '')
            if file_title:
                # Убираем языковые префиксы
                clean_name = self._clean_filename_prefix(file_title)
                # Преобразуем snake_case в PascalCase
                if '_' in clean_name:
                    parts = clean_name.split('_')
                    class_name = ''.join(word.capitalize() for word in parts)
                    return class_name
                else:
                    return clean_name.capitalize()
        
        return None

    # Находит документацию для конкретного файла кода
    def find_doc_for_code_file(self, 
                               code_file_path: str, 
                               class_name: Optional[str] = None) -> Optional[str]:
        """
        Description:
        ---------------
            Находит соответствующую документацию для файла кода, используя 
            имя класса и совместимость языков программирования.

        Args:
        ---------------
            code_file_path: Путь к файлу с кодом
            class_name: Опциональное имя класса для поиска

        Returns:
        ---------------
            Путь к файлу документации если найден, иначе None

        Raises:
        ---------------
            OSError: При ошибке доступа к файловой системе
            
        Examples:
        ---------------
            >>> analyzer.find_doc_for_code_file("/path/to/MyClass.py", "MyClass")
            '/path/to/docs/MyClass.adoc'
        """
        from services.analyzers.analyzer_factory import detect_language_from_file

        # Определяем язык кода
        code_language = detect_language_from_file(code_file_path)
        
        # Если указано имя класса, пробуем найти по нему с учетом языка
        if class_name and class_name in self.class_to_doc_map:
            potential_doc_path = self.class_to_doc_map[class_name]
            doc_structure = self.doc_structures.get(potential_doc_path)
            
            # Проверяем совместимость языков
            if (doc_structure and 
                self._is_doc_language_compatible(code_language, doc_structure)):
                return potential_doc_path
        
        # Поиск по имени файла с учетом языка
        base_name = os.path.splitext(os.path.basename(code_file_path))[0]
        
        # Сначала ищем среди совместимых по языку документов
        compatible_docs = []
        for doc_path, doc_structure in self.doc_structures.items():
            if self._is_doc_language_compatible(code_language, doc_structure):
                doc_base_name = os.path.splitext(
                    os.path.basename(doc_path)
                )[0]
                clean_doc_name = self._clean_filename_prefix(doc_base_name)
                
                # Сравниваем имена файлов без учета регистра
                if clean_doc_name.lower() == base_name.lower():
                    compatible_docs.append(doc_path)
        
        # Если найдены совместимые документы, возвращаем первый
        if compatible_docs:
            return compatible_docs[0]
        
        # Если совместимых не найдено, ищем по старой логике
        for doc_path in self.doc_structures.keys():
            doc_base_name = os.path.splitext(
                os.path.basename(doc_path)
            )[0]
            
            # Проверяем совпадение имен файлов (игнорируя регистр)
            if doc_base_name.lower() == base_name.lower():
                return doc_path
        
        return None

    # Выполняет парсинг всей директории с документацией
    def parse_documentation_directory(self) -> Dict[str, Any]:
        """
        Description:
        ---------------
            Парсит директорию с документацией, обрабатывая все файлы .adoc 
            и .asciidoc, создавая индексы классов и структур документов.

        Args:
        ---------------
            Нет аргументов (использует self.docs_dir_path)

        Returns:
        ---------------
            Словарь структур документов, где ключ - путь к файлу, 
            значение - распарсенная структура

        Raises:
        ---------------
            OSError: При ошибке доступа к файловой системе
            UnicodeDecodeError: При ошибке декодирования файлов
            
        Examples:
        ---------------
            >>> structures = analyzer.parse_documentation_directory()
            >>> len(structures)
            42
        """
        # Рекурсивно проходим по всем файлам в директории документации
        for root, _, files in os.walk(self.docs_dir_path):
            for file in files:
                # Обрабатываем только файлы документации AsciiDoc
                if file.endswith((".adoc", ".asciidoc")):
                    file_path = os.path.join(root, file)
                    try:
                        # Читаем содержимое файла
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Проверяем синтаксис, но НЕ отбрасываем файл 
                        # при ошибках
                        syntax_valid, errors = self.doc_parser.validate_syntax(
                            content
                        )
                        
                        # Парсим документацию независимо от синтаксических ошибок
                        parsed_doc = self.doc_parser.parse(content)
                        
                        # Помечаем документ, если есть синтаксические ошибки
                        if not syntax_valid:
                            parsed_doc['syntax_errors'] = errors
                            print(f"Предупреждение: синтаксические ошибки в "
                                  f"файле {file_path}: {errors}")
                        
                        # Определяем язык документации
                        doc_language = self._detect_doc_language(
                            file_path, 
                            parsed_doc
                        )
                        if doc_language:
                            parsed_doc['detected_language'] = doc_language.value
                        
                        # Сохраняем структуру
                        self.doc_structures[file_path] = parsed_doc
                        
                        # Извлекаем имя класса и создаем индекс
                        class_name = self._extract_class_name(parsed_doc)
                        if class_name:
                            self.class_to_doc_map[class_name] = file_path
                    
                    except Exception as e:
                        print(f"Ошибка при парсинге файла {file_path}: {str(e)}")
                        # Создаем минимальную структуру даже для 
                        # проблемных файлов
                        minimal_doc = {
                            "sections": [],
                            "meta": {
                                "title": os.path.splitext(
                                    os.path.basename(file_path)
                                )[0]
                            },
                            "parse_error": str(e)
                        }
                        self.doc_structures[file_path] = minimal_doc
        
        return self.doc_structures

    # Проверяет совместимость языка кода с языком документации
    def _is_doc_language_compatible(self, 
                                    code_language: Optional[LanguageType], 
                                    doc_structure: Dict[str, Any]) -> bool:
        """
        Description:
        ---------------
            Проверяет совместимость языка программирования кода 
            с языком документации.

        Args:
        ---------------
            code_language: Тип языка программирования кода или None
            doc_structure: Структура документа с метаданными

        Returns:
        ---------------
            True если языки совместимы, иначе False

        Raises:
        ---------------
            ValueError: При некорректном значении языка
            
        Examples:
        ---------------
            >>> analyzer._is_doc_language_compatible(
            ...     LanguageType.PYTHON, 
            ...     {"detected_language": "python"}
            ... )
            True
        """
        # Если язык кода не определен, считаем совместимым
        if not code_language:
            return True
        
        # Получаем язык документации
        doc_language = doc_structure.get('detected_language')
        if isinstance(doc_language, str):
            try:
                doc_language = LanguageType(doc_language)
            except ValueError:
                doc_language = None
        
        # Если язык документации не определен, пытаемся определить его
        if not doc_language:
            doc_language = self._detect_doc_language_from_structure(
                doc_structure
            )
        
        # Если язык документации не определен, считаем совместимым
        if not doc_language:
            return True
        
        return code_language == doc_language

    # Определяет язык программирования из структуры документации
    def _detect_doc_language_from_structure(self, 
                                            doc_structure: Dict[str, Any]
                                            ) -> Optional[LanguageType]:
        """
        Description:
        ---------------
            Определяет язык программирования документации на основе 
            анализа её структуры и содержимого.

        Args:
        ---------------
            doc_structure: Структура документа для анализа

        Returns:
        ---------------
            Определенный тип языка программирования или None

        Raises:
        ---------------
            ValueError: При некорректном значении языка
            
        Examples:
        ---------------
            >>> doc = {"sections": [{"content": "```python\\nprint('hello')"}]}
            >>> analyzer._detect_doc_language_from_structure(doc)
            LanguageType.PYTHON
        """
        # 1. Проверяем уже определенный язык
        detected_lang = doc_structure.get('detected_language')
        if detected_lang:
            try:
                return LanguageType(detected_lang)
            except ValueError:
                pass
        
        # 2. Анализ содержимого блоков кода
        for section in doc_structure.get("sections", []):
            content = section.get("content", "")
            
            # Проверяем маркеры языков в блоках кода
            if ("```java" in content or 
                "[source,java]" in content):
                return LanguageType.JAVA
            elif ("```python" in content or 
                  "[source,python]" in content or 
                  "```py" in content):
                return LanguageType.PYTHON
            elif ("```javascript" in content or 
                  "[source,javascript]" in content or 
                  "```js" in content):
                return LanguageType.JAVASCRIPT
        
        # 3. Анализ ключевых слов в содержимом
        all_content = " ".join([
            s.get("content", "") 
            for s in doc_structure.get("sections", [])
        ])
        
        # Поиск характерных паттернов Java
        if re.search(r'\bpublic\s+class\b|\bprivate\s+\w+\b|'
                     r'\bstatic\s+void\s+main\b', all_content):
            return LanguageType.JAVA
        # Поиск характерных паттернов Python
        elif re.search(r'\bdef\s+\w+\(|\bclass\s+\w+:|import\s+\w+', 
                       all_content):
            return LanguageType.PYTHON
        # Поиск характерных паттернов JavaScript
        elif re.search(r'\bfunction\s+\w+\(|\bconst\s+\w+\s*=|'
                       r'\bvar\s+\w+\s*=', all_content):
            return LanguageType.JAVASCRIPT
        
        return None

    # Удаляет языковые префиксы и постфиксы из имен файлов
    def _clean_filename_prefix(self, filename: str) -> str:
        """
        Description:
        ---------------
            Удаляет языковые префиксы и постфиксы из имени файла 
            для унификации поиска.

        Args:
        ---------------
            filename: Исходное имя файла для очистки

        Returns:
        ---------------
            Очищенное имя файла без префиксов и постфиксов

        Raises:
        ---------------
            AttributeError: При ошибке обработки строки
            
        Examples:
        ---------------
            >>> analyzer._clean_filename_prefix("java_UserController_doc")
            'UserController'
        """
        # Список префиксов для удаления
        prefixes = [
            'java_', 'py_', 'python_', 'js_', 'javascript_', 
            'ts_', 'typescript_', 'cs_', 'csharp_',
            'module_', 'class_', 'api_', 'doc_', 'docs_'
        ]
        
        # Список постфиксов для удаления
        suffixes = [
            '_doc', '_docs', '_documentation', '_api', '_spec'
        ]
        
        filename_lower = filename.lower()
        
        # Удаляем префиксы
        for prefix in prefixes:
            if filename_lower.startswith(prefix):
                filename = filename[len(prefix):]
                filename_lower = filename.lower()
                break
        
        # Удаляем постфиксы
        for suffix in suffixes:
            if filename_lower.endswith(suffix):
                filename = filename[:-len(suffix)]
                break
        
        return filename

    # Определяет язык программирования для документации
    def _detect_doc_language(self, 
                             doc_path: str, 
                             parsed_doc: Dict[str, Any]) -> Optional[LanguageType]:
        """
        Description:
        ---------------
            Определяет язык программирования для документации на основе 
            имени файла, блоков кода и ключевых слов.

        Args:
        ---------------
            doc_path: Путь к файлу документации
            parsed_doc: Распарсенная структура документа

        Returns:
        ---------------
            Определенный тип языка программирования или None

        Raises:
        ---------------
            OSError: При ошибке доступа к файлу
            
        Examples:
        ---------------
            >>> analyzer._detect_doc_language(
            ...     "/docs/python_example.adoc", 
            ...     parsed_doc
            ... )
            LanguageType.PYTHON
        """
        # 1. Анализ префикса имени файла
        filename = os.path.basename(doc_path).lower()
        
        # Проверяем языковые префиксы в имени файла
        if filename.startswith('java_'):
            return LanguageType.JAVA
        elif (filename.startswith('py_') or 
              filename.startswith('python_')):
            return LanguageType.PYTHON
        elif (filename.startswith('js_') or 
              filename.startswith('javascript_')):
            return LanguageType.JAVASCRIPT
        
        # 2. Анализ содержимого блоков кода
        for section in parsed_doc.get("sections", []):
            content = section.get("content", "")
            
            # Поиск языковых маркеров в блоках кода
            if ("```java" in content or 
                "[source,java]" in content):
                return LanguageType.JAVA
            elif ("```python" in content or 
                  "[source,python]" in content or 
                  "```py" in content):
                return LanguageType.PYTHON
            elif ("```javascript" in content or 
                  "[source,javascript]" in content or 
                  "```js" in content):
                return LanguageType.JAVASCRIPT
        
        # 3. Анализ ключевых слов в содержимом
        all_content = " ".join([
            s.get("content", "") 
            for s in parsed_doc.get("sections", [])
        ])
        
        # Поиск характерных синтаксических конструкций
        if re.search(r'\bpublic\s+class\b|\bprivate\s+\w+\b|'
                     r'\bstatic\s+void\s+main\b', all_content):
            return LanguageType.JAVA
        elif re.search(r'\bdef\s+\w+\(|\bclass\s+\w+:|import\s+\w+', 
                       all_content):
            return LanguageType.PYTHON
        elif re.search(r'\bfunction\s+\w+\(|\bconst\s+\w+\s*=|'
                       r'\bvar\s+\w+\s*=', all_content):
            return LanguageType.JAVASCRIPT
        
        return None