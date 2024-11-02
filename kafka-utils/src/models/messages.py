# src/models/messages.py
"""
Description:
    Модуль messages.py определяет модели сообщений для системы, которые используются для обмена данными между 
    компонентами. Основные модели включают типы сообщений для запросов и ответов по генерации документации, обновлений 
    статуса задач, а также уведомлений об ошибках. Эти модели предоставляют структуру для унифицированного представления 
    сообщений с атрибутами, такими как идентификаторы, статусы, детали и метаданные, что облегчает взаимодействие 
    и обработку данных в распределенной системе.
"""

from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field, validator
from uuid import UUID

class MessageType(str, Enum):
    """
    Description:
        Типы сообщений в системе.

    Attributes:
        DOC_GENERATION_REQUEST: Запрос на генерацию документации.
        DOC_GENERATION_RESPONSE: Ответ от сервиса генерации документации.
        DOC_GENERATION_STATUS: Обновление статуса задачи генерации документации.
        ERROR_NOTIFICATION: Уведомление об ошибке.
    """
    DOC_GENERATION_REQUEST  = "doc_generation_request"
    DOC_GENERATION_RESPONSE = "doc_generation_response"
    DOC_GENERATION_STATUS   = "doc_generation_status"
    ERROR_NOTIFICATION      = "error_notification"

class TaskStatus(str, Enum):
    """
    Description:
        Статусы задач в системе.

    Attributes:
        PENDING: Задача ожидает обработки.
        IN_PROGRESS: Задача в процессе обработки.
        COMPLETED: Задача успешно завершена.
        FAILED: Задача завершилась с ошибкой.
        CANCELLED: Задача отменена.
    """
    PENDING     = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED   = "completed"
    FAILED      = "failed"
    CANCELLED   = "cancelled"

class BaseMessage(BaseModel):
    """
    Description:
        Базовая модель для всех сообщений.

    Attributes:
        message_id: Уникальный идентификатор сообщения.
        message_type: Тип сообщения.
        timestamp: Время создания сообщения.
        version: Версия формата сообщения.
        correlation_id: ID для связывания сообщений.
    """
    message_id: UUID = Field(..., description="Уникальный идентификатор сообщения")
    message_type: MessageType = Field(..., description="Тип сообщения")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Время создания сообщения")
    version: str = Field(default="1.0", description="Версия формата сообщения")
    correlation_id: Optional[UUID] = Field(None, description="ID для связывания сообщений")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }

class DocumentGenerationRequest(BaseMessage):
    """
    Description:
        Модель запроса на генерацию документации.

    Attributes:
        task_id: Идентификатор задачи.
        jira_task_id: ID задачи в Jira.
        source_data: Исходные данные для генерации.
        parameters: Дополнительные параметры.
        priority: Приоритет задачи (0-10).
    """
    task_id: UUID = Field(..., description="Идентификатор задачи")
    jira_task_id: str = Field(..., description="ID задачи в Jira")
    source_data: Dict[str, Any] = Field(..., description="Исходные данные для генерации")
    parameters: Optional[Dict[str, Any]] = Field(default={}, description="Дополнительные параметры")
    priority: int = Field(default=0, ge=0, le=10, description="Приоритет задачи (0-10)")

    @validator('source_data')
    def validate_source_data(cls, v):
        """
        Description:
            Валидация исходных данных.

        Args:
            v: Исходные данные.

        Returns:
            Исходные данные.

        Raises:
            ValueError: Если в исходных данных отсутствуют обязательные поля.
        """
        required_fields = ['title', 'description']
        for field in required_fields:
            if field not in v:
                raise ValueError(f"Отсутствует обязательное поле: {field}")
        return v

class DocumentGenerationResponse(BaseMessage):
    """
    Description:
        Модель ответа от сервиса генерации документации.

    Attributes:
        task_id: Идентификатор задачи.
        status: Статус выполнения задачи.
        result: Результат генерации.
        errors: Список ошибок.
        completion_percentage: Процент выполнения.
    """
    task_id: UUID = Field(..., description="Идентификатор задачи")
    status: TaskStatus = Field(..., description="Статус выполнения задачи")
    result: Optional[Dict[str, Any]] = Field(None, description="Результат генерации")
    errors: Optional[List[str]] = Field(default=[], description="Список ошибок")
    completion_percentage: float = Field(
        default=0.0, 
        ge=0.0, 
        le=100.0, 
        description="Процент выполнения"
    )

class StatusUpdate(BaseMessage):
    """
    Description:
        Модель обновления статуса задачи.

    Attributes:
        task_id: Идентификатор задачи.
        status: Новый статус задачи.
        details: Детали статуса.
        progress: Прогресс выполнения в процентах.
    """
    task_id: UUID = Field(..., description="Идентификатор задачи")
    status: TaskStatus = Field(..., description="Новый статус задачи")
    details: Optional[str] = Field(None, description="Детали статуса")
    progress: float = Field(
        default=0.0, 
        ge=0.0, 
        le=100.0, 
        description="Прогресс выполнения в процентах"
    )

class ErrorNotification(BaseMessage):
    """
    Description:
        Модель уведомления об ошибке.

    Attributes:
        task_id: Идентификатор задачи.
        error_code: Код ошибки.
        error_message: Описание ошибки.
        error_details: Детали ошибки.
        severity: Уровень критичности ошибки.
    """
    task_id: Optional[UUID] = Field(None, description="Идентификатор задачи")
    error_code: str = Field(..., description="Код ошибки")
    error_message: str = Field(..., description="Описание ошибки")
    error_details: Optional[Dict[str, Any]] = Field(None, description="Детали ошибки")
    severity: str = Field(default="ERROR", description="Уровень критичности ошибки")