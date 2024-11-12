# app/api/dependencies.py
"""
Description:
    Модуль зависимостей для внедрения зависимостей в маршруты API.
"""

# Локальные модули
from core.services import CardService
from db.repositories import CardRepository
from config.settings import settings


def get_card_repository() -> CardRepository:
    """
    Description:
        Создает экземпляр репозитория карточек.

    Returns:
        CardRepository: Инициализированный репозиторий
    """
    return CardRepository(settings.DB_PATH)


def get_card_service() -> CardService:
    """
    Description:
        Создает экземпляр сервиса карточек с внедренным репозиторием.

    Returns:
        CardService: Инициализированный сервис
    """
    repository = get_card_repository()
    return CardService(repository)