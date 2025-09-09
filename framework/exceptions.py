# framework/exceptions.py

"""
Eccezioni personalizzate per il Database Framework
"""

class DatabaseError(Exception):
    """Eccezione base per errori database generici"""
    pass

class ConnectionError(DatabaseError):
    """Eccezione per errori di connessione"""
    pass

class DuplicateKeyError(DatabaseError):
    """Eccezione per violazioni di chiavi duplicate"""
    pass

class ConstraintViolationError(DatabaseError):
    """Eccezione per violazioni di constraint"""
    pass

class ConfigurationError(DatabaseError):
    """Eccezione per errori di configurazione"""
    pass

class QueryError(DatabaseError):
    """Eccezione per errori nelle query"""
    pass