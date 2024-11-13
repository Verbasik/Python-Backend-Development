# app/api/routes.py
"""
Description:
    Определение маршрутов API для работы с карточками.
"""

# Сторонние библиотеки
from fastapi import APIRouter, Depends, HTTPException
from typing import List

# Локальные модули
from models.domain import Card, Category, CardCreate, CategoryCreate
from core.services import CardService
from api.dependencies import get_card_service


router = APIRouter(tags=["cards"])


@router.post("/cards/", response_model=Card)
async def create_card(
    card: CardCreate,
    service: CardService = Depends(get_card_service)
) -> Card:
    """
    Description:
        Создает новую карточку.

    Args:
        card: Данные для создания карточки
        service: Сервис для работы с карточками

    Returns:
        Card: Созданная карточка

    Raises:
        HTTPException: При ошибке создания карточки
    """
    try:
        return await service.create_card(card)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при создании карточки: {str(e)}"
        )


@router.get("/cards/", response_model=List[Card])
async def get_cards(
    service: CardService = Depends(get_card_service)
) -> List[Card]:
    """
    Description:
        Получает список всех карточек.

    Args:
        service: Сервис для работы с карточками

    Returns:
        List[Card]: Список карточек

    Raises:
        HTTPException: При ошибке получения карточек
    """
    try:
        return await service.get_cards()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при получении карточек: {str(e)}"
        )


@router.get("/cards/random", response_model=Card)
async def get_random_card(
    service: CardService = Depends(get_card_service)
) -> Card:
    """
    Description:
        Получает случайную карточку.

    Args:
        service: Сервис для работы с карточками

    Returns:
        Card: Случайная карточка

    Raises:
        HTTPException: Если карточки не найдены или при ошибке
    """
    try:
        return await service.get_random_card()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при получении случайной карточки: {str(e)}"
        )


@router.delete("/cards/{card_id}")
async def delete_card(
    card_id: int,
    service: CardService = Depends(get_card_service)
) -> dict:
    """
    Description:
        Удаляет карточку по идентификатору.

    Args:
        card_id: Идентификатор карточки для удаления
        service: Сервис для работы с карточками

    Returns:
        dict: Сообщение об успешном удалении

    Raises:
        HTTPException: Если карточка не найдена или при ошибке удаления
    """
    try:
        await service.delete_card(card_id)
        return {"message": f"Карточка с ID {card_id} успешно удалена"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при удалении карточки: {str(e)}"
        )

    
@router.post("/categories/", response_model=Category)
async def create_category(
    category: CategoryCreate,
    service: CardService = Depends(get_card_service)
) -> Category:
    """
    Description:
        Создает новую категорию.

    Args:
        category: Данные для создания категории
        service: Сервис для работы с категориями

    Returns:
        Category: Созданная категория

    Raises:
        HTTPException: При ошибке создания категории
    """
    try:
        return await service.create_category(category)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при создании категории: {str(e)}"
        )


@router.get("/categories/", response_model=List[Category])
async def get_categories(
    service: CardService = Depends(get_card_service)
) -> List[Category]:
    """
    Description:
        Получает список всех категорий.

    Args:
        service: Сервис для работы с категориями

    Returns:
        List[Category]: Список категорий

    Raises:
        HTTPException: При ошибке получения категорий
    """
    try:
        return await service.get_categories()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при получении категорий: {str(e)}"
        )


@router.get("/categories/{category_id}/cards", response_model=List[Card])
async def get_cards_by_category(
    category_id: int,
    service: CardService = Depends(get_card_service)
) -> List[Card]:
    """
    Description:
        Получает список карточек по идентификатору категории.

    Args:
        category_id: Идентификатор категории для поиска карточек
        service: Сервис для работы с карточками

    Returns:
        List[Card]: Список карточек категории

    Raises:
        HTTPException: При ошибке получения карточек категории
    """
    try:
        return await service.get_cards_by_category(category_id)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при получении карточек категории: {str(e)}"
        )


@router.get("/categories/{category_id}/cards/random", response_model=Card)
async def get_random_card_by_category(
    category_id: int,
    service: CardService = Depends(get_card_service)
) -> Card:
    """
    Description:
        Получает случайную карточку по идентификатору категории.

    Args:
        category_id: Идентификатор категории для поиска случайной карточки
        service: Сервис для работы с карточками

    Returns:
        Card: Случайная карточка из категории

    Raises:
        HTTPException: При ошибке получения случайной карточки из категории
    """
    try:
        return await service.get_random_card_by_category(category_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при получении случайной карточки из категории: {str(e)}"
        )