# app/main.py
"""
Description:
    Основной модуль FastAPI приложения для управления карточками.
    Содержит конфигурацию приложения и основные маршруты.
"""

# Стандартные библиотеки
from contextlib import asynccontextmanager
from typing import AsyncGenerator

# Сторонние библиотеки
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

# Локальные модули
from api.routes import router
from db.repositories import init_db
from db.migrations   import apply_migrations


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Description:
        Управляет жизненным циклом приложения.
        Инициализирует базу данных при запуске.

    Args:
        app: Экземпляр FastAPI приложения

    Yields:
        None
    """
    init_db()
    apply_migrations()
    yield


def create_application() -> FastAPI:
    """
    Description:
        Создает и конфигурирует экземпляр FastAPI приложения.

    Returns:
        FastAPI: Сконфигурированное приложение
    """
    application = FastAPI(
        title="Cards API",
        description="API для управления карточками",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # Подключаем маршруты API
    application.include_router(router, prefix="/api")
    
    # Настраиваем статические файлы и шаблоны
    application.mount(
        "/static",
        StaticFiles(directory="static"),
        name="static"
    )
    
    return application


app = create_application()
templates = Jinja2Templates(directory="templates")

# Добавляем обработчик корневого маршрута
@app.get("/")
async def root(request: Request):
    """
    Description:
        Отображает главную страницу приложения.

    Args:
        request: Объект запроса FastAPI

    Returns:
        TemplateResponse: Отрендеренный HTML шаблон
    """
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )