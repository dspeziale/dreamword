# ==============================================================================
# framework/networking/http_client.py - HTTP Client Semplificato
# ==============================================================================

"""
HTTP Client per ModularFramework
Versione semplificata usando solo requests (sincrono)
"""

import requests
from typing import Any, Dict, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class Response:
    """Risposta HTTP standardizzata"""
    status: int
    data: Any
    headers: Dict[str, str]
    url: str
    success: bool


class HTTPClient:
    """Client HTTP semplificato (solo sincrono)"""

    def __init__(self, config):
        """
        Inizializza HTTP client

        Args:
            config: Configurazione networking
        """
        self.config = config
        self.timeout = getattr(config, 'http_timeout', 30)
        self.user_agent = getattr(config, 'user_agent', 'ModularFramework/1.0')
        self.retry_attempts = getattr(config, 'retry_attempts', 3)

    def get(self, url: str, **kwargs) -> Response:
        """GET sincrono"""
        return self._request("GET", url, **kwargs)

    def post(self, url: str, data: Any = None, json: Any = None, **kwargs) -> Response:
        """POST sincrono"""
        return self._request("POST", url, data=data, json=json, **kwargs)

    def put(self, url: str, data: Any = None, json: Any = None, **kwargs) -> Response:
        """PUT sincrono"""
        return self._request("PUT", url, data=data, json=json, **kwargs)

    def delete(self, url: str, **kwargs) -> Response:
        """DELETE sincrono"""
        return self._request("DELETE", url, **kwargs)

    def _request(self, method: str, url: str, **kwargs) -> Response:
        """Esegue richiesta HTTP"""
        kwargs.setdefault("timeout", self.timeout)
        kwargs.setdefault("headers", {}).update({
            "User-Agent": self.user_agent
        })

        last_exception = None

        for attempt in range(self.retry_attempts):
            try:
                response = requests.request(method, url, **kwargs)

                # Prova a parsare JSON
                try:
                    data = response.json()
                except:
                    data = response.text

                return Response(
                    status=response.status_code,
                    data=data,
                    headers=dict(response.headers),
                    url=response.url,
                    success=200 <= response.status_code < 300
                )

            except Exception as e:
                last_exception = e
                if attempt < self.retry_attempts - 1:
                    logger.warning(f"Tentativo {attempt + 1} fallito per {url}: {e}")
                    continue

        # Tutti i tentativi falliti
        return Response(
            status=0,
            data=str(last_exception),
            headers={},
            url=url,
            success=False
        )

    # Metodi asincroni placeholder (per compatibilità)
    async def aget(self, url: str, **kwargs) -> Response:
        """GET asincrono (implementazione sincrona)"""
        return self.get(url, **kwargs)

    async def apost(self, url: str, data: Any = None, json: Any = None, **kwargs) -> Response:
        """POST asincrono (implementazione sincrona)"""
        return self.post(url, data=data, json=json, **kwargs)

    async def close(self):
        """Placeholder per chiusura (compatibilità)"""
        pass