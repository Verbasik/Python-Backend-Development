# src/security/auth.py
"""
Description:
    Модуль auth.py обеспечивает настройку и валидацию параметров безопасности для Kafka. Класс AuthManager управляет 
    созданием и проверкой конфигурации безопасности, поддерживая протоколы SASL и SSL. С помощью класса SecurityConfig 
    можно централизованно хранить параметры безопасности, включая протоколы, аутентификацию SASL и контексты SSL. 
    Эти инструменты позволяют настраивать и проверять аутентификацию и шифрование, что способствует безопасной 
    работе с Kafka в соответствии с требованиями безопасности.
"""

from typing import Dict, Optional, Any
import ssl
import logging
from dataclasses import dataclass
from ..config.settings import KafkaSettings

@dataclass
class SecurityConfig:
    """Конфигурация безопасности для Kafka."""
    security_protocol: str
    sasl_mechanism: Optional[str] = None
    sasl_username:  Optional[str] = None
    sasl_password:  Optional[str] = None
    ssl_context:    Optional[ssl.SSLContext] = None
    ssl_check_hostname: bool = True

class AuthManager:
    """
    Менеджер аутентификации для Kafka.
    """

    def __init__(self, settings: KafkaSettings):
        """
        Инициализация менеджера аутентификации.

        Args:
            settings: Настройки Kafka
        """
        self.settings = settings
        self.logger = logging.getLogger(__name__)

    def create_security_config(self) -> SecurityConfig:
        """
        Создание конфигурации безопасности на основе настроек.

        Returns:
            SecurityConfig: Конфигурация безопасности
        """
        try:
            security_config = SecurityConfig(
                security_protocol=self.settings.KAFKA_SECURITY_PROTOCOL
            )

            # Настройка SASL
            if self.settings.KAFKA_SECURITY_PROTOCOL in ["SASL_PLAINTEXT", "SASL_SSL"]:
                if not all([
                    self.settings.KAFKA_SASL_MECHANISM,
                    self.settings.KAFKA_USERNAME,
                    self.settings.KAFKA_PASSWORD
                ]):
                    raise ValueError("Неполная SASL конфигурация")

                security_config.sasl_mechanism = self.settings.KAFKA_SASL_MECHANISM
                security_config.sasl_username = self.settings.KAFKA_USERNAME
                security_config.sasl_password = self.settings.KAFKA_PASSWORD

            # Настройка SSL
            if self.settings.KAFKA_SECURITY_PROTOCOL in ["SSL", "SASL_SSL"]:
                security_config.ssl_context = self._create_ssl_context()

            self.logger.info(
                f"Создана конфигурация безопасности: "
                f"protocol={security_config.security_protocol}, "
                f"mechanism={security_config.sasl_mechanism}"
            )
            return security_config

        except Exception as e:
            self.logger.error(f"Ошибка при создании конфигурации безопасности: {str(e)}")
            raise

    def _create_ssl_context(self) -> ssl.SSLContext:
        """
        Создание SSL контекста.

        Returns:
            ssl.SSLContext: Сконфигурированный SSL контекст
        """
        try:
            ssl_context = ssl.create_default_context()
            
            if self.settings.KAFKA_SSL_CAFILE:
                ssl_context.load_verify_locations(self.settings.KAFKA_SSL_CAFILE)
            
            return ssl_context

        except Exception as e:
            self.logger.error(f"Ошибка при создании SSL контекста: {str(e)}")
            raise

    def get_security_options(self) -> Dict[str, Any]:
        """
        Получение опций безопасности для клиента Kafka.

        Returns:
            Dict[str, Any]: Словарь с опциями безопасности
        """
        try:
            security_config = self.create_security_config()
            options = {
                "security_protocol": security_config.security_protocol
            }

            if security_config.sasl_mechanism:
                options.update({
                    "sasl_mechanism": security_config.sasl_mechanism,
                    "sasl_plain_username": security_config.sasl_username,
                    "sasl_plain_password": security_config.sasl_password
                })

            if security_config.ssl_context:
                options["ssl_context"] = security_config.ssl_context

            return options

        except Exception as e:
            self.logger.error(f"Ошибка при получении опций безопасности: {str(e)}")
            raise

    def validate_security_config(self) -> bool:
        """
        Валидация конфигурации безопасности.

        Returns:
            bool: True если конфигурация валидна, False в противном случае
        """
        try:
            security_protocol = self.settings.KAFKA_SECURITY_PROTOCOL

            # Проверка SASL конфигурации
            if security_protocol in ["SASL_PLAINTEXT", "SASL_SSL"]:
                if not all([
                    self.settings.KAFKA_SASL_MECHANISM,
                    self.settings.KAFKA_USERNAME,
                    self.settings.KAFKA_PASSWORD
                ]):
                    self.logger.error("Неполная SASL конфигурация")
                    return False

            # Проверка SSL конфигурации
            if security_protocol in ["SSL", "SASL_SSL"]:
                if self.settings.KAFKA_SSL_CAFILE:
                    if not self._verify_ssl_config():
                        return False

            return True

        except Exception as e:
            self.logger.error(f"Ошибка при валидации конфигурации безопасности: {str(e)}")
            return False

    def _verify_ssl_config(self) -> bool:
        """
        Проверка SSL конфигурации.

        Returns:
            bool: True если SSL конфигурация валидна, False в противном случае
        """
        try:
            ssl_context = self._create_ssl_context()
            return bool(ssl_context)
        except Exception as e:
            self.logger.error(f"Ошибка при проверке SSL конфигурации: {str(e)}")
            return False