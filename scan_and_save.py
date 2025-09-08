#!/usr/bin/env python3
# examples/scan_and_save.py
"""
Esempio di scansione di rete con salvataggio risultati nel database
"""

import sys
import time
import json
from pathlib import Path
from datetime import datetime

# Aggiunge il progetto al path
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

# Import del progetto
from database import SQLiteManager
from scanner import NmapScanner
from networking import NetworkInfo
from utils import get_default_logger
from config import get_config


class NetworkScanManager:
    """Gestisce scansioni di rete e salvataggio nel database"""

    def __init__(self, db_name: str = "network_scans.db"):
        self.db = SQLiteManager(db_name)
        self.scanner = NmapScanner()
        self.network_info = NetworkInfo()
        self.logger = get_default_logger("network_scanner", "INFO")

        # Inizializza database
        self._setup_database()

    def _setup_database(self):
        """Crea le tabelle necessarie"""

        # Tabella scansioni
        scans_table = {
            "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "scan_type": "TEXT NOT NULL",
            "target": "TEXT NOT NULL",
            "started_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "completed_at": "TIMESTAMP",
            "duration_seconds": "INTEGER",
            "total_hosts": "INTEGER DEFAULT 0",
            "active_hosts": "INTEGER DEFAULT 0",
            "status": "TEXT DEFAULT 'running'",
            "notes": "TEXT"
        }

        # Tabella host trovati
        hosts_table = {
            "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "scan_id": "INTEGER",
            "ip_address": "TEXT NOT NULL",
            "hostname": "TEXT",
            "mac_address": "TEXT",
            "status": "TEXT",
            "os_info": "TEXT",
            "discovered_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "FOREIGN KEY (scan_id)": "REFERENCES scans(id)"
        }

        # Tabella porte aperte
        ports_table = {
            "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "host_id": "INTEGER",
            "port": "INTEGER NOT NULL",
            "protocol": "TEXT NOT NULL",
            "state": "TEXT NOT NULL",
            "service": "TEXT",
            "version": "TEXT",
            "product": "TEXT",
            "FOREIGN KEY (host_id)": "REFERENCES hosts(id)"
        }

        # Crea le tabelle
        self.db.create_table("scans", scans_table)
        self.db.create_table("hosts", hosts_table)
        self.db.create_table("ports", ports_table)

        self.logger.info("Database scansioni inizializzato")

    def start_scan(self, target: str, scan_type: str, notes: str = "") -> int:
        """Inizia una nuova scansione"""
        scan_data = {
            "scan_type": scan_type,
            "target": target,
            "status": "running",
            "notes": notes
        }

        scan_id = self.db.insert_data("scans", scan_data)
        self.logger.info(f"Scansione iniziata - ID: {scan_id}, Target: {target}, Tipo: {scan_type}")
        return scan_id

    def finish_scan(self, scan_id: int, duration: int, total_hosts: int, active_hosts: int):
        """Completa una scansione"""
        update_data = {
            "completed_at": datetime.now().isoformat(),
            "duration_seconds": duration,
            "total_hosts": total_hosts,
            "active_hosts": active_hosts,
            "status": "completed"
        }

        self.db.update_data("scans", update_data, "id = ?", (scan_id,))
        self.logger.info(f"Scansione {scan_id} completata")

    def save_host(self, scan_id: int, host_data: dict) -> int:
        """Salva un host trovato"""
        host_record = {
            "scan_id": scan_id,
            "ip_address": host_data.get("ip", ""),
            "hostname": host_data.get("hostname", ""),
            "mac_address": host_data.get("mac_address", ""),
            "status": host_data.get("status", "unknown"),
            "os_info": json.dumps(host_data.get("os_detection", []))
        }

        host_id = self.db.insert_data("hosts", host_record)
        self.logger.debug(f"Host salvato: {host_data.get('ip')} (ID: {host_id})")
        return host_id

    def save_ports(self, host_id: int, ports_data: list):
        """Salva le porte di un host"""
        for port in ports_data:
            port_record = {
                "host_id": host_id,
                "port": port.get("port", 0),
                "protocol": port.get("protocol", "tcp"),
                "state": port.get("state", "unknown"),
                "service": port.get("service", ""),
                "version": port.get("version", ""),
                "product": port.get("product", "")
            }

            self.db.insert_data("ports", port_record)

    def ping_sweep_and_save(self, network: str) -> dict:
        """Esegue ping sweep e salva risultati"""
        print(f"\n🔍 PING SWEEP: {network}")
        print("-" * 50)

        start_time = time.time()
        scan_id = self.start_scan(network, "ping_sweep", f"Ping sweep della rete {network}")

        try:
            # Esegue ping sweep
            results = self.scanner.ping_sweep(network)

            if "error" in results:
                print(f"❌ Errore scansione: {results['error']}")
                return results

            # Salva host trovati
            active_hosts = results.get("active_hosts", [])
            total_found = len(active_hosts)

            print(f"✅ Host attivi trovati: {total_found}")

            for host in active_hosts:
                host_id = self.save_host(scan_id, host)
                print(f"  💾 {host['ip']} - {host.get('hostname', 'N/A')} (salvato)")

            # Completa scansione
            duration = int(time.time() - start_time)
            self.finish_scan(scan_id, duration, total_found, total_found)

            print(f"⏱️  Tempo impiegato: {duration} secondi")
            return {
                "scan_id": scan_id,
                "total_found": total_found,
                "duration": duration
            }

        except Exception as e:
            self.logger.error(f"Errore durante ping sweep: {e}")
            self.db.update_data("scans", {"status": "error", "notes": str(e)}, "id = ?", (scan_id,))
            return {"error": str(e)}

    def port_scan_and_save(self, target: str, ports: str = "22,80,135,443,445,3389") -> dict:
        """Esegue scansione porte e salva risultati"""
        print(f"\n🔍 PORT SCAN: {target}")
        print(f"Porte: {ports}")
        print("-" * 50)

        start_time = time.time()
        scan_id = self.start_scan(target, "port_scan", f"Scansione porte {ports}")

        try:
            # Esegue scansione porte
            results = self.scanner.scan_host(target, ports, "-sS")

            if "error" in results:
                print(f"❌ Errore scansione: {results['error']}")
                return results

            # Processa risultati
            hosts_data = results.get("hosts", [])
            total_hosts = len(hosts_data)
            active_hosts = 0

            for host_data in hosts_data:
                if host_data.get("status") == "up":
                    active_hosts += 1

                    # Salva host
                    host_id = self.save_host(scan_id, host_data)

                    # Salva porte aperte
                    open_ports = host_data.get("open_ports", [])
                    if open_ports:
                        self.save_ports(host_id, open_ports)
                        print(f"  💾 {host_data['ip']}: {len(open_ports)} porte aperte")

                        for port in open_ports:
                            print(f"    🔓 {port['port']}/{port['protocol']} - {port.get('state', 'open')}")
                    else:
                        print(f"  💾 {host_data['ip']}: Nessuna porta aperta trovata")

            # Completa scansione
            duration = int(time.time() - start_time)
            self.finish_scan(scan_id, duration, total_hosts, active_hosts)

            print(f"⏱️  Tempo impiegato: {duration} secondi")
            return {
                "scan_id": scan_id,
                "total_hosts": total_hosts,
                "active_hosts": active_hosts,
                "duration": duration
            }

        except Exception as e:
            self.logger.error(f"Errore durante port scan: {e}")
            self.db.update_data("scans", {"status": "error", "notes": str(e)}, "id = ?", (scan_id,))
            return {"error": str(e)}

    def get_scan_history(self, limit: int = 10) -> list:
        """Ottiene storico scansioni"""
        return self.db.execute_query(
            "SELECT * FROM scans ORDER BY started_at DESC LIMIT ?",
            (limit,)
        )

    def get_scan_results(self, scan_id: int) -> dict:
        """Ottiene risultati dettagliati di una scansione"""
        # Info scansione
        scan_info = self.db.execute_query("SELECT * FROM scans WHERE id = ?", (scan_id,))
        if not scan_info:
            return {"error": "Scansione non trovata"}

        # Host trovati
        hosts = self.db.execute_query("""
            SELECT h.*, COUNT(p.id) as port_count 
            FROM hosts h 
            LEFT JOIN ports p ON h.id = p.host_id 
            WHERE h.scan_id = ? 
            GROUP BY h.id
        """, (scan_id,))

        # Porte per ogni host
        for host in hosts:
            host["ports"] = self.db.execute_query(
                "SELECT * FROM ports WHERE host_id = ? ORDER BY port",
                (host["id"],)
            )

        return {
            "scan_info": scan_info[0],
            "hosts": hosts
        }

    def show_scan_summary(self):
        """Mostra riassunto delle scansioni"""
        print("\n📊 RIASSUNTO SCANSIONI")
        print("=" * 50)

        # Statistiche generali
        stats = self.db.execute_query("""
            SELECT 
                COUNT(*) as total_scans,
                SUM(active_hosts) as total_active_hosts,
                AVG(duration_seconds) as avg_duration
            FROM scans WHERE status = 'completed'
        """)

        if stats:
            stat = stats[0]
            print(f"📈 Scansioni completate: {stat['total_scans']}")
            print(f"🖥️  Host attivi trovati: {stat['total_active_hosts'] or 0}")
            print(f"⏱️  Durata media: {stat['avg_duration'] or 0:.1f} secondi")

        # Ultime scansioni
        recent_scans = self.get_scan_history(5)
        print(f"\n📋 Ultime scansioni:")
        for scan in recent_scans:
            status_icon = "✅" if scan["status"] == "completed" else "❌"
            print(f"  {status_icon} {scan['started_at'][:19]} - {scan['scan_type']} su {scan['target']}")

        # Host più scansionati
        popular_hosts = self.db.execute_query("""
            SELECT ip_address, COUNT(*) as scan_count
            FROM hosts 
            GROUP BY ip_address 
            ORDER BY scan_count DESC 
            LIMIT 5
        """)

        if popular_hosts:
            print(f"\n🎯 Host più scansionati:")
            for host in popular_hosts:
                print(f"  {host['ip_address']}: {host['scan_count']} volte")


