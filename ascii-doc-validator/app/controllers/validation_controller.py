# app/controllers/validation_controller.py
"""
Описание программного модуля:
-----------------------------
Данный модуль содержит маршруты API для валидации документации в формате AsciiDoc. 
Маршрут `/validate` принимает файл документации, проверяет его синтаксис, парсит содержимое, 
выполняет валидацию на основе набора правил и возвращает отчет в запрошенном формате.

Функциональное назначение:
---------------------------
Модуль предназначен для предоставления REST API для автоматической проверки документации. 
Он позволяет загружать файлы AsciiDoc, выполнять их анализ и получать результаты в виде 
JSON-отчета или краткой сводки.
"""

# Импорты стандартной библиотеки Python
import os
import json

# Импорты сторонних библиотек
from fastapi import (
    APIRouter,
    File,
    Request,
    UploadFile,
    Form,
    HTTPException,
    Depends,
)  # Для создания API и обработки запросов
from fastapi.responses import JSONResponse
from typing import Optional

# Импорты внутренних сервисов
from app.services.documentation_parser import DocumentationParser
from app.services.validation_rule_engine import ValidationRuleEngine
from app.services.report_generator import ReportGenerator
from app.config.configuration_manager import ConfigurationManager
from app.services.validators.syntax_validator import SyntaxValidator
from app.services.source_code_analyzer import SourceCodeAnalyzer
from app.services.code_documentation_matcher import CodeDocumentationMatcher
from app.models.validation_report import IssueType, ValidationStatus
from app.services.project_documentation_manager import ProjectDocumentationManager
from app.services.project_code_documentation_matcher import ProjectCodeDocumentationMatcher

router = APIRouter()

# Создаем экземпляры сервисов
config_manager       = ConfigurationManager()
doc_parser           = DocumentationParser()
rule_engine          = ValidationRuleEngine()
report_generator     = ReportGenerator()
source_code_analyzer = SourceCodeAnalyzer()
code_doc_matcher     = CodeDocumentationMatcher(source_code_analyzer)


@router.post("/validate")
async def validate_documentation(
    file: UploadFile = File(...),
    format: Optional[str] = Form("json"),
) -> JSONResponse:
    """
    Description:
    ---------------
        Валидирует документацию в формате AsciiDoc.

    Args:
    ---------------
        file: Файл документации в формате AsciiDoc (.adoc или .asciidoc).
        format: Формат возвращаемого отчета ("json" или "summary").

    Returns:
    ---------------
        JSONResponse: Ответ с результатами валидации.

    Raises:
    ---------------
        HTTPException: Если файл имеет неподдерживаемый формат или указан неверный формат отчета.

    Examples:
    ---------------
        >>> POST /validate
        >>> Content-Type: multipart/form-data
        >>> Body:
        >>>     file: example.adoc
        >>>     format: json
        >>> Response:
        {
            "validation_id": "12345",
            "documentation_source": "example.adoc",
            ...
        }
    """
    # Проверяем расширение файла
    if not file.filename.endswith((".adoc", ".asciidoc")):
        raise HTTPException(
            status_code=400,
            detail="Поддерживаются только файлы .adoc или .asciidoc",
        )

    # Читаем содержимое файла
    content = await file.read()
    content_str = content.decode("utf-8")

    # Проверяем синтаксис документации
    syntax_valid, errors = doc_parser.validate_syntax(content_str)
    if not syntax_valid:
        return JSONResponse(
            status_code=400,
            content={"error": "Ошибка синтаксиса AsciiDoc", "details": errors},
        )

    # Парсим документацию
    parsed_doc = doc_parser.parse(content_str)

    # Валидируем документацию
    validation_report = rule_engine.validate(parsed_doc, file.filename)

    # Возвращаем отчет в запрошенном формате
    if format.lower() == "json":
        return JSONResponse(
            content=json.loads(report_generator.generate_json(validation_report)),
            status_code=200
        )
    elif format.lower() == "summary":
        return JSONResponse(
            content=report_generator.generate_summary(validation_report),
            status_code=200,
        )
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Неподдерживаемый формат отчета: {format}",
        )
    
