# examples/basic_usage.py
"""
Esempi di utilizzo del framework Python con gestione automatica directory instance
"""

import sys
import os
import time
from pathlib import Path

# Aggiunge il framework al path
current_dir = Path(__file__).parent
framework_dir = current_dir.parent
sys.path.insert(0, str(framework_dir))

# Import del framework
from database import SQLiteManager, MSSQLManager
from networking import HeartBeat, SimpleServer, NetworkInfo
from scanner import NmapScanner
from utils import setup_logger, get_default_logger
from config import get_config, set_base_directory


def show_configuration():
    """Mostra la configurazione attuale delle directory"""
    print("\n=== CONFIGURAZIONE FRAMEWORK ===")
    config = get_config()
    paths = config.get_full_paths()

    for name, path in paths.items():
        exists = "✓" if Path(path).exists() else "✗"
        print(f"{exists} {name}: {path}")

    print("\nDirectory instance creata automaticamente!")


def example_database():
    """Esempio uso database SQLite con directory instance"""
    print("\n=== ESEMPIO DATABASE SQLITE ===")

    # Logger automatico che usa instance/logs
    logger = get_default_logger("database_example", "INFO")

    # Database automaticamente in instance/database
    db = SQLiteManager("example.db")

    # Mostra info database
    db_info = db.get_database_info()
    print(f"Database path: {db_info['database_path']}")
    print(f"Dimensione: {db_info['file_size_mb']} MB")

    # Crea tabella
    columns = {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "nome": "TEXT NOT NULL",
        "email": "TEXT UNIQUE",
        "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
    }

    if db.create_table("utenti", columns):
        print("Tabella 'utenti' creata con successo")

    # Inserisce dati di esempio
    test_users = [
        {"nome": "Mario Rossi", "email": "mario@test.com"},
        {"nome": "Luigi Verdi", "email": "luigi@test.com"},
        {"nome": "Anna Bianchi", "email": "anna@test.com"}
    ]

    for user in test_users:
        user_id = db.insert_data("utenti", user)
        if user_id:
            print(f"Utente '{user['nome']}' inserito con ID: {user_id}")

    # Query dati
    users = db.execute_query("SELECT * FROM utenti ORDER BY id")
    print(f"\nUtenti nel database ({len(users)}):")
    for user in users:
        print(f"  ID: {user['id']} - {user['nome']} ({user['email']})")

    # Test backup
    backup_path = db.backup_database()
    if backup_path:
        print(f"Backup creato: {backup_path}")


def example_logging():
    """Esempio sistema di logging con instance"""
    print("\n=== ESEMPIO LOGGING ===")

    # Logger con configurazione automatica
    app_logger = get_default_logger("app_test", "DEBUG")
    network_logger = get_default_logger("network_test", "INFO")

    # Test logging
    app_logger.debug("Messaggio di debug")
    app_logger.info("Applicazione avviata")
    app_logger.warning("Questo è un warning")

    network_logger.info("Connessione di rete stabilita")
    network_logger.error("Errore di connessione simulato")

    # Mostra informazioni sui logger
    from utils.logger import get_logger_info
    logger_info = get_logger_info()

    print("\nLogger attivi:")
    for name, info in logger_info.items():
        if name.endswith("_test"):
            print(f"  {name}: livello {info['level']}")
            for handler in info['handlers']:
                if 'file' in handler:
                    print(f"    → Log file: {handler['file']}")


def example_networking():
    """Esempio networking con logging in instance"""
    print("\n=== ESEMPIO NETWORKING ===")

    # Logger automatico
    logger = get_default_logger("network_example", "INFO")

    # Informazioni di rete
    net_info = NetworkInfo()

    print(f"IP locale: {net_info.get_local_ip()}")
    print(f"Hostname: {net_info.get_system_info()['hostname']}")

    # Test ping con logging automatico
    targets = ["8.8.8.8", "1.1.1.1", "google.com"]

    print("\nTest connettività:")
    for target in targets:
        result = net_info.ping_host(target, 1)
        status = "OK" if result['success'] else "FAIL"
        print(f"  {target}: {status}")
        logger.info(f"Ping {target}: {status}")

    # Heartbeat con callback che usa logger
    def on_connection_failure():
        logger.error("HEARTBEAT: Connessione persa!")
        print("HEARTBEAT: Connessione persa!")

    def on_connection_success():
        logger.debug("HEARTBEAT: Connessione OK")

    # Heartbeat verso Google DNS
    hb = HeartBeat("8.8.8.8", 53, interval=5)
    hb.set_failure_callback(on_connection_failure)
    hb.set_success_callback(on_connection_success)

    print("\nAvvio heartbeat per 15 secondi...")
    hb.start()

    try:
        time.sleep(15)
    except KeyboardInterrupt:
        pass
    finally:
        hb.stop()
        logger.info("Heartbeat fermato")


