# app/s3/client.py
"""
Модуль реализует клиент MinIO для работы с S3-совместимым хранилищем.
Предоставляет ограниченный функционал: проверка существования бакетов и директорий,
скачивание файлов из директорий в локальную папку temp.
"""

import os
import logging
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass

# ------------------------------
# Внешние зависимости
# ------------------------------
from minio import Minio
from minio.error import S3Error

# ------------------------------
# Локальные импорты
# ------------------------------
from config.configuration_minio import MinioConfiguration, minio_config


# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MinioException(Exception):
    """
    Description:
    ---------------
        Кастомное исключение для ошибок, связанных с MinIO.

    Args:
    ---------------
        Принимает сообщение об ошибке

    Returns:
    ---------------
        Исключение типа MinioException

    Raises:
    ---------------
        Никогда напрямую не вызывается, служит базовым классом

    Examples:
    ---------------
        >>> try:
        ...     raise MinioException("Test error")
        ... except MinioException as e:
        ...     print(e)
        Test error
    """
    pass


class MinioClient:
    """
    Description:
    ---------------
        Сервис для работы с MinIO. Предоставляет ограниченный набор функций:
        - Проверка существования бакетов
        - Проверка существования директорий
        - Скачивание файлов из директорий в локальную папку temp

    Args:
    ---------------
        config: Экземпляр MinioConfiguration

    Returns:
    ---------------
        Экземпляр MinioClient

    Raises:
    ---------------
        S3Error: Ошибки, возникающие при взаимодействии с MinIO
        MinioException: Обёртка над S3Error для внутреннего использования

    Examples:
    ---------------
        >>> client = MinioClient(minio_config)
        >>> client.is_bucket_exists("test-bucket")
        True
    """
    
    def __init__(self, config: MinioConfiguration):
        self.config = config
        self.client = self._create_client()
        self.temp_dir = Path("temp")
        self._ensure_temp_directory()

    def _create_client(self) -> Minio:
        """
        Description:
        ---------------
            Создает клиентское соединение с MinIO.

        Args:
        ---------------
            Используется конфигурация, переданная в __init__

        Returns:
        ---------------
            Экземпляр клиента MinIO

        Raises:
        ---------------
            S3Error: Ошибка создания клиента MinIO

        Examples:
        ---------------
            >>> client = self._create_client()
            >>> isinstance(client, Minio)
            True
        """
        endpoint = f"{self.config.host}:{self.config.api_port}"
        return Minio(
            endpoint=endpoint,
            access_key=self.config.access_key,
            secret_key=self.config.secret_key,
            secure=self.config.use_ssl
        )

    def _ensure_temp_directory(self):
        """
        Description:
        ---------------
            Убеждается, что временная директория существует.

        Args:
        ---------------
            Используется self.temp_dir — путь к временной директории

        Returns:
        ---------------
            None

        Raises:
        ---------------
            MinioException: Если не удалось создать директорию

        Examples:
        ---------------
            >>> self._ensure_temp_directory()
            Directory created or already exists
        """
        if not self.temp_dir.exists():
            self.temp_dir.mkdir(parents=True)
            logger.info(f"Created temp directory: {self.temp_dir}")

    def is_bucket_exists(self, bucket_name: str) -> bool:
        """
        Description:
        ---------------
            Проверяет, существует ли указанный бакет в MinIO.

        Args:
        ---------------
            bucket_name: Имя бакета

        Returns:
        ---------------
            True если бакет существует, False в противном случае

        Raises:
        ---------------
            MinioException: Если проверка не удалась

        Examples:
        ---------------
            >>> client.is_bucket_exists("test-bucket")
            True
        """
        try:
            return self.client.bucket_exists(bucket_name)
        except Exception as e:
            logger.error(f"Error checking bucket existence: {str(e)}", exc_info=True)
            raise MinioException(f"Error checking bucket existence: {str(e)}") from e

    def is_directory_exists(self, bucket_name: str, directory_path: str) -> bool:
        """
        Description:
        ---------------
            Проверяет наличие указанной директории в бакете.

        Args:
        ---------------
            bucket_name: Имя бакета
            directory_path: Путь к директории в бакете

        Returns:
        ---------------
            True если директория содержит объекты, False в противном случае

        Raises:
        ---------------
            MinioException: Если проверка не удалась

        Examples:
        ---------------
            >>> client.is_directory_exists("test-bucket", "recordings/2024/")
            True
        """
        try:
            # Убеждаемся, что путь заканчивается на '/'
            if not directory_path.endswith('/'):
                directory_path += '/'

            # Проверяем наличие объектов в директории
            objects = self.client.list_objects(
                bucket_name=bucket_name,
                prefix=directory_path,
                recursive=False
            )

            # Если есть хотя бы один объект, директория существует
            for _ in objects:
                return True

            return False

        except Exception as e:
            message = f"Error checking directory existence: {bucket_name}/{directory_path}: {str(e)}"
            logger.error(message, exc_info=True)
            raise MinioException(message) from e

    def download_files_from_directory(self, bucket_name: str, directory_path: str,
                                      preserve_structure: bool = True) -> List[str]:
        """
        Description:
        ---------------
            Скачивает все файлы из указанной директории в локальную папку temp.

        Args:
        ---------------
            bucket_name: Имя бакета
            directory_path: Путь к директории в бакете
            preserve_structure: Сохранять ли структуру директорий при скачивании

        Returns:
        ---------------
            Список путей к скачанным файлам

        Raises:
        ---------------
            MinioException: Если скачивание не удалось

        Examples:
        ---------------
            >>> files = client.download_files_from_directory("test-bucket", "recordings/2024/")
            >>> len(files) > 0
            True
        """
        downloaded_files = []

        try:
            # Проверяем существование бакета
            if not self.is_bucket_exists(bucket_name):
                raise MinioException(f"Bucket '{bucket_name}' does not exist")

            # Убеждаемся, что путь заканчивается на '/'
            if not directory_path.endswith('/'):
                directory_path += '/'

            # Получаем список всех объектов в директории
            objects = self.client.list_objects(
                bucket_name=bucket_name,
                prefix=directory_path,
                recursive=True
            )

            object_count = 0
            for obj in objects:
                # Пропускаем "директории" (объекты, заканчивающиеся на '/')
                if obj.object_name.endswith('/'):
                    continue

                object_count += 1

                # Определяем локальный путь для сохранения
                if preserve_structure:
                    # Сохраняем структуру директорий
                    local_path = self.temp_dir / obj.object_name
                else:
                    # Сохраняем все файлы в корень temp
                    local_path = self.temp_dir / Path(obj.object_name).name

                # Создаём родительские директории если нужно
                local_path.parent.mkdir(parents=True, exist_ok=True)

                # Скачиваем файл
                logger.info(f"Downloading: {obj.object_name} -> {local_path}")
                self.client.fget_object(
                    bucket_name=bucket_name,
                    object_name=obj.object_name,
                    file_path=str(local_path)
                )

                downloaded_files.append(str(local_path))

            if object_count == 0:
                logger.warning(f"No files found in directory: {bucket_name}/{directory_path}")
            else:
                logger.info(f"Successfully downloaded {object_count} files from {bucket_name}/{directory_path}")

            return downloaded_files

        except MinioException:
            raise
        except Exception as e:
            message = f"Error downloading files from {bucket_name}/{directory_path}: {str(e)}"
            logger.error(message, exc_info=True)
            raise MinioException(message) from e

    def clear_temp_directory(self):
        """
        Description:
        ---------------
            Очищает временную директорию temp.

        Args:
        ---------------
            Используется self.temp_dir — путь к временной директории

        Returns:
        ---------------
            None

        Raises:
        ---------------
            MinioException: Если очистка не удалась

        Examples:
        ---------------
            >>> client.clear_temp_directory()
            Temp directory cleared
        """
        try:
            import shutil
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                self.temp_dir.mkdir()
                logger.info("Temp directory cleared")
        except Exception as e:
            logger.error(f"Error clearing temp directory: {str(e)}", exc_info=True)
            raise MinioException(f"Error clearing temp directory: {str(e)}") from e


# ------------------------------
# Глобальный клиент MinIO
# ------------------------------
# Инициализируется один раз при импорте модуля
minio_client = MinioClient(minio_config)