@router.post("/validate-with-code")
async def validate_documentation_with_code(
    doc_file: UploadFile = File(...),
    code_file: UploadFile = File(...),
    format: Optional[str] = Form("json"),
) -> JSONResponse:
    """
    Description:
    ---------------
        Валидирует документацию в формате AsciiDoc, сопоставляя её с исходным кодом.

    Args:
    ---------------
        doc_file: Файл документации в формате AsciiDoc (.adoc или .asciidoc).
        code_file: Файл исходного кода (.java, .py и т.д.).
        format: Формат возвращаемого отчета ("json" или "summary").

    Returns:
    ---------------
        JSONResponse: Ответ с результатами валидации.

    Raises:
    ---------------
        HTTPException: Если файл имеет неподдерживаемый формат или указан неверный формат отчета.

    Examples:
    ---------------
        >>> POST /validate-with-code
        >>> Content-Type: multipart/form-data
        >>> Body:
        >>>     doc_file: example.adoc
        >>>     code_file: Example.java
        >>>     format: json
        >>> Response:
        {
            "validation_id": "12345",
            "documentation_source": "example.adoc",
            ...
        }
    """
    # Проверяем расширение файла документации
    if not doc_file.filename.endswith((".adoc", ".asciidoc")):
        raise HTTPException(
            status_code=400,
            detail="Документация должна быть в формате .adoc или .asciidoc",
        )
    
    # Читаем содержимое файла документации
    doc_content = await doc_file.read()
    doc_content_str = doc_content.decode("utf-8")
    
    # Проверяем синтаксис документации
    syntax_valid, errors = doc_parser.validate_syntax(doc_content_str)
    if not syntax_valid:
        return JSONResponse(
            status_code=400,
            content={"error": "Ошибка синтаксиса AsciiDoc", "details": errors},
        )
    
    # Парсим документацию
    parsed_doc = doc_parser.parse(doc_content_str)

    # # ДЛЯ ОТЛАДКИ
    # print("Структура документации:", json.dumps(parsed_doc, indent=2, ensure_ascii=False, default=str))
    
    # Создаем временные файлы для кода и документации
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(code_file.filename)[1]) as temp_code_file:
        code_content = await code_file.read()
        temp_code_file.write(code_content)
        temp_code_path = temp_code_file.name
    
    try:
        # Анализируем исходный код
        code_structure = source_code_analyzer.analyze_file(temp_code_path)
        
        # Сравниваем документацию с исходным кодом
        api_issues = code_doc_matcher.match_api_endpoints(code_structure, parsed_doc)
        undocumented_issues = code_doc_matcher.find_undocumented_methods(code_structure, parsed_doc)
        missing_methods_issues = code_doc_matcher.find_documented_but_missing_methods(code_structure, parsed_doc)
        
        # Объединяем результаты проверки
        all_issues = api_issues + undocumented_issues + missing_methods_issues
        
        # Валидируем документацию по стандартным правилам
        standard_validation = rule_engine.validate(parsed_doc, doc_file.filename)
        
        # Добавляем новые проблемы к стандартному отчету
        for issue in all_issues:
            standard_validation.issues.append(issue)
        
        # Обновляем сводку и статус
        standard_validation.summary.total_issues += len(all_issues)
        
        # Если найдены проблемы типа SEMANTIC, устанавливаем статус INVALID
        if any(issue.type == IssueType.SEMANTIC for issue in all_issues):
            standard_validation.status = ValidationStatus.INVALID
        
        # Возвращаем отчет в запрошенном формате
        if format.lower() == "json":
            return JSONResponse(
                content=json.loads(report_generator.generate_json(standard_validation)),
                status_code=200
            )
        elif format.lower() == "summary":
            return JSONResponse(
                content=report_generator.generate_summary(standard_validation),
                status_code=200,
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Неподдерживаемый формат отчета: {format}",
            )
    
    finally:
        # Удаляем временный файл
        os.unlink(temp_code_path)

