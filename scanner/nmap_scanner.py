# framework/scanner/nmap_scanner.py
import nmap
import logging
import ipaddress
from typing import List, Dict, Any, Optional
import subprocess
import json


class NmapScanner:
    """Wrapper per scansioni Nmap con metodi semplificati"""

    def __init__(self):
        self.nm = nmap.PortScanner()
        self.logger = logging.getLogger(__name__)
        self._check_nmap_availability()

    def _check_nmap_availability(self):
        """Verifica che Nmap sia installato"""
        try:
            self.nm.nmap_version()
            self.logger.info(f"Nmap versione: {self.nm.nmap_version()}")
        except Exception as e:
            self.logger.error(f"Nmap non disponibile: {e}")
            raise RuntimeError("Nmap non installato o non funzionante")

    def scan_host(self, target: str, ports: str = "1-1000", arguments: str = "-sS") -> Dict[str, Any]:
        """Scansione di un singolo host"""
        try:
            self.logger.info(f"Scansione {target} porte {ports}")

            # Esegue la scansione
            result = self.nm.scan(target, ports, arguments)

            # Elabora i risultati
            scan_result = {
                "target": target,
                "scan_time": result.get("nmap", {}).get("scanstats", {}).get("elapsed", "0"),
                "hosts": [],
                "summary": {
                    "total_hosts": len(result.get("scan", {})),
                    "up_hosts": 0,
                    "down_hosts": 0
                }
            }

            for host_ip, host_data in result.get("scan", {}).items():
                host_info = self._parse_host_data(host_ip, host_data)
                scan_result["hosts"].append(host_info)

                if host_info["status"] == "up":
                    scan_result["summary"]["up_hosts"] += 1
                else:
                    scan_result["summary"]["down_hosts"] += 1

            return scan_result

        except Exception as e:
            self.logger.error(f"Errore scansione {target}: {e}")
            return {"error": str(e), "target": target}

    def scan_network(self, network: str, ports: str = "22,80,443", arguments: str = "-sS") -> Dict[str, Any]:
        """Scansione di una rete (es. 192.168.1.0/24)"""
        try:
            # Valida la rete
            network_obj = ipaddress.ip_network(network, strict=False)
            self.logger.info(f"Scansione rete {network} porte {ports}")

            return self.scan_host(str(network_obj), ports, arguments)

        except Exception as e:
            self.logger.error(f"Errore scansione rete {network}: {e}")
            return {"error": str(e), "network": network}

    def ping_sweep(self, network: str) -> Dict[str, Any]:
        """Ping sweep per trovare host attivi"""
        try:
            self.logger.info(f"Ping sweep su {network}")

            # Usa ping scan (-sn)
            result = self.nm.scan(hosts=network, arguments="-sn")

            active_hosts = []
            for host_ip, host_data in result.get("scan", {}).items():
                if host_data.get("status", {}).get("state") == "up":
                    host_info = {
                        "ip": host_ip,
                        "hostname": host_data.get("hostnames", [{}])[0].get("name", ""),
                        "mac_address": "",
                        "vendor": ""
                    }

                    # Cerca informazioni MAC se disponibili
                    for addr in host_data.get("addresses", {}).values():
                        if ":" in str(addr):  # Probabile MAC address
                            host_info["mac_address"] = addr
                            break

                    active_hosts.append(host_info)

            return {
                "network": network,
                "active_hosts": active_hosts,
                "total_found": len(active_hosts)
            }

        except Exception as e:
            self.logger.error(f"Errore ping sweep {network}: {e}")
            return {"error": str(e), "network": network}

    def port_scan_detailed(self, target: str, ports: str = "1-65535") -> Dict[str, Any]:
        """Scansione dettagliata delle porte con detection servizi"""
        try:
            self.logger.info(f"Scansione dettagliata {target}")

            # Scansione con detection servizi e OS
            arguments = "-sS -sV -O --script=default"
            result = self.nm.scan(target, ports, arguments)

            detailed_result = {
                "target": target,
                "hosts": []
            }

            for host_ip, host_data in result.get("scan", {}).items():
                host_info = self._parse_host_data_detailed(host_ip, host_data)
                detailed_result["hosts"].append(host_info)

            return detailed_result

        except Exception as e:
            self.logger.error(f"Errore scansione dettagliata {target}: {e}")
            return {"error": str(e), "target": target}

    def _parse_host_data(self, host_ip: str, host_data: Dict) -> Dict[str, Any]:
        """Parsing base dei dati host"""
        host_info = {
            "ip": host_ip,
            "status": host_data.get("status", {}).get("state", "unknown"),
            "hostname": "",
            "open_ports": [],
            "filtered_ports": [],
            "closed_ports": []
        }

        # Hostname
        hostnames = host_data.get("hostnames", [])
        if hostnames:
            host_info["hostname"] = hostnames[0].get("name", "")

        # Porte
        for protocol in host_data.get("", {}):
            if protocol.startswith("tcp") or protocol.startswith("udp"):
                for port, port_data in host_data[protocol].items():
                    port_info = {
                        "port": port,
                        "protocol": protocol,
                        "state": port_data.get("state", "unknown")
                    }

                    if port_info["state"] == "open":
                        host_info["open_ports"].append(port_info)
                    elif port_info["state"] == "filtered":
                        host_info["filtered_ports"].append(port_info)
                    else:
                        host_info["closed_ports"].append(port_info)

        return host_info

    def _parse_host_data_detailed(self, host_ip: str, host_data: Dict) -> Dict[str, Any]:
        """Parsing dettagliato dei dati host con servizi e OS"""
        host_info = self._parse_host_data(host_ip, host_data)

        # Aggiunge informazioni dettagliate
        host_info.update({
            "os_detection": [],
            "services": []
        })

        # OS Detection
        os_matches = host_data.get("osmatch", [])
        for os_match in os_matches:
            host_info["os_detection"].append({
                "name": os_match.get("name", ""),
                "accuracy": os_match.get("accuracy", "0")
            })

        # Servizi dettagliati
        for protocol in ["tcp", "udp"]:
            if protocol in host_data:
                for port, port_data in host_data[protocol].items():
                    if port_data.get("state") == "open":
                        service_info = {
                            "port": port,
                            "protocol": protocol,
                            "service": port_data.get("name", "unknown"),
                            "version": port_data.get("version", ""),
                            "product": port_data.get("product", ""),
                            "extrainfo": port_data.get("extrainfo", "")
                        }
                        host_info["services"].append(service_info)

        return host_info

    def vulnerability_scan(self, target: str, ports: str = "1-1000") -> Dict[str, Any]:
        """Scansione vulnerabilità usando script Nmap"""
        try:
            self.logger.info(f"Scansione vulnerabilità {target}")

            # Usa script di vulnerabilità
            arguments = "-sS --script=vuln"
            result = self.nm.scan(target, ports, arguments)

            vuln_result = {
                "target": target,
                "vulnerabilities": []
            }

            for host_ip, host_data in result.get("scan", {}).items():
                # Cerca risultati degli script
                for protocol in ["tcp", "udp"]:
                    if protocol in host_data:
                        for port, port_data in host_data[protocol].items():
                            scripts = port_data.get("script", {})
                            for script_name, script_output in scripts.items():
                                if "vuln" in script_name.lower():
                                    vuln_result["vulnerabilities"].append({
                                        "host": host_ip,
                                        "port": port,
                                        "protocol": protocol,
                                        "script": script_name,
                                        "output": script_output
                                    })

            return vuln_result

        except Exception as e:
            self.logger.error(f"Errore scansione vulnerabilità {target}: {e}")
            return {"error": str(e), "target": target}

    def get_scan_techniques(self) -> Dict[str, str]:
        """Ritorna le tecniche di scansione disponibili"""
        return {
            "tcp_syn": "-sS (TCP SYN scan - stealthy)",
            "tcp_connect": "-sT (TCP connect scan)",
            "udp": "-sU (UDP scan)",
            "ping_sweep": "-sn (Ping sweep only)",
            "service_detection": "-sV (Service version detection)",
            "os_detection": "-O (OS detection)",
            "aggressive": "-A (Aggressive scan - OS, version, scripts)",
            "stealth": "-sS -f (Fragmented packets)",
            "decoy": "-D decoy1,decoy2 (Decoy scan)"
        }