# src/config/constants.py
"""
Description:
  Модуль содержит константы для конфигурации и работы с Kafka.
  Определяет топики, пользователей, права доступа и базовые настройки.
"""

from enum import Enum
from typing import Dict, Set, Any

class KafkaTopics(str, Enum):
    """
    Description:
      Примеры топиков для демонстрации. 
      При использовании библиотеки необходимо определить свои топики на уровне сервиса.
    
    Examples:
        >>> class ServiceKafkaTopics(str, Enum):
        ...     USER_CREATED = "users.events.created"
        ...     USER_UPDATED = "users.events.updated"
    """
    SERVICE_REQUEST = "service.default.request"
    SERVICE_RESPONSE = "service.default.response"


class KafkaUsers(str, Enum):
    """
    Description:
      Примеры пользователей для демонстрации.
      При использовании библиотеки необходимо определить своих пользователей на уровне сервиса.
    
    Examples:
        >>> class ServiceKafkaUsers(str, Enum):
        ...     USER_SERVICE = "user-service"
        ...     NOTIFICATION_SERVICE = "notification-service"
    """
    PRODUCER_SERVICE = "producer-service"
    CONSUMER_SERVICE = "consumer-service"


class KafkaPermissions(str, Enum):
    """
    Description:
      Перечисление прав доступа ACL в Kafka.
      
    Attributes:
        READ: Право на чтение топиков.
        WRITE: Право на запись в топики.
        AUTO_COMMIT_OFFSET: Право на автоматический коммит оффсетов.
        OFFSET_MANAGEMENT: Право на управление оффсетами.
    """
    READ = "read"
    WRITE = "write"
    AUTO_COMMIT_OFFSET = "auto-commit-offset"
    OFFSET_MANAGEMENT = "offset-management"


# Маппинг ACL для разных пользователей и топиков
KAFKA_ACL_MAPPINGS: Dict[str, Dict[str, Set[str]]] = {
    KafkaUsers.PRODUCER_SERVICE.value: {
        KafkaTopics.SERVICE_REQUEST.value: {
            KafkaPermissions.READ.value,
            KafkaPermissions.WRITE.value
        },
        KafkaTopics.SERVICE_RESPONSE.value: {
            KafkaPermissions.READ.value,
            KafkaPermissions.AUTO_COMMIT_OFFSET.value,
            KafkaPermissions.OFFSET_MANAGEMENT.value
        }
    },
    KafkaUsers.CONSUMER_SERVICE.value: {
        KafkaTopics.SERVICE_REQUEST.value: {
            KafkaPermissions.READ.value,
            KafkaPermissions.AUTO_COMMIT_OFFSET.value,
            KafkaPermissions.OFFSET_MANAGEMENT.value
        },
        KafkaTopics.SERVICE_RESPONSE.value: {
            KafkaPermissions.READ.value,
            KafkaPermissions.WRITE.value
        }
    }
}

# Конфигурация топиков Kafka
KAFKA_TOPIC_CONFIGS: Dict[str, Dict[str, Any]] = {
    KafkaTopics.SERVICE_REQUEST.value: {
        "retention.ms": 7 * 24 * 60 * 60 * 1000,  # 7 дней в миллисекундах
        "num.partitions": 12,
        "cleanup.policy": "delete"
    },
    KafkaTopics.SERVICE_RESPONSE.value: {
        "retention.ms": 7 * 24 * 60 * 60 * 1000,  # 7 дней в миллисекундах
        "num.partitions": 12,
        "cleanup.policy": "delete"
    }
}

# Базовая конфигурация Kafka
DEFAULT_KAFKA_CONFIG: Dict[str, Any] = {
    "compression_type": "gzip",                   # Тип сжатия сообщений
    "enable_idempotence": True,                   # Включение идемпотентности
    "acks": "all",                                # Подтверждение записи от всех реплик
    "max_in_flight_requests_per_connection": 5,   # Максимальное количество неподтвержденных запросов
    "retry_backoff_ms": 500,                      # Задержка между повторными попытками
    "request_timeout_ms": 30000,                  # Таймаут запроса (30 секунд)
}

# Конфигурация групп потребителей
CONSUMER_GROUP_CONFIGS: Dict[str, Dict[str, Any]] = {
    KafkaUsers.PRODUCER_SERVICE.value: {
        "auto_offset_reset": "earliest",          # Начинать чтение с начала топика
        "enable_auto_commit": True,               # Включение автоматического коммита
    },
    KafkaUsers.CONSUMER_SERVICE.value: {
        "auto_offset_reset": "earliest",
        "enable_auto_commit": True,
    }
}