# framework/cli/commands.py
import click
from rich.console import Console
from rich.table import Table
from rich.progress import track, Progress
from rich.panel import Panel
from rich.text import Text
import asyncio
import json
import sys
from pathlib import Path

console = Console()


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """🚀 Framework CLI - Strumento da linea di comando"""
    pass


@cli.group()
def db():
    """💾 Comandi database"""
    pass


@db.command()
@click.option('--provider', default='sqlite', type=click.Choice(['sqlite', 'mssql']),
              help='Provider database')
@click.option('--path', default='./data/app.db', help='Path database (SQLite)')
@click.option('--force', is_flag=True, help='Forza reinizializzazione')
def init(provider, path, force):
    """Inizializza database"""
    from framework import ModularFramework

    console.print("🔧 Inizializzazione database...", style="blue")

    try:
        # Configura framework
        fw = ModularFramework()
        fw.config.database.provider = provider

        if provider == 'sqlite':
            fw.config.database.sqlite_path = path

            # Crea directory se non esiste
            Path(path).parent.mkdir(parents=True, exist_ok=True)

            if Path(path).exists() and not force:
                if not click.confirm(f"Database {path} esiste già. Sovrascrivere?"):
                    console.print("❌ Operazione annullata", style="red")
                    return

        # Setup database
        fw.setup_database()

        # Verifica connessione
        with fw.db.get_session() as session:
            result = fw.db.execute_query("SELECT 1 as test")
            if result and result[0]['test'] == 1:
                console.print("✅ Database inizializzato e testato con successo", style="green")
                console.print(f"📍 Provider: {provider}")
                if provider == 'sqlite':
                    console.print(f"📍 Path: {path}")
            else:
                console.print("❌ Errore nella verifica database", style="red")

    except Exception as e:
        console.print(f"❌ Errore inizializzazione: {e}", style="red")
        sys.exit(1)


@db.command()
@click.option('--table', help='Nome tabella specifica')
def info(table):
    """Informazioni database"""
    from framework import ModularFramework

    try:
        fw = ModularFramework()

        # Informazioni generali
        panel_content = []
        panel_content.append(f"Provider: {fw.config.database.provider}")

        if fw.config.database.provider == 'sqlite':
            db_path = Path(fw.config.database.sqlite_path)
            panel_content.append(f"Path: {db_path}")
            panel_content.append(f"Esiste: {'✅' if db_path.exists() else '❌'}")
            if db_path.exists():
                size_mb = db_path.stat().st_size / (1024 * 1024)
                panel_content.append(f"Dimensione: {size_mb:.2f} MB")

        console.print(Panel("\n".join(panel_content), title="🗃️ Informazioni Database"))

        # Lista tabelle
        with fw.db.get_session() as session:
            if fw.config.database.provider == 'sqlite':
                tables_query = "SELECT name FROM sqlite_master WHERE type='table'"
            else:
                tables_query = "SELECT TABLE_NAME as name FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE'"

            tables = fw.db.execute_query(tables_query)

            if tables:
                table_obj = Table(title="📋 Tabelle Database")
                table_obj.add_column("Nome Tabella", style="cyan")
                table_obj.add_column("Info", style="green")

                for t in tables:
                    table_name = t['name']
                    # Conta righe
                    try:
                        count_result = fw.db.execute_query(f"SELECT COUNT(*) as count FROM {table_name}")
                        row_count = count_result[0]['count'] if count_result else 0
                        table_obj.add_row(table_name, f"{row_count} righe")
                    except:
                        table_obj.add_row(table_name, "N/A")

                console.print(table_obj)
            else:
                console.print("⚠️ Nessuna tabella trovata", style="yellow")

    except Exception as e:
        console.print(f"❌ Errore: {e}", style="red")


@cli.group()
def plugin():
    """🔌 Gestione plugin"""
    pass


