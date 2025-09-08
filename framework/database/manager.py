# framework/database/manager.py

"""
Database Manager per ModularFramework

Gestisce connessioni database con provider pattern per SQLite e MSSQL
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, Union
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

# Base per tutti i modelli
Base = declarative_base()


class DatabaseProvider(ABC):
    """Provider base per database"""

    @abstractmethod
    def get_connection_string(self) -> str:
        """Restituisce stringa di connessione"""
        pass

    @abstractmethod
    def get_engine_options(self) -> Dict[str, Any]:
        """Restituisce opzioni per l'engine"""
        pass

    def supports_feature(self, feature: str) -> bool:
        """Verifica se una feature è supportata"""
        return False

    def get_database_info(self) -> Dict[str, Any]:
        """Informazioni sul database"""
        return {}


class DatabaseManager:
    """Manager principale per database"""

    def __init__(self, config):
        """
        Inizializza database manager

        Args:
            config: Configurazione database
        """
        self.config = config
        self.provider = self._get_provider()
        self.engine = None
        self.SessionLocal = None
        self.metadata = Base.metadata

        # Inizializza connessione
        self._initialize()

    def _get_provider(self) -> DatabaseProvider:
        """Factory per provider database"""
        provider_name = self.config.provider.lower()

        if provider_name == "sqlite":
            from .sqlite_provider import SQLiteProvider
            return SQLiteProvider(self.config)
        elif provider_name == "mssql":
            try:
                from .mssql_provider import MSSQLProvider
                return MSSQLProvider(self.config)
            except ImportError as e:
                raise ImportError(
                    "MSSQL provider richiede pyodbc. "
                    "Installa con: pip install pyodbc"
                ) from e
        else:
            raise ValueError(f"Provider non supportato: {provider_name}")

    def _initialize(self):
        """Inizializza engine e session factory"""
        try:
            # Ottieni configurazione dal provider
            connection_string = self.provider.get_connection_string()
            engine_options = self.provider.get_engine_options()

            # Crea engine
            self.engine = create_engine(connection_string, **engine_options)

            # Crea session factory
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )

            logger.info(f"Database manager inizializzato: {self.config.provider}")

        except Exception as e:
            logger.error(f"Errore inizializzazione database: {e}")
            raise

    @contextmanager
    def get_session(self):
        """
        Context manager per sessioni database

        Yields:
            Session SQLAlchemy
        """
        if not self.SessionLocal:
            raise RuntimeError("Database non inizializzato")

        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Errore sessione database: {e}")
            raise
        finally:
            session.close()

    def create_tables(self):
        """Crea tutte le tabelle definite nei modelli"""
        try:
            self.metadata.create_all(bind=self.engine)
            logger.info("Tabelle database create/verificate")
        except Exception as e:
            logger.error(f"Errore creazione tabelle: {e}")
            raise

    def drop_tables(self):
        """Elimina tutte le tabelle (ATTENZIONE!)"""
        try:
            self.metadata.drop_all(bind=self.engine)
            logger.warning("Tutte le tabelle sono state eliminate")
        except Exception as e:
            logger.error(f"Errore eliminazione tabelle: {e}")
            raise

    def execute_query(self, query: str, params: Optional[Dict] = None) -> List[Dict]:
        """
        Esegue query SQL diretta (SELECT) - FIXED per SQLAlchemy v2
        """
        try:
            with self.get_session() as session:
                # Fix: usa text() per query raw
                from sqlalchemy import text
                result = session.execute(text(query), params or {})

                # Converte risultati in lista di dizionari
                if result.returns_rows:
                    columns = result.keys()
                    return [dict(zip(columns, row)) for row in result.fetchall()]
                else:
                    return []

        except Exception as e:
            logger.error(f"Errore esecuzione query: {e}")
            raise

    def execute_command(self, command: str, params: Optional[Dict] = None) -> int:
        """
        Esegue comando SQL (INSERT, UPDATE, DELETE) - FIXED per SQLAlchemy v2
        """
        try:
            with self.get_session() as session:
                # Fix: usa text() per comandi raw
                from sqlalchemy import text
                result = session.execute(text(command), params or {})
                return result.rowcount

        except Exception as e:
            logger.error(f"Errore esecuzione comando: {e}")
            raise

    def test_connection(self) -> bool:
        """
        Testa connessione database - FIXED per SQLAlchemy v2
        """
        try:
            with self.get_session() as session:
                # Fix: usa text() per query test
                from sqlalchemy import text
                result = session.execute(text("SELECT 1 as test"))
                row = result.fetchone()
                return row is not None and row[0] == 1

        except Exception as e:
            logger.error(f"Test connessione fallito: {e}")
            return False

    def get_table_names(self) -> List[str]:
        """
        Ottieni lista nomi tabelle

        Returns:
            Lista nomi tabelle
        """
        try:
            if self.config.provider == "sqlite":
                query = "SELECT name FROM sqlite_master WHERE type='table'"
            elif self.config.provider == "mssql":
                query = "SELECT TABLE_NAME as name FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE'"
            else:
                raise ValueError(f"Provider non supportato: {self.config.provider}")

            results = self.execute_query(query)
            return [row['name'] for row in results]

        except Exception as e:
            logger.error(f"Errore recupero nomi tabelle: {e}")
            return []

    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """
        Informazioni su una tabella

        Args:
            table_name: Nome tabella

        Returns:
            Dizionario con informazioni tabella
        """
        try:
            info = {"name": table_name, "exists": False}

            # Verifica esistenza
            tables = self.get_table_names()
            if table_name not in tables:
                return info

            info["exists"] = True

            # Conta righe
            try:
                count_result = self.execute_query(f"SELECT COUNT(*) as count FROM {table_name}")
                info["row_count"] = count_result[0]["count"] if count_result else 0
            except:
                info["row_count"] = None

            return info

        except Exception as e:
            logger.error(f"Errore informazioni tabella {table_name}: {e}")
            return {"name": table_name, "exists": False, "error": str(e)}

    def backup_database(self, backup_path: str) -> bool:
        """
        Backup database (implementazione base)

        Args:
            backup_path: Path destinazione backup

        Returns:
            True se backup riuscito
        """
        try:
            if self.config.provider == "sqlite":
                # Per SQLite, copia il file
                import shutil
                from pathlib import Path

                source = Path(self.config.sqlite_path)
                destination = Path(backup_path)

                if source.exists():
                    shutil.copy2(source, destination)
                    logger.info(f"Backup SQLite creato: {backup_path}")
                    return True
                else:
                    logger.error(f"File database non trovato: {source}")
                    return False

            elif self.config.provider == "mssql":
                # Per MSSQL, usa comando BACKUP
                backup_command = self.provider.get_backup_command(backup_path)
                self.execute_command(backup_command)
                logger.info(f"Backup MSSQL creato: {backup_path}")
                return True

            return False

        except Exception as e:
            logger.error(f"Errore backup database: {e}")
            return False

    def get_database_size(self) -> Dict[str, Any]:
        """
        Dimensione database

        Returns:
            Informazioni dimensione
        """
        try:
            if self.config.provider == "sqlite":
                from pathlib import Path
                db_path = Path(self.config.sqlite_path)
                if db_path.exists():
                    size_bytes = db_path.stat().st_size
                    return {
                        "size_bytes": size_bytes,
                        "size_mb": round(size_bytes / (1024 * 1024), 2),
                        "size_kb": round(size_bytes / 1024, 2)
                    }

            elif self.config.provider == "mssql":
                queries = self.provider.get_maintenance_queries()
                if "database_size" in queries:
                    results = self.execute_query(queries["database_size"])
                    if results:
                        return {
                            "used_space_mb": results[0].get("used_space_mb", 0),
                            "allocated_space_mb": results[0].get("allocated_space_mb", 0)
                        }

            return {"error": "Impossibile determinare dimensione"}

        except Exception as e:
            logger.error(f"Errore calcolo dimensione database: {e}")
            return {"error": str(e)}

    def optimize_database(self) -> Dict[str, Any]:
        """
        Ottimizza database

        Returns:
            Risultati ottimizzazione
        """
        try:
            return self.provider.optimize_database()
        except Exception as e:
            logger.error(f"Errore ottimizzazione database: {e}")
            return {"error": str(e)}

    def get_status(self) -> Dict[str, Any]:
        """
        Status completo database

        Returns:
            Dizionario con status database
        """
        return {
            "provider": self.config.provider,
            "connected": self.test_connection(),
            "info": self.provider.get_database_info(),
            "tables": self.get_table_names(),
            "size": self.get_database_size()
        }

    def close(self):
        """Chiude connessioni database"""
        try:
            if self.engine:
                self.engine.dispose()
                logger.info("Connessioni database chiuse")
        except Exception as e:
            logger.error(f"Errore chiusura database: {e}")