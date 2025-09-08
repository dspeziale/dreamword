# ==============================================================================
# examples/complete_usage_example.py - Esempio completo di utilizzo
# ==============================================================================

"""
Esempio completo del framework che dimostra tutte le funzionalità:
- Configurazione database SQLite/MSSQL
- Client HTTP sincrono e asincrono
- Sistema plugin
- Server HTTP con WebSocket
- Gestione errori e logging
"""

import asyncio
import sys
from pathlib import Path
from framework import ModularFramework
from framework.database.models import Configuration, LogEntry
from framework.networking.server import HTTPServer
import json


async def complete_example():
    """Esempio completo di tutte le funzionalità"""

    print("🚀 === FRAMEWORK MODULAR - ESEMPIO COMPLETO ===\n")

    try:
        # =======================================================================
        # 1. INIZIALIZZAZIONE FRAMEWORK
        # =======================================================================
        print("📋 1. Inizializzazione Framework...")
        fw = ModularFramework()

        # Configura per uso demo
        fw.config.debug = True
        fw.config.log_level = "INFO"

        print(f"   ✅ Framework inizializzato")
        print(f"   📊 Database provider: {fw.config.database.provider}")
        print(f"   🌐 Server: {fw.config.networking.host}:{fw.config.networking.port}")

        # =======================================================================
        # 2. SETUP DATABASE
        # =======================================================================
        print("\n📊 2. Setup Database...")
        fw.setup_database()

        # Test connessione
        with fw.db.get_session() as session:
            test_result = fw.db.execute_query("SELECT 1 as test")
            if test_result and test_result[0]['test'] == 1:
                print("   ✅ Database connesso e funzionante")
            else:
                raise Exception("Database test fallito")

        # Inserimento dati di esempio
        with fw.db.get_session() as session:
            # Configurazioni
            configs = [
                Configuration(key="app_name", value="Framework Demo", description="Nome applicazione"),
                Configuration(key="version", value="1.0.0", description="Versione app"),
                Configuration(key="max_users", value="100", description="Numero massimo utenti")
            ]

            for config in configs:
                existing = session.query(Configuration).filter(Configuration.key == config.key).first()
                if not existing:
                    session.add(config)

            session.commit()
            print("   ✅ Dati di esempio inseriti")

        # =======================================================================
        # 3. TEST NETWORKING
        # =======================================================================
        print("\n🌐 3. Test Networking...")

        # HTTP Client sincrono
        print("   🔄 Test HTTP sincrono...")
        response = fw.http.get("https://httpbin.org/json")
        if response.success:
            print(f"   ✅ HTTP GET: {response.status}")
        else:
            print(f"   ❌ HTTP GET fallito: {response.status}")

        # HTTP Client asincrono
        print("   🔄 Test HTTP asincrono...")
        async_response = await fw.http.aget("https://httpbin.org/uuid")
        if async_response.success:
            print(f"   ✅ HTTP Async GET: {async_response.status}")
            uuid_data = async_response.data.get('uuid', 'N/A')
            print(f"   📦 UUID ricevuto: {uuid_data}")
        else:
            print(f"   ❌ HTTP Async GET fallito: {async_response.status}")

        # Test POST
        test_data = {"demo": True, "timestamp": "2024-01-01T12:00:00Z"}
        post_response = await fw.http.apost("https://httpbin.org/post", json=test_data)
        if post_response.success:
            print(f"   ✅ HTTP POST: {post_response.status}")

        # =======================================================================
        # 4. SISTEMA PLUGIN
        # =======================================================================
        print("\n🔌 4. Sistema Plugin...")

        # Carica plugin
        plugin_names = ["example_plugin", "cache_plugin"]
        for plugin_name in plugin_names:
            try:
                if fw.plugins.load_plugin(plugin_name):
                    print(f"   ✅ Plugin caricato: {plugin_name}")
                else:
                    print(f"   ⚠️  Plugin non trovato: {plugin_name}")
            except Exception as e:
                print(f"   ❌ Errore caricamento {plugin_name}: {e}")

        # Test plugin example_plugin
        example_plugin = fw.plugins.get_plugin("example_plugin")
        if example_plugin:
            # Test storage
            test_data = {
                "demo_key": "demo_value",
                "numbers": [1, 2, 3, 4, 5],
                "config": {"enabled": True, "level": "advanced"}
            }

            for key, value in test_data.items():
                example_plugin.store_data(key, value, expires_in_days=1)

            # Test retrieval
            retrieved = example_plugin.get_data("demo_key")
            if retrieved == "demo_value":
                print("   ✅ Plugin storage/retrieval funzionante")

            # Aggiungi task
            example_plugin.add_task("health_check")
            example_plugin.add_task("stats_update")

            # Statistiche
            stats = example_plugin.get_statistics()
            print(f"   📊 Plugin stats: {stats['data_store_size']} items, {stats['queue_size']} tasks")

        # Test cache plugin
        cache_plugin = fw.plugins.get_plugin("cache_plugin")
        if cache_plugin:
            # Test cache
            cache_plugin.set("test_key", "test_value", ttl=60)
            cached_value = cache_plugin.get("test_key")
            if cached_value == "test_value":
                print("   ✅ Cache plugin funzionante")

            cache_stats = cache_plugin.stats()
            print(f"   🗄️  Cache: {cache_stats['items_count']} items")

        # =======================================================================
        # 5. SERVER HTTP/WEBSOCKET
        # =======================================================================
        print("\n🌐 5. Avvio Server HTTP/WebSocket...")

        # Crea server
        server = HTTPServer(fw.config.networking)

        # Route personalizzate
        async def demo_api(request):
            from aiohttp import web

            # Ottieni dati dal database
            with fw.db.get_session() as session:
                configs = session.query(Configuration).all()
                config_data = {c.key: c.value for c in configs}

            # Statistiche plugin
            plugin_stats = {}
            for plugin_name in fw.plugins.list_plugins():
                plugin = fw.plugins.get_plugin(plugin_name)
                if hasattr(plugin, 'get_statistics'):
                    plugin_stats[plugin_name] = plugin.get_statistics()

            return web.json_response({
                "status": "ok",
                "message": "Framework Demo API",
                "database_configs": config_data,
                "loaded_plugins": fw.plugins.list_plugins(),
                "plugin_statistics": plugin_stats,
                "server_info": {
                    "framework_version": "1.0.0",
                    "python_version": sys.version
                }
            })

        async def demo_websocket_handler(data, connection):
            """Handler per messaggi WebSocket demo"""
            message_type = data.get('type', 'unknown')

            if message_type == 'get_stats':
                # Invia statistiche
                stats = {
                    'plugins': len(fw.plugins.list_plugins()),
                    'database_configs': len(fw.db.execute_query("SELECT COUNT(*) as count FROM configurations")[0]),
                    'client_id': connection.client_id
                }
                return {"type": "stats_response", "data": stats}

            elif message_type == 'echo':
                # Echo del messaggio
                return {"type": "echo_response", "original": data}

            elif message_type == 'plugin_command':
                # Esegui comando plugin
                plugin_name = data.get('plugin')
                command = data.get('command')
                args = data.get('args', [])

                plugin = fw.plugins.get_plugin(plugin_name)
                if plugin and hasattr(plugin, command):
                    try:
                        result = getattr(plugin, command)(*args)
                        return {"type": "command_result", "result": result}
                    except Exception as e:
                        return {"type": "error", "message": str(e)}
                else:
                    return {"type": "error", "message": "Plugin o comando non trovato"}

            return {"type": "unknown_message", "received": data}

        # Registra route e handlers
        server.add_route('/api/demo', demo_api, ['GET'])
        server.add_websocket_handler('demo', demo_websocket_handler)
        server.add_websocket_handler('get_stats', demo_websocket_handler)
        server.add_websocket_handler('echo', demo_websocket_handler)
        server.add_websocket_handler('plugin_command', demo_websocket_handler)

        # Avvia server
        runner = await server.start()
        print(f"   ✅ Server avviato su http://{fw.config.networking.host}:{fw.config.networking.port}")

        # =======================================================================
        # 6. TEST COMPLETO API
        # =======================================================================
        print("\n🧪 6. Test API Complete...")

        # Test endpoint demo
        api_url = f"http://localhost:{fw.config.networking.port}/api/demo"
        api_response = await fw.http.aget(api_url)

        if api_response.success:
            print("   ✅ API demo endpoint funzionante")
            api_data = api_response.data
            print(f"   📊 Configs in DB: {len(api_data.get('database_configs', {}))}")
            print(f"   🔌 Plugin caricati: {len(api_data.get('loaded_plugins', []))}")
        else:
            print(f"   ❌ API test fallito: {api_response.status}")

        # =======================================================================
        # 7. STATISTICHE FINALI
        # =======================================================================
        print("\n📈 7. Statistiche Finali...")

        # Database stats
        with fw.db.get_session() as session:
            config_count = len(session.query(Configuration).all())
            print(f"   📊 Configurazioni DB: {config_count}")

        # Plugin stats
        for plugin_name in fw.plugins.list_plugins():
            plugin = fw.plugins.get_plugin(plugin_name)
            if hasattr(plugin, 'get_statistics'):
                stats = plugin.get_statistics()
                print(f"   🔌 {plugin_name}: {stats.get('data_store_size', 0)} items")

        # Server stats
        print(f"   🌐 Server connessioni: {server.get_client_count()}")

        print("\n🎉 === ESEMPIO COMPLETATO CON SUCCESSO ===")
        print("\n💡 Endpoint disponibili:")
        print(f"   🩺 Health Check: http://localhost:{fw.config.networking.port}/health")
        print(f"   📊 Status: http://localhost:{fw.config.networking.port}/status")
        print(f"   🔌 WebSocket: ws://localhost:{fw.config.networking.port}/ws")
        print(f"   🎯 Demo API: http://localhost:{fw.config.networking.port}/api/demo")

        print("\n⏳ Server in esecuzione... Premi Ctrl+C per fermarlo")

        # Mantieni server attivo
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Fermando server...")
            await runner.cleanup()
            await fw.cleanup()
            print("✅ Framework chiuso correttamente")

    except Exception as e:
        print(f"\n❌ ERRORE: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


# Test WebSocket separato
async def websocket_client_test():
    """Test client WebSocket"""
    from framework.networking.websocket_client import WebSocketClient
    from framework import ModularFramework

    fw = ModularFramework()

    # Crea client WebSocket
    ws_client = WebSocketClient("ws://localhost:8000/ws", fw.config.networking)

    # Handler per messaggi
    async def message_handler(data):
        print(f"📨 WebSocket ricevuto: {data}")

    ws_client.register_handler("stats_response", message_handler)
    ws_client.register_handler("echo_response", message_handler)
    ws_client.register_handler("default", message_handler)

    # Connetti
    if await ws_client.connect():
        print("✅ WebSocket client connesso")

        # Invia messaggi di test
        await ws_client.send_message({"type": "get_stats"})
        await ws_client.send_message({"type": "echo", "message": "Hello WebSocket!"})

        # Ascolta per 10 secondi
        listen_task = asyncio.create_task(ws_client.listen())
        await asyncio.sleep(10)

        # Disconnetti
        await ws_client.disconnect()
        listen_task.cancel()
        print("✅ WebSocket client disconnesso")
    else:
        print("❌ Impossibile connettersi al WebSocket")


if __name__ == "__main__":
    # Verifica se è un test WebSocket separato
    if len(sys.argv) > 1 and sys.argv[1] == "websocket":
        asyncio.run(websocket_client_test())
    else:
        asyncio.run(complete_example())