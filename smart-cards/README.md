# Smart Cards (MVP)

![link](https://raw.githubusercontent.com/Verbasik/Python-Backend-Development/refs/heads/main/smart-cards/png/image.png)

Веб-приложение для создания и изучения карточек с поддержкой Markdown и LaTeX формул. Разработано специально для изучения научных дисциплин, где требуется работа с математическими формулами, химическими уравнениями и сложным форматированием текста.

## Основные возможности

- ✨ Поддержка Markdown для форматирования текста
- 🔢 Рендеринг LaTeX математических формул
- 🎯 Интуитивный интерфейс для создания и изучения карточек
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
│   └── repositories.py  # Репозитории
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
- `routes.py`: Определение REST API эндпоинтов
- `dependencies.py`: Внедрение зависимостей через FastAPI
- `exceptions.py`: Централизованная обработка ошибок

### Core Layer (app/core/)
- `services.py`: Реализация бизнес-логики
- Асинхронная обработка операций
- Валидация бизнес-правил

### Data Layer (app/db/)
- `repositories.py`: Работа с SQLite через асинхронные операции
- Безопасная обработка SQL-запросов
- Управление жизненным циклом соединений

### Configuration (app/config/)
- `settings.py`: Управление настройками через Pydantic
- Поддержка переменных окружения
- Конфигурация режима отладки

### Models (app/models/)
- `domain.py`: Pydantic модели для валидации данных
- Поддержка сериализации/десериализации
- Документирование схемы данных

## API Endpoints

### Карточки

#### Создание карточки
```http
POST /api/cards/
Content-Type: application/json

{
    "front": "string",
    "back": "string"
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

### CardBase
```python
class CardBase(BaseModel):
    """Базовая модель карточки"""
    front: str  # Передняя сторона
    back: str   # Задняя сторона

class CardCreate(CardBase):
    """Модель для создания карточки"""
    pass

class Card(CardBase):
    """Полная модель карточки"""
    id: Optional[int] = None

    class Config:
        from_attributes = True
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

- [ ] Добавить возможность добавлять карточки по категориям

## Лицензия

MIT

## Вклад в проект

Приветствуются pull request'ы и issues с предложениями по улучшению функциональности, исправлению ошибок или добавлению новых возможностей.
