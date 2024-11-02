# src/monitoring/health.py
"""
Description:
    Модуль health.py предоставляет инструменты для мониторинга состояния и проверки здоровья компонентов Kafka. 
    Он включает классы HealthCheck для выполнения проверок состояния подключения к Kafka, топиков и прав доступа (ACL), 
    ComponentHealth для мониторинга отдельных компонентов, и KafkaHealthManager для координации и периодических 
    проверок здоровья всей системы. Эти инструменты обеспечивают своевременное выявление проблем с производительностью 
    и доступностью компонентов, что способствует устойчивой и эффективной работе системы.
"""

from typing import Dict, Any, List, Optional
from enum import Enum
import logging
import asyncio
from datetime import datetime
from aiokafka.admin import AIOKafkaAdminClient
from aiokafka.structs import TopicPartition
from ..config.settings import KafkaSettings
from ..config.constants import KafkaTopics

class HealthStatus(str, Enum):
    """
    Description:
        Статусы здоровья компонентов.

    Attributes:
        HEALTHY: Компонент здоров.
        DEGRADED: Компонент работает с пониженной производительностью.
        UNHEALTHY: Компонент не работает.
    """
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

class ComponentType(str, Enum):
    """
    Description:
        Типы проверяемых компонентов.

    Attributes:
        KAFKA_BROKER: Брокер Kafka.
        KAFKA_TOPIC: Топик Kafka.
        PRODUCER: Продьюсер Kafka.
        CONSUMER: Консьюмер Kafka.
        ACL: Права доступа (ACL).
    """
    KAFKA_BROKER = "kafka_broker"
    KAFKA_TOPIC = "kafka_topic"
    PRODUCER = "producer"
    CONSUMER = "consumer"
    ACL = "acl"

