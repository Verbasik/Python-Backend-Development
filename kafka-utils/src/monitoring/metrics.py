# src/monitoring/metrics.py
"""
Description:
    Модуль metrics.py предоставляет инструменты для сбора, регистрации и управления метриками в системе Kafka. 
    Основные классы включают KafkaMetricsCollector для инициализации и записи метрик, ProducerMetrics и ConsumerMetrics 
    для отслеживания метрик, связанных с продюсером и консьюмером соответственно. Метрики включают счетчики, измерители 
    и гистограммы, охватывающие показатели производительности, отставание и ошибки, что позволяет мониторить и анализировать 
    поведение системы для оптимизации её работы.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
import time
import logging
from enum import Enum

class MetricType(str, Enum):
    """
    Description:
        Типы метрик.

    Attributes:
        COUNTER: Счетчик.
        GAUGE: Измеритель.
        HISTOGRAM: Гистограмма.
    """
    COUNTER   = "counter"
    GAUGE     = "gauge"
    HISTOGRAM = "histogram"

@dataclass
class MetricValue:
    """
    Description:
        Значение метрики с метаданными.

    Attributes:
        value: Значение метрики.
        timestamp: Время записи значения.
        labels: Метки метрики.
    """
    value: float
    timestamp: float = field(default_factory=time.time)
    labels: Dict[str, str] = field(default_factory=dict)

class KafkaMetricsCollector:
    """
    Description:
        Коллектор метрик для Kafka.
    """

    def __init__(self):
        """
        Description:
            Инициализация коллектора метрик.
        """
        self.logger = logging.getLogger(__name__)
        self._metrics: Dict[str, Dict[str, MetricValue]] = {}
        self._initialize_metrics()

    def _initialize_metrics(self) -> None:
        """
        Description:
            Инициализация базовых метрик.
        """
        # Producer метрики
        self._register_metric(
            "kafka_producer_messages_sent_total",
            MetricType.COUNTER,
            "Общее количество отправленных сообщений"
        )
        self._register_metric(
            "kafka_producer_bytes_sent_total",
            MetricType.COUNTER,
            "Общее количество отправленных байт"
        )
        self._register_metric(
            "kafka_producer_errors_total",
            MetricType.COUNTER,
            "Общее количество ошибок при отправке"
        )
        self._register_metric(
            "kafka_producer_retries_total",
            MetricType.COUNTER,
            "Общее количество повторных попыток отправки"
        )
        self._register_metric(
            "kafka_producer_message_latency_ms",
            MetricType.HISTOGRAM,
            "Задержка отправки сообщений в миллисекундах"
        )

        # Consumer метрики
        self._register_metric(
            "kafka_consumer_messages_received_total",
            MetricType.COUNTER,
            "Общее количество полученных сообщений"
        )
        self._register_metric(
            "kafka_consumer_bytes_received_total",
            MetricType.COUNTER,
            "Общее количество полученных байт"
        )
        self._register_metric(
            "kafka_consumer_errors_total",
            MetricType.COUNTER,
            "Общее количество ошибок при получении"
        )
        self._register_metric(
            "kafka_consumer_lag",
            MetricType.GAUGE,
            "Отставание консьюмера"
        )
        self._register_metric(
            "kafka_consumer_processing_time_ms",
            MetricType.HISTOGRAM,
            "Время обработки сообщений в миллисекундах"
        )

        # Общие метрики
        self._register_metric(
            "kafka_connection_errors_total",
            MetricType.COUNTER,
            "Общее количество ошибок подключения"
        )
        self._register_metric(
            "kafka_connection_retries_total",
            MetricType.COUNTER,
            "Общее количество повторных попыток подключения"
        )
        self._register_metric(
            "kafka_active_connections",
            MetricType.GAUGE,
            "Количество активных подключений"
        )

        # Метрики задач
        self._register_metric(
            "retry_failed_tasks_started",
            MetricType.COUNTER,
            "Количество запусков процесса повторной обработки неудачных задач"
        )
        self._register_metric(
            "retry_failed_tasks_completed",
            MetricType.COUNTER,
            "Количество завершённых процессов повторной обработки неудачных задач"
        )
        self._register_metric(
            "retry_failed_tasks_errors",
            MetricType.COUNTER,
            "Количество ошибок при повторной обработке задач"
        )
        self._register_metric(
            "retry_failed_tasks_processed",
            MetricType.COUNTER,
            "Количество обработанных задач в процессе повторной обработки"
        )
        self._register_metric(
            "retry_failed_tasks_duration_ms",
            MetricType.HISTOGRAM,
            "Время выполнения процесса повторной обработки в миллисекундах"
        )

    def _register_metric(
        self,
        name: str,
        metric_type: MetricType,
        description: Optional[str] = None
    ) -> None:
        """
        Description:
            Регистрация новой метрики.

        Args:
            name: Имя метрики.
            metric_type: Тип метрики.
            description: Описание метрики.
        """
        if name not in self._metrics:
            self._metrics[name] = {
                "type": metric_type,
                "description": description,
                "values": {}
            }

    def record_metric(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Description:
            Запись значения метрики.

        Args:
            name: Имя метрики.
            value: Значение.
            labels: Метки метрики.
        """
        try:
            if name not in self._metrics:
                self.logger.warning(f"Неизвестная метрика: {name}")
                return

            metric_value = MetricValue(
                value=value,
                labels=labels or {}
            )
            
            # Для counter всегда увеличиваем значение
            if self._metrics[name]["type"] == MetricType.COUNTER:
                current_value = self._get_metric_value(name, labels or {})
                metric_value.value += current_value

            self._metrics[name]["values"][self._label_key(labels or {})] = metric_value
            
        except Exception as e:
            self.logger.error(f"Ошибка при записи метрики {name}: {str(e)}")

    def _get_metric_value(self, name: str, labels: Dict[str, str]) -> float:
        """
        Description:
            Получение текущего значения метрики.
        """
        label_key = self._label_key(labels)
        if label_key in self._metrics[name]["values"]:
            return self._metrics[name]["values"][label_key].value
        return 0.0

    @staticmethod
    def _label_key(labels: Dict[str, str]) -> str:
        """
        Description:
            Создание ключа из лейблов.
        """
        return ",".join(f"{k}={v}" for k, v in sorted(labels.items()))

    def get_metrics(self) -> Dict[str, Any]:
        """
        Description:
            Получение всех метрик.

        Returns:
            Dict[str, Any]: Словарь метрик.
        """
        result = {}
        current_time = time.time()
        
        for name, metric_data in self._metrics.items():
            metric_values = []
            for label_key, value in metric_data["values"].items():
                if current_time - value.timestamp <= 300:  # Только метрики за последние 5 минут
                    metric_values.append({
                        "value": value.value,
                        "timestamp": value.timestamp,
                        "labels": value.labels
                    })
            
            result[name] = {
                "type": metric_data["type"],
                "description": metric_data["description"],
                "values": metric_values
            }
        
        return result

    def reset_metrics(self) -> None:
        """
        Description:
            Сброс всех метрик.
        """
        for metric_data in self._metrics.values():
            metric_data["values"].clear()

