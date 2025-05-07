# app/main.py
"""
Описание программного модуля:
-----------------------------
Данный модуль является точкой входа для запуска сервиса валидации документации в формате AsciiDoc. 
Здесь настраивается FastAPI-приложение, добавляется поддержка CORS, регистрируются маршруты API 
и определяется корневой маршрут.

Функциональное назначение:
---------------------------
Модуль предоставляет REST API для автоматической проверки документации в формате AsciiDoc. 
Он позволяет загружать файлы, выполнять их анализ и получать результаты валидации. 
Также здесь настроена поддержка CORS для работы с внешними клиентами.
"""

# Импорты стандартной библиотеки Python
import uvicorn

# Импорты сторонних библиотек
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Импорты внутренних модулей
from controllers.validation_controller import router as validation_router


# Создание экземпляра FastAPI
app = FastAPI(
    title="AsciiDoc Validator",
    description="Сервис валидации документации в формате AsciiDoc",
    version="0.1.0",
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Регистрация маршрутов
app.include_router(validation_router, prefix="/api/v1", tags=["validation"])


@app.get("/")
async def root() -> dict:
    """
    Description:
    ---------------
        Корневой маршрут API.

    Returns:
    ---------------
        dict: Информация о состоянии сервиса.

    Examples:
    ---------------
        >>> GET /
        {
            "service": "AsciiDoc Validator",
            "status": "running",
            "version": "0.1.0"
        }
    """
    return {
        "service": "AsciiDoc Validator",
        "status": "running",
        "version": "0.1.0",
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)