class HealthCheck:
    """
    Description:
        Класс для проверки здоровья компонентов Kafka.
    """

    def __init__(self, settings: KafkaSettings):
        """
        Description:
            Инициализация проверки здоровья.

        Args:
            settings: Настройки Kafka.
        """
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        self._last_check: Dict[str, datetime] = {}
        self._health_status: Dict[str, Dict[str, Any]] = {}

    async def check_health(self) -> Dict[str, Any]:
        """
        Description:
            Проверка здоровья всех компонентов.

        Returns:
            Dict[str, Any]: Статус здоровья системы.
        """
        try:
            # Проверяем все компоненты
            broker_status = await self._check_broker_connection()
            topics_status = await self._check_topics()
            acl_status = await self._check_acl()

            # Определяем общий статус
            overall_status = self._determine_overall_status([
                broker_status["status"],
                topics_status["status"],
                acl_status["status"]
            ])

            health_check_result = {
                "timestamp": datetime.utcnow().isoformat(),
                "status": overall_status,
                "components": {
                    ComponentType.KAFKA_BROKER: broker_status,
                    ComponentType.KAFKA_TOPIC: topics_status,
                    ComponentType.ACL: acl_status
                }
            }

            self._health_status = health_check_result
            return health_check_result

        except Exception as e:
            self.logger.error(f"Ошибка при проверке здоровья: {str(e)}")
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "status": HealthStatus.UNHEALTHY,
                "error": str(e)
            }

    async def _check_broker_connection(self) -> Dict[str, Any]:
        """
        Description:
            Проверка подключения к брокеру.

        Returns:
            Dict[str, Any]: Статус подключения.
        """
        try:
            admin_client = AIOKafkaAdminClient(
                bootstrap_servers=self.settings.KAFKA_BOOTSTRAP_SERVERS,
                client_id=f"{self.settings.SERVICE_NAME}-health-checker"
            )
            await admin_client.start()
            
            # Проверяем список топиков
            topics = await admin_client.list_topics()
            await admin_client.close()

            return {
                "status": HealthStatus.HEALTHY,
                "details": {
                    "broker_count": len(self.settings.KAFKA_BOOTSTRAP_SERVERS.split(",")),
                    "topics_count": len(topics)
                }
            }

        except Exception as e:
            self.logger.error(f"Ошибка подключения к брокеру: {str(e)}")
            return {
                "status": HealthStatus.UNHEALTHY,
                "error": str(e)
            }

    async def _check_topics(self) -> Dict[str, Any]:
        """
        Description:
            Проверка состояния топиков.

        Returns:
            Dict[str, Any]: Статус топиков.
        """
        try:
            admin_client = AIOKafkaAdminClient(
                bootstrap_servers=self.settings.KAFKA_BOOTSTRAP_SERVERS,
                client_id=f"{self.settings.SERVICE_NAME}-health-checker"
            )
            await admin_client.start()

            topics_status = {}
            all_topics = await admin_client.list_topics()

            for topic in KafkaTopics:
                if topic.value not in all_topics:
                    topics_status[topic.value] = {
                        "status": HealthStatus.UNHEALTHY,
                        "error": "Topic not found"
                    }
                    continue

                # Проверяем метаданные топика
                topic_metadata = await admin_client.describe_topics([topic.value])
                topic_info = topic_metadata[0]

                topics_status[topic.value] = {
                    "status": HealthStatus.HEALTHY,
                    "details": {
                        "partitions": len(topic_info.partitions),
                        "is_internal": topic_info.is_internal
                    }
                }

            await admin_client.close()

            # Определяем общий статус топиков
            overall_status = HealthStatus.HEALTHY
            if any(t["status"] == HealthStatus.UNHEALTHY for t in topics_status.values()):
                overall_status = HealthStatus.UNHEALTHY
            elif any(t["status"] == HealthStatus.DEGRADED for t in topics_status.values()):
                overall_status = HealthStatus.DEGRADED

            return {
                "status": overall_status,
                "topics": topics_status
            }

        except Exception as e:
            self.logger.error(f"Ошибка при проверке топиков: {str(e)}")
            return {
                "status": HealthStatus.UNHEALTHY,
                "error": str(e)
            }

    async def _check_acl(self) -> Dict[str, Any]:
        """
        Description:
            Проверка ACL.

        Returns:
            Dict[str, Any]: Статус ACL.
        """
        try:
            # Проверяем права доступа для текущего сервиса
            required_topics = set()
            for topic in KafkaTopics:
                permissions = self.settings.get_acl_permissions(topic.value)
                if permissions:
                    required_topics.add(topic.value)

            if not required_topics:
                return {
                    "status": HealthStatus.UNHEALTHY,
                    "error": "No ACL permissions configured"
                }

            return {
                "status": HealthStatus.HEALTHY,
                "details": {
                    "accessible_topics": list(required_topics)
                }
            }

        except Exception as e:
            self.logger.error(f"Ошибка при проверке ACL: {str(e)}")
            return {
                "status": HealthStatus.UNHEALTHY,
                "error": str(e)
            }

    @staticmethod
    def _determine_overall_status(statuses: List[HealthStatus]) -> HealthStatus:
        """
        Description:
            Определение общего статуса здоровья.

        Args:
            statuses: Список статусов компонентов.

        Returns:
            HealthStatus: Общий статус здоровья.
        """
        if any(status == HealthStatus.UNHEALTHY for status in statuses):
            return HealthStatus.UNHEALTHY
        if any(status == HealthStatus.DEGRADED for status in statuses):
            return HealthStatus.DEGRADED
        return HealthStatus.HEALTHY

    async def check_lag(self, group_id: str) -> Dict[str, Any]:
        """
        Description:
            Проверка отставания консьюмера.

        Args:
            group_id: ID группы потребителей.

        Returns:
            Dict[str, Any]: Информация об отставании.
        """
        try:
            admin_client = AIOKafkaAdminClient(
                bootstrap_servers=self.settings.KAFKA_BOOTSTRAP_SERVERS,
                client_id=f"{self.settings.SERVICE_NAME}-health-checker"
            )
            await admin_client.start()

            # Получаем информацию о группе потребителей
            consumer_group_info = await admin_client.describe_consumer_groups([group_id])
            
            lag_info = {}
            total_lag = 0

            for topic in KafkaTopics:
                topic_partitions = await admin_client.describe_topics([topic.value])
                for partition in topic_partitions[0].partitions:
                    # Получаем последний оффсет топика
                    end_offsets = await admin_client.get_end_offsets(
                        [TopicPartition(topic.value, partition.id)]
                    )
                    # Получаем текущий оффсет группы
                    committed = await admin_client.committed(
                        TopicPartition(topic.value, partition.id),
                        group_id
                    )
                    
                    if committed is not None:
                        lag = end_offsets[TopicPartition(topic.value, partition.id)] - committed
                        lag_info[f"{topic.value}-{partition.id}"] = {
                            "current_offset": committed,
                            "end_offset": end_offsets[TopicPartition(topic.value, partition.id)],
                            "lag": lag
                        }
                        total_lag += lag

            await admin_client.close()

            status = HealthStatus.HEALTHY
            if total_lag > 1000:  # Пороговое значение можно настроить
                status = HealthStatus.DEGRADED
            if total_lag > 10000:  # Критическое отставание
                status = HealthStatus.UNHEALTHY

            return {
                "status": status,
                "group_id": group_id,
                "total_lag": total_lag,
                "partitions": lag_info
            }

        except Exception as e:
            self.logger.error(f"Ошибка при проверке отставания: {str(e)}")
            return {
                "status": HealthStatus.UNHEALTHY,
                "error": str(e)
            }

    async def run_periodic_checks(
        self,
        interval_seconds: int = 60
    ) -> None:
        """
        Description:
            Запуск периодических проверок здоровья.

        Args:
            interval_seconds: Интервал между проверками в секундах.
        """
        while True:
            try:
                await self.check_health()
                await asyncio.sleep(interval_seconds)
            except Exception as e:
                self.logger.error(f"Ошибка при выполнении периодической проверки: {str(e)}")
                await asyncio.sleep(5)  # Короткая пауза перед повторной попыткой

    def get_last_health_status(self) -> Dict[str, Any]:
        """
        Description:
            Получение результатов последней проверки здоровья.

        Returns:
            Dict[str, Any]: Последний статус здоровья.
        """
        return self._health_status

