# framework/plugins/__init__.py

"""
Plugin system del ModularFramework

Sistema di plugin dinamico e estensibile
"""

from .base import Plugin
from .manager import PluginManager

__all__ = [
    'Plugin',
    'PluginManager'
]