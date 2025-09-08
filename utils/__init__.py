# framework/utils/__init__.py
from .logger import setup_logger

# Funzione per logger con path automatico
def get_default_logger(name: str = "framework", level: str = "INFO"):
    """Crea un logger con configurazione automatica dei path"""
    try:
        from ..config import get_log_path
        log_file = get_log_path(f"{name}")
        return setup_logger(name, level, log_file)
    except ImportError:
        # Fallback se config non disponibile
        return setup_logger(name, level)

__all__ = ['setup_logger', 'get_default_logger']