@router.post("/validate-project")
async def validate_project(
    code_dir_path: str = Form(...),
    docs_dir_path: str = Form(...),
    format: Optional[str] = Form("json"),
) -> JSONResponse:
    """
    Description:
    ---------------
        Валидирует проект, сопоставляя исходный код из указанной директории 
        с документацией в формате AsciiDoc из другой указанной директории.

    Args:
    ---------------
        code_dir_path: Путь к директории с исходным кодом проекта.
        docs_dir_path: Путь к директории с документацией в формате AsciiDoc (.adoc).
        format: Формат возвращаемого отчета ("json" или "summary").

    Returns:
    ---------------
        JSONResponse: Ответ с результатами валидации проекта.

    Raises:
    ---------------
        HTTPException: Если директории не существуют или указан неверный формат отчета.
    """
    # Проверяем существование директорий
    if not os.path.isdir(code_dir_path):
        raise HTTPException(
            status_code=400,
            detail=f"Директория с исходным кодом не найдена: {code_dir_path}",
        )
    
    if not os.path.isdir(docs_dir_path):
        raise HTTPException(
            status_code=400,
            detail=f"Директория с документацией не найдена: {docs_dir_path}",
        )
    
    # Анализируем директорию с исходным кодом
    code_structures = source_code_analyzer.analyze_directory(code_dir_path, recursive=True)
    
    # Создаем объект ProjectDocumentationManager для работы с документацией
    doc_manager = ProjectDocumentationManager(docs_dir_path)
    
    # Анализируем директорию с документацией
    doc_structures = doc_manager.parse_documentation_directory()
    
    # Сопоставляем код и документацию
    project_matcher = ProjectCodeDocumentationMatcher(source_code_analyzer)
    validation_report = project_matcher.match_project(code_structures, doc_structures)
    
    # Возвращаем отчет в запрошенном формате
    if format.lower() == "json":
        return JSONResponse(
            content=json.loads(report_generator.generate_project_json(validation_report)),
            status_code=200
        )
    elif format.lower() == "summary":
        return JSONResponse(
            content=report_generator.generate_project_summary(validation_report),
            status_code=200,
        )
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Неподдерживаемый формат отчета: {format}",
        )
    
# Модифицированная версия эндпоинта для работы с путями
@router.post("/validate-project-paths")
async def validate_project_paths(
    request: Request,
    code_dir_path: str = Form(...),
    docs_dir_path: str = Form(...),
    format: Optional[str] = Form("json"),
) -> JSONResponse:
    """
    Description:
    ---------------
        Валидирует проект по указанным путям к директориям с кодом и документацией.

    Args:
    ---------------
        request: Запрос FastAPI.
        code_dir_path: Путь к директории с исходным кодом проекта.
        docs_dir_path: Путь к директории с документацией в формате AsciiDoc (.adoc).
        format: Формат возвращаемого отчета ("json" или "summary").

    Returns:
    ---------------
        JSONResponse: Ответ с результатами валидации проекта.

    Raises:
    ---------------
        HTTPException: Если директории не существуют или указан неверный формат отчета.
    """
    # Проверяем существование директорий
    if not os.path.isdir(code_dir_path):
        raise HTTPException(
            status_code=400,
            detail=f"Директория с исходным кодом не найдена: {code_dir_path}",
        )
    
    if not os.path.isdir(docs_dir_path):
        raise HTTPException(
            status_code=400,
            detail=f"Директория с документацией не найдена: {docs_dir_path}",
        )
    
    try:
        # Анализируем структуру проекта
        project_structure = source_code_analyzer.analyze_project(code_dir_path, docs_dir_path)
        
        # Создаем сопоставитель кода и документации проекта
        project_matcher = ProjectCodeDocumentationMatcher(source_code_analyzer)
        
        # Выполняем сопоставление и валидацию
        validation_report = project_matcher.match_project(
            project_structure.code_structures, 
            project_structure.doc_structures
        )
        
        # Возвращаем отчет в запрошенном формате
        if format.lower() == "json":
            return JSONResponse(
                content=json.loads(report_generator.generate_project_json(validation_report)),
                status_code=200
            )
        elif format.lower() == "summary":
            return JSONResponse(
                content=report_generator.generate_project_summary(validation_report),
                status_code=200,
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Неподдерживаемый формат отчета: {format}",
            )
    
    except Exception as e:
        # Логирование ошибки
        print(f"Ошибка при валидации проекта: {str(e)}")
        
        # Возвращаем сообщение об ошибке
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при валидации проекта: {str(e)}",
        )