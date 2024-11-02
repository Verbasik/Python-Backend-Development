# src/config/user_config.py
"""
Description:
    Модуль user_config.py реализует пользовательскую конфигурацию Kafka через класс CustomKafkaConfig, 
    который расширяет абстрактный базовый класс KafkaConfigABC. Этот класс позволяет пользователям определять собственные 
    топики, пользователей и конфигурации, включая разрешения, настройки топиков и консьюмеров. CustomKafkaConfig 
    автоматически создает дефолтные разрешения и конфигурации, если они не указаны, что обеспечивает гибкость и удобство 
    настройки Kafka в соответствии с потребностями системы.

    Примеры использования включают создание собственных топиков и пользователей с помощью классов Enum, что делает 
    процесс настройки более интуитивным и безопасным.
"""

from typing import Dict, Set, Any, Optional, Type
from enum import Enum
from .config_types import KafkaConfigABC
from .constants import (
    KafkaPermissions
)

class CustomKafkaConfig(KafkaConfigABC):
    """
    Description:
      Пользовательская конфигурация Kafka.
      Позволяет определить собственные топики, пользователей и настройки.

    Examples:
        >>> class MyTopics(str, Enum):
        ...     USER_CREATED = "users.events.created"
        ...     USER_UPDATED = "users.events.updated"
        
        >>> class MyUsers(str, Enum):
        ...     USER_SERVICE = "user-service"
        ...     NOTIFICATION_SERVICE = "notification-service"
        
        >>> config = CustomKafkaConfig(
        ...     topics_enum=MyTopics,
        ...     users_enum=MyUsers
        ... )
    """
    
    def __init__(
        self,
        topics_enum: Type[Enum],
        users_enum: Type[Enum],
        permissions: Optional[Dict[str, Dict[str, Set[str]]]] = None,
        topic_configs: Optional[Dict[str, Dict[str, Any]]] = None,
        consumer_configs: Optional[Dict[str, Dict[str, Any]]] = None
    ):
        """
        Args:
            topics_enum: Enum класс с топиками
            users_enum: Enum класс с пользователями
            permissions: Маппинг разрешений (опционально)
            topic_configs: Конфигурации топиков (опционально)
            consumer_configs: Конфигурации консьюмеров (опционально)
        """
        self.topics_enum = topics_enum
        self.users_enum = users_enum
        
        # Создаем базовые маппинги из enum классов
        self._topics = {t.name: t.value for t in topics_enum}
        self._users = {u.name: u.value for u in users_enum}
        
        # Создаем дефолтные разрешения если не указаны
        self._permissions = permissions or self._create_default_permissions()
        
        # Создаем дефолтные конфигурации топиков если не указаны
        self._topic_configs = topic_configs or self._create_default_topic_configs()
        
        # Создаем дефолтные конфигурации консьюмеров если не указаны
        self._consumer_configs = consumer_configs or self._create_default_consumer_configs()
    
    def get_topics(self) -> Dict[str, str]:
        return self._topics
    
    def get_users(self) -> Dict[str, str]:
        return self._users
    
    def get_permissions(self) -> Dict[str, Dict[str, Set[str]]]:
        return self._permissions
    
    def get_topic_configs(self) -> Dict[str, Dict[str, Any]]:
        return self._topic_configs
    
    def get_consumer_configs(self) -> Dict[str, Dict[str, Any]]:
        return self._consumer_configs
    
    def _create_default_permissions(self) -> Dict[str, Dict[str, Set[str]]]:
        """Создает дефолтные разрешения на основе пользователей и топиков"""
        permissions = {}
        for user in self._users.values():
            permissions[user] = {}
            for topic in self._topics.values():
                # Базовые права для всех
                topic_permissions = {KafkaPermissions.READ.value}
                
                # Если пользователь похож на продюсера
                if 'service' in user.lower() or 'producer' in user.lower():
                    topic_permissions.add(KafkaPermissions.WRITE.value)
                
                # Если пользователь похож на консьюмера
                if 'consumer' in user.lower():
                    topic_permissions.update({
                        KafkaPermissions.AUTO_COMMIT_OFFSET.value,
                        KafkaPermissions.OFFSET_MANAGEMENT.value
                    })
                
                permissions[user][topic] = topic_permissions
                
        return permissions
    
    def _create_default_topic_configs(self) -> Dict[str, Dict[str, Any]]:
        """Создает дефолтные конфигурации топиков"""
        return {
            topic: {
                "retention.ms": 7 * 24 * 60 * 60 * 1000,  # 7 дней
                "num.partitions": 12,
                "cleanup.policy": "delete"
            }
            for topic in self._topics.values()
        }
    
    def _create_default_consumer_configs(self) -> Dict[str, Dict[str, Any]]:
        """Создает дефолтные конфигурации консьюмеров"""
        return {
            user: {
                "auto_offset_reset": "earliest",
                "enable_auto_commit": True,
            }
            for user in self._users.values()
        }