# framework/core/logger.py
from loguru import logger
import sys
from pathlib import Path
from typing import Optional


def setup_logger(config) -> logger:
    """Setup sistema di logging avanzato"""

    # Rimuovi handler default
    logger.remove()

    # Console handler con colori
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=config.log_level,
        colorize=True
    )

    # File handler
    log_file = config.logs_dir / "app.log"
    config.logs_dir.mkdir(exist_ok=True)

    logger.add(
        str(log_file),
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        rotation="10 MB",
        retention="30 days",
        compression="zip"
    )

    return logger