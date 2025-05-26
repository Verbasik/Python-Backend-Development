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
from s3.client import minio_client, MinioException


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

    # Тестируем существование бакета
    bucket_name = "ktalk"
    if minio_client.is_bucket_exists(bucket_name):
        print(f"Bucket '{bucket_name}' exists")

    # Тестируем существование директории
    directory_path = "doc"
    if minio_client.is_directory_exists(bucket_name, directory_path):
        print(f"Directory '{directory_path}' exists in bucket '{bucket_name}'")

    # Пример скачивания файлов из директории
    try:
        downloaded_files = minio_client.download_files_from_directory(
            bucket_name=bucket_name,
            directory_path=directory_path,
            preserve_structure=True
        )
        print(f"Downloaded {len(downloaded_files)} files:")
        for file_path in downloaded_files:
            print(f"  - {file_path}")
    except MinioException as e:
        print(f"Error: {e}")
    
    # Опционально: очистка temp директории
    minio_client.clear_temp_directory()