def main():
    """Funzione principale con menu"""

    try:
        scanner = NetworkScanManager()
        net_info = NetworkInfo()

        while True:
            print("\n" + "=" * 60)
            print("🔍 NETWORK SCANNER CON DATABASE")
            print("=" * 60)
            print("1. Ping Sweep rete locale")
            print("2. Ping Sweep rete personalizzata")
            print("3. Scansione porte localhost")
            print("4. Scansione porte target personalizzato")
            print("5. Mostra storico scansioni")
            print("6. Mostra dettagli scansione")
            print("7. Riassunto statistiche")
            print("8. Info rete locale")
            print("0. Esci")

            choice = input("\nScegli opzione (0-8): ").strip()

            if choice == "0":
                print("👋 Arrivederci!")
                break

            elif choice == "1":
                # Ping sweep rete locale
                local_ip = net_info.get_local_ip()
                network = ".".join(local_ip.split(".")[:-1]) + ".0/24"
                print(f"🌐 Rete locale rilevata: {network}")
                scanner.ping_sweep_and_save(network)

            elif choice == "2":
                # Ping sweep personalizzato
                network = input("Inserisci rete (es. 192.168.1.0/24): ").strip()
                if network:
                    scanner.ping_sweep_and_save(network)

            elif choice == "3":
                # Scansione porte localhost
                scanner.port_scan_and_save("127.0.0.1", "22,80,135,443,445,3389,5432,3306")

            elif choice == "4":
                # Scansione porte personalizzata
                target = input("Target (IP o hostname): ").strip()
                ports = input("Porte (es. 22,80,443 o 1-1000): ").strip()
                if target and ports:
                    scanner.port_scan_and_save(target, ports)

            elif choice == "5":
                # Storico scansioni
                scans = scanner.get_scan_history(20)
                print(f"\n📋 Storico scansioni ({len(scans)}):")
                for scan in scans:
                    status_icon = "✅" if scan["status"] == "completed" else "❌"
                    print(
                        f"  [{scan['id']}] {status_icon} {scan['started_at'][:19]} - {scan['scan_type']} su {scan['target']}")
                    if scan["active_hosts"]:
                        print(f"      🖥️  {scan['active_hosts']} host attivi in {scan['duration_seconds']}s")

            elif choice == "6":
                # Dettagli scansione
                scan_id = input("ID scansione: ").strip()
                if scan_id.isdigit():
                    results = scanner.get_scan_results(int(scan_id))
                    if "error" in results:
                        print(f"❌ {results['error']}")
                    else:
                        scan_info = results["scan_info"]
                        hosts = results["hosts"]

                        print(f"\n📊 Scansione #{scan_info['id']}")
                        print(f"Target: {scan_info['target']}")
                        print(f"Tipo: {scan_info['scan_type']}")
                        print(f"Iniziata: {scan_info['started_at']}")
                        print(f"Durata: {scan_info['duration_seconds']}s")
                        print(f"Host trovati: {len(hosts)}")

                        for host in hosts:
                            print(f"\n🖥️  {host['ip_address']} ({host['hostname'] or 'N/A'})")
                            if host["port_count"] > 0:
                                print(f"   🔓 {host['port_count']} porte aperte:")
                                for port in host["ports"]:
                                    service = f" ({port['service']})" if port['service'] else ""
                                    print(f"     {port['port']}/{port['protocol']}{service}")

            elif choice == "7":
                # Statistiche
                scanner.show_scan_summary()

            elif choice == "8":
                # Info rete
                print(f"\n🌐 INFORMAZIONI RETE LOCALE")
                print("-" * 30)
                print(f"IP locale: {net_info.get_local_ip()}")
                print(f"Hostname: {net_info.get_system_info()['hostname']}")

                interfaces = net_info.get_all_interfaces()
                print(f"\nInterfacce di rete:")
                for name, ips in interfaces.items():
                    print(f"  {name}: {', '.join(ips)}")

            else:
                print("❌ Opzione non valida!")

            input("\n⏎ Premi Enter per continuare...")

    except KeyboardInterrupt:
        print("\n\n👋 Interruzione utente. Arrivederci!")
    except Exception as e:
        print(f"\n❌ Errore: {e}")


if __name__ == "__main__":
    main()