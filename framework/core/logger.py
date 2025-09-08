# framework/core/logger.py

"""
Sistema di logging per ModularFramework - FIXED
"""

from loguru import logger
import sys
from pathlib import Path
from typing import Optional


def setup_logger(config) -> logger:
    """Setup sistema di logging avanzato"""

    # Rimuovi handler default
    logger.remove()

    # Ottieni configurazioni con fallback
    try:
        log_level = config.logging.level
        logs_dir = getattr(config, 'logs_dir', Path('./logs'))
        log_format = getattr(config.logging, 'format',
                             "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> - <level>{message}</level>")
        console_enabled = getattr(config.logging, 'console_enabled', True)
        file_enabled = getattr(config.logging, 'file_enabled', True)
    except AttributeError:
        # Fallback se la configurazione non è completa
        log_level = "INFO"
        logs_dir = Path('./logs')
        log_format = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> - <level>{message}</level>"
        console_enabled = True
        file_enabled = True

    # Console handler con colori (se abilitato)
    if console_enabled:
        logger.add(
            sys.stdout,
            format=log_format,
            level=log_level,
            colorize=True
        )

    # File handler (se abilitato)
    if file_enabled:
        try:
            # Assicura che logs_dir sia un Path object
            if isinstance(logs_dir, str):
                logs_dir = Path(logs_dir)

            logs_dir.mkdir(parents=True, exist_ok=True)
            log_file = logs_dir / "app.log"

            logger.add(
                str(log_file),
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
                level="DEBUG",
                rotation="10 MB",
                retention="30 days",
                compression="zip"
            )
        except Exception as e:
            # Se il file logging fallisce, almeno tieni la console
            print(f"⚠️ Warning: File logging fallito: {e}")

    return logger