@plugin.command()
def list():
    """Lista plugin disponibili e caricati"""
    from framework import ModularFramework

    try:
        fw = ModularFramework()
        loaded_plugins = fw.plugins.list_plugins()

        if loaded_plugins:
            table = Table(title="🔌 Plugin Caricati")
            table.add_column("Nome", style="cyan")
            table.add_column("Stato", style="green")
            table.add_column("Info")

            for plugin_name in loaded_plugins:
                plugin_instance = fw.plugins.get_plugin(plugin_name)
                if plugin_instance:
                    table.add_row(
                        plugin_name,
                        "🟢 Attivo",
                        getattr(plugin_instance, 'description', 'N/A')
                    )
                else:
                    table.add_row(plugin_name, "🔴 Errore", "Plugin non trovato")

            console.print(table)
        else:
            console.print("⚠️ Nessun plugin caricato", style="yellow")

        # Plugin disponibili
        console.print("\n💡 Plugin configurati:", style="blue")
        for plugin_name in fw.config.plugins_enabled:
            status = "🟢 Caricato" if plugin_name in loaded_plugins else "🔴 Non caricato"
            console.print(f"  • {plugin_name}: {status}")

    except Exception as e:
        console.print(f"❌ Errore: {e}", style="red")


@plugin.command()
@click.argument('plugin_name')
def load(plugin_name):
    """Carica un plugin"""
    from framework import ModularFramework

    try:
        fw = ModularFramework()

        console.print(f"📦 Caricamento plugin: {plugin_name}...", style="blue")

        if fw.plugins.load_plugin(plugin_name):
            console.print(f"✅ Plugin {plugin_name} caricato con successo", style="green")

            # Mostra info plugin
            plugin_instance = fw.plugins.get_plugin(plugin_name)
            if plugin_instance:
                console.print(f"📝 Descrizione: {getattr(plugin_instance, 'description', 'N/A')}")
                console.print(f"🏷️ Versione: {getattr(plugin_instance, 'version', 'N/A')}")
        else:
            console.print(f"❌ Errore caricamento plugin {plugin_name}", style="red")

    except Exception as e:
        console.print(f"❌ Errore: {e}", style="red")


@plugin.command()
@click.argument('plugin_name')
def unload(plugin_name):
    """Scarica un plugin"""
    from framework import ModularFramework

    try:
        fw = ModularFramework()

        if plugin_name in fw.plugins.list_plugins():
            fw.plugins.unload_plugin(plugin_name)
            console.print(f"✅ Plugin {plugin_name} scaricato", style="green")
        else:
            console.print(f"⚠️ Plugin {plugin_name} non è caricato", style="yellow")

    except Exception as e:
        console.print(f"❌ Errore: {e}", style="red")


@cli.group()
def server():
    """🌐 Server HTTP/WebSocket"""
    pass


@server.command()
@click.option('--host', default='0.0.0.0', help='Host server')
@click.option('--port', default=8000, type=int, help='Porta server')
@click.option('--debug', is_flag=True, help='Modalità debug')
def start(host, port, debug):
    """Avvia server HTTP/WebSocket"""
    from framework import ModularFramework
    from framework.networking.server import HTTPServer

    async def run_server():
        try:
            console.print("🚀 Avvio server...", style="blue")

            fw = ModularFramework()
            if debug:
                fw.config.debug = True
                fw.config.log_level = "DEBUG"

            fw.config.networking.host = host
            fw.config.networking.port = port

            server = HTTPServer(fw.config.networking)

            # Aggiungi route di esempio
            async def api_info(request):
                from aiohttp import web
                return web.json_response({
                    "service": "ModularFramework API",
                    "version": "1.0.0",
                    "endpoints": [
                        "/health - Health check",
                        "/status - Server status",
                        "/connections - WebSocket info",
                        "/ws - WebSocket endpoint"
                    ]
                })

            async def echo_handler(data, connection):
                return {
                    "type": "echo_response",
                    "original_message": data,
                    "timestamp": data.get("timestamp")
                }

            server.add_route('/api/info', api_info, ['GET'])
            server.add_websocket_handler('echo', echo_handler)

            # Avvia server
            runner = await server.start()

            console.print(Panel(
                f"🌐 Server HTTP: http://{host}:{port}\n"
                f"🔌 WebSocket: ws://{host}:{port}/ws\n"
                f"🩺 Health: http://{host}:{port}/health\n"
                f"📊 Status: http://{host}:{port}/status",
                title="✅ Server Avviato"
            ))

            console.print("💡 Premi Ctrl+C per fermare il server", style="dim")

            # Mantieni server attivo
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                console.print("\n🛑 Fermando server...", style="yellow")
                await runner.cleanup()
                console.print("✅ Server fermato", style="green")

        except Exception as e:
            console.print(f"❌ Errore server: {e}", style="red")
            sys.exit(1)

    asyncio.run(run_server())


