# framework/networking/server.py
from aiohttp import web, WSMsgType
import aiohttp_cors
from typing import Dict, Callable, List, Optional
import json
import logging
import weakref
from datetime import datetime

logger = logging.getLogger(__name__)


class WebSocketConnection:
    """Rappresenta una connessione WebSocket"""

    def __init__(self, ws: web.WebSocketResponse, client_id: str = None):
        self.ws = ws
        self.client_id = client_id or str(id(ws))
        self.connected_at = datetime.now()
        self.metadata = {}

    async def send_json(self, data: Dict):
        """Invia dati JSON"""
        try:
            await self.ws.send_str(json.dumps(data))
            return True
        except Exception as e:
            logger.error(f"Errore invio JSON a {self.client_id}: {e}")
            return False

    async def send_text(self, text: str):
        """Invia testo"""
        try:
            await self.ws.send_str(text)
            return True
        except Exception as e:
            logger.error(f"Errore invio testo a {self.client_id}: {e}")
            return False


class HTTPServer:
    """Server HTTP con supporto WebSocket"""

    def __init__(self, config):
        self.config = config
        self.app = web.Application()
        self.routes: Dict[str, Callable] = {}
        self.websocket_handlers: Dict[str, Callable] = {}
        self.websocket_connections: Dict[str, WebSocketConnection] = {}
        self.middleware_funcs = []

        # Setup CORS
        self.cors = aiohttp_cors.setup(self.app, defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods="*"
            )
        })

        # Route predefinite
        self.app.router.add_get('/health', self._health_check)
        self.app.router.add_get('/ws', self._websocket_handler)
        self.app.router.add_get('/status', self._status_endpoint)
        self.app.router.add_get('/connections', self._connections_info)

        # Aggiungi CORS alle route
        for route in list(self.app.router.routes()):
            self.cors.add(route)

    def add_middleware(self, middleware_func: Callable):
        """Aggiunge middleware"""
        self.middleware_funcs.append(middleware_func)
        self.app.middlewares.append(middleware_func)

    def add_route(self, path: str, handler: Callable, methods: List[str] = ['GET']):
        """Aggiunge route HTTP"""
        for method in methods:
            route = self.app.router.add_route(method, path, handler)
            self.cors.add(route)
        logger.info(f"Route aggiunta: {methods} {path}")

    def add_websocket_handler(self, message_type: str, handler: Callable):
        """Aggiunge handler WebSocket"""
        self.websocket_handlers[message_type] = handler
        logger.info(f"WebSocket handler aggiunto per: {message_type}")

    async def _health_check(self, request):
        """Endpoint health check"""
        return web.json_response({
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "active_connections": len(self.websocket_connections)
        })

    async def _status_endpoint(self, request):
        """Endpoint stato server"""
        return web.json_response({
            "server": "ModularFramework HTTP Server",
            "version": "1.0.0",
            "active_connections": len(self.websocket_connections),
            "uptime": str(datetime.now() - getattr(self, 'start_time', datetime.now())),
            "routes_count": len(list(self.app.router.routes())),
            "websocket_handlers": list(self.websocket_handlers.keys())
        })

    async def _connections_info(self, request):
        """Informazioni sulle connessioni WebSocket"""
        connections_info = []
        for client_id, conn in self.websocket_connections.items():
            connections_info.append({
                "client_id": client_id,
                "connected_at": conn.connected_at.isoformat(),
                "metadata": conn.metadata
            })

        return web.json_response({
            "total_connections": len(self.websocket_connections),
            "connections": connections_info
        })

    async def _websocket_handler(self, request):
        """Handler WebSocket principale"""
        ws = web.WebSocketResponse(heartbeat=30)
        await ws.prepare(request)

        # Genera ID client unico
        client_id = request.headers.get('X-Client-ID', str(id(ws)))
        connection = WebSocketConnection(ws, client_id)

        # Aggiungi metadata dalla richiesta
        connection.metadata = {
            'user_agent': request.headers.get('User-Agent', ''),
            'remote': request.remote,
            'query_params': dict(request.query)
        }

        self.websocket_connections[client_id] = connection
        logger.info(f"Nuova connessione WebSocket: {client_id}")

        # Invia messaggio di benvenuto
        await connection.send_json({
            "type": "connection_established",
            "client_id": client_id,
            "timestamp": datetime.now().isoformat()
        })

        try:
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    await self._handle_websocket_text(connection, msg.data)
                elif msg.type == WSMsgType.BINARY:
                    await self._handle_websocket_binary(connection, msg.data)
                elif msg.type == WSMsgType.ERROR:
                    logger.error(f'WebSocket error {client_id}: {ws.exception()}')
                    break
        except Exception as e:
            logger.error(f"Errore gestione WebSocket {client_id}: {e}")
        finally:
            # Rimuovi connessione
            if client_id in self.websocket_connections:
                del self.websocket_connections[client_id]
            logger.info(f"Connessione WebSocket chiusa: {client_id}")

        return ws

    async def _handle_websocket_text(self, connection: WebSocketConnection, text: str):
        """Gestisce messaggio di testo WebSocket"""
        try:
            data = json.loads(text)
            await self._handle_websocket_message(connection, data)
        except json.JSONDecodeError:
            # Non è JSON, tratta come messaggio di testo semplice
            await self._handle_websocket_message(connection, {
                "type": "text_message",
                "content": text
            })

    async def _handle_websocket_binary(self, connection: WebSocketConnection, data: bytes):
        """Gestisce messaggio binario WebSocket"""
        await self._handle_websocket_message(connection, {
            "type": "binary_message",
            "data": data,
            "size": len(data)
        })

    async def _handle_websocket_message(self, connection: WebSocketConnection, data: Dict):
        """Gestisce messaggio WebSocket processato"""
        message_type = data.get("type", "default")

        # Aggiungi metadata al messaggio
        data["client_id"] = connection.client_id
        data["timestamp"] = datetime.now().isoformat()

        if message_type in self.websocket_handlers:
            try:
                response = await self.websocket_handlers[message_type](data, connection)
                if response:
                    await connection.send_json(response)
            except Exception as e:
                logger.error(f"Errore handler {message_type}: {e}")
                await connection.send_json({
                    "type": "error",
                    "message": f"Errore processamento messaggio: {str(e)}"
                })
        else:
            # Handler di default
            if "default" in self.websocket_handlers:
                await self.websocket_handlers["default"](data, connection)
            else:
                await connection.send_json({
                    "type": "error",
                    "message": f"Handler non trovato per tipo: {message_type}"
                })

    async def broadcast(self, message: Dict, exclude_client: str = None):
        """Invia messaggio a tutti i client WebSocket"""
        if not self.websocket_connections:
            return 0

        message["broadcast_timestamp"] = datetime.now().isoformat()
        successful_sends = 0

        # Lista di connessioni da rimuovere (se morte)
        dead_connections = []

        for client_id, connection in self.websocket_connections.items():
            if exclude_client and client_id == exclude_client:
                continue

            try:
                success = await connection.send_json(message)
                if success:
                    successful_sends += 1
                else:
                    dead_connections.append(client_id)
            except Exception as e:
                logger.error(f"Errore broadcast a {client_id}: {e}")
                dead_connections.append(client_id)

        # Rimuovi connessioni morte
        for client_id in dead_connections:
            del self.websocket_connections[client_id]
            logger.info(f"Rimossa connessione morta: {client_id}")

        logger.debug(f"Broadcast inviato a {successful_sends} client")
        return successful_sends

    async def send_to_client(self, client_id: str, message: Dict) -> bool:
        """Invia messaggio a un client specifico"""
        if client_id not in self.websocket_connections:
            return False

        connection = self.websocket_connections[client_id]
        return await connection.send_json(message)

    def get_connected_clients(self) -> List[str]:
        """Ottieni lista ID client connessi"""
        return list(self.websocket_connections.keys())

    def get_client_count(self) -> int:
        """Ottieni numero client connessi"""
        return len(self.websocket_connections)

    async def start(self):
        """Avvia server"""
        self.start_time = datetime.now()
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.config.host, self.config.port)
        await site.start()
        logger.info(f"🚀 Server avviato su http://{self.config.host}:{self.config.port}")
        return runner


# Esempio handler WebSocket
"""
async def chat_handler(data, connection):
    message = data.get('message', '')
    room = data.get('room', 'general')

    # Broadcast a tutti nella stanza
    broadcast_msg = {
        "type": "chat_message",
        "message": message,
        "room": room,
        "sender": connection.client_id
    }

    # In un'implementazione reale, filtreresti per stanza
    await server.broadcast(broadcast_msg, exclude_client=connection.client_id)

    return {"type": "message_sent", "status": "ok"}

server.add_websocket_handler("chat", chat_handler)
"""