def example_file_management():
    """Esempio gestione file con directory instance"""
    print("\n=== ESEMPIO GESTIONE FILE ===")

    config = get_config()

    # Test file temporaneo
    temp_file = config.get_temp_path("test_file.txt")

    # Scrive file temporaneo
    with open(temp_file, 'w') as f:
        f.write("Questo è un file di test temporaneo\n")
        f.write(f"Creato il: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

    print(f"File temporaneo creato: {temp_file}")

    # Legge file
    with open(temp_file, 'r') as f:
        content = f.read()
        print(f"Contenuto:\n{content}")

    # Cleanup
    print("\nPulizia file temporanei...")
    config.cleanup_temp()

    # Verifica pulizia
    if not Path(temp_file).exists():
        print("File temporaneo rimosso con successo")


def example_advanced_database():
    """Esempio avanzato database con operazioni CRUD"""
    print("\n=== ESEMPIO DATABASE AVANZATO ===")

    db = SQLiteManager("advanced_example.db")
    logger = get_default_logger("db_advanced", "INFO")

    # Crea tabella progetti
    projects_table = {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "nome": "TEXT NOT NULL",
        "descrizione": "TEXT",
        "stato": "TEXT DEFAULT 'nuovo'",
        "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        "updated_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
    }

    db.create_table("progetti", projects_table)

    # Inserisce progetti di esempio
    progetti = [
        {"nome": "Framework Python", "descrizione": "Sviluppo framework per networking", "stato": "in_corso"},
        {"nome": "Scanner di Rete", "descrizione": "Tool per scansioni Nmap", "stato": "completato"},
        {"nome": "Database Manager", "descrizione": "Gestione database SQLite e MSSQL", "stato": "in_corso"}
    ]

    for progetto in progetti:
        project_id = db.insert_data("progetti", progetto)
        logger.info(f"Progetto '{progetto['nome']}' creato con ID {project_id}")

    # Update di un progetto
    updated_rows = db.update_data(
        "progetti",
        {"stato": "completato", "updated_at": "CURRENT_TIMESTAMP"},
        "nome = ?",
        ("Framework Python",)
    )
    print(f"Aggiornati {updated_rows} progetti")

    # Query con filtri
    progetti_attivi = db.execute_query(
        "SELECT * FROM progetti WHERE stato IN (?, ?) ORDER BY created_at DESC",
        ("in_corso", "completato")
    )

    print(f"\nProgetti trovati: {len(progetti_attivi)}")
    for prog in progetti_attivi:
        print(f"  [{prog['stato']}] {prog['nome']}: {prog['descrizione']}")

    # Informazioni tabella
    table_info = db.get_table_info("progetti")
    print(f"\nStruttura tabella 'progetti':")
    for col in table_info:
        print(f"  {col['name']}: {col['type']}")


def main():
    """Funzione principale con menu esempi"""

    # Imposta directory base se necessario
    # set_base_directory("/path/to/your/project")  # Opzionale

    while True:
        print("\n" + "=" * 60)
        print("FRAMEWORK PYTHON - ESEMPI CON DIRECTORY INSTANCE")
        print("=" * 60)
        print("0. Mostra configurazione directory")
        print("1. Database SQLite base")
        print("2. Sistema di logging")
        print("3. Networking e HeartBeat")
        print("4. Gestione file temporanei")
        print("5. Database avanzato (CRUD)")
        print("6. Scanner Nmap")
        print("9. Esci")

        try:
            choice = input("\nScegli esempio (0-9): ").strip()

            if choice == "9":
                print("Arrivederci!")
                break
            elif choice == "0":
                show_configuration()
            elif choice == "1":
                example_database()
            elif choice == "2":
                example_logging()
            elif choice == "3":
                example_networking()
            elif choice == "4":
                example_file_management()
            elif choice == "5":
                example_advanced_database()
            elif choice == "6":
                try:
                    scanner = NmapScanner()
                    print("Scanner Nmap disponibile")

                    # Ping sweep veloce
                    print("Ping sweep rete locale...")
                    results = scanner.ping_sweep("127.0.0.1/32")
                    print(f"Host trovati: {results.get('total_found', 0)}")

                except Exception as e:
                    print(f"Scanner Nmap non disponibile: {e}")
            else:
                print("Scelta non valida!")

            input("\nPremi Enter per continuare...")

        except KeyboardInterrupt:
            print("\n\nInterrotto dall'utente. Arrivederci!")
            break
        except Exception as e:
            print(f"Errore: {e}")
            input("Premi Enter per continuare...")


if __name__ == "__main__":
    main()