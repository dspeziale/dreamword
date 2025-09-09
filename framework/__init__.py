# framework/__init__.py
"""
Database Framework - Un framework semplice e flessibile per gestire database multipli
"""

from .database_framework import (
    DatabaseManager,
    DatabaseConfig,
    DatabaseType,
    DatabaseFactory
)
from .exceptions import (
    DatabaseError,
    ConnectionError,
    DuplicateKeyError,
    ConstraintViolationError
)

__version__ = "1.0.0"
__author__ = "Database Framework Team"

__all__ = [
    'DatabaseManager',
    'DatabaseConfig',
    'DatabaseType',
    'DatabaseFactory',
    'DatabaseError',
    'ConnectionError',
    'DuplicateKeyError',
    'ConstraintViolationError'
]