# main.py - основной файл приложения
# Импорты для библиотек Python стандартной библиотеки
import os
import sqlite3
import random
from contextlib import asynccontextmanager

# Импорты сторонних библиотек
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional

# Создаем контекстный менеджер жизненного цикла
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Description:
        Контекстный менеджер для управления жизненным циклом приложения FastAPI.

    Yields:
        None
    """
    init_db()
    yield

# Инициализация приложения FastAPI
app = FastAPI(lifespan=lifespan)

# Монтируем статические файлы и шаблоны
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Модели данных
class CardBase(BaseModel):
    front: str
    back: str

class CardCreate(CardBase):
    pass

class Card(CardBase):
    id: Optional[int] = None

    class Config:
        from_attributes = True

# База данных
def init_db() -> None:
    """
    Description:
        Инициализирует базу данных SQLite с таблицей для карточек.

    Returns:
        None
    """
    conn = sqlite3.connect('cards.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            front TEXT NOT NULL,
            back TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# API эндпоинты
@app.get("/")
async def read_root(request: Request):
    """
    Description:
        Обрабатывает корневой запрос и возвращает главную страницу.

    Args:
        request: Объект запроса

    Returns:
        Шаблон главной страницы
    """
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/cards/", response_model=Card)
async def create_card(card: CardCreate) -> Card:
    """
    Description:
        Создает новую карточку в базе данных.

    Args:
        card: Объект CardCreate с данными для создания новой карточки

    Returns:
        Созданный объект Card
    """
    conn = sqlite3.connect('cards.db')
    c = conn.cursor()
    c.execute('INSERT INTO cards (front, back) VALUES (?, ?)', (card.front, card.back))
    conn.commit()
    new_id = c.lastrowid
    conn.close()
    return Card(id=new_id, front=card.front, back=card.back)

@app.get("/api/cards/", response_model=List[Card])
async def get_cards() -> List[Card]:
    """
    Description:
        Возвращает список всех карточек из базы данных.

    Returns:
        Список объектов Card
    """
    conn = sqlite3.connect('cards.db')
    c = conn.cursor()
    cards = c.execute('SELECT * FROM cards').fetchall()
    conn.close()
    return [Card(id=card[0], front=card[1], back=card[2]) for card in cards]

@app.get("/api/cards/random", response_model=Card)
async def get_random_card() -> Card:
    """
    Description:
        Возвращает случайную карточку из базы данных.

    Returns:
        Объект Card

    Raises:
        HTTPException: Если карточки не найдены
    """
    conn = sqlite3.connect('cards.db')
    c = conn.cursor()
    card = c.execute('SELECT * FROM cards ORDER BY RANDOM() LIMIT 1').fetchone()
    conn.close()
    if not card:
        raise HTTPException(status_code=404, detail="No cards found")
    return Card(id=card[0], front=card[1], back=card[2])

@app.delete("/api/cards/{card_id}")
async def delete_card(card_id: int) -> dict:
    """
    Description:
        Удаляет карточку по идентификатору.

    Args:
        card_id: Идентификатор карточки для удаления

    Returns:
        Словарь с сообщением об успешном удалении

    Raises:
        HTTPException: Если карточка не найдена
    """
    conn = sqlite3.connect('cards.db')
    c = conn.cursor()
    c.execute('DELETE FROM cards WHERE id = ?', (card_id,))
    affected_rows = conn.total_changes
    conn.commit()
    conn.close()
    if affected_rows == 0:
        raise HTTPException(status_code=404, detail="Card not found")
    return {"message": "Card deleted"}

# Обработка ошибок
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Description:
        Обрабатывает исключения HTTP и возвращает их в виде JSON.

    Args:
        request: Объект запроса
        exc: Исключение HTTP

    Returns:
        JSON-ответ с кодом ошибки и сообщением
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail},
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)