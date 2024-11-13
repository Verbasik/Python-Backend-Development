# app/core/services.py
"""
Description:
    Бизнес-логика для работы с карточками.
"""

# Стандартные библиотеки
from typing import List, Optional

# Сторонние библиотеки
from fastapi import HTTPException

# Локальные модули
from models.domain import Card, Category, CardCreate, CategoryCreate
from db.repositories import CardRepository, CategoryRepository


class CardService:
    """
    Description:
        Сервис для работы с карточками.
        Реализует бизнес-логику и взаимодействие с репозиторием.
    """

    def __init__(self, card_repo: CardRepository, category_repo: CategoryRepository):
        """
        Args:
            card_repo: Репозиторий для работы с данными карточек
        """
        self.card_repo = card_repo
        self.category_repo = category_repo

    async def create_card(self, card: CardCreate) -> Card:
        """
        Description:
            Создает новую карточку.

        Args:
            card: Данные для создания карточки

        Returns:
            Card: Созданная карточка
        """
        return self.card_repo.create(Card(**card.dict()))

    async def get_cards(self) -> List[Card]:
        """
        Description:
            Получает список всех карточек.

        Returns:
            List[Card]: Список карточек
        """
        return self.card_repo.get_all()

    async def get_random_card(self) -> Card:
        """
        Description:
            Получает случайную карточку.

        Returns:
            Card: Случайная карточка

        Raises:
            HTTPException: Если карточки не найдены
        """
        card = self.card_repo.get_random()
        if not card:
            raise HTTPException(
                status_code=404,
                detail="Карточки не найдены"
            )
        return card
    
    async def delete_card(self, card_id: int) -> bool:
        """
        Description:
            Удаляет карточку по идентификатору.

        Args:
            card_id: Идентификатор карточки для удаления

        Returns:
            bool: True если карточка успешно удалена

        Raises:
            HTTPException: Если карточка не найдена или произошла ошибка при удалении
        """
        try:
            if self.card_repo.delete(card_id):
                return True
            raise HTTPException(
                status_code=404,
                detail=f"Карточка с ID {card_id} не найдена"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка при удалении карточки: {str(e)}"
            )
        
    async def create_category(self, category: CategoryCreate) -> Category:
        """
        Description:
            Создает новую категорию на основе переданных данных.

        Args:
            category: Данные для создания категории

        Returns:
            Category: Созданная категория с присвоенным ID
        """
        return self.category_repo.create(Category(**category.dict()))

    async def get_categories(self) -> List[Category]:
        """
        Description:
            Получает список всех категорий.

        Returns:
            List[Category]: Список всех категорий
        """
        return self.category_repo.get_all()

    async def get_cards_by_category(self, category_id: int) -> List[Card]:
        """
        Description:
            Получает список карточек по идентификатору категории.

        Args:
            category_id: Идентификатор категории для поиска карточек

        Returns:
            List[Card]: Список карточек, относящихся к категории
        """
        return self.card_repo.get_by_category(category_id)

    async def get_random_card_by_category(self, category_id: int) -> Card:
        """
        Description:
            Получает случайную карточку по идентификатору категории.

        Args:
            category_id: Идентификатор категории для поиска карточки

        Returns:
            Card: Случайная карточка из выбранной категории

        Raises:
            HTTPException: Если карточки в категории не найдены

        Examples:
            >>> card_service = CardService(card_repo, category_repo)
            >>> random_card = await card_service.get_random_card_by_category(1)
            >>> random_card.front
            'Random Front'
        """
        card = self.card_repo.get_random_by_category(category_id)
        if not card:
            raise HTTPException(
                status_code=404,
                detail=f"Карточки в категории {category_id} не найдены"
            )
        return card