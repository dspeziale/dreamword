# ==============================================================================
# framework/plugins/base.py - Plugin Base Class
# ==============================================================================

"""
Classe base per plugin del ModularFramework
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
import logging

logger = logging.getLogger(__name__)


class Plugin(ABC):
    """Classe base per tutti i plugin del framework"""

    def __init__(self, framework_instance):
        """
        Inizializza plugin

        Args:
            framework_instance: Istanza del framework principale
        """
        self.framework = framework_instance
        self.name = self.__class__.__name__
        self.version = getattr(self, 'version', '1.0.0')
        self.description = getattr(self, 'description', '')
        self.author = getattr(self, 'author', '')

        # Stato plugin
        self.is_initialized = False
        self.is_active = False

        # Logger specifico del plugin
        self.logger = logging.getLogger(f"plugin.{self.name}")

    @abstractmethod
    def initialize(self) -> bool:
        """
        Inizializza il plugin

        Returns:
            True se inizializzazione riuscita
        """
        pass

    @abstractmethod
    def cleanup(self):
        """Pulisce risorse del plugin"""
        pass

    def get_info(self) -> Dict[str, Any]:
        """
        Informazioni sul plugin

        Returns:
            Dizionario con informazioni plugin
        """
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "initialized": self.is_initialized,
            "active": self.is_active,
            "class": self.__class__.__name__,
            "module": self.__class__.__module__
        }

    def get_commands(self) -> Dict[str, callable]:
        """
        Comandi CLI del plugin

        Returns:
            Dizionario nome_comando -> funzione
        """
        return {}

    def get_api_routes(self) -> Dict[str, tuple]:
        """
        Route API del plugin

        Returns:
            Dizionario path -> (metodi, handler)
        """
        return {}

    def __repr__(self):
        return f"Plugin({self.name} v{self.version}, active={self.is_active})"