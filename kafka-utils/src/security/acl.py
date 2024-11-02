# src/security/acl.py
"""
Description:
    Модуль acl.py предоставляет инструменты для управления и проверки прав доступа (ACL) в Kafka. 
    Класс AclManager управляет правами доступа, включая инициализацию кэша ACL, проверку доступа пользователей 
    к топикам, и создание ACL bindings на основе конфигурации. Класс AclEnforcer используется для проверки доступа 
    к топикам с возможностью выброса исключений при отказе в доступе. Эти классы позволяют эффективно управлять 
    правами доступа и обеспечивать безопасность взаимодействий с компонентами Kafka.
"""

from typing import Dict, Set, List, Optional
from enum import Enum
import logging
from dataclasses import dataclass
from ..config.constants import (
    KafkaPermissions,
    KAFKA_ACL_MAPPINGS
)

class ResourceType(str, Enum):
    """Типы ресурсов Kafka для ACL."""
    TOPIC = "topic"
    GROUP = "group"
    CLUSTER = "cluster"
    TRANSACTIONAL_ID = "transactional_id"

@dataclass
class AclBinding:
    """Класс для представления привязки ACL."""
    resource_type: ResourceType
    resource_name: str
    principal: str
    permission_type: KafkaPermissions
    operation: str
    pattern_type: str = "literal"

class AclManager:
    """
    Менеджер для управления ACL в Kafka.
    """

    def __init__(self):
        """Инициализация менеджера ACL."""
        self.logger = logging.getLogger(__name__)
        self._acl_cache: Dict[str, Dict[str, Set[str]]] = {}
        self._initialize_acl_cache()

    def _initialize_acl_cache(self) -> None:
        """Инициализация кэша ACL из конфигурации."""
        self._acl_cache = KAFKA_ACL_MAPPINGS.copy()
        self.logger.info("ACL кэш инициализирован")

    def validate_access(
        self,
        principal: str,
        topic: str,
        required_permission: KafkaPermissions
    ) -> bool:
        """
        Проверка наличия прав доступа.

        Args:
            principal: Идентификатор пользователя/сервиса
            topic: Имя топика
            required_permission: Требуемое право доступа

        Returns:
            bool: True если доступ разрешен, False в противном случае
        """
        try:
            if principal not in self._acl_cache:
                self.logger.warning(f"Пользователь {principal} не найден в ACL")
                return False

            if topic not in self._acl_cache[principal]:
                self.logger.warning(
                    f"Топик {topic} не найден в ACL для пользователя {principal}"
                )
                return False

            has_permission = required_permission.value in self._acl_cache[principal][topic]
            if not has_permission:
                self.logger.warning(
                    f"Отказано в доступе: {principal} -> {topic} "
                    f"[{required_permission.value}]"
                )

            return has_permission

        except Exception as e:
            self.logger.error(f"Ошибка при проверке прав доступа: {str(e)}")
            return False

    def get_user_permissions(
        self,
        principal: str,
        topic: Optional[str] = None
    ) -> Dict[str, Set[str]]:
        """
        Получение прав доступа пользователя.

        Args:
            principal: Идентификатор пользователя/сервиса
            topic: Опциональное имя топика для фильтрации

        Returns:
            Dict[str, Set[str]]: Словарь прав доступа
        """
        try:
            if principal not in self._acl_cache:
                return {}

            if topic:
                return {
                    topic: self._acl_cache[principal].get(topic, set())
                }

            return self._acl_cache[principal]

        except Exception as e:
            self.logger.error(
                f"Ошибка при получении прав доступа для {principal}: {str(e)}"
            )
            return {}

    def create_acl_bindings(self) -> List[AclBinding]:
        """
        Создание списка ACL bindings на основе конфигурации.

        Returns:
            List[AclBinding]: Список ACL bindings
        """
        bindings = []
        try:
            for principal, topics in self._acl_cache.items():
                for topic, permissions in topics.items():
                    for permission in permissions:
                        binding = AclBinding(
                            resource_type=ResourceType.TOPIC,
                            resource_name=topic,
                            principal=f"User:{principal}",
                            permission_type=KafkaPermissions(permission),
                            operation="ALL"
                        )
                        bindings.append(binding)
            
            self.logger.info(f"Создано {len(bindings)} ACL bindings")
            return bindings

        except Exception as e:
            self.logger.error(f"Ошибка при создании ACL bindings: {str(e)}")
            return []

class AclEnforcer:
    """
    Класс для применения ACL правил.
    """

    def __init__(self):
        """Инициализация ACL enforcer."""
        self.acl_manager = AclManager()
        self.logger = logging.getLogger(__name__)

    def check_topic_access(
        self,
        principal: str,
        topic: str,
        required_permission: KafkaPermissions
    ) -> None:
        """
        Проверка доступа к топику с выбросом исключения при отказе.

        Args:
            principal: Идентификатор пользователя/сервиса
            topic: Имя топика
            required_permission: Требуемое право доступа

        Raises:
            PermissionError: Если доступ запрещен
        """
        if not self.acl_manager.validate_access(principal, topic, required_permission):
            error_msg = (
                f"Отказано в доступе: {principal} не имеет права "
                f"{required_permission.value} для топика {topic}"
            )
            self.logger.error(error_msg)
            raise PermissionError(error_msg)