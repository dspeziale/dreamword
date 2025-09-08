# framework/networking/server.py
import socket
import threading
import logging
from typing import Callable, Optional, Dict, Any
import json


class SimpleServer:
    """Server TCP semplice per ricevere connessioni"""

    def __init__(self, host: str = "0.0.0.0", port: int = 8080):
        self.host = host
        self.port = port
        self.running = False
        self.server_socket = None
        self.logger = logging.getLogger(__name__)
        self.client_handler: Optional[Callable] = None
        self.clients: Dict[str, socket.socket] = {}

    def set_client_handler(self, handler: Callable[[socket.socket, str], None]):
        """Imposta il gestore per le connessioni client"""
        self.client_handler = handler

    def default_client_handler(self, client_socket: socket.socket, address: str):
        """Gestore predefinito per i client"""
        try:
            while True:
                data = client_socket.recv(1024)
                if not data:
                    break

                # Echo del messaggio
                response = f"Echo: {data.decode('utf-8')}"
                client_socket.send(response.encode('utf-8'))

        except Exception as e:
            self.logger.error(f"Errore gestione client {address}: {e}")
        finally:
            client_socket.close()
            if address in self.clients:
                del self.clients[address]
            self.logger.info(f"Client {address} disconnesso")

    def start(self):
        """Avvia il server"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)

            self.running = True
            self.logger.info(f"Server avviato su {self.host}:{self.port}")

            while self.running:
                try:
                    client_socket, address = self.server_socket.accept()
                    client_id = f"{address[0]}:{address[1]}"
                    self.clients[client_id] = client_socket

                    self.logger.info(f"Nuova connessione da {client_id}")

                    # Usa il gestore personalizzato o quello predefinito
                    handler = self.client_handler or self.default_client_handler

                    # Avvia thread per gestire il client
                    client_thread = threading.Thread(
                        target=handler,
                        args=(client_socket, client_id),
                        daemon=True
                    )
                    client_thread.start()

                except socket.error as e:
                    if self.running:
                        self.logger.error(f"Errore accept: {e}")

        except Exception as e:
            self.logger.error(f"Errore avvio server: {e}")
        finally:
            self.stop()

    def stop(self):
        """Ferma il server"""
        self.running = False

        # Chiude tutte le connessioni client
        for client_id, client_socket in self.clients.items():
            try:
                client_socket.close()
            except:
                pass
        self.clients.clear()

        # Chiude il socket del server
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass

        self.logger.info("Server fermato")

    def broadcast_message(self, message: str):
        """Invia un messaggio a tutti i client connessi"""
        disconnected = []

        for client_id, client_socket in self.clients.items():
            try:
                client_socket.send(message.encode('utf-8'))
            except:
                disconnected.append(client_id)

        # Rimuove client disconnessi
        for client_id in disconnected:
            if client_id in self.clients:
                del self.clients[client_id]