@cli.group()
def http():
    """🌐 Client HTTP"""
    pass


@http.command()
@click.argument('url')
@click.option('--method', default='GET', type=click.Choice(['GET', 'POST', 'PUT', 'DELETE']))
@click.option('--data', help='Dati da inviare (JSON)')
@click.option('--headers', help='Headers HTTP (JSON)')
@click.option('--timeout', default=30, type=int, help='Timeout richiesta')
def request(url, method, data, headers, timeout):
    """Esegue richiesta HTTP"""
    from framework import ModularFramework

    try:
        fw = ModularFramework()
        fw.config.networking.http_timeout = timeout

        console.print(f"🌐 {method} {url}", style="blue")

        # Parse dati
        json_data = None
        if data:
            try:
                json_data = json.loads(data)
            except json.JSONDecodeError:
                console.print("❌ Dati non sono JSON valido", style="red")
                return

        # Parse headers
        headers_dict = {}
        if headers:
            try:
                headers_dict = json.loads(headers)
            except json.JSONDecodeError:
                console.print("❌ Headers non sono JSON valido", style="red")
                return

        # Esegui richiesta
        with console.status(f"[bold blue]Eseguendo {method} {url}..."):
            if method == 'GET':
                response = fw.http.get(url, headers=headers_dict)
            elif method == 'POST':
                response = fw.http.post(url, json=json_data, headers=headers_dict)
            elif method == 'PUT':
                response = fw.http.put(url, json=json_data, headers=headers_dict)
            elif method == 'DELETE':
                response = fw.http.delete(url, headers=headers_dict)

        # Mostra risultato
        status_style = "green" if response.success else "red"
        console.print(f"Status: {response.status}", style=status_style)
        console.print(f"Success: {response.success}")

        # Headers risposta
        if response.headers:
            headers_table = Table(title="📋 Response Headers")
            headers_table.add_column("Header", style="cyan")
            headers_table.add_column("Value", style="white")

            for key, value in list(response.headers.items())[:10]:  # Prime 10
                headers_table.add_row(key, str(value)[:100])

            console.print(headers_table)

        # Dati risposta
        console.print("\n📄 Response Data:")
        if isinstance(response.data, dict):
            console.print_json(data=response.data)
        else:
            # Limita output per testo lungo
            data_str = str(response.data)
            if len(data_str) > 1000:
                console.print(data_str[:1000] + "... (truncated)")
            else:
                console.print(data_str)

    except Exception as e:
        console.print(f"❌ Errore richiesta: {e}", style="red")


