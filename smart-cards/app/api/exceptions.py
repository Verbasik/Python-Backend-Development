# app/api/exceptions.py
"""
Description:
    Обработчики исключений для API.
"""

# Сторонние библиотеки
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse


async def http_exception_handler(
    request: Request,
    exc: HTTPException
) -> JSONResponse:
    """
    Description:
        Обрабатывает HTTP исключения и возвращает форматированный ответ.

    Args:
        request: Объект HTTP запроса
        exc: Объект исключения

    Returns:
        JSONResponse: Форматированный ответ с деталями ошибки
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail},
    )