# src/config/config_types.py
"""
Description:
    Модуль config_types.py определяет абстрактные типы конфигураций и перечислений для использования в системе настройки. 
    Он включает базовый класс BaseEnum для создания настраиваемых перечислений и абстрактный базовый класс KafkaConfigABC, 
    предназначенный для реализации конфигураций Kafka. KafkaConfigABC содержит методы для получения мапинга топиков, 
    пользователей, разрешений и конфигураций топиков, обеспечивая гибкость и безопасность при настройке прав доступа и 
    управлении конфигурациями Kafka.
"""

from typing import Dict, Set, Any
from enum import Enum
from abc import ABC, abstractmethod

class BaseEnum(str, Enum):
    """Базовый класс для всех перечислений"""
    @classmethod
    def values(cls) -> Set[str]:
        return {item.value for item in cls}

class KafkaConfigABC(ABC):
    """Абстрактный базовый класс для конфигурации Kafka"""
    @abstractmethod
    def get_topics(self) -> Dict[str, str]:
        """Возвращает мапинг топиков"""
        pass
    
    @abstractmethod
    def get_users(self) -> Dict[str, str]:
        """Возвращает мапинг пользователей"""
        pass
    
    @abstractmethod
    def get_permissions(self) -> Dict[str, Dict[str, Set[str]]]:
        """Возвращает мапинг разрешений"""
        pass
    
    @abstractmethod
    def get_topic_configs(self) -> Dict[str, Dict[str, Any]]:
        """Возвращает конфигурации топиков"""
        pass