@cli.command()
@click.option('--config-file', help='Path file configurazione')
def config():
    """Mostra configurazione attuale"""
    from framework import ModularFramework

    try:
        fw = ModularFramework()

        # Configurazione database
        db_config = {
            "provider": fw.config.database.provider,
            "sqlite_path": fw.config.database.sqlite_path,
            "pool_size": fw.config.database.pool_size,
            "echo": fw.config.database.echo
        }

        # Configurazione networking
        net_config = {
            "http_timeout": fw.config.networking.http_timeout,
            "host": fw.config.networking.host,
            "port": fw.config.networking.port,
            "user_agent": fw.config.networking.user_agent
        }

        # Configurazione generale
        general_config = {
            "debug": fw.config.debug,
            "log_level": fw.config.log_level,
            "plugins_enabled": fw.config.plugins_enabled
        }

        console.print(Panel("🗃️ Database", style="blue"))
        console.print_json(data=db_config)

        console.print(Panel("🌐 Networking", style="green"))
        console.print_json(data=net_config)

        console.print(Panel("⚙️ Generale", style="yellow"))
        console.print_json(data=general_config)

    except Exception as e:
        console.print(f"❌ Errore: {e}", style="red")


@cli.command()
def test():
    """Test completo del framework"""
    from framework import ModularFramework

    async def run_tests():
        tests_passed = 0
        tests_total = 0

        console.print("🧪 Avvio test framework...\n", style="blue")

        with Progress() as progress:
            task = progress.add_task("[cyan]Eseguendo test...", total=5)

            try:
                # Test 1: Inizializzazione
                progress.update(task, description="[cyan]Test inizializzazione...")
                fw = ModularFramework()
                tests_total += 1
                tests_passed += 1
                console.print("✅ Inizializzazione: OK")
                progress.advance(task)

                # Test 2: Database
                progress.update(task, description="[cyan]Test database...")
                fw.setup_database()
                with fw.db.get_session() as session:
                    result = fw.db.execute_query("SELECT 1 as test")
                    if result and result[0]['test'] == 1:
                        tests_passed += 1
                        console.print("✅ Database: OK")
                    else:
                        console.print("❌ Database: ERRORE")
                tests_total += 1
                progress.advance(task)

                # Test 3: HTTP Client
                progress.update(task, description="[cyan]Test HTTP client...")
                response = fw.http.get("https://httpbin.org/json")
                if response.success:
                    tests_passed += 1
                    console.print("✅ HTTP Client: OK")
                else:
                    console.print("❌ HTTP Client: ERRORE")
                tests_total += 1
                progress.advance(task)

                # Test 4: HTTP Client Async
                progress.update(task, description="[cyan]Test HTTP client async...")
                async_response = await fw.http.aget("https://httpbin.org/uuid")
                if async_response.success:
                    tests_passed += 1
                    console.print("✅ HTTP Client Async: OK")
                else:
                    console.print("❌ HTTP Client Async: ERRORE")
                tests_total += 1
                progress.advance(task)

                # Test 5: Plugin System
                progress.update(task, description="[cyan]Test plugin system...")
                # Test di base del sistema plugin
                plugin_count = len(fw.plugins.list_plugins())
                tests_passed += 1
                console.print(f"✅ Plugin System: OK ({plugin_count} plugin)")
                tests_total += 1
                progress.advance(task)

                # Cleanup
                await fw.cleanup()

            except Exception as e:
                console.print(f"❌ Errore durante test: {e}", style="red")

        # Risultato finale
        success_rate = (tests_passed / tests_total) * 100 if tests_total > 0 else 0

        result_style = "green" if success_rate == 100 else "yellow" if success_rate >= 80 else "red"

        console.print(f"\n📊 Risultati test:", style="bold")
        console.print(f"✅ Passati: {tests_passed}/{tests_total}", style=result_style)
        console.print(f"📈 Successo: {success_rate:.1f}%", style=result_style)

        if success_rate == 100:
            console.print("🎉 Tutti i test sono passati!", style="green bold")
        elif success_rate >= 80:
            console.print("⚠️ La maggior parte dei test è passata", style="yellow")
        else:
            console.print("❌ Diversi test sono falliti", style="red")
            sys.exit(1)

    asyncio.run(run_tests())


if __name__ == '__main__':
    cli()