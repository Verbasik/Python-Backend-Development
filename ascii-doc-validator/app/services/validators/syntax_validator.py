# app/services/validators/syntax_validator.py
"""
Описание программного модуля:
-----------------------------
Данный модуль содержит класс `SyntaxValidator`, который отвечает за проверку 
синтаксической корректности документации в формате AsciiDoc. Класс выполняет 
проверки на основе набора правил и возвращает список найденных проблем.

Функциональное назначение:
---------------------------
Модуль предназначен для автоматизации процесса проверки синтаксиса AsciiDoc. 
Он позволяет выявлять ошибки в структуре документа, неправильные форматы блоков, 
битые ссылки и другие синтаксические проблемы.
"""

import os
import re
import tempfile
import subprocess
import requests
from typing import List, Dict, Any, Tuple, Set, Optional
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from app.models.validation_report import ValidationIssue, IssueType, IssueLocation


class SyntaxValidator:
    """
    Description:
    ---------------
        Класс для проверки синтаксической корректности AsciiDoc документации.

    Attributes:
    ---------------
        rules: Словарь с правилами проверки синтаксиса.
        temp_dir: Временная директория для создания файлов при валидации.
        checked_urls: Набор уже проверенных URL для кэширования результатов.
    """

    def __init__(self, rules: Optional[Dict[str, Any]] = None):
        """
        Description:
        ---------------
            Инициализирует валидатор синтаксиса.

        Args:
        ---------------
            rules: Правила проверки синтаксиса (опционально).
        """
        self.rules = rules or {}
        self.temp_dir = tempfile.mkdtemp()
        self.checked_urls: Dict[str, bool] = {}  # Кэш для проверенных URL

    def validate(self, content: str, source_path: str) -> List[ValidationIssue]:
        """
        Description:
        ---------------
            Проверяет синтаксическую корректность AsciiDoc документа.

        Args:
        ---------------
            content: Содержимое документации.
            source_path: Путь к исходному файлу документации.

        Returns:
        ---------------
            List[ValidationIssue]: Список найденных проблем.
        """
        issues = []

        # Шаг 1: Проверка базового синтаксиса через asciidoctor
        syntax_issues = self._validate_with_asciidoctor(content, source_path)
        issues.extend(syntax_issues)

        # Шаг 2: Проверка структуры (заголовки, блоки, списки, таблицы)
        structure_issues = self._validate_structure(content, source_path)
        issues.extend(structure_issues)

        # Шаг 3: Проверка ссылок и якорей
        link_issues = self._validate_links(content, source_path)
        issues.extend(link_issues)

        return issues

    def _validate_with_asciidoctor(self, content: str, source_path: str) -> List[ValidationIssue]:
        """
        Description:
        ---------------
            Проверяет синтаксис документа с помощью asciidoctor.

        Args:
        ---------------
            content: Содержимое документации.
            source_path: Путь к исходному файлу документации.

        Returns:
        ---------------
            List[ValidationIssue]: Список найденных проблем.
        """
        issues = []

        # Создаем временный файл для проверки
        with tempfile.NamedTemporaryFile(suffix=".adoc", delete=False, dir=self.temp_dir) as temp_file:
            temp_file_path = temp_file.name
            temp_file.write(content.encode("utf-8"))

        try:
            # Запускаем asciidoctor с опцией проверки синтаксиса (-n)
            result = subprocess.run(
                ["asciidoctor", "-n", "-o", "/dev/null", temp_file_path],
                capture_output=True,
                text=True,
                check=False,
            )

            # Если есть ошибки, обрабатываем их
            if result.returncode != 0:
                # Парсим вывод asciidoctor для извлечения ошибок
                for line in result.stderr.splitlines():
                    # Пример формата ошибки: filename: line X: error message
                    match = re.search(r"line (\d+):(.*)", line)
                    if match:
                        line_num = int(match.group(1))
                        error_msg = match.group(2).strip()
                        
                        # Создаем запись о проблеме
                        issue = ValidationIssue(
                            id=f"SYNTAX-ASCIIDOC-{line_num}",
                            type=IssueType.SYNTAX,
                            location=IssueLocation(
                                line=line_num,
                                section=self._find_section_for_line(content, line_num)
                            ),
                            issue=f"Ошибка синтаксиса AsciiDoc: {error_msg}",
                            original_content=self._get_line_content(content, line_num)
                        )
                        issues.append(issue)
        except FileNotFoundError:
            # Если asciidoctor не установлен, добавляем предупреждение
            issues.append(
                ValidationIssue(
                    id="SYNTAX-ENV-001",
                    type=IssueType.SYNTAX,
                    location=IssueLocation(),
                    issue="Не удалось выполнить проверку с помощью asciidoctor. Убедитесь, что asciidoctor установлен."
                )
            )
        finally:
            # Удаляем временный файл
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

        return issues

    def _validate_structure(self, content: str, source_path: str) -> List[ValidationIssue]:
        """
        Description:
        ---------------
            Проверяет структуру документа (заголовки, блоки, списки, таблицы).

        Args:
        ---------------
            content: Содержимое документации.
            source_path: Путь к исходному файлу документации.

        Returns:
        ---------------
            List[ValidationIssue]: Список найденных проблем.
        """
        issues = []
        lines = content.splitlines()

        # Проверка заголовков
        header_issues = self._validate_headers(lines)
        issues.extend(header_issues)

        # Проверка блоков кода
        code_block_issues = self._validate_code_blocks(lines)
        issues.extend(code_block_issues)

        # Проверка списков
        list_issues = self._validate_lists(lines)
        issues.extend(list_issues)

        # Проверка таблиц
        table_issues = self._validate_tables(lines)
        issues.extend(table_issues)

        return issues

    def _validate_headers(self, lines: List[str]) -> List[ValidationIssue]:
        """
        Description:
        ---------------
            Проверяет корректность заголовков в документе.

        Args:
        ---------------
            lines: Список строк документа.

        Returns:
        ---------------
            List[ValidationIssue]: Список найденных проблем.
        """
        issues = []
        
        # Проверяем уровни заголовков и их порядок
        current_level = 0
        for i, line in enumerate(lines):
            if line.startswith("="):
                # Определяем уровень заголовка
                level_match = re.match(r"^(=+)\s+(.+)$", line)
                if level_match:
                    level = len(level_match.group(1))
                    title = level_match.group(2).strip()
                    
                    # Проверка на пропуск уровня заголовка
                    if level > current_level + 1 and current_level > 0:
                        issues.append(
                            ValidationIssue(
                                id=f"SYNTAX-HEADER-LEVEL-{i+1}",
                                type=IssueType.SYNTAX,
                                location=IssueLocation(line=i+1),
                                issue=f"Заголовок уровня {level} следует за заголовком уровня {current_level}. Пропущен уровень {current_level+1}.",
                                original_content=line
                            )
                        )
                    
                    # Проверка на пустой заголовок
                    if not title:
                        issues.append(
                            ValidationIssue(
                                id=f"SYNTAX-HEADER-EMPTY-{i+1}",
                                type=IssueType.SYNTAX,
                                location=IssueLocation(line=i+1),
                                issue="Заголовок не должен быть пустым.",
                                original_content=line
                            )
                        )
                    
                    current_level = level
                else:
                    # Некорректный формат заголовка
                    issues.append(
                        ValidationIssue(
                            id=f"SYNTAX-HEADER-FORMAT-{i+1}",
                            type=IssueType.SYNTAX,
                            location=IssueLocation(line=i+1),
                            issue="Некорректный формат заголовка. Должен быть '= Заголовок'.",
                            original_content=line
                        )
                    )
        
        return issues

    def _validate_code_blocks(self, lines: List[str]) -> List[ValidationIssue]:
        """
        Description:
        ---------------
            Проверяет корректность блоков кода в документе.

        Args:
        ---------------
            lines: Список строк документа.

        Returns:
        ---------------
            List[ValidationIssue]: Список найденных проблем.
        """
        issues = []
        
        # Проверяем блоки кода на соответствие форматам
        in_block = False
        block_start_line = 0
        block_delimiter = ""
        
        for i, line in enumerate(lines):
            # Проверка начала блока кода
            if (line.startswith("----") or line.startswith("....") or 
                line.startswith("====") or line.startswith("++++") or
                line.startswith("****") or line.startswith("____")):
                if in_block:
                    # Вложенный блок без закрытия предыдущего
                    issues.append(
                        ValidationIssue(
                            id=f"SYNTAX-CODE-BLOCK-NESTED-{i+1}",
                            type=IssueType.SYNTAX,
                            location=IssueLocation(line=i+1),
                            issue=f"Вложенный блок кода без закрытия предыдущего, начатого на строке {block_start_line+1}.",
                            original_content=line
                        )
                    )
                else:
                    in_block = True
                    block_start_line = i
                    block_delimiter = line
            
            # Проверка закрытия блока кода
            elif in_block and line == block_delimiter:
                in_block = False
                block_delimiter = ""
        
        # Проверка на незакрытый блок кода
        if in_block:
            issues.append(
                ValidationIssue(
                    id=f"SYNTAX-CODE-BLOCK-UNCLOSED-{block_start_line+1}",
                    type=IssueType.SYNTAX,
                    location=IssueLocation(line=block_start_line+1),
                    issue="Незакрытый блок кода.",
                    original_content=lines[block_start_line]
                )
            )
        
        return issues

    def _validate_lists(self, lines: List[str]) -> List[ValidationIssue]:
        """
        Description:
        ---------------
            Проверяет корректность списков в документе.

        Args:
        ---------------
            lines: Список строк документа.

        Returns:
        ---------------
            List[ValidationIssue]: Список найденных проблем.
        """
        issues = []
        
        # Проверяем маркированные и нумерованные списки
        in_list = False
        list_type = None  # "ul" для маркированного, "ol" для нумерованного
        list_start_line = 0
        
        for i, line in enumerate(lines):
            stripped_line = line.strip()
            
            # Проверка начала маркированного списка
            if (re.match(r"^\s*[\*\-]\s+\S+", stripped_line) and 
                not in_list):
                in_list = True
                list_type = "ul"
                list_start_line = i
            
            # Проверка начала нумерованного списка
            elif (re.match(r"^\s*\d+\.\s+\S+", stripped_line) and 
                  not in_list):
                in_list = True
                list_type = "ol"
                list_start_line = i
            
            # Проверка смешивания типов списков
            elif in_list and list_type == "ul" and re.match(r"^\s*\d+\.\s+\S+", stripped_line):
                issues.append(
                    ValidationIssue(
                        id=f"SYNTAX-LIST-MIXED-{i+1}",
                        type=IssueType.SYNTAX,
                        location=IssueLocation(line=i+1),
                        issue=f"Смешивание типов списков. Маркированный список начат на строке {list_start_line+1}, а нумерованный на строке {i+1}.",
                        original_content=line
                    )
                )
            elif in_list and list_type == "ol" and re.match(r"^\s*[\*\-]\s+\S+", stripped_line):
                issues.append(
                    ValidationIssue(
                        id=f"SYNTAX-LIST-MIXED-{i+1}",
                        type=IssueType.SYNTAX,
                        location=IssueLocation(line=i+1),
                        issue=f"Смешивание типов списков. Нумерованный список начат на строке {list_start_line+1}, а маркированный на строке {i+1}.",
                        original_content=line
                    )
                )
            
            # Проверка окончания списка (пустая строка)
            elif in_list and not stripped_line:
                in_list = False
                list_type = None
        
        return issues

    def _validate_tables(self, lines: List[str]) -> List[ValidationIssue]:
        """
        Description:
        ---------------
            Проверяет корректность таблиц в документе.

        Args:
        ---------------
            lines: Список строк документа.

        Returns:
        ---------------
            List[ValidationIssue]: Список найденных проблем.
        """
        issues = []
        
        # Проверяем таблицы AsciiDoc
        in_table = False
        table_start_line = 0
        columns_count = 0
        
        for i, line in enumerate(lines):
            # Проверка начала таблицы
            if line.startswith("|===") and not in_table:
                in_table = True
                table_start_line = i
                columns_count = 0
            
            # Проверка строк таблицы
            elif in_table and line.startswith("|"):
                # Подсчет количества ячеек в строке
                cells_count = len(re.findall(r"\|[^|]*", line))
                
                # Если это первая строка с данными, запоминаем количество столбцов
                if columns_count == 0:
                    columns_count = cells_count
                # Иначе проверяем соответствие количества ячеек
                elif cells_count != columns_count:
                    issues.append(
                        ValidationIssue(
                            id=f"SYNTAX-TABLE-COLUMNS-{i+1}",
                            type=IssueType.SYNTAX,
                            location=IssueLocation(line=i+1),
                            issue=f"Несоответствие количества ячеек в строке таблицы. Ожидалось {columns_count}, получено {cells_count}.",
                            original_content=line
                        )
                    )
            
            # Проверка окончания таблицы
            elif line.startswith("|===") and in_table:
                in_table = False
                columns_count = 0
        
        # Проверка на незакрытую таблицу
        if in_table:
            issues.append(
                ValidationIssue(
                    id=f"SYNTAX-TABLE-UNCLOSED-{table_start_line+1}",
                    type=IssueType.SYNTAX,
                    location=IssueLocation(line=table_start_line+1),
                    issue="Незакрытая таблица.",
                    original_content=lines[table_start_line]
                )
            )
        
        return issues

    def _validate_links(self, content: str, source_path: str) -> List[ValidationIssue]:
        """
        Description:
        ---------------
            Проверяет корректность ссылок и якорей в документе.

        Args:
        ---------------
            content: Содержимое документации.
            source_path: Путь к исходному файлу документации.

        Returns:
        ---------------
            List[ValidationIssue]: Список найденных проблем.
        """
        issues = []
        lines = content.splitlines()
        
        # Извлекаем определения якорей (<<anchor_name>>)
        anchors = set()
        internal_links = set()
        external_links = set()
        
        # Регулярные выражения для поиска ссылок
        anchor_pattern = r"\[\[(.+?)\]\]"  # Якорь: [[anchor_name]]
        internal_link_pattern = r"<<(.+?)>>"  # Внутренняя ссылка: <<anchor_name>>
        external_link_pattern = r"(https?://[^\s\[\]]+)"  # Внешняя ссылка: http://example.com

        # Поиск якорей и ссылок в документе
        for i, line in enumerate(lines):
            # Поиск якорей
            for anchor in re.findall(anchor_pattern, line):
                anchors.add(anchor)
            
            # Поиск внутренних ссылок
            for link in re.findall(internal_link_pattern, line):
                # Если ссылка содержит текст, извлекаем только имя якоря
                if "," in link:
                    anchor_name = link.split(",")[0].strip()
                    internal_links.add(anchor_name)
                else:
                    internal_links.add(link)
            
            # Поиск внешних ссылок
            for link in re.findall(external_link_pattern, line):
                external_links.add((link, i))
        
        # Проверка внутренних ссылок на соответствие якорям
        for link in internal_links:
            if link not in anchors:
                # Находим строку с этой ссылкой
                for i, line in enumerate(lines):
                    if f"<<{link}>>" in line:
                        issues.append(
                            ValidationIssue(
                                id=f"SYNTAX-LINK-BROKEN-{i+1}",
                                type=IssueType.SYNTAX,
                                location=IssueLocation(line=i+1),
                                issue=f"Ссылка на несуществующий якорь: '{link}'.",
                                original_content=line
                            )
                        )
                        break
        
        # Проверка внешних ссылок (опционально, может быть отключено)
        if self.rules.get("check_external_links", True):
            for link, line_idx in external_links:
                if not self._check_external_link(link):
                    issues.append(
                        ValidationIssue(
                            id=f"SYNTAX-LINK-EXTERNAL-{line_idx+1}",
                            type=IssueType.SYNTAX,
                            location=IssueLocation(line=line_idx+1),
                            issue=f"Недоступная внешняя ссылка: '{link}'.",
                            original_content=lines[line_idx]
                        )
                    )
        
        return issues

    def _check_external_link(self, url: str) -> bool:
        """
        Description:
        ---------------
            Проверяет доступность внешней ссылки.

        Args:
        ---------------
            url: URL для проверки.

        Returns:
        ---------------
            bool: True, если ссылка доступна, иначе False.
        """
        # Если ссылка уже проверялась, возвращаем кэшированный результат
        if url in self.checked_urls:
            return self.checked_urls[url]
        
        try:
            # Проверяем только головер, чтобы не загружать весь контент
            response = requests.head(url, timeout=5, allow_redirects=True)
            result = response.status_code < 400
            self.checked_urls[url] = result
            return result
        except requests.RequestException:
            self.checked_urls[url] = False
            return False

    def _find_section_for_line(self, content: str, line_num: int) -> Optional[str]:
        """
        Description:
        ---------------
            Находит раздел, в котором находится указанная строка.

        Args:
        ---------------
            content: Содержимое документации.
            line_num: Номер строки.

        Returns:
        ---------------
            Optional[str]: Название раздела или None, если раздел не найден.
        """
        lines = content.splitlines()
        current_section = None
        
        for i, line in enumerate(lines):
            if i + 1 > line_num:
                break
            
            if line.startswith("="):
                # Это заголовок, извлекаем его текст
                current_section = line.lstrip("= ").strip()
        
        return current_section

    def _get_line_content(self, content: str, line_num: int) -> Optional[str]:
        """
        Description:
        ---------------
            Возвращает содержимое указанной строки.

        Args:
        ---------------
            content: Содержимое документации.
            line_num: Номер строки.

        Returns:
        ---------------
            Optional[str]: Содержимое строки или None, если строка не найдена.
        """
        lines = content.splitlines()
        if 0 < line_num <= len(lines):
            return lines[line_num - 1]
        return None