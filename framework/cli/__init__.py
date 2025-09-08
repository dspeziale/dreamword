# framework/cli/__init__.py

"""
CLI components del ModularFramework

Interfaccia command line con Rich
"""

try:
    from .commands import cli
except ImportError:
    cli = None

__all__ = ['cli']