class ComponentHealth:
    """
    Description:
        Класс для мониторинга здоровья отдельных компонентов.
    """

    def __init__(self, component_type: ComponentType):
        """
        Description:
            Инициализация мониторинга компонента.

        Args:
            component_type: Тип компонента.
        """
        self.component_type = component_type
        self.logger = logging.getLogger(__name__)
        self._status = HealthStatus.HEALTHY
        self._last_error: Optional[str] = None
        self._last_check_time = datetime.utcnow()
        self._metrics: Dict[str, float] = {}

    def update_status(
        self,
        status: HealthStatus,
        error: Optional[str] = None,
        metrics: Optional[Dict[str, float]] = None
    ) -> None:
        """
        Description:
            Обновление статуса компонента.

        Args:
            status: Новый статус.
            error: Описание ошибки.
            metrics: Метрики компонента.
        """
        self._status = status
        self._last_error = error
        self._last_check_time = datetime.utcnow()
        if metrics:
            self._metrics.update(metrics)

        if status != HealthStatus.HEALTHY:
            self.logger.warning(
                f"Компонент {self.component_type} в состоянии {status}"
                f"{f': {error}' if error else ''}"
            )

    def get_health_info(self) -> Dict[str, Any]:
        """
        Description:
            Получение информации о здоровье компонента.

        Returns:
            Dict[str, Any]: Информация о состоянии компонента.
        """
        return {
            "component": self.component_type,
            "status": self._status,
            "last_check": self._last_check_time.isoformat(),
            "last_error": self._last_error,
            "metrics": self._metrics
        }

class KafkaHealthManager:
    """
    Description:
        Менеджер здоровья для всех компонентов Kafka.
    """

    def __init__(self, settings: KafkaSettings):
        """
        Инициализация менеджера здоровья.

        Args:
            settings: Настройки Kafka.
        """
        self.settings = settings
        self.health_checker = HealthCheck(settings)
        self.components = {
            component_type: ComponentHealth(component_type)
            for component_type in ComponentType
        }
        self.logger = logging.getLogger(__name__)

    async def start_monitoring(self, check_interval: int = 60) -> None:
        """
        Description:
            Запуск мониторинга здоровья.

        Args:
            check_interval: Интервал проверки в секундах.
        """
        self.logger.info("Запуск мониторинга здоровья Kafka")
        asyncio.create_task(self._run_health_checks(check_interval))

    async def _run_health_checks(self, interval: int) -> None:
        """
        Description:
            Выполнение периодических проверок здоровья.

        Args:
            interval: Интервал между проверками.
        """
        while True:
            try:
                health_status = await self.health_checker.check_health()
                self._update_components_status(health_status)
                await asyncio.sleep(interval)
            except Exception as e:
                self.logger.error(f"Ошибка при проверке здоровья: {str(e)}")
                await asyncio.sleep(5)

    def _update_components_status(self, health_status: Dict[str, Any]) -> None:
        """
        Description:
            Обновление статуса компонентов.

        Args:
            health_status: Результаты проверки здоровья.
        """
        components = health_status.get("components", {})
        for component_type, status in components.items():
            if component_type in self.components:
                self.components[component_type].update_status(
                    status=status["status"],
                    error=status.get("error"),
                    metrics=status.get("details")
                )

    def get_health_status(self) -> Dict[str, Any]:
        """
        Description:
            Получение полного статуса здоровья.

        Returns:
            Dict[str, Any]: Полный статус здоровья системы.
        """
        components_status = {
            component_type: component.get_health_info()
            for component_type, component in self.components.items()
        }

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": self._determine_overall_status(),
            "components": components_status
        }

    def _determine_overall_status(self) -> HealthStatus:
        """
        Description:
            Определение общего статуса системы.

        Returns:
            HealthStatus: Общий статус здоровья.
        """
        statuses = [
            component.get_health_info()["status"]
            for component in self.components.values()
        ]
        return HealthCheck._determine_overall_status(statuses)