# app/config/configuration_minio.py
"""
Модуль содержит класс конфигурации для подключения к MinIO.
Предоставляет удобный способ инициализации параметров подключения через переменные окружения.
"""
import os
from dataclasses import dataclass


@dataclass
class MinioConfiguration:
    """
    Description:
    ---------------
        Класс, представляющий конфигурацию подключения к серверу MinIO.

    Args:
    ---------------
        host: Хост MinIO сервера
        api_port: Порт API MinIO
        access_key: Ключ доступа (логин)
        secret_key: Секретный ключ (пароль)
        use_ssl: Использовать ли SSL-шифрование. По умолчанию False.

    Returns:
    ---------------
        Экземпляр класса MinioConfiguration

    Raises:
    ---------------
        TypeError: Если типы переданных аргументов не соответствуют аннотациям

    Examples:
    ---------------
        >>> config = MinioConfiguration(
        ...     host='localhost',
        ...     api_port='9000',
        ...     access_key='minioadmin',
        ...     secret_key='minioadmin',
        ...     use_ssl=False
        ... )
        >>> config.host
        'localhost'
    """
    host: str
    api_port: str
    access_key: str
    secret_key: str
    use_ssl: bool = False

    @classmethod
    def from_env(cls):
        """
        Description:
        ---------------
            Создает экземпляр MinioConfiguration на основе переменных окружения.

        Args:
        ---------------
            Использует следующие переменные окружения:
            - MINIO_HOST: хост MinIO
            - MINIO_API_PORT: порт API MinIO
            - MINIO_ACCESS_KEY: логин для подключения
            - MINIO_SECRET_KEY: пароль для подключения
            - MINIO_USE_SSL: использовать ли шифрование (true/false)

        Returns:
        ---------------
            Экземпляр класса MinioConfiguration

        Raises:
        ---------------
            ValueError: если значение MINIO_USE_SSL некорректно
            TypeError: если типы данных не соответствуют ожидаемым

        Examples:
        ---------------
            >>> config = MinioConfiguration.from_env()
            >>> isinstance(config.use_ssl, bool)
            True
        """
        # Получение значения MINIO_USE_SSL из окружения и преобразование в boolean
        ssl_value = os.getenv('MINIO_USE_SSL', 'false').lower()

        if ssl_value not in ('true', 'false'):
            raise ValueError("MINIO_USE_SSL должно быть 'true' или 'false'")

        return cls(
            host=os.getenv('MINIO_HOST', 'localhost'),
            api_port=os.getenv('MINIO_API_PORT', '9000'),
            access_key=os.getenv('MINIO_ACCESS_KEY', 'minioadmin'),
            secret_key=os.getenv('MINIO_SECRET_KEY', 'minioadmin'),
            use_ssl=ssl_value == 'true'
        )


# ------------------------------
# Создаем глобальную конфигурацию из переменных окружения
# ------------------------------
# Используется в других частях приложения как minio_config
minio_config = MinioConfiguration.from_env()