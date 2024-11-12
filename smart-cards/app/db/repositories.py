# app/db/repositories.py
"""
Description:
    Репозиторий для работы с базой данных карточек.
"""

# Стандартные библиотеки
import sqlite3
from typing import List, Optional

# Локальные модули
from models.domain import Card


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
                'INSERT INTO cards (front, back) VALUES (?, ?)',
                (card.front, card.back)
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
            cards = cursor.execute('SELECT * FROM cards').fetchall()
            return [
                Card(id=card[0], front=card[1], back=card[2])
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


def init_db() -> None:
    """
    Description:
        Инициализирует базу данных, создавая необходимые таблицы.
    """
    db_path = "cards.db"
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                front TEXT NOT NULL,
                back TEXT NOT NULL
            )
        ''')
        conn.commit()