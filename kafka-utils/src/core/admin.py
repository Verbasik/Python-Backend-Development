# src/core/admin.py
"""
Description:
    Модуль admin.py предоставляет функциональные возможности для администрирования Kafka-топиков, включая 
    управление и валидацию конфигураций топиков, создание и удаление, а также обновление параметров конфигурации. 
    Класс KafkaAdmin инкапсулирует основные операции по администрированию с использованием AIOKafkaAdminClient, 
    обеспечивая поддержку подключения, настройки ACL и валидации топиков. Данный модуль упрощает управление 
    конфигурациями Kafka, делая возможным автоматическое создание топиков при необходимости и обеспечение 
    соответствия конфигураций заданным параметрам.
"""

import logging
from typing import List, Dict, Any, Optional
from aiokafka.admin import AIOKafkaAdminClient, NewTopic
from aiokafka.admin.config_resource import ConfigResource, ConfigResourceType
from ..config.settings import KafkaSettings
from ..config.constants import KAFKA_TOPIC_CONFIGS

class KafkaAdmin:
    """
    Description:
        Класс для администрирования топиков Kafka с поддержкой ACL.
        Предоставляет функционал для создания и управления топиками Kafka,
        включая валидацию конфигурации и обеспечение их существования.

    Attributes:
        settings (KafkaSettings): Конфигурация Kafka
        kafka_config (Optional[KafkaConfigABC]): Пользовательская конфигурация Kafka
        admin_client (Optional[AIOKafkaAdminClient]): Клиент для административных операций

    Examples:
        >>> kafka_settings = KafkaSettings(...)
        >>> admin = KafkaAdmin(kafka_settings)
        >>> await admin.connect()
        >>> await admin.ensure_topics()
        >>> await admin.disconnect()
    """

    def __init__(self, settings: KafkaSettings) -> None:
        """
        Description:
            Инициализация административного клиента Kafka.

        Args:
            settings: Объект с настройками подключения к Kafka

        Examples:
            >>> kafka_settings = KafkaSettings(...)
            >>> admin = KafkaAdmin(kafka_settings)
        """
        self.logger = logging.getLogger(__name__)
        
        self.settings = settings
        self.kafka_config = settings.kafka_config
        self.admin_client: Optional[AIOKafkaAdminClient] = None

    def _get_admin_config(self) -> Dict[str, Any]:
        """
        Description:
            Формирует конфигурацию для административного клиента Kafka.
            
        Returns:
            Dict[str, Any]: Конфигурация для AIOKafkaAdminClient
        """
        config = {
            'bootstrap_servers': self.settings.KAFKA_BOOTSTRAP_SERVERS,
            'client_id': f"{self.settings.SERVICE_NAME}-admin",
            'security_protocol': self.settings.KAFKA_SECURITY_PROTOCOL,
        }

        # Добавляем SASL настройки если требуется
        if self.settings.KAFKA_SECURITY_PROTOCOL in ["SASL_PLAINTEXT", "SASL_SSL"]:
            config.update({
                'sasl_mechanism': self.settings.KAFKA_SASL_MECHANISM,
                'sasl_plain_username': self.settings.KAFKA_USERNAME,
                'sasl_plain_password': self.settings.KAFKA_PASSWORD,
            })

        # Добавляем SSL настройки если требуется
        if self.settings.KAFKA_SECURITY_PROTOCOL in ["SSL", "SASL_SSL"]:
            if self.settings.KAFKA_SSL_CAFILE:
                config['ssl_cafile'] = self.settings.KAFKA_SSL_CAFILE

        return config

    def _get_topic_resource(self, topic_name: str) -> ConfigResource:
        """
        Description:
            Создает объект ConfigResource для топика.
            
        Args:
            topic_name: Имя топика
            
        Returns:
            ConfigResource: Объект конфигурации ресурса для топика
            
        Raises:
            ValueError: Если topic_name не является строкой
        """
        if not isinstance(topic_name, str):
            raise ValueError("topic_name должен быть строкой")
            
        return ConfigResource(
            resource_type=ConfigResourceType.TOPIC,
            name=topic_name
        )

    async def connect(self) -> None:
        """
        Description:
            Установка соединения с Kafka. Создает и инициализирует
            административный клиент с заданными настройками.

        Raises:
            ConnectionError: При ошибке подключения к Kafka

        Examples:
            >>> await admin.connect()
        """
        try:
            admin_config = self._get_admin_config()
            self.admin_client = AIOKafkaAdminClient(**admin_config)
            await self.admin_client.start()
            self.logger.info("Подключение к Kafka Admin успешно установлено")
        except Exception as exc:
            error_msg = f"Ошибка подключения к Kafka Admin: {str(exc)}"
            self.logger.error(error_msg)
            raise ConnectionError(error_msg) from exc

    async def disconnect(self) -> None:
        """
        Description:
            Закрытие соединения с Kafka. Освобождает ресурсы
            административного клиента.

        Examples:
            >>> await admin.disconnect()
        """
        if self.admin_client:
            await self.admin_client.close()
            self.logger.info("Соединение с Kafka Admin закрыто")

    async def ensure_topics(self) -> None:
        """
        Description:
            Проверка существования необходимых топиков и их создание при отсутствии.
            Также проводит валидацию конфигурации существующих топиков.

        Raises:
            ConnectionError: Если отсутствует подключение к Kafka
            Exception: При ошибках создания или валидации топиков

        Examples:
            >>> await admin.ensure_topics()
        """
        existing_topics = await self.admin_client.list_topics()

        if self.kafka_config:
            # Используем пользовательские топики из kafka_config
            topic_configs = self.kafka_config.get_topic_configs()
        else:
            # Используем дефолтные топики из констант
            topic_configs = KAFKA_TOPIC_CONFIGS

        for topic_name in topic_configs:
            try:
                if topic_name not in existing_topics:
                    await self.create_topic(topic_name)
                else:
                    # Сначала валидируем
                    await self.validate_topic_config(topic_name)
                    # Если есть несоответствия, обновляем
                    await self.update_topic_config(topic_name)
            except Exception as e:
                self.logger.error(f"Ошибка обработки топика {topic_name}: {e}")

    async def create_topic(self, topic_name: str) -> None:
        """
        Description:
            Создание нового топика с конфигурацией из KAFKA_TOPIC_CONFIGS.

        Args:
            topic_name: Имя создаваемого топика

        Raises:
            KeyError: Если топик отсутствует в KAFKA_TOPIC_CONFIGS
            Exception: При ошибке создания топика

        Examples:
            >>> await admin.create_topic("my-topic")
        """
        try:
            # Получаем конфигурацию топика
            if self.kafka_config:
                topic_config = self.kafka_config.get_topic_configs().get(topic_name)
            else:
                topic_config = KAFKA_TOPIC_CONFIGS.get(topic_name)
            
            # Создаем описание нового топика
            new_topics = [
                NewTopic(
                    name=topic_name,
                    num_partitions=topic_config['num.partitions'],
                    replication_factor=1,  # TODO: Сделать конфигурируемым
                    topic_configs={
                        'retention.ms': str(topic_config['retention.ms']),
                        'cleanup.policy': topic_config['cleanup.policy']
                    }
                )
            ]
            
            # Создаем топик
            await self.admin_client.create_topics(new_topics)
            self.logger.info(f"Топик {topic_name} успешно создан")
            
        except Exception as exc:
            error_msg = f"Ошибка создания топика {topic_name}: {str(exc)}"
            self.logger.error(error_msg)
            raise Exception(error_msg) from exc

    async def validate_topic_config(self, topic_name: str) -> None:
        """
        Description:
            Проверка соответствия конфигурации существующего топика
            ожидаемым параметрам из конфигурации.

        Args:
            topic_name: Имя проверяемого топика

        Raises:
            KeyError: Если топик отсутствует в конфигурации
            Exception: При ошибке получения конфигурации топика

        Examples:
            >>> await admin.validate_topic_config("my-topic")
        """
        try:
            # Создаем ресурс с правильным типом
            resource = ConfigResource(resource_type=ConfigResourceType.TOPIC, name=topic_name)
            
            # Получаем конфигурацию
            response = await self.admin_client.describe_configs([resource])
            
            if not response:
                self.logger.warning(f"Не удалось получить конфигурацию топика {topic_name}")
                return
                
            # Обработка ответа
            current_config = {}
            # Получаем конфигурацию из ответа
            if hasattr(response[0], 'configs'):
                # Новый формат ответа
                for config in response[0].configs:
                    current_config[config.name] = config.value
            else:
                # Старый формат или альтернативный ответ
                self.logger.debug(f"Получен ответ в формате: {type(response[0])}")
                self.logger.debug(f"Содержимое ответа: {response[0]}")
                # Пытаемся извлечь конфигурацию из любого доступного формата
                try:
                    if isinstance(response[0], tuple):
                        # Если это кортеж, берем второй элемент как конфигурацию
                        current_config = response[0][1]
                except Exception as e:
                    self.logger.error(f"Ошибка извлечения конфигурации: {str(e)}")
                    raise
                    
            # Получаем ожидаемую конфигурацию
            if self.kafka_config:
                expected_config = self.kafka_config.get_topic_configs().get(topic_name)
            else:
                expected_config = KAFKA_TOPIC_CONFIGS.get(topic_name)

            self._validate_config_parameters(topic_name, expected_config, current_config)
                
        except Exception as exc:
            error_msg = f"Ошибка проверки конфигурации топика {topic_name}: {str(exc)}"
            self.logger.error(error_msg)
            raise Exception(error_msg) from exc

    def _validate_config_parameters(
        self, 
        topic_name: str,
        expected_config: Dict[str, Any],
        current_config: Dict[str, Any]
    ) -> None:
        """
        Description:
            Проверяет соответствие параметров конфигурации.
            
        Args:
            topic_name: Имя топика
            expected_config: Ожидаемая конфигурация
            current_config: Текущая конфигурация
        """
        for key, expected_value in expected_config.items():
            current_value = current_config.get(key)
            if str(current_value) != str(expected_value):
                self.logger.warning(
                    f"Несоответствие конфигурации топика {topic_name} "
                    f"для параметра {key}: ожидалось {expected_value}, "
                    f"текущее значение {current_value}"
                )

    async def update_topic_config(self, topic_name: str) -> None:
        """
        Description:
            Обновление конфигурации существующего топика.

        Args:
            topic_name: Имя топика

        Raises:
            Exception: При ошибке обновления конфигурации

        Examples:
            >>> await admin.update_topic_config("my-topic")
        """
        try:
            # Получаем конфигурацию топика
            if self.kafka_config:
                config = self.kafka_config.get_topic_configs().get(topic_name)
            else:
                config = KAFKA_TOPIC_CONFIGS.get(topic_name)

            if not config:
                raise KeyError(f"Конфигурация для топика {topic_name} не найдена")

            resources = [ConfigResource(
                resource_type=ConfigResourceType.TOPIC,
                name=topic_name,
                configs={
                    'retention.ms': str(config['retention.ms']),
                    'cleanup.policy': config['cleanup.policy']
                }
            )]

            await self.admin_client.alter_configs(resources)

            self.logger.info(f"Конфигурация топика {topic_name} обновлена")

        except Exception as e:
            raise Exception(f"Ошибка обновления конфигурации топика {topic_name}: {e}")