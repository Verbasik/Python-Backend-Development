# app/models/code_structure.py
"""
Описание программного модуля:
-----------------------------
Данный модуль содержит набор классов для хранения структурированного представления 
исходного кода. Классы описывают различные элементы кода, такие как классы, методы, 
параметры и их взаимосвязи. Модуль использует Pydantic для валидации данных 
и предоставляет строгую типизацию для всех полей.

Функциональное назначение:
---------------------------
Модуль предназначен для создания унифицированного представления исходного кода 
различных языков программирования. Это позволяет проводить сравнение между 
кодом и документацией независимо от используемого языка программирования.
"""

# Импорты стандартной библиотеки Python
from enum import Enum
from typing import List, Dict, Optional, Any, Set

# Импорты сторонних библиотек
from pydantic import BaseModel, Field


class LanguageType(str, Enum):
    """
    Description:
    ---------------
        Перечисление поддерживаемых языков программирования.

    Args:
    ---------------
        JAVA: Java
        PYTHON: Python
        JAVASCRIPT: JavaScript
        TYPESCRIPT: TypeScript
        CSHARP: C#
        OTHER: Другие языки
    """
    JAVA       = "JAVA"
    PYTHON     = "PYTHON"
    JAVASCRIPT = "JAVASCRIPT"
    TYPESCRIPT = "TYPESCRIPT"
    CSHARP     = "CSHARP"
    OTHER      = "OTHER"


class AnnotationInfo(BaseModel):
    """
    Description:
    ---------------
        Модель для описания аннотации или декоратора.

    Args:
    ---------------
        name: Название аннотации или декоратора
        parameters: Параметры аннотации (опционально)

    Examples:
    ---------------
        >>> annotation = AnnotationInfo(name="RequestMapping", parameters={"value": "/api"})
    """
    name: str
    parameters: Optional[Dict[str, Any]] = None


class ParameterInfo(BaseModel):
    """
    Description:
    ---------------
        Модель для описания параметра метода или функции.

    Args:
    ---------------
        name: Имя параметра
        type: Тип параметра (если указан)
        default_value: Значение по умолчанию (опционально)
        required: Является ли параметр обязательным
        annotations: Список аннотаций параметра
        description: Описание параметра из документации (опционально)

    Examples:
    ---------------
        >>> param = ParameterInfo(
        ...     name="id", 
        ...     type="Long", 
        ...     required=True,
        ...     annotations=[AnnotationInfo(name="PathVariable")]
        ... )
    """
    name: str
    type: Optional[str] = None
    default_value: Optional[str] = None
    required: bool = True
    annotations: List[AnnotationInfo] = []
    description: Optional[str] = None


class MethodInfo(BaseModel):
    """
    Description:
    ---------------
        Модель для описания метода или функции.

    Args:
    ---------------
        name: Имя метода
        documentation: Документация метода (опционально)
        modifiers: Список модификаторов (public, private, static и т.д.)
        return_type: Тип возвращаемого значения (опционально)
        parameters: Список параметров метода
        exceptions: Список исключений, которые может выбрасывать метод
        annotations: Список аннотаций метода
        is_api_endpoint: Является ли метод API-эндпоинтом
        http_method: HTTP-метод (GET, POST и т.д.) для API-эндпоинта (опционально)
        path: Путь API-эндпоинта (опционально)
        line_start: Номер строки начала метода
        line_end: Номер строки окончания метода

    Examples:
    ---------------
        >>> method = MethodInfo(
        ...     name="getUser",
        ...     documentation="Returns user by ID",
        ...     modifiers=["public"],
        ...     return_type="User",
        ...     parameters=[ParameterInfo(name="id", type="Long", required=True)],
        ...     annotations=[AnnotationInfo(name="GetMapping", parameters={"value": "/users/{id}"})],
        ...     is_api_endpoint=True,
        ...     http_method="GET",
        ...     path="/users/{id}",
        ...     line_start=10,
        ...     line_end=15
        ... )
    """
    name: str
    documentation: Optional[str] = None
    modifiers: List[str] = []
    return_type: Optional[str] = None
    parameters: List[ParameterInfo] = []
    exceptions: List[str] = []
    annotations: List[AnnotationInfo] = []
    is_api_endpoint: bool = False
    http_method: Optional[str] = None
    path: Optional[str] = None
    line_start: int
    line_end: int


