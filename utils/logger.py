# framework/utils/logger.py
import logging
import logging.handlers
import os
from datetime import datetime
from typing import Optional


def setup_logger(name: str = "framework",
                 level: str = "INFO",
                 log_file: Optional[str] = None,
                 max_file_size: int = 10 * 1024 * 1024,  # 10MB
                 backup_count: int = 5) -> logging.Logger:
    """
    Configura il sistema di logging per il framework

    Args:
        name: Nome del logger
        level: Livello di logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path del file di log (opzionale)
        max_file_size: Dimensione massima file di log in bytes
        backup_count: Numero di file di backup da mantenere

    Returns:
        Logger configurato
    """

    # Converte stringa livello in costante logging
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }

    log_level = level_map.get(level.upper(), logging.INFO)

    # Crea logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    # Evita duplicazione se già configurato
    if logger.handlers:
        return logger

    # Formattatore
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Handler console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Handler file se specificato
    if log_file:
        # Crea directory se non esiste
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # Rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    logger.info(f"Logger '{name}' configurato - livello: {level}")
    return logger