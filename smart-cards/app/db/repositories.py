# app/db/repositories.py
"""
Description:
    Репозиторий для работы с базой данных карточек.
"""

# Стандартные библиотеки
import sqlite3
from typing import List, Optional

# Локальные модули
from config.settings import settings
from models.domain import (
    Card,
    Category
)


class CardRepository:
    """
    Description:
        Репозиторий для работы с карточками в SQLite базе данных.
    """

    def __init__(self, db_path: str):
        """
        Args:
            db_path: Путь к файлу базы данных
        """
        self.db_path = db_path

    def create(self, card: Card) -> Card:
        """
        Description:
            Создает новую карточку в базе данных.

        Args:
            card: Данные карточки для создания

        Returns:
            Card: Созданная карточка с присвоенным ID
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO cards (front, back, category_id) VALUES (?, ?, ?)',
                (card.front, card.back, card.category_id)
            )
            conn.commit()
            card.id = cursor.lastrowid
            return card

    def get_all(self) -> List[Card]:
        """
        Description:
            Получает все карточки из базы данных.

        Returns:
            List[Card]: Список всех карточек
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cards = cursor.execute('''
                SELECT c.*, cat.name, cat.description 
                FROM cards c
                LEFT JOIN categories cat ON c.category_id = cat.id
            ''').fetchall()
            return [
                Card(
                    id=card[0],
                    front=card[1],
                    back=card[2],
                    category_id=card[3],
                    category=Category(
                        id=card[3],
                        name=card[4],
                        description=card[5]
                    ) if card[3] else None
                )
                for card in cards
            ]
        
    def get_random(self) -> Optional[Card]:
        """
        Description:
            Получает случайную карточку из базы данных.

        Returns:
            Optional[Card]: Случайная карточка или None, если база пуста
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            card = cursor.execute(
                'SELECT * FROM cards ORDER BY RANDOM() LIMIT 1'
            ).fetchone()
            return (
                Card(id=card[0], front=card[1], back=card[2])
                if card else None
            )
        
    def get_random_by_category(self, category_id: int) -> Optional[Card]:
        """
        Description:
            Получение случайной карточки из указанной категории
        
        Args:
            category_id: ID категории
            
        Returns:
            Optional[Card]: Случайная карточка или None, если карточек нет
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            card = cursor.execute('''
                SELECT c.*, cat.name as category_name, cat.description as category_description 
                FROM cards c
                LEFT JOIN categories cat ON c.category_id = cat.id
                WHERE c.category_id = ?
                ORDER BY RANDOM()
                LIMIT 1
            ''', (category_id,)).fetchone()
            
            if not card:
                return None
                
            return Card(
                id=card[0],
                front=card[1],
                back=card[2],
                category_id=card[3],
                category=Category(
                    id=card[3],
                    name=card[4],
                    description=card[5]
                ) if card[3] else None
            )

    def get_by_category(self, category_id: int) -> List[Card]:
        """
        Description:
            Получение всех карточек из указанной категории
        
        Args:
            category_id: ID категории
            
        Returns:
            List[Card]: Список карточек
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cards = cursor.execute('''
                SELECT c.*, cat.name as category_name, cat.description as category_description 
                FROM cards c
                LEFT JOIN categories cat ON c.category_id = cat.id
                WHERE c.category_id = ?
            ''', (category_id,)).fetchall()
            
            return [
                Card(
                    id=card[0],
                    front=card[1],
                    back=card[2],
                    category_id=card[3],
                    category=Category(
                        id=card[3],
                        name=card[4],
                        description=card[5]
                    ) if card[3] else None
                )
                for card in cards
            ]
        
    def delete(self, card_id: int) -> bool:
        """
        Description:
            Удаляет карточку из базы данных по идентификатору.

        Args:
            card_id: Идентификатор карточки для удаления

        Returns:
            bool: True если карточка была удалена, False если карточка не найдена
            
        Raises:
            sqlite3.Error: При ошибке работы с базой данных
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'DELETE FROM cards WHERE id = ?',
                (card_id,)
            )
            conn.commit()
            return cursor.rowcount > 0
        

class CategoryRepository:
    """
    Description:
        Репозиторий для работы с категориями в SQLite базе данных.
    """

    def __init__(self, db_path: str):
        """
        Description:
            Инициализирует репозиторий с путем к базе данных.

        Args:
            db_path: Путь к файлу базы данных
        """
        self.db_path = db_path

    def create(self, category: Category) -> Category:
        """
        Description:
            Создает новую категорию в базе данных.

        Args:
            category: Данные категории для создания

        Returns:
            Category: Созданная категория с присвоенным ID

        Examples:
            >>> category_repo = CategoryRepository("db.sqlite")
            >>> new_category = Category(name="Science", description="Science category")
            >>> created_category = category_repo.create(new_category)
            >>> created_category.id
            1
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO categories (name, description) VALUES (?, ?)',
                (category.name, category.description)
            )
            conn.commit()
            category.id = cursor.lastrowid
            return category
        
    def get_by_id(self, category_id: int) -> Optional[Category]:
        """
        Description:
            Получение категории по ID
        
        Args:
            category_id: ID категории
            
        Returns:
            Optional[Category]: Категория или None, если не найдена
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            category = cursor.execute('''
                SELECT c.*, COUNT(ca.id) as cards_count 
                FROM categories c 
                LEFT JOIN cards ca ON c.id = ca.category_id 
                WHERE c.id = ?
                GROUP BY c.id
            ''', (category_id,)).fetchone()
            
            if not category:
                return None
                
            return Category(
                id=category[0],
                name=category[1],
                description=category[2],
                cards_count=category[3]
            )

    def get_all(self) -> List[Category]:
        """
        Description:
            Получает все категории из базы данных.

        Returns:
            List[Category]: Список всех категорий

        Examples:
            >>> category_repo = CategoryRepository("db.sqlite")
            >>> all_categories = category_repo.get_all()
            >>> len(all_categories)
            5
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            categories = cursor.execute('''
                SELECT c.*, COUNT(ca.id) as cards_count 
                FROM categories c 
                LEFT JOIN cards ca ON c.id = ca.category_id 
                GROUP BY c.id
            ''').fetchall()
            return [
                Category(
                    id=cat[0], 
                    name=cat[1], 
                    description=cat[2],
                    cards_count=cat[3]
                )
                for cat in categories
            ]


def init_db() -> None:
    """
    Description:
        Инициализирует базу данных, создавая необходимые таблицы для карточек и категорий.
    """
    db_path = settings.DB_PATH

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Создаем таблицу категорий
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT
            )
        ''')
        
        # Создаем таблицу карточек с внешним ключом
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                front TEXT NOT NULL,
                back TEXT NOT NULL,
                category_id INTEGER,
                FOREIGN KEY (category_id) REFERENCES categories (id)
            )
        ''')
        conn.commit()