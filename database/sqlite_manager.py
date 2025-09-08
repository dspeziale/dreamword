# framework/database/sqlite_manager.py
import sqlite3
import logging
import os
import sys
from typing import List, Dict, Any, Optional
from contextlib import contextmanager
from pathlib import Path


class SQLiteManager:
    """Gestione database SQLite con context manager e logging"""

    def __init__(self, db_name: str = "main.db"):
        """
        Inizializza il manager SQLite

        Args:
            db_name: Nome del database (sarà salvato in instance/database/)
        """
        # Importazione sicura del config
        try:
            from ..config import get_config
            config = get_config()
            self.db_path = config.get_database_path(db_name)
        except (ImportError, ValueError):
            # Fallback: crea instance directory manualmente
            self._setup_fallback_path(db_name)

        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Database SQLite: {self.db_path}")

    def _setup_fallback_path(self, db_name: str):
        """Setup path fallback se config non disponibile"""
        # Trova la directory del progetto
        current_file = Path(__file__).resolve()

        # Cerca la directory che contiene 'framework'
        project_root = current_file.parent.parent.parent
        if not (project_root / "framework").exists():
            project_root = Path.cwd()

        # Crea structure instance
        instance_dir = project_root / "instance" / "database"
        instance_dir.mkdir(parents=True, exist_ok=True)

        if not db_name.endswith('.db'):
            db_name += '.db'
        self.db_path = str(instance_dir / db_name)

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

    def update_data(self, table_name: str, data: Dict[str, Any], where_clause: str, where_params: tuple = ()) -> int:
        """Aggiorna dati in una tabella"""
        try:
            set_clause = ", ".join([f"{key} = ?" for key in data.keys()])
            query = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"
            params = tuple(data.values()) + where_params
            return self.execute_non_query(query, params)
        except Exception as e:
            self.logger.error(f"Errore aggiornamento {table_name}: {e}")
            return 0

    def delete_data(self, table_name: str, where_clause: str, where_params: tuple = ()) -> int:
        """Elimina dati da una tabella"""
        try:
            query = f"DELETE FROM {table_name} WHERE {where_clause}"
            return self.execute_non_query(query, where_params)
        except Exception as e:
            self.logger.error(f"Errore eliminazione da {table_name}: {e}")
            return 0

    def get_table_info(self, table_name: str) -> List[Dict[str, Any]]:
        """Ottiene informazioni sulla struttura di una tabella"""
        try:
            return self.execute_query(f"PRAGMA table_info({table_name})")
        except Exception as e:
            self.logger.error(f"Errore informazioni tabella {table_name}: {e}")
            return []

    def get_database_info(self) -> Dict[str, Any]:
        """Ottiene informazioni sul database"""
        try:
            # Lista tabelle
            tables = self.execute_query(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )

            # Dimensione file
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

    def backup_database(self, backup_name: str = None) -> str:
        """Crea un backup del database"""
        try:
            if backup_name is None:
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"backup_{timestamp}.db"

            # Usa temp directory se disponibile
            try:
                from ..config import get_temp_path
                backup_path = get_temp_path(backup_name)
            except ImportError:
                backup_path = str(Path(self.db_path).parent / backup_name)

            # Esegue backup
            with self.get_connection() as conn:
                backup_conn = sqlite3.connect(backup_path)
                conn.backup(backup_conn)
                backup_conn.close()

            self.logger.info(f"Backup creato: {backup_path}")
            return backup_path

        except Exception as e:
            self.logger.error(f"Errore backup database: {e}")
            return ""