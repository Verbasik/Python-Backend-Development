# src/config/settings.py
"""
Description:
  Модуль содержит настройки для работы с Kafka.
  Обеспечивает валидацию конфигурации и управление настройками безопасности.
"""

from typing import Optional, Dict, Any, Set
from pydantic_settings import BaseSettings
from pydantic import validator
from .config_types import KafkaConfigABC
from .constants import (
    CONSUMER_GROUP_CONFIGS,
    KAFKA_ACL_MAPPINGS,
    DEFAULT_KAFKA_CONFIG
)

class KafkaSettings(BaseSettings):
    """
    Description:
      Класс настроек Kafka с валидацией.

    Attributes:
        KAFKA_BOOTSTRAP_SERVERS: Список серверов Kafka для подключения.
        KAFKA_SECURITY_PROTOCOL: Протокол безопасности (PLAINTEXT, SSL, SASL_PLAINTEXT, SASL_SSL).
        KAFKA_SASL_MECHANISM: Механизм SASL аутентификации.
        KAFKA_USERNAME: Имя пользователя для SASL аутентификации.
        KAFKA_PASSWORD: Пароль для SASL аутентификации.
        SERVICE_NAME: Имя сервиса (должно соответствовать одному из KafkaUsers).
        KAFKA_SSL_CAFILE: Путь к CA файлу для SSL.
        PRODUCER_CONFIG: Дополнительная конфигурация producer'а.
        CONSUMER_CONFIG: Дополнительная конфигурация consumer'а.
        kafka_config: Пользовательская конфигурация.

    Examples:
        >>> settings = KafkaSettings(
        ...     KAFKA_BOOTSTRAP_SERVERS="localhost:9092",
        ...     SERVICE_NAME="aiagents-orchestrator"
        ... )
        >>> settings.get_producer_config()
        {'bootstrap.servers': 'localhost:9092', 'security.protocol': 'PLAINTEXT', ...}
    """

    KAFKA_BOOTSTRAP_SERVERS: str
    KAFKA_SECURITY_PROTOCOL: str = "PLAINTEXT"
    KAFKA_SASL_MECHANISM: Optional[str] = None
    KAFKA_USERNAME: Optional[str] = None
    KAFKA_PASSWORD: Optional[str] = None
    SERVICE_NAME: str
    KAFKA_SSL_CAFILE: Optional[str] = None
    PRODUCER_CONFIG: Dict[str, Any] = DEFAULT_KAFKA_CONFIG
    CONSUMER_CONFIG: Dict[str, Any] = {}
    kafka_config: Optional[KafkaConfigABC] = None

    @validator("SERVICE_NAME")
    def validate_service_name(cls, v: str, values: Dict[str, Any]) -> str:
        """
        Description:
          Валидация имени сервиса.

        Args:
            v: Имя сервиса для валидации.
            values: Пользовательские конфигурационные настройки

        Returns:
            Валидное имя сервиса.

        Raises:
            ValueError: Если имя сервиса не соответствует списку разрешенных.
        """
        # Получаем конфигурацию
        kafka_config = values.get('kafka_config')
        
        if kafka_config is not None:
            valid_users = set(kafka_config.get_users().values())
            if v not in valid_users:
                raise ValueError(f"Service name must be one of: {list(valid_users)}")
        
        return v

    @validator("KAFKA_SECURITY_PROTOCOL")
    def validate_security_protocol(cls, v: str) -> str:
        """
        Description:
          Валидация протокола безопасности.

        Args:
            v: Протокол безопасности для валидации.

        Returns:
            Валидный протокол безопасности.

        Raises:
            ValueError: Если протокол не соответствует списку разрешенных.
        """
        valid_protocols = ["PLAINTEXT", "SSL", "SASL_PLAINTEXT", "SASL_SSL"]
        if v not in valid_protocols:
            raise ValueError(f"Security protocol must be one of: {valid_protocols}")
        return v

    @validator("CONSUMER_CONFIG", pre=True)
    def build_consumer_config(
        cls, v: Dict[str, Any], values: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Description:
          Построение конфигурации consumer'а.

        Args:
            v: Базовая конфигурация consumer'а.
            values: Словарь значений других полей.

        Returns:
            Итоговая конфигурация consumer'а.
        """
        service_name = values.get("SERVICE_NAME")
        if not service_name:
            return v

        config = CONSUMER_GROUP_CONFIGS.get(service_name, {}).copy()
        config.update(v)
        return config

    def get_producer_config(self) -> Dict[str, Any]:
        """
        Description:
          Получение полной конфигурации producer'а, включая настройки безопасности.

        Returns:
            Полная конфигурация producer'а.

        Examples:
            >>> settings.get_producer_config()
            {'bootstrap.servers': 'localhost:9092', 'security.protocol': 'PLAINTEXT', ...}
        """
        config = self.PRODUCER_CONFIG.copy()
        self._add_security_config(config)
        return config

    def get_consumer_config(self) -> Dict[str, Any]:
        """
        Description:
          Получение полной конфигурации consumer'а, включая настройки безопасности.

        Returns:
            Полная конфигурация consumer'а.

        Examples:
            >>> settings.get_consumer_config()
            {'bootstrap.servers': 'localhost:9092', 'group.id': 'orchestrator-group', ...}
        """
        config = self.CONSUMER_CONFIG.copy()
        self._add_security_config(config)
        return config

    def _add_security_config(self, config: Dict[str, Any]) -> None:
        """
        Description:
          Добавление настроек безопасности в конфигурацию.

        Args:
            config: Конфигурация для дополнения настройками безопасности.

        Raises:
            ValueError: Если настройки SASL неполные.
        """
        config["bootstrap.servers"] = self.KAFKA_BOOTSTRAP_SERVERS
        config["security.protocol"] = self.KAFKA_SECURITY_PROTOCOL

        if self.KAFKA_SECURITY_PROTOCOL in ["SASL_PLAINTEXT", "SASL_SSL"]:
            if not all([
                self.KAFKA_SASL_MECHANISM,
                self.KAFKA_USERNAME,
                self.KAFKA_PASSWORD
            ]):
                raise ValueError("SASL configuration is incomplete")

            config["sasl.mechanism"] = self.KAFKA_SASL_MECHANISM
            config["sasl.username"] = self.KAFKA_USERNAME
            config["sasl.password"] = self.KAFKA_PASSWORD

        if self.KAFKA_SECURITY_PROTOCOL in ["SSL", "SASL_SSL"]:
            if self.KAFKA_SSL_CAFILE:
                config["ssl.ca.location"] = self.KAFKA_SSL_CAFILE

    def get_acl_permissions(self, topic: str) -> Set[str]:
        """
        Description:
          Получение списка разрешений ACL для текущего сервиса и указанного топика.

        Args:
            topic: Имя топика для проверки разрешений.

        Returns:
            Набор разрешений для указанного топика.

        Examples:
            >>> settings.get_acl_permissions("orchestrator.asciidoc.request")
            {'read', 'write'}
        """
        if self.kafka_config:
            return self.kafka_config.get_permissions().get(self.SERVICE_NAME, {}).get(topic, set())
        else:
            return KAFKA_ACL_MAPPINGS.get(self.SERVICE_NAME, {}).get(topic, set())
    
    def get_admin_config(self) -> Dict[str, Any]:
        """
        Description:
            Возвращает конфигурацию для административного клиента.
            
        Returns:
            Dict[str, Any]: Базовая конфигурация без специфичных для producer настроек
        """
        config = {
            'bootstrap_servers': self.KAFKA_BOOTSTRAP_SERVERS,
            'security_protocol': self.KAFKA_SECURITY_PROTOCOL,
        }
        
        # Добавляем только базовые настройки безопасности
        if self.KAFKA_SECURITY_PROTOCOL in ["SASL_PLAINTEXT", "SASL_SSL"]:
            config.update({
                'sasl_mechanism': self.KAFKA_SASL_MECHANISM,
                'sasl_plain_username': self.KAFKA_USERNAME,
                'sasl_plain_password': self.KAFKA_PASSWORD,
            })

        if self.KAFKA_SECURITY_PROTOCOL in ["SSL", "SASL_SSL"] and self.KAFKA_SSL_CAFILE:
            config['ssl_cafile'] = self.KAFKA_SSL_CAFILE

        return config

    class Config:
        """
        Description:
          Конфигурация для класса настроек.
        
        Attributes:
            env_file: Путь к файлу с переменными окружения.
            env_file_encoding: Кодировка файла с переменными окружения.
            case_sensitive: Флаг чувствительности к регистру.
        """
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True