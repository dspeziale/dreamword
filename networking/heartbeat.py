# framework/networking/heartbeat.py
import socket
import time
import threading
import logging
from typing import Callable, Optional


class HeartBeat:
    """Sistema di heartbeat per monitorare connessioni"""

    def __init__(self, target_host: str, target_port: int, interval: int = 30):
        self.target_host = target_host
        self.target_port = target_port
        self.interval = interval
        self.running = False
        self.thread = None
        self.logger = logging.getLogger(__name__)
        self.on_failure_callback: Optional[Callable] = None
        self.on_success_callback: Optional[Callable] = None

    def set_failure_callback(self, callback: Callable):
        """Imposta callback per errori di connessione"""
        self.on_failure_callback = callback

    def set_success_callback(self, callback: Callable):
        """Imposta callback per connessioni riuscite"""
        self.on_success_callback = callback

    def check_connection(self) -> bool:
        """Verifica se il target è raggiungibile"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((self.target_host, self.target_port))
            sock.close()
            return result == 0
        except Exception as e:
            self.logger.error(f"Errore heartbeat: {e}")
            return False

    def _heartbeat_loop(self):
        """Loop principale del heartbeat"""
        while self.running:
            is_alive = self.check_connection()

            if is_alive:
                self.logger.debug(f"Heartbeat OK: {self.target_host}:{self.target_port}")
                if self.on_success_callback:
                    try:
                        self.on_success_callback()
                    except Exception as e:
                        self.logger.error(f"Errore callback success: {e}")
            else:
                self.logger.warning(f"Heartbeat FAILED: {self.target_host}:{self.target_port}")
                if self.on_failure_callback:
                    try:
                        self.on_failure_callback()
                    except Exception as e:
                        self.logger.error(f"Errore callback failure: {e}")

            time.sleep(self.interval)

    def start(self):
        """Avvia il monitoraggio heartbeat"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
            self.thread.start()
            self.logger.info(f"Heartbeat avviato per {self.target_host}:{self.target_port}")

    def stop(self):
        """Ferma il monitoraggio heartbeat"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
            self.logger.info("Heartbeat fermato")