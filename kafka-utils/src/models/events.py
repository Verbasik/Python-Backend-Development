# src/models/events.py
"""
Description:
    Модуль events.py определяет модели событий для системы. Модели включают базовые события и их расширенные версии,
    такие как TaskEvent для задач, SystemEvent для системных операций, KafkaEvent для операций Kafka и MetricsEvent 
    для сбора метрик. Эти модели обеспечивают унифицированное представление данных о событиях с атрибутами, такими как 
    идентификаторы, типы, уровни критичности и дополнительные метаданные, что позволяет гибко обрабатывать и логировать 
    различные виды событий в системе.
"""

from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field, validator
from uuid import UUID

class EventType(str, Enum):
    """
    Description:
        Типы событий в системе.

    Attributes:
        TASK_CREATED: Событие создания задачи.
        TASK_STARTED: Событие запуска задачи.
        TASK_COMPLETED: Событие завершения задачи.
        TASK_FAILED: Событие неудачного завершения задачи.
        TASK_CANCELLED: Событие отмены задачи.
        SYSTEM_ERROR: Системная ошибка.
        KAFKA_ERROR: Ошибка Kafka.
    """
    TASK_CREATED   = "task_created"
    TASK_STARTED   = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED    = "task_failed"
    TASK_CANCELLED = "task_cancelled"
    SYSTEM_ERROR   = "system_error"
    KAFKA_ERROR    = "kafka_error"

class EventSeverity(str, Enum):
    """
    Description:
        Уровни критичности событий.

    Attributes:
        DEBUG: Отладочный уровень.
        INFO: Информационный уровень.
        WARNING: Предупреждение.
        ERROR: Ошибка.
        CRITICAL: Критическая ошибка.
    """
    DEBUG    = "debug"
    INFO     = "info"
    WARNING  = "warning"
    ERROR    = "error"
    CRITICAL = "critical"

class BaseEvent(BaseModel):
    """
    Description:
        Базовая модель для всех событий.

    Attributes:
        event_id: Уникальный идентификатор события.
        event_type: Тип события.
        timestamp: Время события.
        service_name: Имя сервиса-источника события.
        severity: Уровень критичности.
    """
    event_id: UUID = Field(..., description="Уникальный идентификатор события")
    event_type: EventType = Field(..., description="Тип события")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Время события")
    service_name: str = Field(..., description="Имя сервиса-источника события")
    severity: EventSeverity = Field(default=EventSeverity.INFO, description="Уровень критичности")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }

class TaskEvent(BaseEvent):
    """
    Description:
        Модель события, связанного с задачей.

    Attributes:
        task_id: Идентификатор задачи.
        task_type: Тип задачи.
        status: Статус задачи.
        details: Детали события.
        metadata: Метаданные события.
    """
    task_id: UUID = Field(..., description="Идентификатор задачи")
    task_type: str = Field(..., description="Тип задачи")
    status: str = Field(..., description="Статус задачи")
    details: Optional[str] = Field(None, description="Детали события")
    metadata: Optional[Dict[str, Any]] = Field(default={}, description="Метаданные события")

class SystemEvent(BaseEvent):
    """
    Description:
        Модель системного события.

    Attributes:
        component: Компонент системы.
        action: Выполненное действие.
        status: Статус выполнения.
        details: Детали события.
        metadata: Метаданные события.
    """
    component: str = Field(..., description="Компонент системы")
    action: str = Field(..., description="Выполненное действие")
    status: str = Field(..., description="Статус выполнения")
    details: Optional[str] = Field(None, description="Детали события")
    metadata: Optional[Dict[str, Any]] = Field(default={}, description="Метаданные события")

class KafkaEvent(BaseEvent):
    """
    Description:
        Модель события, связанного с Kafka.

    Attributes:
        topic: Имя топика.
        partition: Номер партиции.
        offset: Оффсет сообщения.
        operation: Тип операции.
        status: Статус операции.
        error_details: Детали ошибки.
    """
    topic: str = Field(..., description="Имя топика")
    partition: Optional[int] = Field(None, description="Номер партиции")
    offset: Optional[int] = Field(None, description="Оффсет сообщения")
    operation: str = Field(..., description="Тип операции")
    status: str = Field(..., description="Статус операции")
    error_details: Optional[Dict[str, Any]] = Field(None, description="Детали ошибки")

class MetricsEvent(BaseEvent):
    """
    Description:
        Модель события с метриками.

    Attributes:
        metrics_type: Тип метрик.
        metrics: Значения метрик.
        interval: Интервал сбора метрик.
        tags: Теги метрик.
    """
    metrics_type: str = Field(..., description="Тип метрик")
    metrics: Dict[str, Any] = Field(..., description="Значения метрик")
    interval: str = Field(..., description="Интервал сбора метрик")
    tags: Optional[Dict[str, str]] = Field(default={}, description="Теги метрик")

    @validator('metrics')
    def validate_metrics(cls, v):
        """
        Description:
            Валидация метрик.

        Args:
            v: Значения метрик.

        Returns:
            Значения метрик.

        Raises:
            ValueError: Если значения метрик пусты.
        """
        if not v:
            raise ValueError("Метрики не могут быть пустыми")
        return v