import pytest
from framework import ModularFramework
from framework.plugins.base import Plugin


class TestPlugin(Plugin):
    """Plugin di test"""

    def __init__(self, framework_instance):
        super().__init__(framework_instance)
        self.description = "Plugin di test"
        self.initialized = False

    def initialize(self) -> bool:
        self.initialized = True
        return True

    def cleanup(self):
        self.initialized = False

    def test_method(self):
        return "test_result"


class TestPlugins:
    """Test suite per sistema plugin"""

    def test_plugin_loading(self, framework_instance):
        """Test caricamento plugin"""
        # Registra plugin di test manualmente
        plugin_instance = TestPlugin(framework_instance)
        framework_instance.plugins.plugins["test_plugin"] = plugin_instance
        plugin_instance.initialize()

        assert "test_plugin" in framework_instance.plugins.list_plugins()
        assert plugin_instance.initialized is True

    def test_plugin_methods(self, framework_instance):
        """Test metodi plugin"""
        plugin_instance = TestPlugin(framework_instance)
        framework_instance.plugins.plugins["test_plugin"] = plugin_instance
        plugin_instance.initialize()

        # Test metodo personalizzato
        result = plugin_instance.test_method()
        assert result == "test_result"

    def test_plugin_unloading(self, framework_instance):
        """Test scaricamento plugin"""
        plugin_instance = TestPlugin(framework_instance)
        framework_instance.plugins.plugins["test_plugin"] = plugin_instance
        plugin_instance.initialize()

        # Verifica che sia caricato
        assert "test_plugin" in framework_instance.plugins.list_plugins()

        # Scarica plugin
        framework_instance.plugins.unload_plugin("test_plugin")

        # Verifica che sia scaricato
        assert "test_plugin" not in framework_instance.plugins.list_plugins()
        assert plugin_instance.initialized is False