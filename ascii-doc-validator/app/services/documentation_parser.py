# app/services/documentation_parser.py
"""
Описание программного модуля:
-----------------------------
Данный модуль содержит класс `DocumentationParser`, который отвечает за парсинг 
документации в формате AsciiDoc и извлечение структурированных данных. Класс также 
предоставляет метод для проверки синтаксической корректности документации.

Функциональное назначение:
---------------------------
Модуль предназначен для анализа и обработки документации в формате AsciiDoc. Он позволяет 
извлекать заголовки, разделы и метаданные из документа, а также проверять его синтаксис. 
Это упрощает автоматизацию процессов валидации и анализа документации.
"""

import os
import re
import tempfile
from typing import Dict, Any, Optional, Tuple, List
from .validators.syntax_validator import SyntaxValidator


class DocumentationParser:
    """
    Description:
    ---------------
        Класс для парсинга и анализа документации в формате AsciiDoc.

    Examples:
    ---------------
        >>> parser = DocumentationParser()
        >>> content = "= Example Title\n\nThis is a sample document."
        >>> parsed_data = parser.parse(content)
        >>> print(parsed_data["meta"]["title"])
        Example Title
    """

    def __init__(self):
        """
        Description:
        ---------------
            Инициализирует парсер документации.
        """
        self.syntax_validator = SyntaxValidator()

    def parse(self, content: str) -> Dict[str, Any]:
        """
        Description:
        ---------------
            Парсит документацию в формате AsciiDoc и возвращает структурированные данные.

        Args:
        ---------------
            content (str): Содержимое документации в формате AsciiDoc.

        Returns:
        ---------------
            Dict[str, Any]: Структурированные данные, включая разделы и метаданные.
        """
        # Используем asciidoc-py для парсинга
        try:
            # Вызов asciidoc-py через subprocess или нативный интерфейс
            parsed_data = self._parse_asciidoc(content)
        except Exception as e:
            # Если произошла ошибка, используем базовый парсинг
            parsed_data = self._basic_parse(content)
            
        return parsed_data
    
    def _parse_asciidoc(self, content: str) -> Dict[str, Any]:
        """
        Description:
        ---------------
            Парсит AsciiDoc с использованием asciidoc-py.

        Args:
        ---------------
            content: Содержимое документации.

        Returns:
        ---------------
            Dict[str, Any]: Структурированные данные из документации.
        """
        # Создаем временный файл для парсинга
        with tempfile.NamedTemporaryFile(suffix=".adoc", delete=False) as temp_file:
            temp_file_path = temp_file.name
            temp_file.write(content.encode("utf-8"))
        
        try:
            # Создаем структуру результата
            result = {
                "sections": [],
                "meta": {
                    "title": self._extract_title(content),
                    "total_lines": len(content.splitlines()),
                    "document_type": "asciidoc"
                },
                "attributes": self._extract_attributes(content),
                "toc": self._extract_toc(content)
            }
            
            # Добавляем секции
            lines = content.splitlines()
            current_section = None
            
            for i, line in enumerate(lines):
                # Проверка на заголовки в AsciiDoc
                if line.startswith('='):
                    # Определяем уровень заголовка по количеству знаков =
                    level = len(line) - len(line.lstrip('='))
                    title = line.lstrip('= ').strip()
                    
                    section = {
                        "id": f"section-{len(result['sections'])+1}",
                        "title": title,
                        "level": level,
                        "content": [],
                        "line_number": i + 1
                    }
                    
                    result["sections"].append(section)
                    current_section = section
                elif current_section is not None:
                    current_section["content"].append(line)
            
            # Обработка содержимого секций
            for section in result["sections"]:
                content_text = "\n".join(section["content"])
                section["content"] = content_text
                
                # Извлекаем блоки кода, списки, таблицы и другие элементы
                section["blocks"] = self._extract_blocks(content_text)
                section["links"] = self._extract_links(content_text)
            
            return result
        
        finally:
            # Удаляем временный файл
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
    
    def _basic_parse(self, content: str) -> Dict[str, Any]:
        """
        Description:
        ---------------
            Базовый парсинг AsciiDoc без использования сторонних библиотек.

        Args:
        ---------------
            content: Содержимое документации.

        Returns:
        ---------------
            Dict[str, Any]: Структурированные данные из документации.
        """
        # Базовая реализация, как в оригинальной версии
        result = {
            "sections": [],
            "meta": {
                "title": self._extract_title(content),
                "total_lines": len(content.splitlines()),
            }
        }
        
        # Парсим документ
        lines = content.splitlines()
        current_section = None
        
        for i, line in enumerate(lines):
            # Проверка на заголовки в AsciiDoc
            if line.startswith('='):
                # Определяем уровень заголовка по количеству знаков =
                level = len(line) - len(line.lstrip('='))
                title = line.lstrip('= ').strip()
                
                section = {
                    "title": title,
                    "level": level,
                    "content": [],
                    "line_number": i + 1
                }
                
                result["sections"].append(section)
                current_section = section
            elif current_section is not None:
                current_section["content"].append(line)
        
        return result
    
    def _extract_title(self, content: str) -> Optional[str]:
        """
        Description:
        ---------------
            Извлекает заголовок документа.

        Args:
        ---------------
            content: Содержимое документации.

        Returns:
        ---------------
            Optional[str]: Заголовок документа или None, если заголовок не найден.
        """
        lines = content.splitlines()
        for line in lines:
            if line.startswith("= "):
                return line[2:].strip()
        return None
    
    def _extract_attributes(self, content: str) -> Dict[str, str]:
        """
        Description:
        ---------------
            Извлекает атрибуты документа AsciiDoc.

        Args:
        ---------------
            content: Содержимое документации.

        Returns:
        ---------------
            Dict[str, str]: Словарь атрибутов.
        """
        attributes = {}
        pattern = r":([^:]+):\s*(.*)"
        
        for line in content.splitlines():
            match = re.match(pattern, line)
            if match:
                key = match.group(1).strip()
                value = match.group(2).strip()
                attributes[key] = value
        
        return attributes
    
    def _extract_toc(self, content: str) -> List[Dict[str, Any]]:
        """
        Description:
        ---------------
            Извлекает оглавление (TOC) из документа.

        Args:
        ---------------
            content: Содержимое документации.

        Returns:
        ---------------
            List[Dict[str, Any]]: Список элементов оглавления.
        """
        toc = []
        lines = content.splitlines()
        
        for i, line in enumerate(lines):
            if line.startswith('='):
                level = len(line) - len(line.lstrip('='))
                title = line.lstrip('= ').strip()
                
                toc_item = {
                    "level": level,
                    "title": title,
                    "line": i + 1
                }
                toc.append(toc_item)
        
        return toc
    
    def _extract_blocks(self, content: str) -> List[Dict[str, Any]]:
        """
        Description:
        ---------------
            Извлекает блоки кода, примечания и т.д. из текста.

        Args:
        ---------------
            content: Содержимое секции.

        Returns:
        ---------------
            List[Dict[str, Any]]: Список блоков.
        """
        blocks = []
        lines = content.splitlines()
        
        in_block = False
        block_start = -1
        block_type = ""
        block_content = []
        
        for i, line in enumerate(lines):
            # Определение начала блока
            if (line.startswith("----") or line.startswith("....") or 
                line.startswith("====") or line.startswith("++++") or
                line.startswith("****") or line.startswith("____")):
                
                if not in_block:
                    in_block = True
                    block_start = i
                    block_type = line[:4]
                    block_content = []
                elif line == block_type:
                    # Окончание блока
                    blocks.append({
                        "type": self._determine_block_type(block_type, lines[block_start-1] if block_start > 0 else ""),
                        "content": "\n".join(block_content),
                        "start_line": block_start + 1,
                        "end_line": i + 1
                    })
                    in_block = False
                    block_type = ""
                    block_content = []
                else:
                    block_content.append(line)
            elif in_block:
                block_content.append(line)
        
        return blocks
    
    def _determine_block_type(self, delimiter: str, previous_line: str) -> str:
        """
        Description:
        ---------------
            Определяет тип блока по его разделителю и предыдущей строке.

        Args:
        ---------------
            delimiter: Разделитель блока.
            previous_line: Предыдущая строка.

        Returns:
        ---------------
            str: Тип блока.
        """
        if delimiter == "----":
            if previous_line.startswith("[source"):
                return "code"
            return "listing"
        elif delimiter == "....":
            return "literal"
        elif delimiter == "====":
            return "example"
        elif delimiter == "++++":
            return "passthrough"
        elif delimiter == "****":
            return "sidebar"
        elif delimiter == "____":
            return "quote"
        else:
            return "unknown"
    
    def _extract_links(self, content: str) -> List[Dict[str, Any]]:
        """
        Description:
        ---------------
            Извлекает ссылки из текста.

        Args:
        ---------------
            content: Содержимое секции.

        Returns:
        ---------------
            List[Dict[str, Any]]: Список ссылок.
        """
        links = []
        
        # Регулярные выражения для поиска ссылок
        anchor_pattern = r"\[\[(.+?)\]\]"  # Якорь: [[anchor_name]]
        internal_link_pattern = r"<<(.+?)>>"  # Внутренняя ссылка: <<anchor_name>>
        external_link_pattern = r"(https?://[^\s\[\]]+)"  # Внешняя ссылка: http://example.com
        
        # Поиск ссылок в тексте
        for i, line in enumerate(content.splitlines()):
            # Поиск якорей
            for anchor in re.findall(anchor_pattern, line):
                links.append({
                    "type": "anchor",
                    "text": anchor,
                    "line": i + 1
                })
            
            # Поиск внутренних ссылок
            for link in re.findall(internal_link_pattern, line):
                links.append({
                    "type": "internal",
                    "text": link,
                    "line": i + 1
                })
            
            # Поиск внешних ссылок
            for link in re.findall(external_link_pattern, line):
                links.append({
                    "type": "external",
                    "url": link,
                    "line": i + 1
                })
        
        return links

    def validate_syntax(self, content: str) -> Tuple[bool, list]:
        """
        Description:
        ---------------
            Проверяет синтаксическую корректность AsciiDoc документа.

        Args:
        ---------------
            content (str): Содержимое документации.

        Returns:
        ---------------
            Tuple[bool, list]: 
                - bool: True, если документ синтаксически корректен, иначе False.
                - list: Список ошибок, если они есть.
        """
        # Используем SyntaxValidator для проверки документа
        issues = self.syntax_validator.validate(content, "temp_source.adoc")
        
        # Преобразуем issues в простой список строк для обратной совместимости
        error_messages = [issue.issue for issue in issues]
        
        # Возвращаем результат: документ валиден, если нет ошибок
        return len(issues) == 0, error_messages