# framework/networking/info.py
import socket
import psutil
import platform
import logging
from typing import Dict, List, Any
import subprocess
import ipaddress


class NetworkInfo:
    """Raccolta informazioni di rete del sistema"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def get_local_ip(self) -> str:
        """Ottiene l'IP locale principale"""
        try:
            # Connessione a un IP esterno per determinare l'interfaccia usata
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except:
            return "127.0.0.1"

    def get_all_interfaces(self) -> Dict[str, List[str]]:
        """Ottiene tutte le interfacce di rete e relativi IP"""
        interfaces = {}

        try:
            for interface, addrs in psutil.net_if_addrs().items():
                ips = []
                for addr in addrs:
                    if addr.family == socket.AF_INET:  # Solo IPv4
                        ips.append(addr.address)
                if ips:
                    interfaces[interface] = ips
        except Exception as e:
            self.logger.error(f"Errore lettura interfacce: {e}")

        return interfaces

    def get_network_stats(self) -> Dict[str, Any]:
        """Ottiene statistiche di rete"""
        try:
            stats = psutil.net_io_counters()
            return {
                "bytes_sent": stats.bytes_sent,
                "bytes_recv": stats.bytes_recv,
                "packets_sent": stats.packets_sent,
                "packets_recv": stats.packets_recv,
                "errin": stats.errin,
                "errout": stats.errout,
                "dropin": stats.dropin,
                "dropout": stats.dropout
            }
        except Exception as e:
            self.logger.error(f"Errore lettura statistiche: {e}")
            return {}

    def get_open_ports(self) -> List[Dict[str, Any]]:
        """Ottiene le porte aperte in ascolto"""
        ports = []

        try:
            for conn in psutil.net_connections(kind='inet'):
                if conn.status == psutil.CONN_LISTEN:
                    ports.append({
                        "protocol": "TCP" if conn.type == socket.SOCK_STREAM else "UDP",
                        "local_address": conn.laddr.ip,
                        "local_port": conn.laddr.port,
                        "pid": conn.pid,
                        "process_name": psutil.Process(conn.pid).name() if conn.pid else "Unknown"
                    })
        except Exception as e:
            self.logger.error(f"Errore lettura porte: {e}")

        return ports

    def ping_host(self, host: str, count: int = 4) -> Dict[str, Any]:
        """Esegue ping verso un host"""
        try:
            # Determina comando ping basato su OS
            if platform.system().lower() == "windows":
                cmd = ["ping", "-n", str(count), host]
            else:
                cmd = ["ping", "-c", str(count), host]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            return {
                "host": host,
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr
            }
        except Exception as e:
            self.logger.error(f"Errore ping {host}: {e}")
            return {
                "host": host,
                "success": False,
                "output": "",
                "error": str(e)
            }

    def get_system_info(self) -> Dict[str, Any]:
        """Ottiene informazioni di sistema"""
        return {
            "hostname": socket.gethostname(),
            "platform": platform.platform(),
            "processor": platform.processor(),
            "architecture": platform.architecture(),
            "local_ip": self.get_local_ip(),
            "interfaces": self.get_all_interfaces()
        }