# framework/database/__init__.py

"""
Database components del ModularFramework

Supporta SQLite e MSSQL con SQLAlchemy ORM
"""

from .manager import DatabaseManager, DatabaseProvider
from .models import Base, BaseModel, Configuration, LogEntry, PluginData, SessionData, ApiKey

try:
    from .sqlite_provider import SQLiteProvider
except ImportError:
    SQLiteProvider = None

try:
    from .mssql_provider import MSSQLProvider
except ImportError:
    MSSQLProvider = None

__all__ = [
    'DatabaseManager', 'DatabaseProvider',
    'Base', 'BaseModel', 'Configuration', 'LogEntry',
    'PluginData', 'SessionData', 'ApiKey',
    'SQLiteProvider', 'MSSQLProvider'
]
