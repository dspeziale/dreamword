# framework/networking/websocket_client.py
import asyncio
import websockets
from typing import Callable, Optional, Dict, Any
import json
import logging

logger = logging.getLogger(__name__)


class WebSocketClient:
    """Client WebSocket asincrono"""

    def __init__(self, uri: str, config):
        self.uri = uri
        self.config = config
        self.websocket = None
        self.is_connected = False
        self.message_handlers: Dict[str, Callable] = {}
        self.auto_reconnect = True
        self.reconnect_delay = 5

    async def connect(self) -> bool:
        """Connetti al server WebSocket"""
        try:
            self.websocket = await websockets.connect(
                self.uri,
                timeout=self.config.http_timeout,
                ping_interval=20,
                ping_timeout=10
            )
            self.is_connected = True
            logger.info(f"Connesso a WebSocket: {self.uri}")
            return True
        except Exception as e:
            logger.error(f"Errore connessione WebSocket: {e}")
            return False

    async def disconnect(self):
        """Disconnetti dal server"""
        self.auto_reconnect = False
        if self.websocket:
            await self.websocket.close()
            self.is_connected = False
            logger.info("WebSocket disconnesso")

    async def send_message(self, message: Dict[str, Any]) -> bool:
        """Invia messaggio JSON"""
        if not self.is_connected:
            logger.warning("WebSocket non connesso")
            return False

        try:
            await self.websocket.send(json.dumps(message))
            logger.debug(f"Messaggio inviato: {message}")
            return True
        except Exception as e:
            logger.error(f"Errore invio messaggio: {e}")
            return False

    async def send_text(self, text: str) -> bool:
        """Invia messaggio di testo"""
        if not self.is_connected:
            return False

        try:
            await self.websocket.send(text)
            return True
        except Exception as e:
            logger.error(f"Errore invio testo: {e}")
            return False

    async def listen(self):
        """Ascolta messaggi in arrivo con auto-reconnect"""
        while self.auto_reconnect:
            try:
                if not self.is_connected:
                    await self.connect()
                    if not self.is_connected:
                        await asyncio.sleep(self.reconnect_delay)
                        continue

                async for message in self.websocket:
                    try:
                        # Prova a parsare come JSON
                        data = json.loads(message)
                        await self._handle_message(data)
                    except json.JSONDecodeError:
                        # Messaggio non JSON - gestisci come testo
                        await self._handle_message({"type": "text", "data": message})

            except websockets.exceptions.ConnectionClosed:
                logger.warning("Connessione WebSocket chiusa")
                self.is_connected = False
                if self.auto_reconnect:
                    logger.info(f"Tentativo riconnessione in {self.reconnect_delay} secondi...")
                    await asyncio.sleep(self.reconnect_delay)
            except Exception as e:
                logger.error(f"Errore nel loop di ascolto: {e}")
                self.is_connected = False
                if self.auto_reconnect:
                    await asyncio.sleep(self.reconnect_delay)

    def register_handler(self, message_type: str, handler: Callable):
        """Registra handler per tipo di messaggio"""
        self.message_handlers[message_type] = handler
        logger.debug(f"Handler registrato per tipo: {message_type}")

    async def _handle_message(self, data: Dict[str, Any]):
        """Gestisce messaggio ricevuto"""
        message_type = data.get("type", "default")

        if message_type in self.message_handlers:
            try:
                await self.message_handlers[message_type](data)
            except Exception as e:
                logger.error(f"Errore nell'handler {message_type}: {e}")
        else:
            # Handler di default
            if "default" in self.message_handlers:
                await self.message_handlers["default"](data)
            else:
                logger.debug(f"Nessun handler per tipo messaggio: {message_type}")


# Esempio di uso
"""
async def message_handler(data):
    print(f"Messaggio ricevuto: {data}")

ws_client = WebSocketClient("ws://localhost:8080/ws", config)
ws_client.register_handler("chat", message_handler)

await ws_client.connect()
await ws_client.send_message({"type": "join", "room": "general"})

# Avvia listener in background
asyncio.create_task(ws_client.listen())
"""