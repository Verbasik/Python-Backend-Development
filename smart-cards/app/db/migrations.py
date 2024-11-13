# app/db/migrations.py
"""
Description:
    Модуль для применения миграций базы данных.
    Создает таблицу категорий и добавляет поле category_id в таблицу карточек.
"""

import sqlite3
from config.settings import settings


def apply_migrations() -> None:
    """
    Description:
        Применяет миграции для базы данных.
        Создает таблицу категорий и добавляет поле category_id в таблицу карточек.

    Raises:
        sqlite3.Error: В случае ошибок при работе с базой данных.
    """
    with sqlite3.connect(settings.DB_PATH) as conn:
        cursor = conn.cursor()

        # Создаем таблицу категорий, если она не существует
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT
            )
        ''')

        # Добавляем поле category_id в таблицу cards, если оно не существует
        cursor.execute('''
            PRAGMA foreign_keys = ON;
        ''')  # Включаем поддержку внешних ключей
        try:
            cursor.execute('''
                ALTER TABLE cards ADD COLUMN category_id INTEGER REFERENCES categories(id)
            ''')
        except sqlite3.OperationalError:
            # Если столбец уже существует, пропускаем
            pass
        
        conn.commit()