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
from models.domain import Card, CardCreate
from db.repositories import CardRepository


class CardService:
    """
    Description:
        Сервис для работы с карточками.
        Реализует бизнес-логику и взаимодействие с репозиторием.
    """

    def __init__(self, repository: CardRepository):
        """
        Args:
            repository: Репозиторий для работы с данными карточек
        """
        self.repository = repository

    async def create_card(self, card: CardCreate) -> Card:
        """
        Description:
            Создает новую карточку.

        Args:
            card: Данные для создания карточки

        Returns:
            Card: Созданная карточка
        """
        return self.repository.create(Card(**card.dict()))

    async def get_cards(self) -> List[Card]:
        """
        Description:
            Получает список всех карточек.

        Returns:
            List[Card]: Список карточек
        """
        return self.repository.get_all()

    async def get_random_card(self) -> Card:
        """
        Description:
            Получает случайную карточку.

        Returns:
            Card: Случайная карточка

        Raises:
            HTTPException: Если карточки не найдены
        """
        card = self.repository.get_random()
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
            if self.repository.delete(card_id):
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