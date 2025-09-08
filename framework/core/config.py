# framework/core/config.py

"""
Sistema di configurazione centralizzato per ModularFramework
Fix completo per Pydantic v2
"""

import os
from typing import Any, Dict, Optional, Union, List
from pathlib import Path
from dotenv import load_dotenv

# Pydantic v2 imports
try:
    from pydantic_settings import BaseSettings
    from pydantic import Field, ConfigDict

    PYDANTIC_V2 = True
except ImportError:
    try:
        from pydantic import BaseSettings, Field

        ConfigDict = None
        PYDANTIC_V2 = False
    except ImportError:
        raise ImportError("Pydantic non installato. Installa con: pip install pydantic pydantic-settings")

# Carica file .env se presente
env_file = Path(".env")
if env_file.exists():
    load_dotenv(env_file)


class DatabaseConfig(BaseSettings):
    """Configurazione database"""

    provider: str = Field(default="sqlite")
    sqlite_path: str = Field(default="./data/app.db")

    # MSSQL
    mssql_server: Optional[str] = Field(default=None)
    mssql_database: Optional[str] = Field(default=None)
    mssql_username: Optional[str] = Field(default=None)
    mssql_password: Optional[str] = Field(default=None)
    mssql_driver: str = Field(default="ODBC Driver 17 for SQL Server")
    mssql_trusted_connection: bool = Field(default=False)
    mssql_port: int = Field(default=1433)

    # Pool
    pool_size: int = Field(default=5)
    max_overflow: int = Field(default=10)
    pool_timeout: int = Field(default=30)
    pool_recycle: int = Field(default=3600)

    # Logging
    echo: bool = Field(default=False)
    echo_pool: bool = Field(default=False)

    if PYDANTIC_V2:
        model_config = ConfigDict(extra="ignore")


class NetworkingConfig(BaseSettings):
    """Configurazione networking"""

    http_timeout: int = Field(default=30)
    max_connections: int = Field(default=100)
    retry_attempts: int = Field(default=3)
    retry_delay: float = Field(default=1.0)
    user_agent: str = Field(default="ModularFramework/1.0")

    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    workers: int = Field(default=1)

    if PYDANTIC_V2:
        model_config = ConfigDict(extra="ignore")


class LoggingConfig(BaseSettings):
    """Configurazione logging"""

    level: str = Field(default="INFO")
    format: str = Field(
        default="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> - <level>{message}</level>")
    file_enabled: bool = Field(default=True)
    console_enabled: bool = Field(default=True)

    if PYDANTIC_V2:
        model_config = ConfigDict(extra="ignore")


class SecurityConfig(BaseSettings):
    """Configurazione sicurezza"""

    api_key_length: int = Field(default=32)
    api_key_prefix: str = Field(default="fw_")
    password_min_length: int = Field(default=8)
    rate_limit_enabled: bool = Field(default=True)

    if PYDANTIC_V2:
        model_config = ConfigDict(extra="ignore")


class PluginConfig(BaseSettings):
    """Configurazione plugin"""

    builtin_dir: str = Field(default="framework.plugins.builtin")
    external_dir: str = Field(default="./plugins_external")
    auto_load: bool = Field(default=True)
    enabled: List[str] = Field(default_factory=list)

    if PYDANTIC_V2:
        model_config = ConfigDict(extra="ignore")


class CacheConfig(BaseSettings):
    """Configurazione cache"""

    enabled: bool = Field(default=True)
    default_ttl: int = Field(default=300)
    max_size: int = Field(default=1000)
    backend: str = Field(default="memory")

    if PYDANTIC_V2:
        model_config = ConfigDict(extra="ignore")


class FrameworkConfig(BaseSettings):
    """Configurazione principale del framework"""

    # Informazioni generali
    name: str = Field(default="ModularFramework")
    version: str = Field(default="1.0.0")
    description: str = Field(default="Framework Python modulare")

    # Modalità
    debug: bool = Field(default=False)
    testing: bool = Field(default=False)
    production: bool = Field(default=False)

    # Directory - usando stringhe invece di Path per evitare problemi
    data_dir: str = Field(default="./data")
    plugins_dir: str = Field(default="./plugins_external")
    logs_dir: str = Field(default="./logs")
    temp_dir: str = Field(default="./temp")

    # Configurazioni moduli - usando default semplici
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    networking: NetworkingConfig = Field(default_factory=NetworkingConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    plugins: PluginConfig = Field(default_factory=PluginConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)

    def __init__(self, **data):
        """Inizializzazione personalizzata per creare directory"""
        super().__init__(**data)
        # Crea directory dopo inizializzazione
        for dir_name in ['data_dir', 'plugins_dir', 'logs_dir', 'temp_dir']:
            dir_path = Path(getattr(self, dir_name))
            dir_path.mkdir(parents=True, exist_ok=True)
            # Aggiorna con Path object
            setattr(self, dir_name, dir_path)

    def is_development(self) -> bool:
        return self.debug and not self.production

    def is_production(self) -> bool:
        return self.production and not self.debug

    def get_environment(self) -> str:
        if self.production:
            return "production"
        elif self.testing:
            return "testing"
        elif self.debug:
            return "development"
        else:
            return "unknown"

    def to_dict(self) -> Dict[str, Any]:
        if PYDANTIC_V2:
            return self.model_dump()
        else:
            return self.dict()

    # Configurazione Pydantic v2 - MOLTO PERMISSIVA
    if PYDANTIC_V2:
        model_config = ConfigDict(
            extra="ignore",  # Ignora tutti i campi extra
            validate_assignment=False,  # Non validare assignment
            arbitrary_types_allowed=True,  # Permetti tipi arbitrari
            env_nested_delimiter="__"
        )
    else:
        class Config:
            extra = "ignore"
            validate_assignment = False
            arbitrary_types_allowed = True
            env_nested_delimiter = "__"


# Istanza singleton
_config_instance: Optional[FrameworkConfig] = None


def get_config() -> FrameworkConfig:
    """Ottieni istanza singleton della configurazione"""
    global _config_instance
    if _config_instance is None:
        try:
            _config_instance = FrameworkConfig()
        except Exception as e:
            # Fallback con configurazione vuota
            print(f"⚠️ Errore configurazione, uso default: {e}")
            _config_instance = FrameworkConfig.model_construct() if PYDANTIC_V2 else FrameworkConfig()
    return _config_instance


def reset_config():
    """Reset configurazione"""
    global _config_instance
    _config_instance = None


# Esportazioni
__all__ = [
    'FrameworkConfig',
    'DatabaseConfig',
    'NetworkingConfig',
    'LoggingConfig',
    'SecurityConfig',
    'PluginConfig',
    'CacheConfig',
    'get_config',
    'reset_config'
]