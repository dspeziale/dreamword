# framework/__init__.py
"""
Framework Python per applicazioni di rete e database
Utilizza la directory 'instance' per log e database
"""

__version__ = "1.0.0"
__author__ = "Il tuo nome"

from .config import get_config, set_base_directory
from .database import SQLiteManager, MSSQLManager
from .networking import HeartBeat, SimpleServer, NetworkInfo
from .scanner import NmapScanner
from .utils import setup_logger, get_default_logger

__all__ = [
    'get_config',
    'set_base_directory',
    'SQLiteManager',
    'MSSQLManager',
    'HeartBeat',
    'SimpleServer',
    'NetworkInfo',
    'NmapScanner',
    'setup_logger',
    'get_default_logger'
]