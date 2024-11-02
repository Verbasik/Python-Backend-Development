# src/core/producer.py
"""
Description:
    Модуль producer.py реализует асинхронную отправку сообщений в Kafka с использованием класса KafkaProducer. 
    Данный класс поддерживает подключение, отправку сообщений с проверкой ACL, обработку ошибок и повторные попытки 
    отправки при сбоях, а также собирает метрики производительности для мониторинга. KafkaProducer предоставляет 
    удобный интерфейс для работы с Kafka в асинхронных приложениях, обеспечивая надежную доставку сообщений и 
    адаптируемую конфигурацию для различных сценариев использования.
"""

from typing import Dict, Any, Optional
import json
import logging
import asyncio
from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError
from ..config.settings import KafkaSettings
from ..config.constants import KafkaPermissions

class KafkaProducer:
    """
    Description:
        Класс для асинхронной отправки сообщений в Kafka с поддержкой ACL
        и встроенным мониторингом производительности.

    Attributes:
        settings (KafkaSettings): Конфигурация подключения к Kafka
        producer (Optional[AIOKafkaProducer]): Экземпляр Kafka продюсера
        logger (logging.Logger): Логгер для записи событий
        _metrics (Dict[str, int]): Метрики работы продюсера

    Examples:
        >>> settings = KafkaSettings()
        >>> producer = KafkaProducer(settings=settings)
        >>> async with producer:
        ...     await producer.send_message(
        ...         topic='my_topic',
        ...         message={'key': 'value'},
        ...         key='message_key'
        ...     )
    """
    
    def __init__(self, settings: KafkaSettings) -> None:
        """
        Description:
            Инициализация Kafka продюсера.
        
        Args:
            settings: Настройки подключения к Kafka с конфигурацией ACL
        """
        self.settings = settings
        self.producer: Optional[AIOKafkaProducer] = None
        self.logger = logging.getLogger(__name__)
        
        # Инициализация метрик работы продюсера
        self._metrics: Dict[str, int] = {
            'messages_sent': 0,     # Количество успешно отправленных сообщений
            'bytes_sent': 0,        # Объем отправленных данных в байтах
            'errors': 0,            # Количество критических ошибок
            'retries': 0            # Количество повторных попыток отправки
        }

    async def __aenter__(self) -> 'KafkaProducer':
        """
        Description:
            Контекстный менеджер для автоматического подключения к Kafka.
        
        Returns:
            KafkaProducer: Экземпляр продюсера
            
        Examples:
            >>> async with KafkaProducer(settings) as producer:
            ...     # Работа с продюсером
        """
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Description:
            Контекстный менеджер для автоматического отключения от Kafka.
        """
        await self.disconnect()

    async def connect(self) -> None:
        """
        Description:
            Установка асинхронного соединения с Kafka брокером.
        
        Raises:
            ConnectionError: При ошибке подключения к Kafka
            
        Examples:
            >>> await producer.connect()
            # Устанавливает соединение с Kafka
        """
        try:
            producer_config = self._adapt_producer_config(
                self.settings.get_producer_config()
            )
            
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.settings.KAFKA_BOOTSTRAP_SERVERS,
                client_id=f"{self.settings.SERVICE_NAME}-producer",
                **producer_config
            )
            await self.producer.start()
            self.logger.info("Подключение к Kafka Producer успешно установлено")
        except Exception as e:
            self.logger.error(f"Ошибка подключения к Kafka Producer: {str(e)}")
            raise ConnectionError(f"Ошибка подключения к Kafka: {str(e)}")

    async def disconnect(self) -> None:
        """
        Description:
            Корректное закрытие соединения с Kafka.
        
        Examples:
            >>> await producer.disconnect()
            # Закрывает соединение с Kafka
        """
        if self.producer:
            try:
                await self.producer.stop()
                self.logger.info("Соединение с Kafka успешно закрыто")
            except Exception as e:
                self.logger.error(f"Ошибка при закрытии соединения: {str(e)}")
                raise RuntimeError(f"Ошибка при закрытии соединения: {str(e)}")

    def _validate_topic_access(self, topic: str) -> None:
        """
        Description:
            Проверка прав доступа сервиса к указанному топику.
        
        Args:
            topic: Имя топика для проверки доступа
            
        Raises:
            PermissionError: Если у сервиса нет прав на запись в топик
            
        Examples:
            >>> producer._validate_topic_access('my_topic')
            # Проверяет права доступа к топику
        """
        permissions = self.settings.get_acl_permissions(topic)
        if KafkaPermissions.WRITE.value not in permissions:
            raise PermissionError(
                f"Сервис {self.settings.SERVICE_NAME} не имеет прав "
                f"на запись в топик {topic}"
            )

    async def send_message(
        self, 
        topic: str, 
        message: Dict[str, Any], 
        key: Optional[str] = None,
        max_retries: int = 3
    ) -> None:
        """
        Description:
            Асинхронная отправка сообщения в Kafka с поддержкой повторных попыток
            при возникновении ошибок.
        
        Args:
            topic: Топик для отправки сообщения
            message: Сообщение в формате словаря для сериализации в JSON
            key: Ключ сообщения для партиционирования (опционально)
            max_retries: Максимальное количество попыток отправки при ошибке
            
        Raises:
            ConnectionError: При ошибке отправки после всех попыток
            PermissionError: При отсутствии прав доступа к топику
            ValueError: При невалидном формате сообщения
            
        Examples:
            >>> message = {'user_id': 123, 'action': 'login'}
            >>> await producer.send_message(
            ...     topic='user_events',
            ...     message=message,
            ...     key='user_123'
            ... )
        """
        if not self.producer:
            await self.connect()

        # Проверка прав доступа к топику
        self._validate_topic_access(topic)

        # Валидация входных данных
        if not isinstance(message, dict):
            raise ValueError("Параметр message должен быть словарем")

        retries = 0
        while retries < max_retries:
            try:
                # Сериализация сообщения и ключа
                value = json.dumps(message).encode('utf-8')
                key_bytes = key.encode('utf-8') if key else None

                # Отправка сообщения и ожидание подтверждения
                await self.producer.send_and_wait(
                    topic=topic,
                    value=value,
                    key=key_bytes
                )

                # Обновление метрик успешной отправки
                self._update_metrics(value)
                
                self.logger.info(
                    f"Сообщение успешно отправлено в топик {topic}"
                    f"{f' с ключом {key}' if key else ''}"
                )
                return

            except KafkaError as e:
                retries += 1
                self._metrics['retries'] += 1
                
                self.logger.warning(
                    f"Попытка {retries}/{max_retries} отправки сообщения "
                    f"в топик {topic} не удалась: {str(e)}"
                )
                
                if retries == max_retries:
                    self._metrics['errors'] += 1
                    self.logger.error(
                        f"Не удалось отправить сообщение в топик {topic} "
                        f"после {max_retries} попыток"
                    )
                    raise ConnectionError(f"Ошибка отправки сообщения в Kafka: {str(e)}")
                
                # Экспоненциальная задержка перед повторной попыткой
                await asyncio.sleep(min(2 ** retries, 10))

            except Exception as e:
                self._metrics['errors'] += 1
                self.logger.error(f"Неожиданная ошибка при отправке сообщения: {str(e)}")
                raise

    def _update_metrics(self, message_value: bytes) -> None:
        """
        Description:
            Обновление метрик после успешной отправки сообщения.
        
        Args:
            message_value: Сериализованное сообщение в байтах
            
        Examples:
            >>> producer._update_metrics(message_bytes)
            # Обновляет внутренние метрики продюсера
        """
        self._metrics['messages_sent'] += 1
        self._metrics['bytes_sent'] += len(message_value)

    def get_metrics(self) -> Dict[str, int]:
        """
        Description:
            Получение текущих метрик работы продюсера.
        
        Returns:
            Dict[str, int]: Словарь с метриками производительности:
                - messages_sent: Количество успешно отправленных сообщений
                - bytes_sent: Объем отправленных данных в байтах
                - errors: Количество критических ошибок
                - retries: Количество повторных попыток отправки
        
        Examples:
            >>> metrics = producer.get_metrics()
            >>> print(f"Отправлено сообщений: {metrics['messages_sent']}")
        """
        return self._metrics.copy()  # Возвращаем копию для безопасности
    
    def _adapt_producer_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Description:
            Адаптирует конфигурацию для AIOKafkaProducer.
            
        Returns:
            Dict[str, Any]: Адаптированная конфигурация
        """
        adapted_config = {}
        
        # Маппинг параметров конфигурации
        parameter_mapping = {
            "compression.type": "compression_type",
            "enable.idempotence": "enable_idempotence",
            "max.in.flight.requests.per.connection": "max_in_flight_requests_per_connection",
            "retry.backoff.ms": "retry_backoff_ms",
            "request.timeout.ms": "request_timeout_ms",
            "acks": "acks",
        }
        
        # Преобразование параметров
        for old_param, new_param in parameter_mapping.items():
            if old_param in config:
                value = config[old_param]
                # Преобразование строковых значений в числа где необходимо
                if new_param in ["retry_backoff_ms", "request_timeout_ms"]:
                    value = int(value)
                adapted_config[new_param] = value
        
        # Добавляем параметры безопасности
        if "security.protocol" in config:
            adapted_config["security_protocol"] = config["security.protocol"]
        if "sasl.mechanism" in config:
            adapted_config["sasl_mechanism"] = config["sasl.mechanism"]
        if "sasl.username" in config:
            adapted_config["sasl_plain_username"] = config["sasl.username"]
        if "sasl.password" in config:
            adapted_config["sasl_plain_password"] = config["sasl.password"]
        
        return adapted_config