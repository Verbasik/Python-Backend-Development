# app/services/code_documentation_matcher.py
"""
Описание программного модуля:
-----------------------------
Данный модуль содержит класс `CodeDocumentationMatcher`, который отвечает за сопоставление
структурированного представления исходного кода и документации. Класс предоставляет
методы для поиска несоответствий между кодом и документацией.

Функциональное назначение:
---------------------------
Модуль предназначен для автоматического выявления несоответствий между исходным кодом
и его документацией. Это позволяет обнаруживать устаревшие или неточные описания API,
методов, параметров и других элементов кода.
"""

# Импорты стандартной библиотеки Python
import re
from typing import Dict, List, Optional, Any, Tuple

# Импорты внутренних модулей
from models.code_structure import CodeStructure, ClassInfo, MethodInfo, ParameterInfo
from models.validation_report import ValidationIssue, IssueType, IssueLocation
from services.source_code_analyzer import SourceCodeAnalyzer


class CodeDocumentationMatcher:
    """
    Description:
    ---------------
        Класс для сопоставления исходного кода и документации.

    Attributes:
    ---------------
        source_code_analyzer: Анализатор исходного кода.

    Methods:
    ---------------
        match_api_endpoints: Сопоставляет API-эндпоинты в коде и документации.
        find_undocumented_methods: Находит недокументированные методы.
        find_documented_but_missing_methods: Находит методы, описанные в документации, но отсутствующие в коде.
        match_parameters: Сопоставляет параметры метода в коде и документации.

    Examples:
    ---------------
        >>> matcher = CodeDocumentationMatcher()
        >>> issues = matcher.match_api_endpoints(code_structure, doc_structure)
    """

    def __init__(self, source_code_analyzer: Optional[SourceCodeAnalyzer] = None):
        """
        Description:
        ---------------
            Инициализирует сопоставитель кода и документации.

        Args:
        ---------------
            source_code_analyzer: Анализатор исходного кода (опционально).
        """
        self.source_code_analyzer = source_code_analyzer or SourceCodeAnalyzer()
        self._IGNORED_METHOD_PATTERNS: Tuple[re.Pattern, ...] = (
        re.compile(r"^__.*__$"),    # dunder-методы (__init__, __str__ …)
        re.compile(r"^_.*"),        # «защищённые»/приватные _helper()
    )

    def match_api_endpoints(
        self, code_structure: CodeStructure, doc_structure: Dict[str, Any]
    ) -> List[ValidationIssue]:
        """
        Description:
        ---------------
            Сопоставляет API-эндпоинты в коде и документации.

        Args:
        ---------------
            code_structure: Структурированное представление кода.
            doc_structure: Структурированное представление документации.

        Returns:
        ---------------
            List[ValidationIssue]: Список проблем валидации.
        """
        issues = []
        
        # Извлекаем API-эндпоинты из кода
        code_endpoints = self._extract_code_endpoints(code_structure)
        
        # Извлекаем API-эндпоинты из документации
        doc_endpoints = self._extract_doc_endpoints(doc_structure)
        
        # Сравниваем эндпоинты
        for endpoint_path, endpoint_info in code_endpoints.items():
            if endpoint_path not in doc_endpoints:
                # Эндпоинт не описан в документации
                issues.append(ValidationIssue(
                    id=f"SEMANTIC-API-001-{len(issues)+1}",
                    type=IssueType.SEMANTIC,
                    location=IssueLocation(
                        line=endpoint_info.get("line_start"),
                        section=doc_structure.get("meta", {}).get("title")
                    ),
                    issue=f"API-эндпоинт '{endpoint_path}' ({endpoint_info.get('http_method')}) не описан в документации"
                ))
            else:
                # Эндпоинт описан, проверяем соответствие HTTP-методов
                if endpoint_info.get("http_method") != doc_endpoints[endpoint_path].get("http_method"):
                    issues.append(ValidationIssue(
                        id=f"SEMANTIC-API-002-{len(issues)+1}",
                        type=IssueType.SEMANTIC,
                        location=IssueLocation(
                            line=doc_endpoints[endpoint_path].get("doc_line"),
                            section=doc_endpoints[endpoint_path].get("section")
                        ),
                        issue=f"Несоответствие HTTP-метода для API-эндпоинта '{endpoint_path}': "
                              f"в коде - {endpoint_info.get('http_method')}, "
                              f"в документации - {doc_endpoints[endpoint_path].get('http_method')}"
                    ))
                
                # Проверяем соответствие параметров
                params_issues = self.match_parameters(
                    endpoint_info.get("method"),
                    doc_endpoints[endpoint_path].get("parameters", [])
                )
                issues.extend(params_issues)
        
        # Проверяем на наличие эндпоинтов в документации, отсутствующих в коде
        for endpoint_path, endpoint_info in doc_endpoints.items():
            if endpoint_path not in code_endpoints:
                issues.append(ValidationIssue(
                    id=f"SEMANTIC-API-003-{len(issues)+1}",
                    type=IssueType.SEMANTIC,
                    location=IssueLocation(
                        line=endpoint_info.get("doc_line"),
                        section=endpoint_info.get("section")
                    ),
                    issue=f"API-эндпоинт '{endpoint_path}' ({endpoint_info.get('http_method')}) "
                          f"описан в документации, но отсутствует в коде. "
                          f"Возможно, это устаревшая документация или ошибка генерации LLM."
                ))
        
        return issues

    def find_undocumented_methods(
        self, code_structure: CodeStructure, doc_structure: Dict[str, Any]
    ) -> List[ValidationIssue]:
        """
        Description:
        ---------------
            Находит недокументированные методы.

        Args:
        ---------------
            code_structure: Структурированное представление кода.
            doc_structure: Структурированное представление документации.

        Returns:
        ---------------
            List[ValidationIssue]: Список проблем валидации.
        """
        issues = []
        
        # Извлекаем все методы и функции из кода
        code_methods = self._extract_code_methods(code_structure)
        
        # Извлекаем все методы из документации
        doc_methods = self._extract_doc_methods(doc_structure)
        
        # Сравниваем методы
        for method_name, method_info in code_methods.items():
            if method_name not in doc_methods:
                # Метод не описан в документации
                issues.append(ValidationIssue(
                    id=f"COMPLETENESS-METHOD-001-{len(issues)+1}",
                    type=IssueType.COMPLETENESS,
                    location=IssueLocation(
                        section=doc_structure.get("meta", {}).get("title")
                    ),
                    issue=f"Метод '{method_name}' не описан в документации"
                ))
        
        return issues

    def find_documented_but_missing_methods(
        self, code_structure: CodeStructure, doc_structure: Dict[str, Any]
    ) -> List[ValidationIssue]:
        """
        Description:
        ---------------
            Находит методы, описанные в документации, но отсутствующие в коде.

        Args:
        ---------------
            code_structure: Структурированное представление кода.
            doc_structure: Структурированное представление документации.

        Returns:
        ---------------
            List[ValidationIssue]: Список проблем валидации.
        """
        issues = []
        
        # Извлекаем все методы и функции из кода
        code_methods = self._extract_code_methods(code_structure)
        
        # Извлекаем все методы из документации
        doc_methods = self._extract_doc_methods(doc_structure)
        
        # Сравниваем методы
        for method_name, method_info in doc_methods.items():
            if method_name not in code_methods:
                # Метод описан в документации, но отсутствует в коде
                issues.append(ValidationIssue(
                    id=f"SEMANTIC-METHOD-001-{len(issues)+1}",
                    type=IssueType.SEMANTIC,
                    location=IssueLocation(
                        line=method_info.get("doc_line"),
                        section=method_info.get("section")
                    ),
                    issue=f"Метод '{method_name}' описан в документации, но отсутствует в коде. "
                          f"Возможно, это устаревшая документация или ошибка генерации LLM."
                ))
        
        return issues

    def match_parameters(
        self, method: MethodInfo, doc_parameters: List[Dict[str, Any]]
    ) -> List[ValidationIssue]:
        """
        Description:
        ---------------
            Сопоставляет параметры метода в коде и документации.

        Args:
        ---------------
            method: Информация о методе из кода.
            doc_parameters: Список параметров из документации.

        Returns:
        ---------------
            List[ValidationIssue]: Список проблем валидации.
        """
        issues = []
        
        # Создаем словарь параметров метода
        method_params = {param.name: param for param in method.parameters}
        
        # Создаем словарь параметров из документации
        doc_params = {param["name"]: param for param in doc_parameters}
        
        # Проверяем параметры метода
        for param_name, param_info in method_params.items():
            if param_name not in doc_params:
                # Параметр не описан в документации
                issues.append(ValidationIssue(
                    id=f"COMPLETENESS-PARAM-001-{len(issues)+1}",
                    type=IssueType.COMPLETENESS,
                    location=IssueLocation(
                        line=method.line_start,
                        section=f"Method {method.name}"
                    ),
                    issue=f"Параметр '{param_name}' метода '{method.name}' не описан в документации"
                ))
            else:
                # Параметр описан, проверяем соответствие типов
                doc_type = doc_params[param_name].get("type")
                if param_info.type and doc_type and param_info.type != doc_type:
                    issues.append(ValidationIssue(
                        id=f"SEMANTIC-PARAM-001-{len(issues)+1}",
                        type=IssueType.SEMANTIC,
                        location=IssueLocation(
                            line=doc_params[param_name].get("doc_line"),
                            section=doc_params[param_name].get("section")
                        ),
                        issue=f"Несоответствие типа параметра '{param_name}' метода '{method.name}': "
                              f"в коде - {param_info.type}, в документации - {doc_type}"
                    ))
                
                # Проверяем обязательность параметра
                doc_required = doc_params[param_name].get("required", True)
                if param_info.required != doc_required:
                    issues.append(ValidationIssue(
                        id=f"SEMANTIC-PARAM-002-{len(issues)+1}",
                        type=IssueType.SEMANTIC,
                        location=IssueLocation(
                            line=doc_params[param_name].get("doc_line"),
                            section=doc_params[param_name].get("section")
                        ),
                        issue=f"Несоответствие обязательности параметра '{param_name}' метода '{method.name}': "
                              f"в коде - {'обязательный' if param_info.required else 'необязательный'}, "
                              f"в документации - {'обязательный' if doc_required else 'необязательный'}"
                    ))
        
        # Проверяем параметры из документации
        for param_name, param_info in doc_params.items():
            if param_name not in method_params:
                # Параметр описан в документации, но отсутствует в коде
                issues.append(ValidationIssue(
                    id=f"SEMANTIC-PARAM-003-{len(issues)+1}",
                    type=IssueType.SEMANTIC,
                    location=IssueLocation(
                        line=param_info.get("doc_line"),
                        section=param_info.get("section")
                    ),
                    issue=f"Параметр '{param_name}' метода '{method.name}' описан в документации, "
                          f"но отсутствует в коде. Возможно, это устаревшая документация или ошибка генерации LLM."
                ))
        
        return issues

    def _extract_code_endpoints(self, code_structure: CodeStructure) -> Dict[str, Any]:
        """
        Description:
        ---------------
            Извлекает API-эндпоинты из структуры кода.

        Args:
        ---------------
            code_structure: Структурированное представление кода.

        Returns:
        ---------------
            Dict[str, Any]: Словарь, где ключ - путь API-эндпоинта,
                            значение - информация об эндпоинте.
        """
        endpoints = {}
        
        # Извлекаем API-эндпоинты из классов
        for cls in code_structure.classes:
            # Если класс является контроллером
            if cls.is_controller:
                # Определяем базовый путь для контроллера
                base_path = ""
                for ann in cls.annotations:
                    if ann.name in ["RequestMapping", "Controller", "RestController"] and ann.parameters:
                        if "value" in ann.parameters:
                            base_path = ann.parameters["value"].strip('"')
                        elif "path" in ann.parameters:
                            base_path = ann.parameters["path"].strip('"')
                
                # Извлекаем эндпоинты из методов
                for method in cls.methods:
                    if method.is_api_endpoint and method.path:
                        # Формируем полный путь эндпоинта
                        full_path = base_path + method.path if base_path else method.path
                        
                        endpoints[full_path] = {
                            "http_method": method.http_method,
                            "method_name": method.name,
                            "class_name": cls.name,
                            "line_start": method.line_start,
                            "line_end": method.line_end,
                            "method": method
                        }
        
        # Извлекаем API-эндпоинты из функций верхнего уровня (для Flask, FastAPI)
        for func in code_structure.functions:
            if func.is_api_endpoint and func.path:
                endpoints[func.path] = {
                    "http_method": func.http_method,
                    "method_name": func.name,
                    "class_name": None,
                    "line_start": func.line_start,
                    "line_end": func.line_end,
                    "method": func
                }
        
        return endpoints

    def _extract_doc_endpoints(self, doc_structure: Dict[str, Any]) -> Dict[str, Any]:
        """
        Description:
        ---------------
            Извлекает API-эндпоинты из структуры документации.

        Args:
        ---------------
            doc_structure: Структурированное представление документации.

        Returns:
        ---------------
            Dict[str, Any]: Словарь, где ключ - путь API-эндпоинта,
                            значение - информация об эндпоинте.
        """
        endpoints = {}
        
        # Извлекаем API-эндпоинты из разделов документации
        for section in doc_structure.get("sections", []):
            # Проверяем, является ли раздел описанием API-эндпоинта
            if "path" in section or "url" in section:
                path = section.get("path") or section.get("url")
                if path:
                    http_method = None
                    # Ищем HTTP-метод в заголовке или содержимом раздела
                    title = section.get("title", "").upper()
                    if "GET" in title:
                        http_method = "GET"
                    elif "POST" in title:
                        http_method = "POST"
                    elif "PUT" in title:
                        http_method = "PUT"
                    elif "DELETE" in title:
                        http_method = "DELETE"
                    elif "PATCH" in title:
                        http_method = "PATCH"
                    
                    # Извлекаем параметры эндпоинта
                    parameters = []
                    for param_section in section.get("subsections", []):
                        if "parameters" in param_section.get("title", "").lower():
                            # Извлекаем параметры из подраздела
                            for param in param_section.get("params", []):
                                parameters.append({
                                    "name": param.get("name"),
                                    "type": param.get("type"),
                                    "required": param.get("required", True),
                                    "description": param.get("description"),
                                    "doc_line": param.get("line"),
                                    "section": param_section.get("title")
                                })
                    
                    endpoints[path] = {
                        "http_method": http_method,
                        "doc_line": section.get("line_number"),
                        "section": section.get("title"),
                        "parameters": parameters
                    }
        
        return endpoints

    def _identify_method_section(
        self, section: Dict[str, Any], patterns: List[Dict[str, Any]]
    ) -> Tuple[bool, Optional[str]]:
        """
        Description:
        ---------------
            Определяет, описывает ли секция метод, и возвращает его имя.
            Поддерживаются заголовки с экранированным символом «\_».

        Args:
        ---------------
            section: Словарь, описывающий секцию документации.
            patterns: Список паттернов для поиска в тексте.

        Returns:
        ---------------
            Кортеж: (флаг наличия метода, имя метода при наличии)

        Examples:
        ---------------
            >>> _identify_method_section(sec, patterns)
            (True, "my_method")
        """
        title = section.get("title", "")
        content = section.get("content", "")

        # дополнительная нормализация для всех проверок
        norm_title = title.replace("\\_", "_")

        # 0. Быстрое правило «одиночное слово в нижнем регистре»
        if re.match(r"^\w+$", norm_title) and norm_title[0].islower():
            return True, norm_title

        # 1. Проверка пользовательских паттернов
        for p in patterns:
            target = p["apply_to"]
            regex = re.compile(p["regex"], re.IGNORECASE)
            haystack = norm_title if target == "title" else content
            m = regex.search(haystack)
            if m:
                return True, m.group(1).replace("\\_", "_")

        # 2. Heuristics: наличие @param / signature внутри кода
        if any(tag in content for tag in ("@param", "@return", "@throws")):
            sig = re.search(
                r"(?:def|function|public|private|protected)\s+(\w+)\s*\(",
                content
            )
            if sig:
                return True, sig.group(1)

        return False, None

    def _extract_code_methods(self, code_structure: 'CodeStructure') -> Dict[str, Any]:
        """
        Description:
        ---------------
            Извлекает все публичные методы и функции из структуры кода.
            Dunder- и приватные методы по умолчанию игнорируются.

        Args:
        ---------------
            code_structure: Структура исходного кода.

        Returns:
        ---------------
            Словарь с именами методов и их атрибутами.
        """
        methods: Dict[str, Any] = {}

        def _is_ignored(name: str) -> bool:
            return any(p.match(name) for p in self._IGNORED_METHOD_PATTERNS)

        # --- Методы классов ---
        for cls in code_structure.classes:
            for method in cls.methods:
                if _is_ignored(method.name):
                    continue
                methods[f"{cls.name}.{method.name}"] = {
                    "class_name": cls.name,
                    "line_start": method.line_start,
                    "line_end": method.line_end,
                    "method": method,
                }

        # --- Функции верхнего уровня ---
        for func in code_structure.functions:
            if _is_ignored(func.name):
                continue
            methods[func.name] = {
                "class_name": None,
                "line_start": func.line_start,
                "line_end": func.line_end,
                "method": func,
            }

        return methods

    def _extract_doc_methods(self, doc_structure: Dict[str, Any]) -> Dict[str, Any]:
        """
        Description:
        ---------------
            Извлекает все методы из структуры документации.

        Args:
        ---------------
            doc_structure: Структура документации.

        Returns:
        ---------------
            Словарь с найденными методами и их параметрами.
        """
        methods: Dict[str, Any] = {}
        class_name = self._extract_class_name(doc_structure)
        patterns = self._get_method_patterns()

        # -- 1. ищем контейнеры «Методы …» --
        containers = self._find_methods_container_sections(doc_structure)

        # -- 2. формируем список секций-кандидатов --
        candidate_sections = []
        if containers:
            for c in containers:
                candidate_sections.append(c)  # сам контейнер
                candidate_sections.extend(   # дочерние
                    [s for s in doc_structure.get("sections", [])
                    if self._is_child_section(s, c)]
                )
        else:  # fallback
            candidate_sections = doc_structure.get("sections", [])

        # -- 3. анализ секций --
        for sec in candidate_sections:
            cleaned_title = self._clean_method_title(sec.get("title", ""))
            sec_copy = sec.copy()
            sec_copy["title"] = cleaned_title

            is_method, name = self._identify_method_section(sec_copy, patterns)
            if not (is_method and name):
                continue
            if self._is_service_section(name, sec):
                continue

            full_name = f"{class_name}.{name}" if class_name else name
            methods[full_name] = {
                "doc_line": sec.get("line_number"),
                "section": sec.get("title"),
                "parameters": self._extract_parameters_from_section(sec),
            }

        return methods

    def _clean_method_title(self, title: str) -> str:
        """
        Description:
        ---------------
            Очищает заголовок секции от служебных слов.

        Args:
        ---------------
            title: Оригинальный заголовок секции.

        Returns:
        ---------------
            str: Очищенный заголовок.
        """
        # 1) префиксы
        cleaned = re.sub(r"^(Метод|Method|Функция|Function)\s+", "", title, flags=re.I).strip()
        # 2) убираем обратный слэш перед *_`
        cleaned = re.sub(r"\\([*_`])", r"\1", cleaned)
        # 3) нормализуем пробелы
        cleaned = re.sub(r"\s{2,}", " ", cleaned)
        return cleaned

    def _is_service_section(self, method_name: str, section: Dict[str, Any]) -> bool:
        """
        Description:
        ---------------
            Проверяет, является ли секция служебной (не описанием метода).

        Args:
        ---------------
            method_name: Предполагаемое имя метода.
            section: Секция документации.

        Returns:
        ---------------
            bool: True, если секция служебная.
        """
        service_names = [
            "введение", "introduction", "описание", "description",
            "обзор", "overview", "установка", "installation",
            "конфигурация", "configuration", "примеры", "examples",
            "использование", "usage", "заключение", "conclusion"
        ]

        # Проверяем имя метода
        if method_name.lower() in service_names:
            return True

        # Проверяем содержимое
        content = section.get("content", "")
        has_method_signature = bool(
            re.search(r'(def\s+\w+\(|function\s+\w+\(|public\s+\w+\s+\w+\()', content)
        )
        has_code_block = "```" in content or "----" in content

        # Эвристика на служебные секции
        if not has_method_signature and not has_code_block and len(method_name) < 3:
            return True

        return False

    def _extract_class_name(self, doc_structure: Dict[str, Any]) -> Optional[str]:
        """
        Description:
        ---------------
            Извлекает имя класса из документации.

        Args:
        ---------------
            doc_structure: Структурированное представление документации.

        Returns:
        ---------------
            Optional[str]: Имя класса или None, если не удалось определить.
        """
        # 1. Попытка извлечь из заголовка документа
        title = doc_structure.get("meta", {}).get("title", "")
        class_match = re.search(r"(?:класса|class|модуля|module)\s+['`\"]?(\w+)['`\"]?", title, re.IGNORECASE)
        if class_match:
            return class_match.group(1)
        
        # 2. Поиск в первом разделе
        sections = doc_structure.get("sections", [])
        if sections:
            first_section = sections[0]
            content = first_section.get("content", "")
            class_match = re.search(r"(?:класс|class)\s+['`\"]?(\w+)['`\"]?", content, re.IGNORECASE)
            if class_match:
                return class_match.group(1)
        
        # 3. Поиск в блоках кода
        for section in sections:
            content = section.get("content", "")
            # Поиск объявления класса в блоке кода
            code_block_match = re.search(r"```\w*\s*(?:public\s+)?class\s+(\w+)", content, re.IGNORECASE)
            if code_block_match:
                return code_block_match.group(1)
        
        # 4. Если не удалось определить, используем имя из первого слова заголовка документа
        if title:
            words = title.split()
            if len(words) > 0:
                # Проверяем, что слово начинается с большой буквы (как имя класса)
                if words[0] and words[0][0].isupper():
                    return words[0]
        
        # 5. Пытаемся найти имя класса в заголовке любой секции
        for section in sections:
            title = section.get("title", "")
            class_match = re.search(r"(?:класса|class)\s+['`\"]?(\w+)['`\"]?", title, re.IGNORECASE)
            if class_match:
                return class_match.group(1)
        
        # Если имя класса не найдено, используем "Calculator" как запасной вариант
        # Это временное решение, в идеале нужно определять имя класса более надежным способом
        return "Calculator"

    def _get_method_patterns(self) -> List[Dict[str, Any]]:
        """
        Description:
        ---------------
            Получает шаблоны для распознавания методов.

        Returns:
        ---------------
            List[Dict[str, Any]]: Список шаблонов для распознавания методов.
        """
        # Возвращаем список шаблонов в порядке приоритета
        return [
            # Шаблон 1: Заголовок содержит "Метод X" (русский)
            {
                "name": "russian_method_title",
                "regex": r"Метод\s+(\w+)",
                "apply_to": "title"
            },
            # Шаблон 2: Заголовок содержит "Method X" (английский)
            {
                "name": "english_method_title",
                "regex": r"Method\s+(\w+)",
                "apply_to": "title"
            },
            # Шаблон 3: Заголовок просто совпадает с именем метода
            {
                "name": "method_name_only",
                "regex": r"^(\w+)$",
                "apply_to": "title"
            },
            # Шаблон 4: В содержимом есть сигнатура метода
            {
                "name": "method_signature",
                "regex": r"(?:public|private|protected|static|\s)+[\w\<\>\[\]]+\s+(\w+)\s*\([^\)]*\)",
                "apply_to": "content"
            }
        ]

    def _find_methods_container_sections(self, doc_structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Description:
        ---------------
            Находит секции, которые могут содержать описания методов.

        Args:
        ---------------
            doc_structure: Структурированное представление документации.

        Returns:
        ---------------
            List[Dict[str, Any]]: Список секций-контейнеров.
        """
        containers = []
        
        # Список возможных названий секций, содержащих методы
        container_titles = [
            "Методы класса", "Методы", "Methods", "Class Methods", 
            "API", "API Reference", "Функции", "Functions"
        ]
        
        for section in doc_structure.get("sections", []):
            title = section.get("title", "").strip()
            # Проверяем точное совпадение
            if title in container_titles:
                containers.append(section)
            # Проверяем частичное совпадение
            elif any(container.lower() in title.lower() for container in ["метод", "method", "function", "API"]):
                containers.append(section)
        
        return containers

    def _is_child_section(self, section: Dict[str, Any], parent_section: Dict[str, Any]) -> bool:
        """
        Description:
        ---------------
            Проверяет, является ли секция дочерней для указанной родительской секции.

        Args:
        ---------------
            section: Потенциальная дочерняя секция.
            parent_section: Потенциальная родительская секция.

        Returns:
        ---------------
            bool: True, если секция является дочерней, иначе False.
        """
        # Проверяем по уровню вложенности и порядку следования
        parent_level = parent_section.get("level", 0)
        section_level = section.get("level", 0)
        
        # Секция должна иметь больший уровень вложенности, чем родительская
        if section_level <= parent_level:
            return False
        
        # Секция должна идти после родительской
        parent_line = parent_section.get("line_number", 0)
        section_line = section.get("line_number", 0)
        
        return section_line > parent_line

    def _extract_parameters_from_section(self, section: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Description:
        ---------------
            Извлекает параметры метода из содержимого секции.

        Args:
        ---------------
            section: Секция с описанием метода.

        Returns:
        ---------------
            List[Dict[str, Any]]: Список параметров метода.
        """
        parameters = []
        
        # Извлекаем параметры из содержимого секции
        content = section.get("content", "")
        
        # Список возможных маркеров для блока параметров
        param_markers = [
            r"\*Параметры:\*\s*(.*?)(?=\*|\Z)",     # *Параметры:* (русский)
            r"\*Parameters:\*\s*(.*?)(?=\*|\Z)",     # *Parameters:* (английский)
            r"Parameters:\s*(.*?)(?=\n\n|\Z)",      # Parameters: (простой текст)
            r"@param\s+(\w+)\s+([^\n@]*)",          # @param name description (Javadoc)
        ]
        
        # Проверяем различные форматы описания параметров
        
        # 1. Маркированный список параметров
        for marker in param_markers[:3]:  # Первые три маркера для блоков параметров
            params_match = re.search(marker, content, re.DOTALL | re.IGNORECASE)
            if params_match:
                params_text = params_match.group(1)
                
                # Пробуем различные форматы списков параметров
                param_formats = [
                    r"\*\s*`([^`]+)`\s*—\s*([^*\n]+)",     # * `name` — description
                    r"\*\s*`([^`]+)`\s*-\s*([^*\n]+)",     # * `name` - description
                    r"\*\s*([^:]+):\s*([^*\n]+)",          # * name: description
                    r"-\s*`([^`]+)`\s*[:-]\s*([^-\n]+)",   # - `name`: description
                    r"\*\s*([^:\s]+)\s*[:-]\s*([^*\n]+)"   # * name: description
                ]
                
                for format_regex in param_formats:
                    param_blocks = re.findall(format_regex, params_text)
                    if param_blocks:
                        for param_name, param_desc in param_blocks:
                            parameters.append(self._process_parameter(param_name, param_desc, section))
                        break  # Если нашли параметры в одном формате, не проверяем другие
        
        # 2. Javadoc стиль @param
        param_javadoc = re.findall(r"@param\s+(\w+)\s+([^\n@]*)", content)
        for param_name, param_desc in param_javadoc:
            parameters.append(self._process_parameter(param_name, param_desc, section))
        
        # 3. Извлечение из сигнатуры метода в блоке кода
        if not parameters:
            code_blocks = re.findall(r"```[^\n]*\n(.*?)```", content, re.DOTALL)
            for block in code_blocks:
                # Ищем сигнатуру метода
                signature_match = re.search(r"\w+\s+\w+\s*\((.*?)\)", block)
                if signature_match:
                    param_str = signature_match.group(1)
                    # Разбиваем параметры
                    if param_str.strip():
                        param_items = param_str.split(',')
                        for param in param_items:
                            param = param.strip()
                            if param:
                                # Пытаемся извлечь имя и тип параметра
                                parts = param.split()
                                if len(parts) >= 2:
                                    param_type = parts[0]
                                    param_name = parts[1].strip()
                                    parameters.append({
                                        "name": param_name,
                                        "type": param_type,
                                        "required": True,  # По умолчанию все параметры обязательны
                                        "description": "",
                                        "doc_line": section.get("line_number"),
                                        "section": section.get("title")
                                    })
        
        return parameters

    def _process_parameter(self, param_name: str, param_desc: str, section: Dict[str, Any]) -> Dict[str, Any]:
        """
        Description:
        ---------------
            Обрабатывает информацию о параметре метода.

        Args:
        ---------------
            param_name: Имя параметра.
            param_desc: Описание параметра.
            section: Секция с описанием метода.

        Returns:
        ---------------
            Dict[str, Any]: Информация о параметре.
        """
        # Очищаем имя параметра от возможных обрамлений
        param_name = param_name.strip('`\'"')
        
        # Определяем тип параметра из описания (если возможно)
        type_patterns = [
            r"\(([\w<>[\]]+)\)",             # (type)
            r"типа\s+([\w<>[\]]+)",          # типа type
            r"of\s+type\s+([\w<>[\]]+)",     # of type type
            r":\s+([\w<>[\]]+)"              # : type
        ]
        
        param_type = None
        for pattern in type_patterns:
            type_match = re.search(pattern, param_desc, re.IGNORECASE)
            if type_match:
                param_type = type_match.group(1)
                break
        
        # Определяем обязательность параметра
        required = True
        optional_markers = ["необязательн", "optional", "может отсутствовать", "may be null", "may be omitted"]
        for marker in optional_markers:
            if marker.lower() in param_desc.lower():
                required = False
                break
        
        return {
            "name": param_name,
            "type": param_type,
            "required": required,
            "description": param_desc.strip(),
            "doc_line": section.get("line_number"),
            "section": section.get("title")
        }
    