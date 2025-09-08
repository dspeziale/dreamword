# framework/__init__.py

"""
ModularFramework - Framework Python modulare e estensibile - FIXED
"""

from typing import Optional, List
import asyncio
import sys
from pathlib import Path

# Core imports
from .core.config import get_config, FrameworkConfig
from .core.logger import setup_logger
from .core.exceptions import FrameworkError

# Database imports
from .database.manager import DatabaseManager

# Networking imports
from .networking.http_client import HTTPClient

# Plugin imports
from .plugins.manager import PluginManager

# Version
__version__ = "1.0.0"
__author__ = "Framework Team"
__license__ = "MIT"


class ModularFramework:
    """
    Classe principale del Framework Modulare - FIXED
    """

    def __init__(self, config_path: Optional[str] = None, config_override: Optional[dict] = None):
        """
        Inizializza il framework

        Args:
            config_path: Path opzionale al file di configurazione
            config_override: Dizionario per override configurazione
        """
        # Carica configurazione
        self.config = get_config()

        # Applica override se forniti
        if config_override:
            self._apply_config_override(config_override)

        # Setup logging - FIXED per usare config.logging.level
        self.logger = setup_logger(self.config)

        # Flag per stato inizializzazione
        self._initialized = False
        self._database_setup = False

        # Inizializza componenti core
        try:
            self._initialize_core_components()
            self._initialized = True
            self.logger.info(f"🚀 ModularFramework v{__version__} inizializzato")

        except Exception as e:
            self.logger.error(f"❌ Errore inizializzazione framework: {e}")
            raise FrameworkError(f"Inizializzazione fallita: {e}")

    def _apply_config_override(self, override: dict):
        """Applica override alla configurazione"""
        # Semplice update diretto degli attributi
        for key, value in override.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)

    def _initialize_core_components(self):
        """Inizializza componenti core del framework"""
        self.logger.debug("🔧 Inizializzazione componenti core...")

        # Crea directory necessarie
        self._ensure_directories()

        # Inizializza database manager
        self.logger.debug("📊 Inizializzazione database manager...")
        self.db = DatabaseManager(self.config.database)

        # Inizializza HTTP client
        self.logger.debug("🌐 Inizializzazione HTTP client...")
        self.http = HTTPClient(self.config.networking)

        # Inizializza plugin manager
        self.logger.debug("🔌 Inizializzazione plugin manager...")
        self.plugins = PluginManager(self)

        # Setup plugin paths
        self._setup_plugin_paths()

        self.logger.debug("✅ Componenti core inizializzati")

    def _ensure_directories(self):
        """Crea directory necessarie se non esistono"""
        directories = [
            self.config.data_dir,
            self.config.plugins_dir,
            self.config.logs_dir
        ]

        for directory in directories:
            if isinstance(directory, str):
                directory = Path(directory)
            directory.mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"📁 Directory assicurata: {directory}")

    def _setup_plugin_paths(self):
        """Configura percorsi per plugin"""
        # Plugin builtin
        self.plugins.add_plugin_path("framework.plugins.builtin")

        # Plugin esterni
        plugins_dir = self.config.plugins_dir
        if isinstance(plugins_dir, str):
            plugins_dir = Path(plugins_dir)

        if plugins_dir.exists():
            # Aggiunge directory plugins al Python path se necessario
            plugins_str = str(plugins_dir.absolute())
            if plugins_str not in sys.path:
                sys.path.insert(0, plugins_str)

            self.plugins.add_plugin_path("plugins_external")
            self.logger.debug(f"🔌 Path plugin esterni: {plugins_dir}")

    def setup_database(self, create_tables: bool = True):
        """
        Configura il database

        Args:
            create_tables: Se True, crea le tabelle se non esistono
        """
        if self._database_setup:
            self.logger.warning("⚠️ Database già configurato")
            return

        try:
            self.logger.info("📊 Setup database...")

            if create_tables:
                self.db.create_tables()
                self.logger.info(f"✅ Tabelle create/verificate")

            # Test connessione
            with self.db.get_session() as session:
                result = self.db.execute_query("SELECT 1 as test")
                if result and result[0]['test'] == 1:
                    self.logger.info(f"✅ Database funzionante ({self.config.database.provider})")
                    self._database_setup = True
                else:
                    raise FrameworkError("Test connessione database fallito")

        except Exception as e:
            self.logger.error(f"❌ Errore setup database: {e}")
            raise FrameworkError(f"Setup database fallito: {e}")

    def load_plugins(self, plugin_names: Optional[List[str]] = None, ignore_errors: bool = True):
        """
        Carica plugin specificati o dalla configurazione

        Args:
            plugin_names: Lista nomi plugin da caricare (None = usa config)
            ignore_errors: Se True, continua anche se alcuni plugin falliscono
        """
        plugins_to_load = plugin_names or self.config.plugins.enabled

        if not plugins_to_load:
            self.logger.info("ℹ️ Nessun plugin da caricare")
            return

        self.logger.info(f"🔌 Caricamento {len(plugins_to_load)} plugin...")

        loaded_count = 0
        failed_count = 0

        for plugin_name in plugins_to_load:
            try:
                if self.plugins.load_plugin(plugin_name):
                    self.logger.info(f"✅ Plugin caricato: {plugin_name}")
                    loaded_count += 1
                else:
                    self.logger.error(f"❌ Errore caricamento: {plugin_name}")
                    failed_count += 1
                    if not ignore_errors:
                        raise FrameworkError(f"Caricamento plugin {plugin_name} fallito")

            except Exception as e:
                self.logger.error(f"❌ Eccezione caricamento {plugin_name}: {e}")
                failed_count += 1
                if not ignore_errors:
                    raise

        self.logger.info(f"📊 Plugin caricati: {loaded_count}, falliti: {failed_count}")

    def get_plugin(self, plugin_name: str):
        """Ottieni istanza di un plugin caricato"""
        return self.plugins.get_plugin(plugin_name)

    def list_loaded_plugins(self) -> List[str]:
        """Ottieni lista plugin caricati"""
        return self.plugins.list_plugins()

    def get_status(self) -> dict:
        """
        Ottieni stato corrente del framework

        Returns:
            Dizionario con informazioni di stato
        """
        status = {
            "framework": {
                "version": __version__,
                "initialized": self._initialized,
                "database_setup": self._database_setup
            },
            "database": {
                "provider": self.config.database.provider,
                "connected": False
            },
            "plugins": {
                "loaded": self.plugins.list_plugins(),
                "count": len(self.plugins.list_plugins())
            },
            "configuration": {
                "debug": self.config.debug,
                "environment": self.config.get_environment()
            }
        }

        # Test connessione database
        try:
            with self.db.get_session() as session:
                result = self.db.execute_query("SELECT 1 as test")
                status["database"]["connected"] = bool(result and result[0]['test'] == 1)
        except:
            status["database"]["connected"] = False

        return status

    def health_check(self) -> dict:
        """
        Esegue controllo salute completo

        Returns:
            Risultati health check
        """
        health = {
            "overall": "healthy",
            "checks": {},
            "timestamp": None
        }

        # Check database
        try:
            with self.db.get_session() as session:
                result = self.db.execute_query("SELECT 1 as test")
                if result and result[0]['test'] == 1:
                    health["checks"]["database"] = {"status": "healthy", "details": "Connection OK"}
                else:
                    health["checks"]["database"] = {"status": "unhealthy", "details": "Query failed"}
                    health["overall"] = "unhealthy"
        except Exception as e:
            health["checks"]["database"] = {"status": "unhealthy", "details": str(e)}
            health["overall"] = "unhealthy"

        # Check plugin
        plugin_status = []
        for plugin_name in self.plugins.list_plugins():
            plugin = self.plugins.get_plugin(plugin_name)
            if plugin:
                plugin_status.append({"name": plugin_name, "status": "loaded"})
            else:
                plugin_status.append({"name": plugin_name, "status": "error"})

        health["checks"]["plugins"] = {
            "status": "healthy",
            "details": f"{len(plugin_status)} plugins loaded",
            "plugins": plugin_status
        }

        return health

    async def cleanup(self):
        """
        Cleanup completo del framework
        """
        self.logger.info("🧹 Cleanup framework...")

        try:
            # Chiudi HTTP client asincrono
            if hasattr(self.http, 'close'):
                await self.http.close()
                self.logger.debug("🌐 HTTP client chiuso")

            # Scarica tutti i plugin
            for plugin_name in list(self.plugins.plugins.keys()):
                self.plugins.unload_plugin(plugin_name)
                self.logger.debug(f"🔌 Plugin scaricato: {plugin_name}")

            # Cleanup database connections se necessario
            if hasattr(self.db, 'close'):
                self.db.close()
                self.logger.debug("📊 Connessioni database chiuse")

            self.logger.info("✅ Framework chiuso correttamente")

        except Exception as e:
            self.logger.error(f"❌ Errore durante cleanup: {e}")
            raise FrameworkError(f"Cleanup fallito: {e}")

    def __repr__(self):
        """Rappresentazione stringa del framework"""
        return (
            f"ModularFramework(version={__version__}, "
            f"db={self.config.database.provider}, "
            f"plugins={len(self.plugins.list_plugins())}, "
            f"initialized={self._initialized})"
        )


# Export principali
__all__ = [
    'ModularFramework',
    'FrameworkConfig',
    'get_config',
    'FrameworkError',
    '__version__'
]

# Convenience imports per uso diretto
from .core.config import FrameworkConfig
from .core.exceptions import FrameworkError