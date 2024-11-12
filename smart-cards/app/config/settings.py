# app/config/settings.py
"""
Description:
    Конфигурационные настройки приложения.
"""

# Сторонние библиотеки
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Description:
        Класс настроек приложения.
        
    Attributes:
        DB_PATH: Путь к файлу базы данных
        API_PREFIX: Префикс для API маршрутов
        DEBUG: Режим отладки
    """
    DB_PATH: str = "cards.db"
    API_PREFIX: str = "/api"
    DEBUG: bool = False

    class Config:
        env_file = ".env"


settings = Settings()