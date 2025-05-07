# app/services/analyzers/java_analyzer.py
"""
Описание программного модуля:
-----------------------------
Данный модуль содержит класс `JavaAnalyzer` для анализа исходного кода на языке Java.
Анализатор использует библиотеку javalang для парсинга Java-кода и преобразования его
в структурированное представление.

Функциональное назначение:
---------------------------
Модуль предназначен для анализа Java-кода, извлечения информации о классах, методах,
полях и их взаимосвязях. Это позволяет создать унифицированное представление кода
для дальнейшего сравнения с документацией.
"""

# Импорты стандартной библиотеки Python
import os
from typing import Dict, List, Optional, Any, Tuple, Set

# Импорты сторонних библиотек
import javalang
from javalang.tree import (
    CompilationUnit, ClassDeclaration, MethodDeclaration, 
    FieldDeclaration, FormalParameter, Annotation
)

# Импорты внутренних модулей
from services.analyzers.language_specific_analyzer import LanguageSpecificAnalyzer
from models.code_structure import (
    CodeStructure, ClassInfo, MethodInfo, FieldInfo, ParameterInfo, 
    AnnotationInfo, ImportInfo, LanguageType
)


class JavaAnalyzer(LanguageSpecificAnalyzer):
    """
    Description:
    ---------------
        Анализатор исходного кода на языке Java.

    Methods:
    ---------------
        analyze: Анализирует исходный код из строки.
        analyze_file: Анализирует исходный код из файла.
        _parse_annotations: Парсит аннотации Java.
        _parse_method: Парсит метод Java.
        _parse_field: Парсит поле класса Java.
        _parse_class: Парсит класс Java.
        _parse_compilation_unit: Парсит единицу компиляции Java.

    Examples:
    ---------------
        >>> analyzer = JavaAnalyzer()
        >>> structure = analyzer.analyze_file("path/to/file.java")
    """

    def __init__(self):
        """
        Description:
        ---------------
            Инициализирует анализатор Java-кода.
        """
        super().__init__(LanguageType.JAVA, ["java"])

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
            # Парсинг Java-кода с помощью javalang
            tree = javalang.parse.parse(source_code)
            
            # Извлечение информации из AST
            return self._parse_compilation_unit(tree, file_path, source_code)
        except Exception as e:
            raise ValueError(f"Ошибка при парсинге Java-кода: {str(e)}")

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

    def _parse_annotations(self, annotations: List[Annotation]) -> List[AnnotationInfo]:
        """
        Description:
        ---------------
            Парсит аннотации Java.

        Args:
        ---------------
            annotations: Список аннотаций из javalang.

        Returns:
        ---------------
            List[AnnotationInfo]: Список моделей аннотаций.
        """
        result = []
        
        for annotation in annotations:
            params = {}
            if annotation.element is not None:
                for element in annotation.element:
                    if isinstance(element, javalang.tree.ElementValuePair):
                        params[element.name] = element.value
            
            result.append(AnnotationInfo(
                name=annotation.name,
                parameters=params if params else None
            ))
        
        return result

    def _parse_method(self, method: MethodDeclaration, source_lines: List[str]) -> MethodInfo:
        """
        Description:
        ---------------
            Парсит метод Java.

        Args:
        ---------------
            method: Объект MethodDeclaration из javalang.
            source_lines: Список строк исходного кода.

        Returns:
        ---------------
            MethodInfo: Модель метода.
        """
        # Извлечение модификаторов
        modifiers = list(method.modifiers) if method.modifiers else []
        
        # Извлечение аннотаций
        annotations = self._parse_annotations(method.annotations)
        
        # Проверка, является ли метод API-эндпоинтом
        is_api_endpoint = False
        http_method = None
        path = None
        
        # Проверка наличия аннотаций Spring REST Controller
        for ann in annotations:
            if ann.name in [
                "RequestMapping", "GetMapping", "PostMapping", 
                "PutMapping", "DeleteMapping", "PatchMapping"
            ]:
                is_api_endpoint = True
                
                # Определение HTTP-метода
                if ann.name == "RequestMapping" and ann.parameters and "method" in ann.parameters:
                    http_method = ann.parameters["method"].strip('"')
                elif ann.name == "GetMapping":
                    http_method = "GET"
                elif ann.name == "PostMapping":
                    http_method = "POST"
                elif ann.name == "PutMapping":
                    http_method = "PUT"
                elif ann.name == "DeleteMapping":
                    http_method = "DELETE"
                elif ann.name == "PatchMapping":
                    http_method = "PATCH"
                
                # Извлечение пути
                if ann.parameters:
                    if "value" in ann.parameters:
                        path = ann.parameters["value"].strip('"')
                    elif "path" in ann.parameters:
                        path = ann.parameters["path"].strip('"')
        
        # Извлечение параметров
        parameters = []
        for param in method.parameters:
            annotations_param = []
            if hasattr(param, 'annotations') and param.annotations:
                annotations_param = self._parse_annotations(param.annotations)
            
            parameters.append(ParameterInfo(
                name=param.name,
                type=param.type.name if hasattr(param, 'type') and param.type else None,
                required=True,  # По умолчанию все параметры Java обязательны
                annotations=annotations_param
            ))
        
        # Извлечение исключений
        exceptions = []
        if method.throws:
            for ex in method.throws:
                if isinstance(ex, str):
                    exceptions.append(ex)       # Если ex это строка, добавляем её как есть
                elif hasattr(ex, 'name'):
                    exceptions.append(ex.name)  # Если ex это объект с атрибутом name
        
        # Извлечение документации (JavaDoc)
        documentation = None
        if hasattr(method, 'documentation') and method.documentation:
            documentation = method.documentation
        
        # Определение начальной и конечной строки метода
        line_start = method.position.line if hasattr(method, 'position') and method.position else 0
        line_end = 0
        
        # Попытка определить конечную строку метода
        for i in range(line_start, len(source_lines)):
            if source_lines[i].strip().endswith("}"):
                line_end = i + 1
                break
        
        return MethodInfo(
            name=method.name,
            documentation=documentation,
            modifiers=modifiers,
            return_type=method.return_type.name if method.return_type else "void",
            parameters=parameters,
            exceptions=exceptions,
            annotations=annotations,
            is_api_endpoint=is_api_endpoint,
            http_method=http_method,
            path=path,
            line_start=line_start,
            line_end=line_end
        )

    def _parse_field(self, field: FieldDeclaration, source_lines: List[str]) -> List[FieldInfo]:
        """
        Description:
        ---------------
            Парсит поле класса Java.

        Args:
        ---------------
            field: Объект FieldDeclaration из javalang.
            source_lines: Список строк исходного кода.

        Returns:
        ---------------
            List[FieldInfo]: Список моделей полей.
        """
        result = []
        
        # Извлечение модификаторов
        modifiers = list(field.modifiers) if field.modifiers else []
        
        # Извлечение аннотаций
        annotations = self._parse_annotations(field.annotations)
        
        # Извлечение типа поля
        field_type = field.type.name if hasattr(field.type, 'name') else str(field.type)
        
        # Извлечение документации (JavaDoc)
        documentation = None
        if hasattr(field, 'documentation') and field.documentation:
            documentation = field.documentation
        
        # Определение строки поля
        line = field.position.line if hasattr(field, 'position') and field.position else 0
        
        # Создание модели для каждой переменной в декларации поля
        for declarator in field.declarators:
            default_value = None
            if hasattr(declarator, 'initializer') and declarator.initializer:
                if hasattr(declarator.initializer, 'value'):
                    default_value = declarator.initializer.value
                elif hasattr(declarator.initializer, 'qualifier'):
                    default_value = f"{declarator.initializer.qualifier}.{declarator.initializer.member}"
            
            result.append(FieldInfo(
                name=declarator.name,
                documentation=documentation,
                modifiers=modifiers,
                type=field_type,
                default_value=default_value,
                annotations=annotations,
                line=line
            ))
        
        return result

    def _parse_class(
        self, cls: ClassDeclaration, source_lines: List[str]
    ) -> ClassInfo:
        """
        Description:
        ---------------
            Парсит класс Java.

        Args:
        ---------------
            cls: Объект ClassDeclaration из javalang.
            source_lines: Список строк исходного кода.

        Returns:
        ---------------
            ClassInfo: Модель класса.
        """
        # Извлечение модификаторов
        modifiers = list(cls.modifiers) if cls.modifiers else []
        
        # Извлечение аннотаций
        annotations = self._parse_annotations(cls.annotations)
        
        # Проверка, является ли класс контроллером
        is_controller = False
        for ann in annotations:
            if ann.name in ["Controller", "RestController"]:
                is_controller = True
                break
        
        # Извлечение суперклассов
        superclasses = []
        if cls.extends:
            superclasses.append(cls.extends.name)
        
        # Извлечение интерфейсов
        interfaces = []
        if cls.implements:
            interfaces = [impl.name for impl in cls.implements]
        
        # Извлечение методов
        methods = []
        for method in cls.methods:
            methods.append(self._parse_method(method, source_lines))
        
        # Извлечение полей
        fields = []
        for field in cls.fields:
            fields.extend(self._parse_field(field, source_lines))
        
        # Извлечение документации (JavaDoc)
        documentation = None
        if hasattr(cls, 'documentation') and cls.documentation:
            documentation = cls.documentation
        
        # Определение начальной и конечной строки класса
        line_start = cls.position.line if hasattr(cls, 'position') and cls.position else 0
        line_end = 0
        
        # Попытка определить конечную строку класса
        for i in range(line_start, len(source_lines)):
            if source_lines[i].strip() == "}":
                line_end = i + 1
                break
        
        return ClassInfo(
            name=cls.name,
            documentation=documentation,
            modifiers=modifiers,
            methods=methods,
            fields=fields,
            superclasses=superclasses,
            interfaces=interfaces,
            annotations=annotations,
            is_controller=is_controller,
            line_start=line_start,
            line_end=line_end
        )

    def _parse_compilation_unit(
        self, tree: CompilationUnit, file_path: str, source_code: str
    ) -> CodeStructure:
        """
        Description:
        ---------------
            Парсит единицу компиляции Java.

        Args:
        ---------------
            tree: Объект CompilationUnit из javalang.
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
        for imp in tree.imports:
            imports.append(ImportInfo(
                module=imp.path,
                line=imp.position.line if hasattr(imp, 'position') and imp.position else 0
            ))
        
        # Извлечение классов
        classes = []
        for cls in tree.types:
            if isinstance(cls, javalang.tree.ClassDeclaration):
                classes.append(self._parse_class(cls, source_lines))
        
        # Создание метаданных
        metadata = {
            "language": LanguageType.JAVA.value,
            "file_path": file_path,
            "package": tree.package.name if tree.package else None
        }
        
        # Создание структуры кода
        return CodeStructure(
            metadata=metadata,
            imports=imports,
            classes=classes,
            functions=[],   # В Java нет функций верхнего уровня
            enums=[],       # TODO: Добавить поддержку перечислений
            interfaces=[],  # TODO: Добавить поддержку интерфейсов
            constants=[]    # TODO: Добавить поддержку констант
        )