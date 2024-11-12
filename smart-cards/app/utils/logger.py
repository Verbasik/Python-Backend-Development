# app/utils/logger.py
"""
Description:
    Утилиты для логирования.
"""

# Стандартные библиотеки
import logging
from typing import logging


def setup_logger() -> logging:
    """
    Description:
        Настраивает и возвращает логгер приложения.

    Returns:
        logging.Logger: Настроенный логгер
        
    Examples:
        >>> logger = setup_logger()
        >>> logger.info("Application started")
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)