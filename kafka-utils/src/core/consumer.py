# src/core/consumer.py
"""
Description:
    Модуль consumer.py предоставляет функциональные возможности для асинхронного получения и обработки сообщений из 
    Kafka. Класс KafkaConsumer реализует методы для управления подключением, чтения и обработки сообщений, а также 
    мониторинга производительности, включая сбор метрик, работу с отставанием (lag) и управление оффсетами. 
    Поддерживается гибкая настройка конфигурации, проверка прав доступа (ACL) и управление получением сообщений, 
    что делает его удобным инструментом для построения масштабируемых и надежных систем на базе Kafka.
"""

from typing import Dict, Any, Optional, AsyncIterator, List, Union
import json
import logging
import asyncio
from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaError
from aiokafka.structs import TopicPartition
from ..config.settings import KafkaSettings
from ..config.constants import KafkaPermissions

class KafkaConsumer:
    """
    Description:
        Класс для асинхронного получения и обработки сообщений из Kafka с поддержкой ACL 
        и встроенным мониторингом производительности.

    Attributes:
        settings (KafkaSettings): Конфигурация подключения к Kafka
        topics (List[str]): Список топиков для подписки
        group_id (str): Идентификатор группы потребителей
        consumer (Optional[AIOKafkaConsumer]): Экземпляр Kafka консьюмера
        logger (logging.Logger): Логгер для записи событий
        _metrics (Dict[str, Any]): Метрики работы консьюмера

    Examples:
        >>> settings = KafkaSettings()
        >>> consumer = KafkaConsumer(
        ...     settings=settings,
        ...     topics=['my_topic'],
        ...     group_id='my_group'
        ... )
        >>> async with consumer:
        ...     async for message in consumer.consume_messages():
        ...         print(message)
    """
    
    def __init__(
        self, 
        settings: KafkaSettings,
        topics: List[str],
        group_id: Optional[str] = None
    ) -> None:
        """
        Description:
            Инициализация Kafka консьюмера.
        
        Args:
            settings: Настройки подключения к Kafka
            topics: Список топиков для подписки
            group_id: Идентификатор группы потребителей (опционально)
        """
        self.settings = settings
        self.topics = topics
        self.group_id = group_id or f"{settings.SERVICE_NAME}-group"
        self.consumer: Optional[AIOKafkaConsumer] = None
        self.logger = logging.getLogger(__name__)
        
        # Инициализация метрик работы консьюмера
        self._metrics = {
            'messages_received': 0,      # Количество полученных сообщений
            'bytes_received': 0,         # Объем полученных данных в байтах
            'errors': 0,                 # Количество ошибок
            'commits': 0,                # Количество успешных коммитов
            'processing_time': 0,        # Общее время обработки сообщений
            'last_processed_offset': {}  # Последний обработанный оффсет по топикам
        }

    def _validate_topics_access(self) -> None:
        """
        Description:
            Проверка прав доступа сервиса к запрошенным топикам.
        
        Raises:
            PermissionError: Если у сервиса нет прав на чтение из топика
            
        Examples:
            >>> consumer._validate_topics_access()
            # Проверяет права доступа ко всем топикам
        """
        for topic in self.topics:
            permissions = self.settings.get_acl_permissions(topic)
            if KafkaPermissions.READ.value not in permissions:
                raise PermissionError(
                    f"Сервис {self.settings.SERVICE_NAME} не имеет прав "
                    f"на чтение из топика {topic}"
                )

    async def __aenter__(self) -> 'KafkaConsumer':
        """
        Description:
            Контекстный менеджер для автоматического подключения к Kafka.
        
        Returns:
            Экземпляр KafkaConsumer
            
        Examples:
            >>> async with KafkaConsumer(settings, topics) as consumer:
            ...     # Работа с консьюмером
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
            >>> await consumer.connect()
            # Устанавливает соединение с Kafka
        """
        try:
            # Проверка прав доступа перед подключением
            self._validate_topics_access()

            # Адаптация конфигурации
            config = self._adapt_consumer_config(
                self.settings.get_consumer_config()
            )
            
            # Установка group_id
            config['group_id'] = self.group_id
            
            self.consumer = AIOKafkaConsumer(
                *self.topics,
                bootstrap_servers=self.settings.KAFKA_BOOTSTRAP_SERVERS,
                client_id=f"{self.settings.SERVICE_NAME}-consumer",
                **config
            )
            
            await self.consumer.start()
            self.logger.info(
                f"Подключение к Kafka успешно установлено. "
                f"Топики: {self.topics}"
            )
        except Exception as e:
            self.logger.error(f"Ошибка подключения к Kafka Consumer: {str(e)}")
            raise ConnectionError(f"Ошибка подключения к Kafka: {str(e)}")

    async def disconnect(self) -> None:
        """
        Description:
            Корректное закрытие соединения с Kafka.
        
        Raises:
            RuntimeError: При ошибке закрытия соединения
            
        Examples:
            >>> await consumer.disconnect()
            # Закрывает соединение с Kafka
        """
        if self.consumer:
            try:
                # Сохранение оффсетов перед отключением при ручном управлении
                if not self.settings.CONSUMER_CONFIG.get('enable.auto.commit', True):
                    await self.commit_offsets()
                await self.consumer.stop()
                self.logger.info("Соединение с Kafka успешно закрыто")
            except Exception as e:
                self.logger.error(f"Ошибка при закрытии соединения: {str(e)}")
                raise RuntimeError(f"Ошибка при закрытии соединения: {str(e)}")

    async def consume_messages(
        self, 
        batch_size: int = 100,
        timeout_ms: int = 1000,
        max_retries: int = 3
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Description:
            Асинхронное получение и декодирование сообщений из Kafka.
        
        Args:
            batch_size: Максимальное количество сообщений в одном батче
            timeout_ms: Таймаут ожидания сообщений в миллисекундах
            max_retries: Максимальное количество попыток при ошибке
            
        Yields:
            Dict[str, Any]: Декодированное сообщение с метаданными
            
        Raises:
            ConnectionError: При ошибке получения сообщений
            
        Examples:
            >>> async for message in consumer.consume_messages(batch_size=10):
            ...     print(message)
        """
        if not self.consumer:
            await self.connect()

        retries = 0
        while True:
            try:
                # Получение батча сообщений с учетом таймаута
                start_time = asyncio.get_event_loop().time()
                messages = await self.consumer.getmany(
                    timeout_ms=timeout_ms,
                    max_records=batch_size
                )
                
                if not messages:
                    retries = 0  # Сброс счетчика попыток при пустом батче
                    continue

                # Обработка полученных сообщений по топикам и партициям
                for topic_partition, batch in messages.items():
                    for message in batch:
                        try:
                            # Декодирование JSON сообщения
                            decoded_message = json.loads(
                                message.value.decode('utf-8')
                            )
                            
                            # Добавление служебных метаданных
                            decoded_message.update({
                                '_metadata': {
                                    'topic': message.topic,
                                    'partition': message.partition,
                                    'offset': message.offset,
                                    'timestamp': message.timestamp,
                                    'key': message.key.decode('utf-8') if message.key else None
                                }
                            })

                            # Обновление метрик обработки
                            self._update_metrics(message, start_time)

                            yield decoded_message

                        except json.JSONDecodeError as e:
                            self._metrics['errors'] += 1
                            self.logger.error(
                                f"Ошибка декодирования сообщения: "
                                f"топик={message.topic}, partition={message.partition}, "
                                f"offset={message.offset}, error={str(e)}"
                            )
                            continue

                # Ручной коммит оффсетов, если автокоммит выключен
                if not self.settings.CONSUMER_CONFIG.get('enable.auto.commit', True):
                    await self.commit_offsets()

                retries = 0  # Сброс счетчика после успешной обработки

            except KafkaError as e:
                retries += 1
                self._metrics['errors'] += 1
                self.logger.warning(
                    f"Попытка {retries}/{max_retries} получения сообщений "
                    f"не удалась: {str(e)}"
                )
                
                if retries >= max_retries:
                    self.logger.error("Превышено максимальное количество попыток")
                    raise ConnectionError(f"Ошибка получения сообщений: {str(e)}")
                
                # Экспоненциальная задержка перед повторной попыткой
                await asyncio.sleep(min(2 ** retries, 10))

            except Exception as e:
                self.logger.error(f"Неожиданная ошибка при получении сообщений: {str(e)}")
                raise

    def _update_metrics(self, message: Any, start_time: float) -> None:
        """
        Description:
            Обновление метрик обработки сообщений.
        
        Args:
            message: Обработанное сообщение
            start_time: Время начала обработки сообщения
            
        Examples:
            >>> self._update_metrics(message, start_time)
            # Обновляет внутренние метрики консьюмера
        """
        self._metrics['messages_received'] += 1
        self._metrics['bytes_received'] += len(message.value)
        self._metrics['processing_time'] += (
            asyncio.get_event_loop().time() - start_time
        )
        self._metrics['last_processed_offset'][
            f"{message.topic}-{message.partition}"
        ] = message.offset

    async def commit_offsets(self) -> None:
        """
        Description:
            Подтверждение обработки сообщений путем коммита оффсетов.
        
        Raises:
            RuntimeError: При ошибке коммита оффсетов
            
        Examples:
            >>> await consumer.commit_offsets()
            # Подтверждает обработку полученных сообщений
        """
        try:
            await self.consumer.commit()
            self._metrics['commits'] += 1
        except Exception as e:
            self.logger.error(f"Ошибка при коммите оффсетов: {str(e)}")
            raise RuntimeError(f"Ошибка при коммите оффсетов: {str(e)}")

    async def seek_to_beginning(
        self, 
        partitions: Optional[List[TopicPartition]] = None
    ) -> None:
        """
        Description:
            Перемещение указателя чтения в начало топика или партиции.
        
        Args:
            partitions: Список партиций для перемещения указателя
            
        Raises:
            RuntimeError: При ошибке перемещения указателя
            
        Examples:
            >>> await consumer.seek_to_beginning()
            # Перемещает указатель в начало всех партиций
        """
        if not self.consumer:
            await self.connect()

        try:
            if partitions is None:
                # Если партиции не указаны, используем все доступные
                partitions = [
                    TopicPartition(topic, partition)
                    for topic in self.topics
                    for partition in self.consumer.partitions_for_topic(topic)
                ]
            
            await self.consumer.seek_to_beginning(partitions)
            self.logger.info(f"Указатель чтения перемещен в начало: {partitions}")
        except Exception as e:
            self.logger.error(f"Ошибка при перемещении указателя: {str(e)}")
            raise RuntimeError(f"Ошибка при перемещении указателя: {str(e)}")

    async def seek_to_end(
        self, 
        partitions: Optional[List[TopicPartition]] = None
    ) -> None:
        """
        Description:
            Перемещение указателя чтения в конец топика или партиции.
        
        Args:
            partitions: Список партиций для перемещения указателя
            
        Raises:
            RuntimeError: При ошибке перемещения указателя
            
        Examples:
            >>> await consumer.seek_to_end()
            # Перемещает указатель в конец всех партиций
        """
        if not self.consumer:
            await self.connect()

        try:
            if partitions is None:
                partitions = [
                    TopicPartition(topic, partition)
                    for topic in self.topics
                    for partition in self.consumer.partitions_for_topic(topic)
                ]
            
            await self.consumer.seek_to_end(partitions)
            self.logger.info(f"Указатель чтения перемещен в конец: {partitions}")
        except Exception as e:
            self.logger.error(f"Ошибка при перемещении указателя: {str(e)}")
            raise RuntimeError(f"Ошибка при перемещении указателя: {str(e)}")

    async def get_current_offsets(self) -> Dict[str, Dict[int, int]]:
            """
            Description:
                Получение текущих позиций (оффсетов) для всех топиков и партиций.
            
            Returns:
                Dict[str, Dict[int, int]]: Словарь текущих оффсетов в формате
                    {topic: {partition: offset}}
            
            Raises:
                RuntimeError: При ошибке получения оффсетов
                
            Examples:
                >>> offsets = await consumer.get_current_offsets()
                >>> print(offsets)
                {'my_topic': {0: 100, 1: 200}}
            """
            if not self.consumer:
                await self.connect()

            try:
                offsets: Dict[str, Dict[int, int]] = {}
                for topic in self.topics:
                    offsets[topic] = {}
                    for partition in self.consumer.partitions_for_topic(topic):
                        position = await self.consumer.position(
                            TopicPartition(topic, partition)
                        )
                        offsets[topic][partition] = position
                return offsets
            except Exception as e:
                self.logger.error(f"Ошибка при получении текущих оффсетов: {str(e)}")
                raise RuntimeError(f"Ошибка при получении текущих оффсетов: {str(e)}")

    def get_metrics(self) -> Dict[str, Union[int, float, Dict]]:
        """
        Description:
            Получение метрик работы консьюмера.
        
        Returns:
            Dict[str, Union[int, float, Dict]]: Словарь с метриками производительности:
                - messages_received: Количество полученных сообщений
                - bytes_received: Объем полученных данных в байтах
                - errors: Количество ошибок
                - commits: Количество успешных коммитов
                - processing_time: Общее время обработки сообщений
                - last_processed_offset: Последние обработанные оффсеты
        
        Examples:
            >>> metrics = consumer.get_metrics()
            >>> print(f"Получено сообщений: {metrics['messages_received']}")
        """
        return self._metrics

    async def pause_topics(self) -> None:
        """
        Description:
            Временная приостановка получения сообщений из топиков.
        
        Raises:
            RuntimeError: При ошибке приостановки получения сообщений
            
        Examples:
            >>> await consumer.pause_topics()
            # Приостанавливает получение сообщений
        """
        if self.consumer:
            try:
                partitions = self.consumer.assignment()
                self.consumer.pause(partitions)
                self.logger.info(
                    f"Получение сообщений приостановлено для партиций: {partitions}"
                )
            except Exception as e:
                self.logger.error(
                    f"Ошибка при приостановке получения сообщений: {str(e)}"
                )
                raise RuntimeError(
                    f"Ошибка при приостановке получения сообщений: {str(e)}"
                )

    async def resume_topics(self) -> None:
        """
        Description:
            Возобновление получения сообщений из топиков после паузы.
        
        Raises:
            RuntimeError: При ошибке возобновления получения сообщений
            
        Examples:
            >>> await consumer.resume_topics()
            # Возобновляет получение сообщений после паузы
        """
        if self.consumer:
            try:
                partitions = self.consumer.assignment()
                self.consumer.resume(partitions)
                self.logger.info(
                    f"Получение сообщений возобновлено для партиций: {partitions}"
                )
            except Exception as e:
                self.logger.error(
                    f"Ошибка при возобновлении получения сообщений: {str(e)}"
                )
                raise RuntimeError(
                    f"Ошибка при возобновлении получения сообщений: {str(e)}"
                )

    async def get_lag(self) -> Dict[str, Dict[int, int]]:
        """
        Description:
            Получение информации об отставании (lag) для каждого топика и партиции.
            Lag показывает разницу между последним доступным сообщением в топике
            и последним прочитанным сообщением консьюмером.
        
        Returns:
            Dict[str, Dict[int, int]]: Словарь с отставанием в формате
                {topic: {partition: lag}}
            
        Raises:
            RuntimeError: При ошибке получения информации об отставании
            
        Examples:
            >>> lag_info = await consumer.get_lag()
            >>> print(f"Отставание по партициям: {lag_info}")
        """
        if not self.consumer:
            await self.connect()

        try:
            lag_info: Dict[str, Dict[int, int]] = {}
            
            for topic in self.topics:
                lag_info[topic] = {}
                for partition in self.consumer.partitions_for_topic(topic):
                    tp = TopicPartition(topic, partition)
                    
                    # Получаем последний закоммиченный оффсет
                    committed = await self.consumer.committed(tp)
                    if committed is None:
                        continue
                    
                    # Получаем последний доступный оффсет в топике
                    end_offset = (await self.consumer.end_offsets([tp]))[tp]
                    
                    # Вычисляем отставание как разницу между последним доступным
                    # и последним прочитанным сообщением
                    lag = end_offset - committed
                    lag_info[topic][partition] = lag
            
            return lag_info
        except Exception as e:
            self.logger.error(
                f"Ошибка при получении информации об отставании: {str(e)}"
            )
            raise RuntimeError(
                f"Ошибка при получении информации об отставании: {str(e)}"
            )
        
    def _adapt_consumer_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Адаптирует конфигурацию для AIOKafkaConsumer."""
        adapted_config = {}
        
        # Маппинг параметров
        parameter_mapping = {
            "auto.offset.reset": "auto_offset_reset",
            "enable.auto.commit": "enable_auto_commit",
            "auto.commit.interval.ms": "auto_commit_interval_ms",
            "max.poll.interval.ms": "max_poll_interval_ms",
            "security.protocol": "security_protocol",
        }
        
        for old_param, new_param in parameter_mapping.items():
            if old_param in config:
                adapted_config[new_param] = config[old_param]
        
        # Добавление параметров безопасности
        if "sasl.mechanism" in config:
            adapted_config["sasl_mechanism"] = config["sasl.mechanism"]
        if "sasl.username" in config:
            adapted_config["sasl_plain_username"] = config["sasl.username"]
        if "sasl.password" in config:
            adapted_config["sasl_plain_password"] = config["sasl.password"]
            
        return adapted_config