class FieldInfo(BaseModel):
    """
    Description:
    ---------------
        Модель для описания поля класса.

    Args:
    ---------------
        name: Имя поля
        documentation: Документация поля (опционально)
        modifiers: Список модификаторов (public, private, static и т.д.)
        type: Тип поля
        default_value: Значение по умолчанию (опционально)
        annotations: Список аннотаций поля
        line: Номер строки, на которой определено поле

    Examples:
    ---------------
        >>> field = FieldInfo(
        ...     name="id",
        ...     modifiers=["private"],
        ...     type="Long",
        ...     annotations=[AnnotationInfo(name="Id")],
        ...     line=15
        ... )
    """
    name: str
    documentation: Optional[str] = None
    modifiers: List[str] = []
    type: str
    default_value: Optional[str] = None
    annotations: List[AnnotationInfo] = []
    line: int


class ClassInfo(BaseModel):
    """
    Description:
    ---------------
        Модель для описания класса.

    Args:
    ---------------
        name: Имя класса
        documentation: Документация класса (опционально)
        modifiers: Список модификаторов (public, private, abstract и т.д.)
        methods: Список методов класса
        fields: Список полей класса
        superclasses: Список суперклассов (наследование)
        interfaces: Список интерфейсов, которые реализует класс
        annotations: Список аннотаций класса
        is_controller: Является ли класс контроллером
        line_start: Номер строки начала класса
        line_end: Номер строки окончания класса

    Examples:
    ---------------
        >>> class_info = ClassInfo(
        ...     name="UserController",
        ...     documentation="Controller for user management",
        ...     modifiers=["public"],
        ...     methods=[],
        ...     fields=[],
        ...     superclasses=[],
        ...     interfaces=[],
        ...     annotations=[AnnotationInfo(name="RestController")],
        ...     is_controller=True,
        ...     line_start=5,
        ...     line_end=50
        ... )
    """
    name: str
    documentation: Optional[str] = None
    modifiers: List[str] = []
    methods: List[MethodInfo] = []
    fields: List[FieldInfo] = []
    superclasses: List[str] = []
    interfaces: List[str] = []
    annotations: List[AnnotationInfo] = []
    is_controller: bool = False
    line_start: int
    line_end: int


class ImportInfo(BaseModel):
    """
    Description:
    ---------------
        Модель для описания импорта.

    Args:
    ---------------
        module: Название импортируемого модуля
        alias: Псевдоним модуля (опционально)
        elements: Список импортируемых элементов (опционально)
        line: Номер строки, на которой определен импорт

    Examples:
    ---------------
        >>> import_info = ImportInfo(
        ...     module="java.util.List",
        ...     line=3
        ... )
    """
    module: str
    alias: Optional[str] = None
    elements: List[str] = []
    line: int


class CodeStructure(BaseModel):
    """
    Description:
    ---------------
        Модель для хранения структурированного представления исходного кода.

    Args:
    ---------------
        metadata: Метаданные кода (язык, путь к файлу и т.д.)
        imports: Список импортов
        classes: Список классов
        functions: Список функций верхнего уровня (для языков без классов)
        enums: Список перечислений
        interfaces: Список интерфейсов (для ООП-языков)
        constants: Список констант верхнего уровня

    Examples:
    ---------------
        >>> code_structure = CodeStructure(
        ...     metadata={"language": "JAVA", "file_path": "UserController.java"},
        ...     imports=[ImportInfo(module="java.util.List", line=1)],
        ...     classes=[ClassInfo(...)],
        ...     functions=[],
        ...     enums=[],
        ...     interfaces=[],
        ...     constants=[]
        ... )
    """
    metadata: Dict[str, Any]
    imports: List[ImportInfo] = []
    classes: List[ClassInfo] = []
    functions: List[MethodInfo] = []
    enums: List[Any] = []
    interfaces: List[Any] = []
    constants: List[Any] = []

    def to_dict(self) -> Dict[str, Any]:
        """
        Description:
        ---------------
            Преобразует структуру кода в словарь.

        Returns:
        ---------------
            Dict[str, Any]: Структура кода в виде словаря.
        """
        return self.model_dump()

    def to_json(self) -> str:
        """
        Description:
        ---------------
            Преобразует структуру кода в JSON-строку.

        Returns:
        ---------------
            str: Структура кода в виде JSON-строки.
        """
        import json
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CodeStructure':
        """
        Description:
        ---------------
            Создает структуру кода из словаря.

        Args:
        ---------------
            data: Словарь с данными структуры кода.

        Returns:
        ---------------
            CodeStructure: Экземпляр класса CodeStructure.
        """
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> 'CodeStructure':
        """
        Description:
        ---------------
            Создает структуру кода из JSON-строки.

        Args:
        ---------------
            json_str: JSON-строка с данными структуры кода.

        Returns:
        ---------------
            CodeStructure: Экземпляр класса CodeStructure.
        """
        import json
        return cls.from_dict(json.loads(json_str))