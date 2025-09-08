#!/usr/bin/env python3
# examples/quick_scan.py
"""
Test veloce di scansione con salvataggio database
"""

import sys
from pathlib import Path

# Aggiunge il progetto al path
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

# Import
from database import SQLiteManager
from scanner import NmapScanner
from networking import NetworkInfo
from utils import get_default_logger


def quick_test():
    """Test veloce delle funzionalità"""

    print("🚀 QUICK TEST - Scansione + Database")
    print("=" * 50)

    # Setup
    logger = get_default_logger("quick_scan", "INFO")
    db = SQLiteManager("quick_test.db")

    # Crea tabella semplice per i risultati
    table_structure = {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "ip_address": "TEXT NOT NULL",
        "hostname": "TEXT",
        "status": "TEXT",
        "scan_time": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        "notes": "TEXT"
    }

    if db.create_table("scan_results", table_structure):
        print("✅ Tabella 'scan_results' creata")

    # Test 1: Info rete locale
    print("\n🌐 Info rete locale:")
    net_info = NetworkInfo()
    local_ip = net_info.get_local_ip()
    hostname = net_info.get_system_info()['hostname']

    print(f"  IP: {local_ip}")
    print(f"  Hostname: {hostname}")

    # Salva info locale nel DB
    local_data = {
        "ip_address": local_ip,
        "hostname": hostname,
        "status": "local_machine",
        "notes": "Informazioni macchina locale"
    }

    local_id = db.insert_data("scan_results", local_data)
    print(f"✅ Info locale salvate nel DB (ID: {local_id})")

    # Test 2: Ping test
    print(f"\n🔍 Test ping:")
    test_targets = [
        ("8.8.8.8", "Google DNS"),
        ("1.1.1.1", "Cloudflare DNS"),
        ("127.0.0.1", "Localhost")
    ]

    for ip, description in test_targets:
        ping_result = net_info.ping_host(ip, 1)
        status = "online" if ping_result['success'] else "offline"

        print(f"  {ip} ({description}): {status}")

        # Salva risultato ping
        ping_data = {
            "ip_address": ip,
            "hostname": description,
            "status": status,
            "notes": f"Ping test - {'successo' if ping_result['success'] else 'fallito'}"
        }

        ping_id = db.insert_data("scan_results", ping_data)
        logger.info(f"Ping {ip}: {status} (salvato ID: {ping_id})")

    # Test 3: Scanner Nmap (se disponibile)
    print(f"\n🔍 Test scanner Nmap:")
    try:
        scanner = NmapScanner()
        print("✅ Scanner Nmap disponibile")

        # Scan veloce di localhost
        print("  Scansione porte localhost...")
        scan_result = scanner.scan_host("127.0.0.1", "22,80,443", "-sS")

        if "error" not in scan_result:
            hosts = scan_result.get("hosts", [])
            for host in hosts:
                open_ports = host.get("open_ports", [])
                port_list = [f"{p['port']}/{p['protocol']}" for p in open_ports]

                scan_data = {
                    "ip_address": host["ip"],
                    "hostname": host.get("hostname", ""),
                    "status": host["status"],
                    "notes": f"Nmap scan - Porte aperte: {', '.join(port_list) if port_list else 'nessuna'}"
                }

                scan_id = db.insert_data("scan_results", scan_data)
                print(f"  ✅ Risultati salvati (ID: {scan_id})")

                if port_list:
                    print(f"    🔓 Porte aperte: {', '.join(port_list)}")
                else:
                    print(f"    🔒 Nessuna porta aperta trovata")
        else:
            print(f"  ❌ Errore scan: {scan_result['error']}")

    except Exception as e:
        print(f"  ⚠️  Scanner non disponibile: {e}")

        # Salva anche questo nel DB
        error_data = {
            "ip_address": "N/A",
            "hostname": "Scanner Test",
            "status": "error",
            "notes": f"Scanner Nmap non disponibile: {str(e)}"
        }
        db.insert_data("scan_results", error_data)

    # Test 4: Mostra risultati dal database
    print(f"\n📊 Risultati dal database:")
    all_results = db.execute_query("SELECT * FROM scan_results ORDER BY scan_time DESC")

    print(f"  📝 Record totali: {len(all_results)}")
    for result in all_results:
        time_str = result['scan_time'][:19] if result['scan_time'] else 'N/A'
        print(f"  [{result['id']}] {time_str} - {result['ip_address']} ({result['status']})")
        print(f"      {result['notes']}")

    # Test 5: Info database
    print(f"\n💾 Info database:")
    db_info = db.get_database_info()
    print(f"  📁 Path: {db_info['database_path']}")
    print(f"  📏 Dimensione: {db_info['file_size_mb']} MB")
    print(f"  📋 Tabelle: {', '.join(db_info['tables'])}")

    print(f"\n🎉 Test completato con successo!")
    print(f"Database salvato in: {db_info['database_path']}")


if __name__ == "__main__":
    try:
        quick_test()
    except KeyboardInterrupt:
        print(f"\n\n👋 Interruzione utente")
    except Exception as e:
        print(f"\n❌ Errore: {e}")
        import traceback

        traceback.print_exc()