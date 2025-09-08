import pytest
import asyncio
from framework import ModularFramework
from framework.networking.server import HTTPServer


class TestNetworking:
    """Test suite per networking"""

    def test_http_client_sync(self, framework_instance):
        """Test HTTP client sincrono"""
        response = framework_instance.http.get("https://httpbin.org/json")

        assert response is not None
        assert response.status == 200
        assert response.success is True
        assert isinstance(response.data, dict)

    @pytest.mark.asyncio
    async def test_http_client_async(self, framework_instance):
        """Test HTTP client asincrono"""
        response = await framework_instance.http.aget("https://httpbin.org/uuid")

        assert response is not None
        assert response.status == 200
        assert response.success is True
        assert 'uuid' in response.data

    @pytest.mark.asyncio
    async def test_http_post(self, framework_instance):
        """Test HTTP POST"""
        test_data = {"test": "data", "number": 42}
        response = await framework_instance.http.apost(
            "https://httpbin.org/post",
            json=test_data
        )

        assert response.success is True
        assert response.status == 200
        assert response.data['json'] == test_data

    def test_http_error_handling(self, framework_instance):
        """Test gestione errori HTTP"""
        # URL non valido
        response = framework_instance.http.get("https://invalid-url-that-does-not-exist.com")
        assert response.success is False
        assert response.status == 0

    @pytest.mark.asyncio
    async def test_server_creation(self, framework_instance):
        """Test creazione server"""
        server = HTTPServer(framework_instance.config.networking)
        assert server is not None

        # Test route aggiunta
        async def test_route(request):
            from aiohttp import web
            return web.json_response({"test": "ok"})

        server.add_route('/test', test_route, ['GET'])

        # Verifica che la route sia stata aggiunta
        routes = list(server.app.router.routes())
        test_routes = [r for r in routes if str(r.resource) == '/test']
        assert len(test_routes) > 0