class ProducerMetrics:
    """
    Description:
        Метрики для Producer.
    """
    
    def __init__(self, collector: KafkaMetricsCollector):
        self.collector = collector

    def record_message_sent(self, topic: str, size: int) -> None:
        """
        Description:
            Запись отправленного сообщения.
        """
        labels = {"topic": topic}
        self.collector.record_metric("kafka_producer_messages_sent_total", 1, labels)
        self.collector.record_metric("kafka_producer_bytes_sent_total", size, labels)

    def record_error(self, topic: str, error_type: str) -> None:
        """
        Description:
            Запись ошибки.
        """
        self.collector.record_metric(
            "kafka_producer_errors_total",
            1,
            {"topic": topic, "error_type": error_type}
        )

    def record_retry(self, topic: str) -> None:
        """
        Description:
            Запись повторной попытки.
        """
        self.collector.record_metric(
            "kafka_producer_retries_total",
            1,
            {"topic": topic}
        )

class ConsumerMetrics:
    """
    Description:
        Метрики для Consumer.
    """
    
    def __init__(self, collector: KafkaMetricsCollector):
        self.collector = collector

    def record_message_received(self, topic: str, size: int) -> None:
        """
        Description:
            Запись полученного сообщения.
        """
        labels = {"topic": topic}
        self.collector.record_metric("kafka_consumer_messages_received_total", 1, labels)
        self.collector.record_metric("kafka_consumer_bytes_received_total", size, labels)

    def record_lag(self, topic: str, partition: int, lag: int) -> None:
        """
        Description:
            Запись отставания консьюмера.
        """
        self.collector.record_metric(
            "kafka_consumer_lag",
            lag,
            {"topic": topic, "partition": str(partition)}
        )

    def record_processing_time(self, topic: str, time_ms: float) -> None:
        """
        Description:
            Запись времени обработки.
        """
        self.collector.record_metric(
            "kafka_consumer_processing_time_ms",
            time_ms,
            {"topic": topic}
        )