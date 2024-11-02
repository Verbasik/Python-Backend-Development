# Инструкция по использованию Kafka Utils Library

## Оглавление
1. [Установка и настройка](#установка-и-настройка)
2. [Конфигурация окружения](#конфигурация-окружения)
3. [Настройка топиков и пользователей](#настройка-топиков-и-пользователей)
4. [Интеграция с FastAPI](#интеграция-с-fastapi)
5. [Рекомендации для Production](#рекомендации-для-production)

## Установка и настройка

### 1. Установка библиотеки
```bash
pip install kafka-async-lib
```

### 2. Создание базовой структуры проекта
```
my_service/
├── app/
│   ├── main.py                # FastAPI приложение
│   ├── core/
│   │   ├── config.py          # Настройки приложения
│   │   └── kafka_config.py    # Конфигурация Kafka
│   └── services/
│       └── message_handler.py # Обработка сообщений
├── .env                       # Переменные окружения
└── requirements.txt           # Зависимости
```

## Конфигурация окружения

### 1. Настройка .env файла
```env
# =============================================
# Основные настройки подключения
# =============================================

# Список брокеров Kafka (рекомендуется минимум 3 для production)
KAFKA_BOOTSTRAP_SERVERS='localhost:9092'

# Уникальное имя сервиса (используется для ACL)
SERVICE_NAME='my-service'

# =============================================
# Настройки безопасности
# =============================================

# Протокол безопасности:
# - PLAINTEXT: для разработки
# - SSL: с шифрованием
# - SASL_PLAINTEXT: только аутентификация
# - SASL_SSL: аутентификация + шифрование (для production)
KAFKA_SECURITY_PROTOCOL='PLAINTEXT'

# SASL настройки (для production)
KAFKA_SASL_MECHANISM='PLAIN'
# KAFKA_USERNAME='service-user'
# KAFKA_PASSWORD='secret-password'
# KAFKA_SSL_CAFILE='/path/to/ca.pem'

# =============================================
# Настройки Consumer
# =============================================

# Стратегия чтения при первом подключении
# - earliest: чтение с начала (рекомендуется)
# - latest: только новые сообщения
KAFKA_AUTO_OFFSET_RESET='earliest'

# Максимальный интервал между poll() (5 минут)
KAFKA_MAX_POLL_INTERVAL_MS='300000'

# Размер батча для чтения
KAFKA_MAX_POLL_RECORDS='500'

# Автоматический коммит
KAFKA_ENABLE_AUTO_COMMIT='true'

# =============================================
# Production настройки (опционально)
# =============================================

# KAFKA_RETRY_BACKOFF_MS='500'          # Задержка ретраев
# KAFKA_COMPRESSION_TYPE='gzip'         # Сжатие
# KAFKA_BATCH_SIZE='16384'              # Размер батча
# KAFKA_LINGER_MS='10'                  # Задержка отправки
# KAFKA_REQUEST_TIMEOUT_MS='30000'      # Таймаут
# KAFKA_MAX_IN_FLIGHT_REQUESTS='5'      # Параллельные запросы
```

## Настройка топиков и пользователей

### 1. Создание конфигурации Kafka (app/core/kafka_config.py)
```python
from enum import Enum
from dataclasses import dataclass
from kafka_utils.config import CustomKafkaConfig
from kafka_utils.config.constants import KafkaPermissions

# Определение топиков
class ServiceTopics(str, Enum):
    """
    Description:
        Перечисление доступных топиков Kafka.

    CopyAttributes:
        REQUEST:  Топик для входящих запросов.
        RESPONSE: Топик для исходящих ответов.

    Examples:
        >>> topic = ServiceTopics.REQUEST
        >>> print(topic.value)
        'service.request'
    """
    REQUEST  = "service.request"
    RESPONSE = "service.response"

# Определение пользователей
class ServiceUsers(str, Enum):
    """
    Description:
        Перечисление пользователей сервиса.

    CopyAttributes:
        SERVICE:  Основной сервис.
        EXTERNAL: Внешний сервис.

    Examples:
        >>> user = ServiceUsers.SERVICE
        >>> print(user.value)
        'my-service'
    """
    SERVICE  = "my-service"
    EXTERNAL = "external-service"

@dataclass
class KafkaConfigHolder:
    """
    Description:
        Держатель конфигурации Kafka.
        
    CopyArgs:
        config: Экземпляр CustomKafkaConfig.

    Examples:
        >>> kafka_config = CustomKafkaConfig(...)
        >>> holder = KafkaConfigHolder(kafka_config)
    """
    config: CustomKafkaConfig

# Настройка прав доступа
service_permissions = {
    ServiceUsers.SERVICE.value: {
        ServiceTopics.REQUEST.value: {
            KafkaPermissions.READ.value,
            KafkaPermissions.WRITE.value,
            KafkaPermissions.AUTO_COMMIT_OFFSET.value
        },
        ServiceTopics.RESPONSE.value: {
            KafkaPermissions.READ.value,
            KafkaPermissions.AUTO_COMMIT_OFFSET.value
        }
    }
}

# Конфигурация топиков
topic_configs = {
    ServiceTopics.REQUEST.value: {
        "retention.ms": 7 * 24 * 60 * 60 * 1000,  # 7 дней
        "num.partitions": 12,
        "cleanup.policy": "delete"
    },
    ServiceTopics.RESPONSE.value: {
        "retention.ms": 7 * 24 * 60 * 60 * 1000,
        "num.partitions": 12,
        "cleanup.policy": "delete"
    }
}

# Создание конфигурации
kafka_config = CustomKafkaConfig(
    topics_enum=ServiceTopics,
    users_enum=ServiceUsers,
    permissions=service_permissions,
    topic_configs=topic_configs
)

kafka_config_holder = KafkaConfigHolder(kafka_config)
```

### 2. Настройка конфигурации приложения (app/core/config.py)
```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from kafka_utils.config.settings import KafkaSettings
from .kafka_config import kafka_config_holder

class KafkaEnvSettings(BaseSettings):
    """
    Description:
        Настройки Kafka из переменных окружения.
    
    Attributes:
        KAFKA_BOOTSTRAP_SERVERS: Список брокеров Kafka.
        KAFKA_SECURITY_PROTOCOL: Протокол безопасности (default: "PLAINTEXT").
        KAFKA_SASL_MECHANISM: Механизм аутентификации SASL.
        KAFKA_USERNAME: Имя пользователя для аутентификации.
        KAFKA_PASSWORD: Пароль для аутентификации.
        KAFKA_SSL_CAFILE: Путь к CA-файлу для SSL.
        KAFKA_AUTO_OFFSET_RESET: Стратегия сброса смещения.
        KAFKA_MAX_POLL_INTERVAL_MS: Максимальный интервал опроса.
        KAFKA_MAX_POLL_RECORDS: Максимальное количество записей за опрос.
        KAFKA_ENABLE_AUTO_COMMIT: Включение автоматической фиксации смещения.
    """
    KAFKA_BOOTSTRAP_SERVERS: str
    KAFKA_SECURITY_PROTOCOL: str = "PLAINTEXT"
    KAFKA_SASL_MECHANISM: Optional[str] = None
    KAFKA_USERNAME: Optional[str] = None
    KAFKA_PASSWORD: Optional[str] = None
    KAFKA_SSL_CAFILE: Optional[str] = None
    KAFKA_AUTO_OFFSET_RESET: str = "earliest"
    KAFKA_MAX_POLL_INTERVAL_MS: str = "300000"
    KAFKA_MAX_POLL_RECORDS: str = "500"
    KAFKA_ENABLE_AUTO_COMMIT: str = "true"
    
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=True
    )

class Settings(BaseSettings):
    """
    Description:
        Основные настройки приложения.
    
    Attributes:
        SERVICE_NAME: Имя сервиса.
        _kafka_settings: Кэшированные настройки Kafka.
    """
    SERVICE_NAME: str
    _kafka_settings: Optional[KafkaSettings] = None
    
    @property
    def kafka(self) -> KafkaSettings:
        """
        Description:
            Инициализация настроек Kafka.
        
        Returns:
            KafkaSettings: Настройки Kafka.
        
        Examples:
            >>> settings = Settings(SERVICE_NAME="my-service")
            >>> kafka_settings = settings.kafka
        """
        if self._kafka_settings is None:
            kafka_env = KafkaEnvSettings()
            self._kafka_settings = KafkaSettings(
                kafka_config=kafka_config_holder.config,
                KAFKA_BOOTSTRAP_SERVERS=kafka_env.KAFKA_BOOTSTRAP_SERVERS,
                KAFKA_SECURITY_PROTOCOL=kafka_env.KAFKA_SECURITY_PROTOCOL,
                KAFKA_SASL_MECHANISM=kafka_env.KAFKA_SASL_MECHANISM,
                KAFKA_USERNAME=kafka_env.KAFKA_USERNAME,
                KAFKA_PASSWORD=kafka_env.KAFKA_PASSWORD,
                SERVICE_NAME=self.SERVICE_NAME,
                CONSUMER_CONFIG={
                    "auto_offset_reset": kafka_env.KAFKA_AUTO_OFFSET_RESET,
                    "max_poll_interval_ms": int(kafka_env.KAFKA_MAX_POLL_INTERVAL_MS),
                    "max_poll_records": int(kafka_env.KAFKA_MAX_POLL_RECORDS),
                    "enable_auto_commit": kafka_env.KAFKA_ENABLE_AUTO_COMMIT.lower() == "true"
                }
            )
        return self._kafka_settings

settings = Settings()
```

## Интеграция с FastAPI

### 1. Создание основного приложения (app/main.py)
```python
import asyncio
import logging
from fastapi import FastAPI
from contextlib import asynccontextmanager

from kafka_utils.core import KafkaAdmin, KafkaProducer, KafkaConsumer
from kafka_utils.monitoring import HealthCheck, KafkaMetricsCollector

from core.config import settings
from core.kafka_config import ServiceTopics

# Глобальные компоненты
kafka_admin       = None
kafka_producer    = None
kafka_consumer    = None
health_checker    = None
metrics_collector = None
background_tasks  = []

async def initialize_components() -> None:
    """
    Description:
        Инициализация компонентов приложения.
    
    Raises:
        Exception: При ошибке инициализации компонентов.
    
    Examples:
        >>> async def startup():
        ...     await initialize_components()
    """
    global kafka_admin, kafka_producer, kafka_consumer, health_checker, metrics_collector
    
    try:
        # Admin client
        kafka_admin = KafkaAdmin(settings.kafka)
        await kafka_admin.connect()
        await kafka_admin.ensure_topics()
        
        # Producer
        kafka_producer = KafkaProducer(settings.kafka)
        await kafka_producer.connect()
        
        # Consumer
        kafka_consumer = KafkaConsumer(
            settings=settings.kafka,
            topics=[ServiceTopics.RESPONSE.value],
            group_id="my-service-group"
        )
        await kafka_consumer.connect()
        
        # Мониторинг
        health_checker = HealthCheck(settings.kafka)
        metrics_collector = KafkaMetricsCollector()
        
        # Запуск фоновых задач
        background_tasks.extend([
            asyncio.create_task(process_messages()),
            asyncio.create_task(periodic_health_check())
        ])
        
    except Exception as e:
        logging.error(f"Ошибка инициализации: {str(e)}")
        await cleanup_components()
        raise

async def cleanup_components() -> None:
    """
    Description:
        Очистка ресурсов приложения.
    
    Examples:
        >>> async def shutdown():
        ...     await cleanup_components()
    """
    for task in background_tasks:
        task.cancel()
        
    if kafka_producer:
        await kafka_producer.disconnect()
    if kafka_consumer:
        await kafka_consumer.disconnect()
    if kafka_admin:
        await kafka_admin.disconnect()

async def process_messages() -> None:
    """
    Description:
        Обработка сообщений из Kafka.
    
    Raises:
        Exception: При критической ошибке обработки сообщений.
    """
    try:
        async for message in kafka_consumer.consume_messages():
            try:
                logging.info(f"Получено сообщение: {message}")

                metrics_collector.record_metric(
                    "messages_processed",
                    1,
                    {"topic": message["_metadata"]["topic"]}
                )
            except Exception as e:
                logging.error(f"Ошибка обработки: {str(e)}")
                
                metrics_collector.record_metric(
                    "processing_errors",
                    1,
                    {"error_type": type(e).__name__}
                )
    except Exception as e:
        logging.error(f"Критическая ошибка: {str(e)}")
        raise

async def periodic_health_check() -> None:
    """
    Description:
        Периодическая проверка здоровья сервиса.
    """
    while True:
        try:
            health_status = await health_checker.check_health()
            logging.info(f"Статус здоровья: {health_status['status']}")
            await asyncio.sleep(60)  # Проверка каждую минуту
        except Exception as e:
            logging.error(f"Ошибка проверки здоровья: {str(e)}")
            await asyncio.sleep(5)   # Повторная попытка через 5 секунд

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Description:
        Управление жизненным циклом приложения FastAPI.
    
    Args:
        app: Экземпляр FastAPI приложения.
    """
    await initialize_components()
    yield
    await cleanup_components()

# Создание приложения
app = FastAPI(lifespan=lifespan)

@app.get("/actuator/metrics")
async def get_metrics() -> Dict[str, Any]:
    """
    Description:
        Получение метрик приложения.
    
    Returns:
        Dict[str, Any]: Словарь метрик.
    """
    return metrics_collector.get_metrics()

@app.get("/actuator/health")
async def healthcheck() -> Dict[str, Any]:
    """
    Description:
        Проверка здоровья приложения.
    
    Returns:
        Dict[str, Any]: Статус здоровья приложения.
    """
    return await health_checker.check_health()
```

## Рекомендации для Production

### 1. Безопасность
- Включите SASL_SSL для шифрования и аутентификации
- Используйте сильные пароли и регулярно их меняйте
- Настройте ACL для минимально необходимых прав
- Храните чувствительные данные в защищенном хранилище

### 2. Надежность
- Настройте репликацию топиков (рекомендуется min.insync.replicas=2)
- Включите идемпотентность для producer
- Используйте механизм ретраев для обработки ошибок
- Настройте мониторинг и алертинг

### 3. Производительность
- Оптимизируйте размер батчей
- Настройте compression.type='gzip'
- Мониторьте lag консьюмеров
- Настройте подходящее количество партиций

### 4. Мониторинг
- Настройте логирование с ротацией
- Добавьте алерты на критические метрики
- Мониторьте использование ресурсов
- Регулярно проверяйте метрики производительности

### 5. Масштабирование
- Используйте несколько инстансов за балансировщиком
- Правильно настройте группы потребителей
- Мониторьте нагрузку и масштабируйте при необходимости
