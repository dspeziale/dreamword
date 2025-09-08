# framework/utils/logger.py
import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path
from typing import Optional


def setup_logger(name: str = "framework",
                 level: str = "INFO",
                 log_file: Optional[str] = None,
                 max_file_size: int = 10 * 1024 * 1024,  # 10MB
                 backup_count: int = 5,
                 force_instance_dir: bool = True) -> logging.Logger:
    """
    Configura il sistema di logging per il framework

    Args:
        name: Nome del logger
        level: Livello di logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path del file di log (opzionale)
        max_file_size: Dimensione massima file di log in bytes
        backup_count: Numero di file di backup da mantenere
        force_instance_dir: Se True, forza l'uso della directory instance

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

    # Handler file se specificato o se force_instance_dir è True
    if log_file or force_instance_dir:
        if log_file is None and force_instance_dir:
            # Genera automaticamente il path usando config
            log_file = _get_auto_log_path(name)

        # Usa il path fornito o quello auto-generato
        final_log_path = _ensure_instance_directory(log_file)

        # Crea directory se non esiste
        log_dir = os.path.dirname(final_log_path)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # Rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            final_log_path,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        logger.info(f"Logger '{name}' configurato - livello: {level} - file: {final_log_path}")
    else:
        logger.info(f"Logger '{name}' configurato - livello: {level} - solo console")

    return logger


def _get_auto_log_path(logger_name: str) -> str:
    """Genera automaticamente un path per il log usando il config"""
    try:
        # Tenta di usare il sistema di config
        from ..config import get_log_path
        return get_log_path(logger_name)
    except ImportError:
        # Fallback manuale
        return _get_fallback_log_path(logger_name)


def _get_fallback_log_path(logger_name: str) -> str:
    """Genera path di fallback per i log"""
    # Trova la directory del progetto
    current_file = Path(__file__).resolve()

    # Cerca di andare alla root del progetto
    project_root = current_file.parent.parent.parent
    if not (project_root / "framework").exists():
        project_root = Path.cwd()

    # Crea directory logs in instance
    logs_dir = project_root / "instance" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    log_filename = logger_name if logger_name.endswith('.log') else f"{logger_name}.log"
    return str(logs_dir / log_filename)


def _ensure_instance_directory(log_file: str) -> str:
    """Assicura che il log vada nella directory instance"""
    log_path = Path(log_file)

    # Se il path è già sotto instance, ok
    if "instance" in log_path.parts:
        return str(log_path)

    # Altrimenti, sposta sotto instance/logs
    try:
        from ..config import get_log_path
        filename = log_path.name
        return get_log_path(filename)
    except ImportError:
        # Fallback
        return _get_fallback_log_path(log_path.stem)


def get_logger_info() -> dict:
    """Ritorna informazioni sui logger attivi"""
    active_loggers = {}

    # Ottiene tutti i logger attivi
    for name in logging.Logger.manager.loggerDict:
        logger = logging.getLogger(name)
        if logger.handlers:
            handlers_info = []
            for handler in logger.handlers:
                handler_info = {
                    "type": type(handler).__name__,
                    "level": logging.getLevelName(handler.level)
                }
                if hasattr(handler, 'baseFilename'):
                    handler_info["file"] = handler.baseFilename
                handlers_info.append(handler_info)

            active_loggers[name] = {
                "level": logging.getLevelName(logger.level),
                "handlers": handlers_info
            }

    return active_loggers


def cleanup_old_logs(days_to_keep: int = 30):
    """Pulisce i log più vecchi di X giorni"""
    try:
        from ..config import get_config
        logs_dir = Path(get_config().logs_dir)
    except ImportError:
        # Fallback
        logs_dir = Path.cwd() / "instance" / "logs"

    if not logs_dir.exists():
        return

    from datetime import datetime, timedelta
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)

    removed_count = 0
    for log_file in logs_dir.glob("*.log*"):
        try:
            if log_file.stat().st_mtime < cutoff_date.timestamp():
                log_file.unlink()
                removed_count += 1
        except Exception:
            continue

    print(f"Rimossi {removed_count} file di log più vecchi di {days_to_keep} giorni")