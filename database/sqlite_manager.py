# database/sqlite_manager.py (versione senza import relativi)
import sqlite3
import logging
import os
import sys
from typing import List, Dict, Any, Optional
from contextlib import contextmanager
from pathlib import Path

# Aggiunge il parent directory al path per importare config
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

try:
    from config import get_config
except ImportError:
    # Fallback se config non è disponibile
    class DummyConfig:
        def __init__(self):
            self.base_dir = Path.cwd()
            self.instance_dir = self.base_dir / "instance"
            self.database_dir = self.instance_dir / "database"
            self._create_directories()

        def _create_directories(self):
            self.database_dir.mkdir(parents=True, exist_ok=True)

        def get_database_path(self, db_name: str) -> str:
            if not db_name.endswith('.db'):
                db_name += '.db'
            return str(self.database_dir / db_name)


    def get_config():
        return DummyConfig()


class SQLiteManager:
    """Gestione database SQLite con context manager e logging"""

    def __init__(self, db_name: str = "main.db"):
        """
        Inizializza il manager SQLite

        Args:
            db_name: Nome del database (sarà salvato in instance/database/)
        """
        config = get_config()
        self.db_path = config.get_database_path(db_name)
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Database SQLite: {self.db_path}")

    @contextmanager
    def get_connection(self):
        """Context manager per gestire le connessioni"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Risultati come dizionari
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            self.logger.error(f"Errore database: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Esegue una query SELECT e ritorna i risultati"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def execute_non_query(self, query: str, params: tuple = ()) -> int:
        """Esegue INSERT, UPDATE, DELETE e ritorna righe modificate"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount

    def create_table(self, table_name: str, columns: Dict[str, str]) -> bool:
        """Crea una tabella se non esiste"""
        try:
            columns_sql = ", ".join([f"{name} {type_}" for name, type_ in columns.items()])
            query = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_sql})"
            self.execute_non_query(query)
            self.logger.info(f"Tabella {table_name} creata/verificata")
            return True
        except Exception as e:
            self.logger.error(f"Errore creazione tabella {table_name}: {e}")
            return False

    def insert_data(self, table_name: str, data: Dict[str, Any]) -> Optional[int]:
        """Inserisce dati in una tabella"""
        try:
            columns = ", ".join(data.keys())
            placeholders = ", ".join(["?" for _ in data])
            query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"

            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, tuple(data.values()))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            self.logger.error(f"Errore inserimento in {table_name}: {e}")
            return None

    def get_database_info(self) -> Dict[str, Any]:
        """Ottiene informazioni sul database"""
        try:
            # Lista tabelle
            tables = self.execute_query(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )

            # Dimensione file
            import os
            file_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0

            return {
                "database_path": self.db_path,
                "file_size_bytes": file_size,
                "file_size_mb": round(file_size / 1024 / 1024, 2),
                "tables": [t["name"] for t in tables],
                "table_count": len(tables)
            }
        except Exception as e:
            self.logger.error(f"Errore informazioni database: {e}")
            return {"error": str(e)}