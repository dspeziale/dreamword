# framework/core/__init__.py

"""
Core components del ModularFramework - FIXED
"""

from .config import (
    FrameworkConfig, DatabaseConfig, NetworkingConfig,
    LoggingConfig, SecurityConfig, PluginConfig, CacheConfig,
    get_config, reset_config
)

from .exceptions import (
    FrameworkError, DatabaseError, NetworkingError,
    PluginError, ConfigurationError
)

from .logger import setup_logger

# Import base solo se esiste
try:
    from .base import (
        BaseComponent, ConfigurableComponent,
        EventEmitter, ServiceComponent, Result
    )
except ImportError:
    # File base.py non esiste, crea placeholder
    class BaseComponent:
        pass


    class ConfigurableComponent:
        pass


    class EventEmitter:
        pass


    class ServiceComponent:
        pass


    class Result:
        def __init__(self, success: bool, data=None, error=None):
            self.success = success
            self.data = data
            self.error = error

__all__ = [
    # Config
    'FrameworkConfig', 'DatabaseConfig', 'NetworkingConfig',
    'LoggingConfig', 'SecurityConfig', 'PluginConfig', 'CacheConfig',
    'get_config', 'reset_config',

    # Exceptions
    'FrameworkError', 'DatabaseError', 'NetworkingError',
    'PluginError', 'ConfigurationError',

    # Logger
    'setup_logger',

    # Base classes
    'BaseComponent', 'ConfigurableComponent',
    'EventEmitter', 'ServiceComponent', 'Result'
]