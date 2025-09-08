# framework/database/sqlite_provider.py

"""
Provider SQLite per ModularFramework

Implementa DatabaseProvider per database SQLite
"""

from typing import Dict, Any
from pathlib import Path
from .manager import DatabaseProvider


class SQLiteProvider(DatabaseProvider):
    """Provider per database SQLite"""

    def __init__(self, config):
        """
        Inizializza provider SQLite

        Args:
            config: Configurazione database
        """
        self.config = config
        # Assicura che la directory del database esista
        db_path = Path(config.sqlite_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)

    def get_connection_string(self) -> str:
        """
        Genera stringa di connessione SQLite

        Returns:
            Connection string per SQLAlchemy
        """
        # SQLite supporta URI relative e assolute
        db_path = Path(self.config.sqlite_path).resolve()
        return f"sqlite:///{db_path}"

    def get_engine_options(self) -> Dict[str, Any]:
        """
        Opzioni specifiche per engine SQLite

        Returns:
            Dizionario con opzioni engine
        """
        return {
            # SQLite opzioni specifiche
            "pool_pre_ping": True,
            "pool_recycle": self.config.pool_recycle,
            "connect_args": {
                "check_same_thread": False,  # Permette uso multi-thread
                "timeout": 20,  # Timeout connessione
                "isolation_level": None,  # Autocommit mode
            },
            # Echo opzioni
            "echo": self.config.echo,
            "echo_pool": self.config.echo_pool,
        }

    def get_dialect_options(self) -> Dict[str, Any]:
        """
        Opzioni specifiche del dialetto SQLite

        Returns:
            Opzioni dialetto
        """
        return {
            "json_serializer": None,  # Usa serializer default
            "json_deserializer": None,  # Usa deserializer default
        }

    def supports_feature(self, feature: str) -> bool:
        """
        Verifica se una feature è supportata

        Args:
            feature: Nome della feature

        Returns:
            True se supportata
        """
        # Features supportate da SQLite
        supported_features = {
            "transactions": True,
            "foreign_keys": True,
            "indexes": True,
            "triggers": True,
            "views": True,
            "stored_procedures": False,  # SQLite non supporta stored procedures
            "json": True,  # SQLite 3.38+ supporta JSON
            "full_text_search": True,  # FTS
            "window_functions": True,  # SQLite 3.25+
            "cte": True,  # Common Table Expressions
            "upsert": True,  # INSERT OR REPLACE
        }

        return supported_features.get(feature, False)

    def get_database_info(self) -> Dict[str, Any]:
        """
        Informazioni sul database

        Returns:
            Dizionario con informazioni database
        """
        db_path = Path(self.config.sqlite_path)

        info = {
            "provider": "sqlite",
            "database_path": str(db_path.resolve()),
            "exists": db_path.exists(),
            "readable": db_path.is_file() if db_path.exists() else False,
            "writable": self._check_writable(db_path),
        }

        if db_path.exists():
            stat = db_path.stat()
            info.update({
                "size_bytes": stat.st_size,
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "created": stat.st_ctime,
                "modified": stat.st_mtime,
            })

        return info

    def _check_writable(self, db_path: Path) -> bool:
        """
        Verifica se il database è scrivibile

        Args:
            db_path: Path del database

        Returns:
            True se scrivibile
        """
        try:
            if db_path.exists():
                # Testa se possiamo aprire in modalità scrittura
                with open(db_path, 'a'):
                    pass
                return True
            else:
                # Testa se possiamo creare il file
                try:
                    with open(db_path, 'w'):
                        pass
                    db_path.unlink()  # Rimuovi file di test
                    return True
                except:
                    return False
        except:
            return False

    def get_maintenance_queries(self) -> Dict[str, str]:
        """
        Query di manutenzione SQLite

        Returns:
            Dizionario con query di manutenzione
        """
        return {
            "vacuum": "VACUUM;",
            "analyze": "ANALYZE;",
            "integrity_check": "PRAGMA integrity_check;",
            "foreign_key_check": "PRAGMA foreign_key_check;",
            "table_info": "SELECT name FROM sqlite_master WHERE type='table';",
            "index_info": "SELECT name FROM sqlite_master WHERE type='index';",
            "database_size": "SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size();",
            "cache_size": "PRAGMA cache_size;",
            "journal_mode": "PRAGMA journal_mode;",
            "synchronous": "PRAGMA synchronous;",
        }

    def optimize_database(self) -> Dict[str, Any]:
        """
        Ottimizza database SQLite

        Returns:
            Risultati ottimizzazione
        """
        # Questa funzione richiederebbe accesso all'engine
        # Per ora restituisce solo i comandi da eseguire
        return {
            "commands": [
                "VACUUM;",  # Ricompatta database
                "ANALYZE;",  # Aggiorna statistiche
                "PRAGMA optimize;",  # Ottimizzazioni automatiche
            ],
            "description": "Comandi per ottimizzare database SQLite"
        }

    def get_backup_command(self, backup_path: str) -> str:
        """
        Comando per backup database

        Args:
            backup_path: Path di destinazione backup

        Returns:
            Comando SQL per backup
        """
        return f"VACUUM INTO '{backup_path}';"

    def validate_connection_string(self, connection_string: str) -> bool:
        """
        Valida stringa di connessione

        Args:
            connection_string: Stringa da validare

        Returns:
            True se valida
        """
        try:
            # SQLite connection string inizia con sqlite:///
            if not connection_string.startswith("sqlite:///"):
                return False

            # Estrai path del database
            db_path = connection_string.replace("sqlite:///", "")
            path = Path(db_path)

            # Verifica che la directory parent sia valida
            return path.parent.exists() or path.parent == Path(".")

        except Exception:
            return False