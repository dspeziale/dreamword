# examples/basic_usage.py
"""
Esempi di utilizzo del framework Python
"""

import sys
import os
import time
4
# Aggiunge il framework al path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from database import (
    SQLiteManager, MSSQLManager
)
from networking import (
    HeartBeat, SimpleServer, NetworkInfo
)

from scanner import ( NmapScanner)
from utils import (setup_logger)


def example_database():
    """Esempio uso database SQLite"""
    print("\n=== ESEMPIO DATABASE SQLITE ===")

    # Setup logger
    logger = setup_logger("database_example", "INFO", "logs/database.log")

    # Inizializza database
    db = SQLiteManager("test.db")

    # Crea tabella
    columns = {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "nome": "TEXT NOT NULL",
        "email": "TEXT UNIQUE",
        "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
    }

    db.create_table("utenti", columns)

    # Inserisce dati
    user_data = {
        "nome": "Mario Rossi",
        "email": "mario@test.com"
    }

    user_id = db.insert_data("utenti", user_data)
    print(f"Utente inserito con ID: {user_id}")

    # Query dati
    users = db.execute_query("SELECT * FROM utenti WHERE nome LIKE ?", ("%Mario%",))
    print(f"Utenti trovati: {users}")


def example_networking():
    """Esempio networking e heartbeat"""
    print("\n=== ESEMPIO NETWORKING ===")

    # Setup logger
    logger = setup_logger("network_example", "INFO")

    # Informazioni di rete
    net_info = NetworkInfo()

    print(f"IP locale: {net_info.get_local_ip()}")
    print(f"Interfacce: {net_info.get_all_interfaces()}")

    # Test ping
    ping_result = net_info.ping_host("8.8.8.8", 2)
    print(f"Ping Google DNS: {'Successo' if ping_result['success'] else 'Fallito'}")

    # Heartbeat example
    def on_failure():
        print("HEARTBEAT: Connessione persa!")

    def on_success():
        print("HEARTBEAT: Connessione OK")

    # Heartbeat verso Google DNS
    hb = HeartBeat("8.8.8.8", 53, interval=10)
    hb.set_failure_callback(on_failure)
    hb.set_success_callback(on_success)

    print("Avvio heartbeat (premi Ctrl+C per fermare)...")
    hb.start()

    try:
        time.sleep(30)  # Monitora per 30 secondi
    except KeyboardInterrupt:
        pass
    finally:
        hb.stop()


def example_server():
    """Esempio server TCP"""
    print("\n=== ESEMPIO SERVER ===")

    def custom_handler(client_socket, address):
        """Gestore personalizzato per client"""
        print(f"Nuovo client: {address}")

        try:
            # Invia messaggio di benvenuto
            welcome = f"Benvenuto {address}! Scrivi 'quit' per uscire.\n"
            client_socket.send(welcome.encode('utf-8'))

            while True:
                data = client_socket.recv(1024)
                if not data:
                    break

                message = data.decode('utf-8').strip()
                print(f"Ricevuto da {address}: {message}")

                if message.lower() == 'quit':
                    client_socket.send("Arrivederci!\n".encode('utf-8'))
                    break

                # Echo del messaggio
                response = f"Echo: {message}\n"
                client_socket.send(response.encode('utf-8'))

        except Exception as e:
            print(f"Errore con client {address}: {e}")
        finally:
            client_socket.close()
            print(f"Client {address} disconnesso")

    # Crea e configura server
    server = SimpleServer("127.0.0.1", 8080)
    server.set_client_handler(custom_handler)

    print("Server in ascolto su 127.0.0.1:8080")
    print("Connettiti con: telnet 127.0.0.1 8080")
    print("Premi Ctrl+C per fermare...")

    try:
        server.start()
    except KeyboardInterrupt:
        print("\nChiusura server...")
        server.stop()


def example_nmap():
    """Esempio scansioni Nmap"""
    print("\n=== ESEMPIO NMAP SCANNER ===")

    try:
        scanner = NmapScanner()

        # Mostra tecniche disponibili
        print("Tecniche di scansione disponibili:")
        for name, desc in scanner.get_scan_techniques().items():
            print(f"  {name}: {desc}")

        # Ping sweep della rete locale
        print("\n--- Ping Sweep ---")
        local_network = "192.168.1.0/24"  # Modifica secondo la tua rete
        ping_results = scanner.ping_sweep(local_network)

        if "active_hosts" in ping_results:
            print(f"Host attivi trovati: {ping_results['total_found']}")
            for host in ping_results["active_hosts"][:5]:  # Mostra primi 5
                print(f"  {host['ip']} - {host['hostname']}")

        # Scansione porte comuni su localhost
        print("\n--- Scansione Porte Localhost ---")
        port_scan = scanner.scan_host("127.0.0.1", "22,80,135,443,445,3389")

        if "hosts" in port_scan:
            for host in port_scan["hosts"]:
                print(f"Host: {host['ip']} - Status: {host['status']}")
                if host["open_ports"]:
                    print("  Porte aperte:")
                    for port in host["open_ports"]:
                        print(f"    {port['port']}/{port['protocol']}")

        # Scansione dettagliata (commentata per sicurezza)
        # print("\n--- Scansione Dettagliata ---")
        # detailed = scanner.port_scan_detailed("scanme.nmap.org", "22,80,443")
        # print(f"Risultati dettagliati: {detailed}")

    except Exception as e:
        print(f"Errore scanner: {e}")
        print("Assicurati che Nmap sia installato e accessibile")


def example_mssql():
    """Esempio database MSSQL (richiede configurazione)"""
    print("\n=== ESEMPIO MSSQL (DEMO) ===")

    # Questo è solo un esempio di configurazione
    # Modifica i parametri secondo il tuo ambiente

    try:
        # Connessione con autenticazione Windows
        db = MSSQLManager(
            server="localhost\\SQLEXPRESS",
            database="TestDB",
            trusted_connection=True
        )

        # Test connessione
        result = db.execute_query("SELECT @@VERSION as version")
        print(f"Connesso a SQL Server: {result}")

    except Exception as e:
        print(f"Errore MSSQL (normale se non configurato): {e}")


def main():
    """Funzione principale con menu esempi"""

    while True:
        print("\n" + "=" * 50)
        print("FRAMEWORK PYTHON - ESEMPI")
        print("=" * 50)
        print("1. Database SQLite")
        print("2. Networking e HeartBeat")
        print("3. Server TCP")
        print("4. Scanner Nmap")
        print("5. Database MSSQL (demo)")
        print("0. Esci")

        try:
            choice = input("\nScegli esempio (0-5): ").strip()

            if choice == "0":
                print("Arrivederci!")
                break
            elif choice == "1":
                example_database()
            elif choice == "2":
                example_networking()
            elif choice == "3":
                example_server()
            elif choice == "4":
                example_nmap()
            elif choice == "5":
                example_mssql()
            else:
                print("Scelta non valida!")

        except KeyboardInterrupt:
            print("\n\nInterrotto dall'utente. Arrivederci!")
            break
        except Exception as e:
            print(f"Errore: {e}")


if __name__ == "__main__":
    main()