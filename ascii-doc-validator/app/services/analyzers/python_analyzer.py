# app/services/analyzers/python_analyzer.py
"""
Описание программного модуля:
-----------------------------
Данный модуль содержит класс `PythonAnalyzer` для анализа исходного кода на языке Python.
Анализатор использует встроенный модуль ast для парсинга Python-кода и преобразования его
в структурированное представление.

Функциональное назначение:
---------------------------
Модуль предназначен для анализа Python-кода, извлечения информации о классах, методах,
функциях и их взаимосвязях. Это позволяет создать унифицированное представление кода
для дальнейшего сравнения с документацией.
"""

# Импорты стандартной библиотеки Python
import os
import ast
import inspect
from typing import Dict, List, Optional, Any, Tuple, Set, Union

# Импорты внутренних модулей
from services.analyzers.language_specific_analyzer import LanguageSpecificAnalyzer
from models.code_structure import (
    CodeStructure, ClassInfo, MethodInfo, FieldInfo, ParameterInfo, 
    AnnotationInfo, ImportInfo, LanguageType
)


class PythonAnalyzer(LanguageSpecificAnalyzer):
    """
    Description:
    ---------------
        Анализатор исходного кода на языке Python.

    Methods:
    ---------------
        analyze: Анализирует исходный код из строки.
        analyze_file: Анализирует исходный код из файла.
        _extract_docstring: Извлекает docstring из узла AST.
        _parse_annotations: Парсит декораторы Python.
        _parse_function: Парсит функцию или метод Python.
        _parse_class: Парсит класс Python.
        _parse_module: Парсит модуль Python.

    Examples:
    ---------------
        >>> analyzer = PythonAnalyzer()
        >>> structure = analyzer.analyze_file("path/to/file.py")
    """

    def __init__(self):
        """
        Description:
        ---------------
            Инициализирует анализатор Python-кода.
        """
        super().__init__(LanguageType.PYTHON, ["py"])
        
        # Маппинг декораторов Flask/FastAPI к HTTP-методам
        self.api_decorators = {
            "route": None,  # Метод определяется в параметрах
            "get": "GET",
            "post": "POST",
            "put": "PUT",
            "delete": "DELETE",
            "patch": "PATCH",
            "options": "OPTIONS",
            "head": "HEAD"
        }

    def analyze(self, source_code: str, file_path: str) -> CodeStructure:
        """
        Description:
        ---------------
            Анализирует исходный код из строки.

        Args:
        ---------------
            source_code: Строка с исходным кодом.
            file_path: Путь к файлу (для метаданных).

        Returns:
        ---------------
            CodeStructure: Структурированное представление кода.

        Raises:
        ---------------
            ValueError: Если произошла ошибка при парсинге кода.
        """
        try:
            # Парсинг Python-кода с помощью ast
            tree = ast.parse(source_code)
            
            # Извлечение информации из AST
            return self._parse_module(tree, file_path, source_code)
        except SyntaxError as e:
            raise ValueError(f"Ошибка синтаксиса Python: {str(e)}")
        except Exception as e:
            raise ValueError(f"Ошибка при парсинге Python-кода: {str(e)}")

    def analyze_file(self, file_path: str) -> CodeStructure:
        """
        Description:
        ---------------
            Анализирует исходный код из файла.

        Args:
        ---------------
            file_path: Путь к файлу с исходным кодом.

        Returns:
        ---------------
            CodeStructure: Структурированное представление кода.

        Raises:
        ---------------
            FileNotFoundError: Если файл не найден.
            ValueError: Если формат файла не поддерживается или произошла ошибка при парсинге.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Файл не найден: {file_path}")
        
        if not self.is_supported_file(file_path):
            raise ValueError(f"Неподдерживаемый формат файла: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()
        
        return self.analyze(source_code, file_path)

    def _extract_docstring(self, node: Union[ast.FunctionDef, ast.ClassDef]) -> Optional[str]:
        """
        Description:
        ---------------
            Извлекает docstring из узла AST.

        Args:
        ---------------
            node: Узел AST (функция или класс).

        Returns:
        ---------------
            Optional[str]: Docstring или None, если отсутствует.
        """
        if not node.body:
            return None
        
        first_node = node.body[0]
        if isinstance(first_node, ast.Expr) and isinstance(first_node.value, ast.Str):
            return first_node.value.s.strip()
        
        return None

    def _parse_annotations(self, decorators: List[ast.expr]) -> Tuple[List[AnnotationInfo], bool, Optional[str], Optional[str]]:
        """
        Description:
        ---------------
            Парсит декораторы Python.

        Args:
        ---------------
            decorators: Список декораторов из ast.

        Returns:
        ---------------
            Tuple[List[AnnotationInfo], bool, Optional[str], Optional[str]]: 
            Список моделей аннотаций, флаг API-эндпоинта, HTTP-метод, путь.
        """
        result = []
        is_api_endpoint = False
        http_method = None
        path = None
        
        for decorator in decorators:
            name = None
            parameters = {}
            
            # Извлечение имени декоратора
            if isinstance(decorator, ast.Name):
                name = decorator.id
            elif isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Name):
                    name = decorator.func.id
                elif isinstance(decorator.func, ast.Attribute):
                    if isinstance(decorator.func.value, ast.Name) and decorator.func.value.id in ["app", "blueprint", "router"]:
                        # Flask/FastAPI декораторы
                        name = decorator.func.attr
                        
                        # Проверка, является ли декоратор API-эндпоинтом
                        if name in self.api_decorators:
                            is_api_endpoint = True
                            http_method = self.api_decorators[name]
                            
                            # Извлечение пути API из аргументов декоратора
                            if decorator.args:
                                if isinstance(decorator.args[0], ast.Str):
                                    path = decorator.args[0].s
                            
                            # Извлечение HTTP-метода из keyword аргументов
                            if name == "route" and decorator.keywords:
                                for keyword in decorator.keywords:
                                    if keyword.arg == "methods":
                                        if isinstance(keyword.value, ast.List) and keyword.value.elts:
                                            if isinstance(keyword.value.elts[0], ast.Str):
                                                http_method = keyword.value.elts[0].s
                                    elif keyword.arg == "path" or keyword.arg == "rule":
                                        if isinstance(keyword.value, ast.Str):
                                            path = keyword.value.s
                
                # Извлечение параметров декоратора
                if hasattr(decorator, 'keywords'):
                    for keyword in decorator.keywords:
                        if isinstance(keyword.value, ast.Str):
                            parameters[keyword.arg] = keyword.value.s
                        elif isinstance(keyword.value, ast.Num):
                            parameters[keyword.arg] = keyword.value.n
                        elif isinstance(keyword.value, ast.NameConstant):
                            parameters[keyword.arg] = keyword.value.value
            
            if name:
                result.append(AnnotationInfo(
                    name=name,
                    parameters=parameters if parameters else None
                ))
        
        return result, is_api_endpoint, http_method, path

    def _parse_function(
        self, func: Union[ast.FunctionDef, ast.AsyncFunctionDef], source_lines: List[str], is_method: bool = False
    ) -> MethodInfo:
        """
        Description:
        ---------------
            Парсит функцию или метод Python.

        Args:
        ---------------
            func: Объект FunctionDef или AsyncFunctionDef из ast.
            source_lines: Список строк исходного кода.
            is_method: Флаг, указывающий, является ли функция методом класса.

        Returns:
        ---------------
            MethodInfo: Модель метода.
        """
        # Извлечение docstring
        documentation = self._extract_docstring(func)
        
        # Извлечение декораторов
        annotations, is_api_endpoint, http_method, path = self._parse_annotations(func.decorator_list)
        
        # Извлечение параметров
        parameters = []
        for arg in func.args.args:
            # Пропускаем self и cls для методов
            if is_method and arg.arg in ["self", "cls"]:
                continue
            
            # Извлечение типа параметра
            param_type = None
            if hasattr(arg, 'annotation') and arg.annotation:
                if isinstance(arg.annotation, ast.Name):
                    param_type = arg.annotation.id
                elif isinstance(arg.annotation, ast.Attribute):
                    param_type = f"{arg.annotation.value.id}.{arg.annotation.attr}"
                elif isinstance(arg.annotation, ast.Subscript):
                    if isinstance(arg.annotation.value, ast.Name):
                        param_type = arg.annotation.value.id
            
            # Определение, является ли параметр обязательным
            required = True
            default_value = None
            
            # Проверка наличия значения по умолчанию
            if func.args.defaults:
                # Вычисляем позицию параметра с конца
                pos_from_end = len(func.args.args) - func.args.args.index(arg) - 1
                if pos_from_end < len(func.args.defaults):
                    required = False
                    
                    # Извлечение значения по умолчанию
                    default = func.args.defaults[-pos_from_end - 1]
                    if isinstance(default, ast.Str):
                        default_value = f'"{default.s}"'
                    elif isinstance(default, ast.Num):
                        default_value = str(default.n)
                    elif isinstance(default, ast.NameConstant):
                        default_value = str(default.value)
                    elif isinstance(default, ast.Name):
                        default_value = default.id
            
            parameters.append(ParameterInfo(
                name=arg.arg,
                type=param_type,
                required=required,
                default_value=default_value,
                annotations=[]
            ))
        
        # Извлечение возвращаемого типа
        return_type = None
        if hasattr(func, 'returns') and func.returns:
            if isinstance(func.returns, ast.Name):
                return_type = func.returns.id
            elif isinstance(func.returns, ast.Attribute):
                return_type = f"{func.returns.value.id}.{func.returns.attr}"
            elif isinstance(func.returns, ast.Subscript):
                if isinstance(func.returns.value, ast.Name):
                    return_type = func.returns.value.id
        
        # Определение начальной и конечной строки функции
        line_start = func.lineno
        line_end = func.end_lineno if hasattr(func, 'end_lineno') else 0
        
        # Если end_lineno не определено, пытаемся определить по отступам
        if line_end == 0:
            func_indent = None
            for i, line in enumerate(source_lines[line_start-1:], line_start):
                if i == line_start:
                    # Определяем уровень отступа функции
                    func_indent = len(line) - len(line.lstrip())
                    continue
                
                if line.strip() and len(line) - len(line.lstrip()) <= func_indent:
                    line_end = i - 1
                    break
            
            if line_end == 0:
                line_end = len(source_lines)
        
        return MethodInfo(
            name=func.name,
            documentation=documentation,
            modifiers=["async"] if isinstance(func, ast.AsyncFunctionDef) else [],
            return_type=return_type,
            parameters=parameters,
            exceptions=[],  # В Python нет явного объявления исключений
            annotations=annotations,
            is_api_endpoint=is_api_endpoint,
            http_method=http_method,
            path=path,
            line_start=line_start,
            line_end=line_end
        )

    def _parse_class(self, cls: ast.ClassDef, source_lines: List[str]) -> ClassInfo:
        """
        Description:
        ---------------
            Парсит класс Python.

        Args:
        ---------------
            cls: Объект ClassDef из ast.
            source_lines: Список строк исходного кода.

        Returns:
        ---------------
            ClassInfo: Модель класса.
        """
        # Извлечение docstring
        documentation = self._extract_docstring(cls)
        
        # Извлечение декораторов
        annotations, _, _, _ = self._parse_annotations(cls.decorator_list)
        
        # Извлечение суперклассов
        superclasses = []
        for base in cls.bases:
            if isinstance(base, ast.Name):
                superclasses.append(base.id)
            elif isinstance(base, ast.Attribute):
                superclasses.append(f"{base.value.id}.{base.attr}")
        
        # Проверка, является ли класс контроллером
        is_controller = False
        for ann in annotations:
            if "Controller" in ann.name or "View" in ann.name:
                is_controller = True
                break
        
        # Извлечение методов и полей
        methods = []
        fields = []
        
        for item in cls.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                methods.append(self._parse_function(item, source_lines, is_method=True))
            elif isinstance(item, ast.Assign):
                # Поля класса (атрибуты)
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        # Определяем тип поля
                        field_type = None
                        default_value = None
                        
                        # Извлечение значения по умолчанию
                        if isinstance(item.value, ast.Str):
                            field_type = "str"
                            default_value = f'"{item.value.s}"'
                        elif isinstance(item.value, ast.Num):
                            field_type = "int" if isinstance(item.value.n, int) else "float"
                            default_value = str(item.value.n)
                        elif isinstance(item.value, ast.List):
                            field_type = "list"
                            default_value = "[]"
                        elif isinstance(item.value, ast.Dict):
                            field_type = "dict"
                            default_value = "{}"
                        elif isinstance(item.value, ast.NameConstant):
                            if item.value.value is None:
                                field_type = "None"
                            elif isinstance(item.value.value, bool):
                                field_type = "bool"
                            default_value = str(item.value.value)
                        elif isinstance(item.value, ast.Name):
                            field_type = item.value.id
                        
                        fields.append(FieldInfo(
                            name=target.id,
                            documentation=None,
                            modifiers=[],
                            type=field_type or "Any",
                            default_value=default_value,
                            annotations=[],
                            line=item.lineno
                        ))
            elif isinstance(item, ast.AnnAssign):
                # Поля класса с аннотацией типа
                if isinstance(item.target, ast.Name):
                    # Извлечение типа поля
                    field_type = None
                    if isinstance(item.annotation, ast.Name):
                        field_type = item.annotation.id
                    elif isinstance(item.annotation, ast.Attribute):
                        field_type = f"{item.annotation.value.id}.{item.annotation.attr}"
                    elif isinstance(item.annotation, ast.Subscript):
                        if isinstance(item.annotation.value, ast.Name):
                            field_type = item.annotation.value.id
                    
                    # Извлечение значения по умолчанию
                    default_value = None
                    if item.value:
                        if isinstance(item.value, ast.Str):
                            default_value = f'"{item.value.s}"'
                        elif isinstance(item.value, ast.Num):
                            default_value = str(item.value.n)
                        elif isinstance(item.value, ast.List):
                            default_value = "[]"
                        elif isinstance(item.value, ast.Dict):
                            default_value = "{}"
                        elif isinstance(item.value, ast.NameConstant):
                            default_value = str(item.value.value)
                        elif isinstance(item.value, ast.Name):
                            default_value = item.value.id
                    
                    fields.append(FieldInfo(
                        name=item.target.id,
                        documentation=None,
                        modifiers=[],
                        type=field_type or "Any",
                        default_value=default_value,
                        annotations=[],
                        line=item.lineno
                    ))
        
        # Определение начальной и конечной строки класса
        line_start = cls.lineno
        line_end = cls.end_lineno if hasattr(cls, 'end_lineno') else 0
        
        # Если end_lineno не определено, пытаемся определить по отступам
        if line_end == 0:
            cls_indent = None
            for i, line in enumerate(source_lines[line_start-1:], line_start):
                if i == line_start:
                    # Определяем уровень отступа класса
                    cls_indent = len(line) - len(line.lstrip())
                    continue
                
                if line.strip() and len(line) - len(line.lstrip()) <= cls_indent:
                    line_end = i - 1
                    break
            
            if line_end == 0:
                line_end = len(source_lines)
        
        return ClassInfo(
            name=cls.name,
            documentation=documentation,
            modifiers=[],
            methods=methods,
            fields=fields,
            superclasses=superclasses,
            interfaces=[],                # В Python нет явного понятия интерфейсов
            annotations=annotations,
            is_controller=is_controller,
            line_start=line_start,
            line_end=line_end
        )

    def _parse_module(
        self, tree: ast.Module, file_path: str, source_code: str
    ) -> CodeStructure:
        """
        Description:
        ---------------
            Парсит модуль Python.

        Args:
        ---------------
            tree: Объект Module из ast.
            file_path: Путь к файлу (для метаданных).
            source_code: Исходный код.

        Returns:
        ---------------
            CodeStructure: Структурированное представление кода.
        """
        # Разбиение исходного кода на строки
        source_lines = source_code.splitlines()
        
        # Извлечение импортов
        imports = []
        for node in tree.body:
            if isinstance(node, ast.Import):
                for name in node.names:
                    imports.append(ImportInfo(
                        module=name.name,
                        alias=name.asname,
                        line=node.lineno
                    ))
            elif isinstance(node, ast.ImportFrom):
                for name in node.names:
                    full_module = f"{node.module}.{name.name}" if node.module else name.name
                    imports.append(ImportInfo(
                        module=full_module,
                        alias=name.asname,
                        line=node.lineno
                    ))
        
        # Извлечение классов
        classes = []
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                classes.append(self._parse_class(node, source_lines))
        
        # Извлечение функций верхнего уровня
        functions = []
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append(self._parse_function(node, source_lines))
        
        # Создание метаданных
        metadata = {
            "language": LanguageType.PYTHON.value,
            "file_path": file_path,
            "module": os.path.splitext(os.path.basename(file_path))[0]
        }
        
        # Создание структуры кода
        return CodeStructure(
            metadata=metadata,
            imports=imports,
            classes=classes,
            functions=functions,
            enums=[],        # TODO: Добавить поддержку перечислений
            interfaces=[],   # В Python нет явных интерфейсов
            constants=[]     # TODO: Добавить поддержку констант
        )