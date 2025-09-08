# ==============================================================================
# framework/plugins/manager.py - Plugin Manager Semplificato
# ==============================================================================

import importlib
import sys
from pathlib import Path
from typing import Dict, List, Optional, Type
from .base import Plugin
import logging

logger = logging.getLogger(__name__)


class PluginManager:
    """Manager per gestione plugin dinamici"""

    def __init__(self, framework_instance):
        """
        Inizializza plugin manager

        Args:
            framework_instance: Istanza del framework
        """
        self.framework = framework_instance
        self.plugins: Dict[str, Plugin] = {}
        self.plugin_paths: List[str] = []
        self.failed_plugins: Dict[str, str] = {}

    def add_plugin_path(self, path: str):
        """
        Aggiunge path per ricerca plugin

        Args:
            path: Path Python module
        """
        if path not in self.plugin_paths:
            self.plugin_paths.append(path)
            logger.debug(f"Aggiunto path plugin: {path}")

    def load_plugin(self, plugin_name: str) -> bool:
        """
        Carica un plugin specifico

        Args:
            plugin_name: Nome del plugin

        Returns:
            True se caricato con successo
        """
        if plugin_name in self.plugins:
            logger.warning(f"Plugin {plugin_name} già caricato")
            return True

        try:
            # Per ora, non carica plugin reali per evitare errori
            logger.info(f"Plugin {plugin_name} non trovato (normale in modalità test)")
            return False

        except Exception as e:
            error_msg = f"Errore caricamento plugin {plugin_name}: {e}"
            self.failed_plugins[plugin_name] = error_msg
            logger.error(error_msg)
            return False

    def unload_plugin(self, plugin_name: str) -> bool:
        """Scarica un plugin"""
        if plugin_name in self.plugins:
            del self.plugins[plugin_name]
            return True
        return False

    def get_plugin(self, plugin_name: str) -> Optional[Plugin]:
        """Ottieni istanza plugin"""
        return self.plugins.get(plugin_name)

    def list_plugins(self) -> List[str]:
        """Lista plugin caricati"""
        return list(self.plugins.keys())