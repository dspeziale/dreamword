# framework/networking/__init__.py

"""
Networking components del ModularFramework

HTTP client, WebSocket client e server HTTP/WebSocket
"""

from .http_client import HTTPClient, Response

try:
    from .websocket_client import WebSocketClient
except ImportError:
    WebSocketClient = None

try:
    from .server import HTTPServer, WebSocketConnection
except ImportError:
    HTTPServer = None
    WebSocketConnection = None

__all__ = [
    'HTTPClient', 'Response',
    'WebSocketClient',
    'HTTPServer', 'WebSocketConnection'
]