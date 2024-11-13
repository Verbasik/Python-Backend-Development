# app/api/dependencies.py
"""
Description:
    Модуль зависимостей для внедрения зависимостей в маршруты API.
"""

# Локальные модули
from core.services import CardService
from db.repositories import CardRepository, CategoryRepository
from config.settings import settings


def get_card_repository() -> CardRepository:
    """
    Description:
        Создает экземпляр репозитория карточек, инициализируя его путем к базе данных.

    Returns:
        CardRepository: Инициализированный репозиторий для работы с карточками.

    Examples:
        >>> card_repo = get_card_repository()
        >>> isinstance(card_repo, CardRepository)
        True
    """
    return CardRepository(settings.DB_PATH)


def get_category_repository() -> CategoryRepository:
    """
    Description:
        Создает экземпляр репозитория категорий, инициализируя его путем к базе данных.

    Returns:
        CategoryRepository: Инициализированный репозиторий для работы с категориями.

    Examples:
        >>> category_repo = get_category_repository()
        >>> isinstance(category_repo, CategoryRepository)
        True
    """
    return CategoryRepository(settings.DB_PATH)


def get_card_service() -> CardService:
    """
    Description:
        Создает экземпляр сервиса карточек, внедряя репозитории карточек и категорий.

    Returns:
        CardService: Инициализированный сервис для работы с карточками и категориями.

    Examples:
        >>> card_service = get_card_service()
        >>> isinstance(card_service, CardService)
        True
    """
    card_repo = get_card_repository()
    category_repo = get_category_repository()
    
    return CardService(card_repo, category_repo)