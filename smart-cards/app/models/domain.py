# app/models/domain.py
"""
Description:
    Модели данных для карточек.
"""

# Сторонние библиотеки
from pydantic import BaseModel
from typing import Optional


class CardBase(BaseModel):
    """
    Description:
        Базовая модель карточки.
        
    Attributes:
        front: Передняя сторона карточки
        back: Задняя сторона карточки
    """
    front: str
    back: str


class CardCreate(CardBase):
    """
    Description:
        Модель для создания карточки.
    """
    pass


class Card(CardBase):
    """
    Description:
        Полная модель карточки с идентификатором.
        
    Attributes:
        id: Уникальный идентификатор карточки
    """
    id: Optional[int] = None

    class Config:
        from_attributes = True
