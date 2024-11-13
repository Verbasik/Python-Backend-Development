# Smart Cards (MVP)

![link](https://raw.githubusercontent.com/Verbasik/Python-Backend-Development/refs/heads/main/smart-cards/png/image.png)

Веб-приложение для создания и изучения карточек с поддержкой Markdown и LaTeX формул. Разработано специально для изучения научных дисциплин, где требуется работа с математическими формулами, химическими уравнениями и сложным форматированием текста.

## Основные возможности

- ✨ Поддержка Markdown для форматирования текста
- 🔢 Рендеринг LaTeX математических формул
- 🎯 Интуитивный интерфейс для создания и изучения карточек
- 📂 Организация карточек по категориям
- 🔍 Фильтрация и изучение карточек по категориям
- ⚡ Горячие клавиши для быстрой работы
- 🔄 Случайный порядок показа карточек
- 💾 Локальное хранение данных в SQLite

## Архитектура приложения

Приложение построено на принципах многослойной архитектуры с четким разделением ответственности:

```
app/
├── api/                 # API слой
│   ├── dependencies.py  # Внедрение зависимостей
│   ├── exceptions.py    # Обработка исключений
│   └── routes.py        # Маршруты API
├── config/              # Конфигурация
│   └── settings.py      # Настройки приложения
├── core/                # Бизнес-логика
│   └── services.py      # Сервисы
├── db/                  # Доступ к данным
│   ├── repositories.py  # Репозитории
│   └── migrations.py    # Миграции базы данных
├── models/              # Модели данных
│   └── domain.py        # Доменные модели
├── static/              # Статические файлы
│   ├── css/             # Стили
│   └── js/              # JavaScript
├── templates/           # HTML шаблоны
│   └── index.html       # Главная страница
└── utils/               # Утилиты
    └── logger.py        # Логирование
```

## Компоненты

### API Layer (app/api/)
- `routes.py`: Определение REST API эндпоинтов для карточек и категорий
- `dependencies.py`: Внедрение зависимостей через FastAPI
- `exceptions.py`: Централизованная обработка ошибок

### Core Layer (app/core/)
- `services.py`: Реализация бизнес-логики для карточек и категорий
- Асинхронная обработка операций
- Валидация бизнес-правил
- Управление категориями

### Data Layer (app/db/)
- `repositories.py`: Работа с SQLite через асинхронные операции
- Безопасная обработка SQL-запросов
- Управление жизненным циклом соединений
- `migrations.py`: Управление схемой базы данных

### Configuration (app/config/)
- `settings.py`: Управление настройками через Pydantic
- Поддержка переменных окружения
- Конфигурация режима отладки

### Models (app/models/)
- `domain.py`: Pydantic модели для валидации данных
- Поддержка сериализации/десериализации
- Документирование схемы данных
- Модели категорий и связей с карточками

## API Endpoints

### Категории

#### Создание категории
```http
POST /api/categories/
Content-Type: application/json

{
    "name": "string",
    "description": "string"
}
```

#### Получение всех категорий
```http
GET /api/categories/
```

#### Получение карточек категории
```http
GET /api/categories/{category_id}/cards
```

#### Получение случайной карточки из категории
```http
GET /api/categories/{category_id}/cards/random
```

### Карточки

#### Создание карточки
```http
POST /api/cards/
Content-Type: application/json

{
    "front": "string",
    "back": "string",
    "category_id": "integer"
}
```

#### Получение всех карточек
```http
GET /api/cards/
```

#### Получение случайной карточки
```http
GET /api/cards/random
```

#### Удаление карточки
```http
DELETE /api/cards/{card_id}
```

## Модели данных

### CategoryBase
```python
class CategoryBase(BaseModel):
    """Базовая модель категории"""
    name: constr(min_length=1, max_length=50)
    description: Optional[str] = None

class CategoryCreate(CategoryBase):
    """Модель для создания категории"""
    pass

class Category(CategoryBase):
    """Полная модель категории"""
    id: Optional[int] = None
    cards_count: Optional[int] = 0

    class Config:
        from_attributes = True
```

### CardBase
```python
class CardBase(BaseModel):
    """Базовая модель карточки"""
    front: constr(min_length=1)
    back: constr(min_length=1)
    category_id: Optional[int] = None

class CardCreate(CardBase):
    """Модель для создания карточки"""
    pass

class Card(CardBase):
    """Полная модель карточки"""
    id: Optional[int] = None
    category: Optional[Category] = None

    class Config:
        from_attributes = True
```

## База данных

### Схема
```sql
CREATE TABLE categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT
);

CREATE TABLE cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    front TEXT NOT NULL,
    back TEXT NOT NULL,
    category_id INTEGER REFERENCES categories(id)
);
```

## Конфигурация

Приложение использует Pydantic для управления конфигурацией:

```python
class Settings(BaseSettings):
    DB_PATH: str = "cards.db"
    API_PREFIX: str = "/api"
    DEBUG: bool = False

    class Config:
        env_file = ".env"
```

## Горячие клавиши

- `Space/Enter` - перевернуть карточку
- `ArrowRight/n` - следующая карточка
- `Delete` - удалить текущую карточку

## Поддерживаемый синтаксис

### Markdown
- Заголовки (h1-h6)
- Списки (маркированные и нумерованные)
- Выделение текста (жирный, курсив)
- Код (inline и блоки)
- Ссылки
- Изображения

### LaTeX
- Inline math: `$формула$`
- Display math: `$$формула$$`
- Поддержка всех стандартных команд LaTeX
- Автоматическое масштабирование формул

## Зависимости

### Основные
- Python 3.7+
- FastAPI
- Uvicorn
- SQLite3
- Pydantic
- Jinja2

### Frontend
- MathJax
- Marked
- ES6+ JavaScript

## Установка и запуск

1. Клонируйте репозиторий:
    ```bash
    git clone <git link>
    cd smart-cards
    ```

2. Создайте виртуальное окружение:
    ```bash
    # Linux/macOS
    python -m venv venv
    source venv/bin/activate
    
    # Windows
    python -m venv venv
    venv\Scripts\activate
    ```

3. Установите зависимости:
    ```bash
    pip install -r requirements.txt
    ```

4. Запустить сервер:
   ```bash
   python main.py
   ```

5. Открыть в браузере: http://localhost:8000

## Системные требования

- Python 3.7+
- Современный веб-браузер с поддержкой ES6
- SQLite 3

## Безопасность

- Санитизация markdown-контента
- Защита от SQL-инъекций через параметризованные запросы
- Валидация входных данных через Pydantic

## Ограничения

- Локальное хранение данных в SQLite
- Отсутствие системы авторизации
- Ограниченные возможности поиска и фильтрации

## Планы по развитию

- [✅] Добавить возможность добавлять карточки по категориям

## Лицензия

MIT

## Вклад в проект

Приветствуются pull request'ы и issues с предложениями по улучшению функциональности, исправлению ошибок или добавлению новых возможностей.
