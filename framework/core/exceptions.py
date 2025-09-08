# framework/core/exceptions.py

class FrameworkError(Exception):
    """Eccezione base del framework"""
    pass

class DatabaseError(FrameworkError):
    """Errori database"""
    pass

class NetworkingError(FrameworkError):
    """Errori networking"""
    pass

class PluginError(FrameworkError):
    """Errori plugin"""
    pass

class ConfigurationError(FrameworkError):
    """Errori configurazione"""
    pass

class ValidationError(FrameworkError):
    """Errori validazione dati"""
    pass

class AuthenticationError(FrameworkError):
    """Errori autenticazione"""
    pass

class AuthorizationError(FrameworkError):
    """Errori autorizzazione"""
    pass