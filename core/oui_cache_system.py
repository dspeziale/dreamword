import os
import re
import time
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
import logging
from core.sqlite_manager import SQLiteCRUD


class OUICache:
    """
    Sistema di cache per il file OUI (Organizationally Unique Identifier) di IEEE.
    Gestisce download, parsing e caching locale dei dati OUI per lookup MAC address.
    """

    def __init__(self, instance_dir: str = "instance"):
        """
        Inizializza il sistema di cache OUI.

        Args:
            instance_dir (str): Directory dove salvare il database e i file
        """
        self.instance_dir = instance_dir
        self.db_path = os.path.join(instance_dir, "oui_cache.db")

        # URL principale e backup per il file OUI
        self.oui_urls = [
            "https://standards-oui.ieee.org/oui/oui.txt",
            "http://linuxnet.ca/ieee/oui.txt",  # Mirror più veloce
            "https://standards.ieee.org/regauth/oui/oui.txt"  # URL legacy
        ]

        # Configurazione cache
        self.cache_duration_days = 7  # Aggiorna cache ogni 7 giorni

        # Setup logging
        self.logger = self._setup_logger()

        # Crea directory instance se non exists
        os.makedirs(instance_dir, exist_ok=True)

        # Inizializza database
        self._init_database()

    def _setup_logger(self) -> logging.Logger:
        """Configura il logger per la classe."""
        logger = logging.getLogger(f"{__name__}.OUICache")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    def _init_database(self):
        """Inizializza le tabelle del database per la cache OUI."""
        try:
            with SQLiteCRUD(self.db_path) as db:
                # Tabella per memorizzare i record OUI
                db.create_table(
                    "oui_records",
                    {
                        "id": "INTEGER",
                        "oui": "TEXT UNIQUE NOT NULL",  # Es: "00-50-56"
                        "oui_hex": "TEXT NOT NULL",  # Es: "005056"
                        "company_name": "TEXT NOT NULL",
                        "company_address": "TEXT",
                        "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                        "updated_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
                    },
                    primary_key="id"
                )

                # Crea indici per performance
                db.execute_query(
                    "CREATE INDEX IF NOT EXISTS idx_oui ON oui_records(oui)"
                )
                db.execute_query(
                    "CREATE INDEX IF NOT EXISTS idx_oui_hex ON oui_records(oui_hex)"
                )
                db.execute_query(
                    "CREATE INDEX IF NOT EXISTS idx_company_name ON oui_records(company_name)"
                )

                # Tabella per metadata della cache
                db.create_table(
                    "cache_metadata",
                    {
                        "id": "INTEGER",
                        "key": "TEXT UNIQUE NOT NULL",
                        "value": "TEXT",
                        "updated_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
                    },
                    primary_key="id"
                )

                self.logger.info("Database OUI cache inizializzato correttamente")

        except Exception as e:
            self.logger.error(f"Errore nell'inizializzazione del database: {e}")
            raise

    def _download_oui_file(self) -> Optional[str]:
        """
        Scarica il file OUI da uno degli URL disponibili.

        Returns:
            Optional[str]: Contenuto del file OUI o None se fallisce
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        for url in self.oui_urls:
            try:
                self.logger.info(f"Tentativo download da: {url}")

                response = requests.get(
                    url,
                    headers=headers,
                    timeout=60,
                    stream=True
                )
                response.raise_for_status()

                # Controlla dimensione file (dovrebbe essere ~3-4MB)
                content_length = response.headers.get('content-length')
                if content_length and int(content_length) < 1000000:  # Meno di 1MB
                    self.logger.warning(f"File troppo piccolo da {url}: {content_length} bytes")
                    continue

                content = response.text

                # Verifica che il contenuto sia valido
                if "OUI/MA-L" in content and "Organization" in content:
                    self.logger.info(f"Download completato da {url}: {len(content)} caratteri")
                    return content
                else:
                    self.logger.warning(f"Contenuto non valido da {url}")

            except requests.RequestException as e:
                self.logger.warning(f"Errore download da {url}: {e}")
                continue
            except Exception as e:
                self.logger.error(f"Errore inaspettato con {url}: {e}")
                continue

        self.logger.error("Impossibile scaricare il file OUI da tutti gli URL")
        return None

    def _parse_oui_content(self, content: str) -> List[Dict[str, str]]:
        """
        Parsa il contenuto del file OUI.

        Args:
            content (str): Contenuto del file OUI

        Returns:
            List[Dict]: Lista dei record OUI parsati
        """
        records = []
        current_record = {}

        lines = content.split('\n')

        # Pattern per identificare una riga OUI
        oui_pattern = re.compile(r'^([0-9A-F]{2}-[0-9A-F]{2}-[0-9A-F]{2})\s*\(hex\)\s+(.+)$')
        base16_pattern = re.compile(r'^([0-9A-F]{6})\s*\(base 16\)\s+(.+)$')

        for line in lines:
            line = line.strip()

            if not line or line.startswith('#'):
                continue

            # Cerca pattern OUI (hex)
            oui_match = oui_pattern.match(line)
            if oui_match:
                # Se abbiamo un record precedente, lo aggiungiamo
                if current_record.get('oui'):
                    records.append(current_record.copy())

                # Inizia nuovo record
                current_record = {
                    'oui': oui_match.group(1),
                    'company_name': oui_match.group(2).strip(),
                    'company_address': ''
                }
                continue

            # Cerca pattern base 16
            base16_match = base16_pattern.match(line)
            if base16_match:
                if current_record.get('oui'):
                    current_record['oui_hex'] = base16_match.group(1)
                    # Il nome dell'azienda potrebbe essere diverso nella riga base16
                    company_name_base16 = base16_match.group(2).strip()
                    if len(company_name_base16) > len(current_record['company_name']):
                        current_record['company_name'] = company_name_base16
                continue

            # Se siamo in un record attivo, questa è probabilmente l'indirizzo
            if current_record.get('oui') and line:
                if current_record['company_address']:
                    current_record['company_address'] += ' ' + line
                else:
                    current_record['company_address'] = line

        # Aggiungi ultimo record
        if current_record.get('oui'):
            records.append(current_record)

        # Filtra e pulisci i record
        cleaned_records = []
        for record in records:
            if record.get('oui') and record.get('company_name'):
                # Genera oui_hex se non presente
                if not record.get('oui_hex'):
                    record['oui_hex'] = record['oui'].replace('-', '')

                # Pulisci i campi
                record['company_name'] = record['company_name'][:255]  # Limita lunghezza
                record['company_address'] = record.get('company_address', '')[:500]

                cleaned_records.append(record)

        self.logger.info(f"Parsati {len(cleaned_records)} record OUI validi")
        return cleaned_records

    def _save_to_cache(self, records: List[Dict[str, str]]):
        """
        Salva i record OUI nella cache del database.

        Args:
            records (List[Dict]): Lista dei record da salvare
        """
        try:
            with SQLiteCRUD(self.db_path) as db:
                # Svuota tabella esistente
                db.execute_query("DELETE FROM oui_records")

                # Inserisci nuovi record in batch
                self.logger.info("Inserimento record nel database...")

                for i, record in enumerate(records):
                    try:
                        db.insert("oui_records", {
                            'oui': record['oui'],
                            'oui_hex': record['oui_hex'],
                            'company_name': record['company_name'],
                            'company_address': record['company_address']
                        })

                        # Progress log ogni 1000 record
                        if (i + 1) % 1000 == 0:
                            self.logger.info(f"Inseriti {i + 1}/{len(records)} record")

                    except Exception as e:
                        self.logger.warning(f"Errore inserimento record {record.get('oui')}: {e}")

                # Aggiorna metadata della cache
                db.execute_query(
                    "INSERT OR REPLACE INTO cache_metadata (key, value, updated_at) VALUES (?, ?, ?)",
                    ('last_update', datetime.now().isoformat(), datetime.now().isoformat())
                )

                db.execute_query(
                    "INSERT OR REPLACE INTO cache_metadata (key, value, updated_at) VALUES (?, ?, ?)",
                    ('total_records', str(len(records)), datetime.now().isoformat())
                )

                self.logger.info(f"Cache aggiornata con {len(records)} record OUI")

        except Exception as e:
            self.logger.error(f"Errore nel salvataggio della cache: {e}")
            raise

    def update_cache(self, force: bool = False) -> bool:
        """
        Aggiorna la cache OUI se necessario.

        Args:
            force (bool): Forza l'aggiornamento anche se la cache è recente

        Returns:
            bool: True se cache aggiornata, False altrimenti
        """
        try:
            # Controlla se è necessario aggiornare
            if not force and not self._needs_update():
                self.logger.info("Cache OUI già aggiornata")
                return False

            self.logger.info("Inizio aggiornamento cache OUI...")

            # Scarica file OUI
            content = self._download_oui_file()
            if not content:
                return False

            # Parsa contenuto
            records = self._parse_oui_content(content)
            if not records:
                self.logger.error("Nessun record valido trovato nel file OUI")
                return False

            # Salva in cache
            self._save_to_cache(records)

            self.logger.info("Cache OUI aggiornata con successo")
            return True

        except Exception as e:
            self.logger.error(f"Errore nell'aggiornamento della cache: {e}")
            return False

    def _needs_update(self) -> bool:
        """Controlla se la cache ha bisogno di essere aggiornata."""
        try:
            with SQLiteCRUD(self.db_path) as db:
                result = db.select(
                    "cache_metadata",
                    "key = ?",
                    ("last_update",)
                )

                if not result:
                    return True

                last_update_str = result[0]['value']
                last_update = datetime.fromisoformat(last_update_str)

                # Controlla se sono passati abbastanza giorni
                if datetime.now() - last_update > timedelta(days=self.cache_duration_days):
                    return True

                # Controlla se ci sono record nella cache
                count = db.count("oui_records")
                return count == 0

        except Exception as e:
            self.logger.warning(f"Errore nel controllo aggiornamento cache: {e}")
            return True

    def lookup_mac(self, mac_address: str) -> Optional[Dict[str, str]]:
        """
        Cerca informazioni sul vendor di un MAC address.

        Args:
            mac_address (str): MAC address da cercare (formati supportati:
                              00:50:56:XX:XX:XX, 00-50-56-XX-XX-XX, 005056XXXXXX)

        Returns:
            Optional[Dict]: Informazioni del vendor o None se non trovato
        """
        try:
            # Estrai OUI dal MAC address
            oui = self._extract_oui(mac_address)
            if not oui:
                return None

            # Aggiorna cache se necessario
            self.update_cache()

            with SQLiteCRUD(self.db_path) as db:
                # Cerca per OUI formato con trattini
                result = db.select(
                    "oui_records",
                    "oui = ? OR oui_hex = ?",
                    (oui.replace(':', '-').replace('.', '-').upper(),
                     oui.replace(':', '').replace('-', '').replace('.', '').upper())
                )

                if result:
                    record = result[0]
                    return {
                        'oui': record['oui'],
                        'oui_hex': record['oui_hex'],
                        'vendor': record['company_name'],
                        'address': record['company_address'],
                        'mac_queried': mac_address
                    }

                return None

        except Exception as e:
            self.logger.error(f"Errore nella ricerca MAC {mac_address}: {e}")
            return None

    def _extract_oui(self, mac_address: str) -> Optional[str]:
        """
        Estrae l'OUI (primi 3 byte) da un MAC address.

        Args:
            mac_address (str): MAC address in vari formati

        Returns:
            Optional[str]: OUI nel formato XX-XX-XX o None se invalido
        """
        # Rimuovi tutti i separatori comuni
        mac_clean = re.sub(r'[:\-\.]', '', mac_address.strip().upper())

        # Verifica che sia esadecimale e almeno 6 caratteri
        if not re.match(r'^[0-9A-F]{6,12}$', mac_clean):
            return None

        # Prendi primi 6 caratteri (3 byte = OUI)
        oui_hex = mac_clean[:6]

        # Converte nel formato XX-XX-XX
        return f"{oui_hex[0:2]}-{oui_hex[2:4]}-{oui_hex[4:6]}"

    def search_vendor(self, vendor_name: str, limit: int = 10) -> List[Dict[str, str]]:
        """
        Cerca vendor per nome o parte del nome.

        Args:
            vendor_name (str): Nome o parte del nome del vendor
            limit (int): Limite massimo risultati

        Returns:
            List[Dict]: Lista dei vendor trovati
        """
        try:
            # Aggiorna cache se necessario
            self.update_cache()

            with SQLiteCRUD(self.db_path) as db:
                results = db.execute_query(
                    "SELECT * FROM oui_records WHERE company_name LIKE ? ORDER BY company_name LIMIT ?",
                    (f"%{vendor_name}%", limit)
                )

                return [
                    {
                        'oui': row['oui'],
                        'oui_hex': row['oui_hex'],
                        'vendor': row['company_name'],
                        'address': row['company_address']
                    }
                    for row in results
                ]

        except Exception as e:
            self.logger.error(f"Errore nella ricerca vendor '{vendor_name}': {e}")
            return []

    def get_cache_stats(self) -> Dict[str, any]:
        """
        Restituisce statistiche sulla cache.

        Returns:
            Dict: Statistiche della cache
        """
        try:
            with SQLiteCRUD(self.db_path) as db:
                # Conta totale record
                total_records = db.count("oui_records")

                # Ottieni ultimo aggiornamento
                metadata = db.select("cache_metadata", "key = ?", ("last_update",))
                last_update = None
                if metadata:
                    last_update = datetime.fromisoformat(metadata[0]['value'])

                # Dimensione database
                db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0

                return {
                    'total_records': total_records,
                    'last_update': last_update,
                    'cache_age_days': (datetime.now() - last_update).days if last_update else None,
                    'needs_update': self._needs_update(),
                    'database_size_mb': round(db_size / (1024 * 1024), 2),
                    'database_path': self.db_path
                }

        except Exception as e:
            self.logger.error(f"Errore nel recupero statistiche: {e}")
            return {}


# Esempio di utilizzo
if __name__ == "__main__":
    # Inizializza cache OUI
    oui_cache = OUICache()

    # Aggiorna cache (scarica se necessario)
    print("Aggiornamento cache OUI...")
    oui_cache.update_cache()

    # Test lookup MAC address
    test_macs = [
        "00:50:56:12:34:56",  # VMware
        "00:1B:21:AA:BB:CC",  # Apple
        "00:E0:4C:11:22:33",  # Realtek
        "08:00:27:DD:EE:FF",  # VirtualBox
    ]

    print("\n=== Test Lookup MAC Address ===")
    for mac in test_macs:
        result = oui_cache.lookup_mac(mac)
        if result:
            print(f"MAC: {mac}")
            print(f"  Vendor: {result['vendor']}")
            print(f"  OUI: {result['oui']} ({result['oui_hex']})")
            print(f"  Address: {result['address'][:100]}...")
            print()
        else:
            print(f"MAC: {mac} - Vendor non trovato")

    # Test ricerca per vendor
    print("\n=== Test Ricerca Vendor ===")
    vendors_to_search = ["Apple", "Cisco", "Intel"]

    for vendor in vendors_to_search:
        results = oui_cache.search_vendor(vendor, limit=3)
        print(f"Ricerca '{vendor}': {len(results)} risultati")
        for result in results:
            print(f"  {result['oui']} - {result['vendor']}")
        print()

    # Mostra statistiche cache
    print("\n=== Statistiche Cache ===")
    stats = oui_cache.get_cache_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")