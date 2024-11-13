# app/models/domain.py
"""
Description:
    Модели данных для карточек.
"""

# Сторонние библиотеки
from pydantic import BaseModel, constr
from typing import Optional


class CategoryBase(BaseModel):
    """
    Description:
        Базовая модель категории.
        
    Attributes:
        name: Название категории
        description: Описание категории (необязательное)
    """
    name: str
    description: Optional[str] = None


class CategoryCreate(CategoryBase):
    """
    Description:
        Модель для создания категории.
        Наследуется от CategoryBase, используется при создании новых категорий.
    """
    pass


class Category(CategoryBase):
    """
    Description:
        Полная модель категории с идентификатором.
        
    Attributes:
        id: Уникальный идентификатор категории (необязательное)
    """
    id: Optional[int] = None

    class Config:
        from_attributes = True


class CardBase(BaseModel):
    """
    Description:
        Базовая модель карточки.
        
    Attributes:
        front: Передняя сторона карточки
        back: Задняя сторона карточки
        category_id: Уникальный идентификатор категории
    """
    front: str
    back: str
    category_id: Optional[int] = None


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
        category: Связь с категорией
    """
    id: Optional[int] = None
    category: Optional[Category] = None

    class Config:
        from_attributes = True
