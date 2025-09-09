# framework/database_framework.py

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
import sqlite3
import logging
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum

from .exceptions import (
    DatabaseError,
    ConnectionError,
    DuplicateKeyError,
    ConstraintViolationError,
    ConfigurationError
)

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseType(Enum):
    SQLITE = "sqlite"
    MYSQL = "mysql"
    MSSQL = "mssql"


@dataclass
class DatabaseConfig:
    """Configurazione per la connessione al database"""
    db_type: DatabaseType
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    file_path: Optional[str] = None  # Per SQLite
    additional_params: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Validazione della configurazione"""
        if self.db_type == DatabaseType.SQLITE:
            if not self.file_path:
                self.file_path = ":memory:"
        elif self.db_type in [DatabaseType.MYSQL, DatabaseType.MSSQL]:
            if not all([self.host, self.database, self.username]):
                raise ConfigurationError(
                    f"Per {self.db_type.value} servono: host, database, username"
                )


class DatabaseConnection(ABC):
    """Classe base astratta per tutte le connessioni database"""

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self._connection = None

    @abstractmethod
    def connect(self):
        """Stabilisce connessione al database"""
        pass

    @abstractmethod
    def disconnect(self):
        """Chiude connessione al database"""
        pass

    @abstractmethod
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict]:
        """Esegue una query SELECT e ritorna i risultati"""
        pass

    @abstractmethod
    def execute_command(self, command: str, params: Optional[tuple] = None) -> int:
        """Esegue un comando INSERT/UPDATE/DELETE e ritorna righe affette"""
        pass

    @abstractmethod
    def execute_many(self, command: str, params_list: List[tuple]) -> int:
        """Esegue lo stesso comando con parametri multipli"""
        pass

    @contextmanager
    def transaction(self):
        """Context manager per transazioni"""
        try:
            self.begin_transaction()
            yield self
            self.commit()
        except Exception as e:
            self.rollback()
            raise e

    @abstractmethod
    def begin_transaction(self):
        pass

    @abstractmethod
    def commit(self):
        pass

    @abstractmethod
    def rollback(self):
        pass

    @property
    def is_connected(self) -> bool:
        """Verifica se la connessione è attiva"""
        return self._connection is not None


class SQLiteConnection(DatabaseConnection):
    """Implementazione per SQLite"""

    def connect(self):
        try:
            self._connection = sqlite3.connect(
                self.config.file_path or ":memory:",
                check_same_thread=False
            )
            self._connection.row_factory = sqlite3.Row
            logger.info(f"Connesso a SQLite: {self.config.file_path}")
        except Exception as e:
            logger.error(f"Errore connessione SQLite: {e}")
            raise ConnectionError(f"Impossibile connettersi a SQLite: {e}")

    def disconnect(self):
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.info("Disconnesso da SQLite")

    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict]:
        if not self._connection:
            raise ConnectionError("Nessuna connessione attiva")

        cursor = self._connection.cursor()
        try:
            cursor.execute(query, params or ())
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Errore query SQLite: {e}")
            raise DatabaseError(f"Errore esecuzione query: {e}")
        finally:
            cursor.close()

    def execute_command(self, command: str, params: Optional[tuple] = None) -> int:
        if not self._connection:
            raise ConnectionError("Nessuna connessione attiva")

        cursor = self._connection.cursor()
        try:
            cursor.execute(command, params or ())
            self._connection.commit()
            return cursor.rowcount
        except sqlite3.IntegrityError as e:
            self._connection.rollback()
            if "UNIQUE constraint failed" in str(e):
                raise DuplicateKeyError(f"Chiave duplicata: {e}")
            else:
                raise ConstraintViolationError(f"Violazione constraint: {e}")
        except Exception as e:
            logger.error(f"Errore comando SQLite: {e}")
            self._connection.rollback()
            raise DatabaseError(f"Errore SQLite: {e}")
        finally:
            cursor.close()

    def execute_many(self, command: str, params_list: List[tuple]) -> int:
        if not self._connection:
            raise ConnectionError("Nessuna connessione attiva")

        cursor = self._connection.cursor()
        try:
            cursor.executemany(command, params_list)
            self._connection.commit()
            return cursor.rowcount
        except sqlite3.IntegrityError as e:
            self._connection.rollback()
            if "UNIQUE constraint failed" in str(e):
                raise DuplicateKeyError(f"Chiave duplicata: {e}")
            else:
                raise ConstraintViolationError(f"Violazione constraint: {e}")
        except Exception as e:
            logger.error(f"Errore executemany SQLite: {e}")
            self._connection.rollback()
            raise DatabaseError(f"Errore SQLite: {e}")
        finally:
            cursor.close()

    def begin_transaction(self):
        if self._connection:
            self._connection.execute("BEGIN")

    def commit(self):
        if self._connection:
            self._connection.commit()

    def rollback(self):
        if self._connection:
            self._connection.rollback()


class MySQLConnection(DatabaseConnection):
    """Implementazione per MySQL"""

    def __init__(self, config: DatabaseConfig):
        super().__init__(config)
        try:
            import mysql.connector
            self.mysql = mysql.connector
        except ImportError:
            raise ImportError("mysql-connector-python non installato. Usa: pip install mysql-connector-python")

    def connect(self):
        try:
            self._connection = self.mysql.connect(
                host=self.config.host,
                port=self.config.port or 3306,
                user=self.config.username,
                password=self.config.password,
                database=self.config.database,
                autocommit=False
            )
            logger.info(f"Connesso a MySQL: {self.config.host}:{self.config.port}")
        except Exception as e:
            logger.error(f"Errore connessione MySQL: {e}")
            raise ConnectionError(f"Impossibile connettersi a MySQL: {e}")

    def disconnect(self):
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.info("Disconnesso da MySQL")

    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict]:
        if not self._connection:
            raise ConnectionError("Nessuna connessione attiva")

        cursor = self._connection.cursor(dictionary=True)
        try:
            cursor.execute(query, params or ())
            return cursor.fetchall()
        except Exception as e:
            logger.error(f"Errore query MySQL: {e}")
            raise DatabaseError(f"Errore esecuzione query: {e}")
        finally:
            cursor.close()

    def execute_command(self, command: str, params: Optional[tuple] = None) -> int:
        if not self._connection:
            raise ConnectionError("Nessuna connessione attiva")

        cursor = self._connection.cursor()
        try:
            cursor.execute(command, params or ())
            self._connection.commit()
            return cursor.rowcount
        except self.mysql.IntegrityError as e:
            self._connection.rollback()
            if "Duplicate entry" in str(e):
                raise DuplicateKeyError(f"Chiave duplicata MySQL: {e}")
            else:
                raise ConstraintViolationError(f"Violazione constraint MySQL: {e}")
        except Exception as e:
            logger.error(f"Errore comando MySQL: {e}")
            self._connection.rollback()
            raise DatabaseError(f"Errore MySQL: {e}")
        finally:
            cursor.close()

    def execute_many(self, command: str, params_list: List[tuple]) -> int:
        if not self._connection:
            raise ConnectionError("Nessuna connessione attiva")

        cursor = self._connection.cursor()
        try:
            cursor.executemany(command, params_list)
            self._connection.commit()
            return cursor.rowcount
        except Exception as e:
            logger.error(f"Errore executemany MySQL: {e}")
            self._connection.rollback()
            raise DatabaseError(f"Errore MySQL: {e}")
        finally:
            cursor.close()

    def begin_transaction(self):
        if self._connection:
            self._connection.start_transaction()

    def commit(self):
        if self._connection:
            self._connection.commit()

    def rollback(self):
        if self._connection:
            self._connection.rollback()


class MSSQLConnection(DatabaseConnection):
    """Implementazione per SQL Server"""

    def __init__(self, config: DatabaseConfig):
        super().__init__(config)
        try:
            import pyodbc
            self.pyodbc = pyodbc
        except ImportError:
            raise ImportError("pyodbc non installato. Usa: pip install pyodbc")

    def connect(self):
        try:
            connection_string = (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={self.config.host},{self.config.port or 1433};"
                f"DATABASE={self.config.database};"
                f"UID={self.config.username};"
                f"PWD={self.config.password};"
            )
            self._connection = self.pyodbc.connect(connection_string, autocommit=False)
            logger.info(f"Connesso a SQL Server: {self.config.host}:{self.config.port}")
        except Exception as e:
            logger.error(f"Errore connessione SQL Server: {e}")
            raise ConnectionError(f"Impossibile connettersi a SQL Server: {e}")

    def disconnect(self):
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.info("Disconnesso da SQL Server")

    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict]:
        if not self._connection:
            raise ConnectionError("Nessuna connessione attiva")

        cursor = self._connection.cursor()
        try:
            cursor.execute(query, params or ())
            columns = [column[0] for column in cursor.description]
            rows = cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            logger.error(f"Errore query SQL Server: {e}")
            raise DatabaseError(f"Errore esecuzione query: {e}")
        finally:
            cursor.close()

    def execute_command(self, command: str, params: Optional[tuple] = None) -> int:
        if not self._connection:
            raise ConnectionError("Nessuna connessione attiva")

        cursor = self._connection.cursor()
        try:
            cursor.execute(command, params or ())
            self._connection.commit()
            return cursor.rowcount
        except self.pyodbc.IntegrityError as e:
            self._connection.rollback()
            if "UNIQUE KEY constraint" in str(e) or "PRIMARY KEY constraint" in str(e):
                raise DuplicateKeyError(f"Chiave duplicata SQL Server: {e}")
            else:
                raise ConstraintViolationError(f"Violazione constraint SQL Server: {e}")
        except Exception as e:
            logger.error(f"Errore comando SQL Server: {e}")
            self._connection.rollback()
            raise DatabaseError(f"Errore SQL Server: {e}")
        finally:
            cursor.close()

    def execute_many(self, command: str, params_list: List[tuple]) -> int:
        if not self._connection:
            raise ConnectionError("Nessuna connessione attiva")

        cursor = self._connection.cursor()
        try:
            cursor.executemany(command, params_list)
            self._connection.commit()
            return cursor.rowcount
        except self.pyodbc.IntegrityError as e:
            self._connection.rollback()
            if "UNIQUE KEY constraint" in str(e) or "PRIMARY KEY constraint" in str(e):
                raise DuplicateKeyError(f"Chiave duplicata SQL Server: {e}")
            else:
                raise ConstraintViolationError(f"Violazione constraint SQL Server: {e}")
        except Exception as e:
            logger.error(f"Errore executemany SQL Server: {e}")
            self._connection.rollback()
            raise DatabaseError(f"Errore SQL Server: {e}")
        finally:
            cursor.close()

    def begin_transaction(self):
        if self._connection:
            self._connection.autocommit = False

    def commit(self):
        if self._connection:
            self._connection.commit()

    def rollback(self):
        if self._connection:
            self._connection.rollback()


class DatabaseFactory:
    """Factory per creare connessioni database"""

    @staticmethod
    def create_connection(config: DatabaseConfig) -> DatabaseConnection:
        connections = {
            DatabaseType.SQLITE: SQLiteConnection,
            DatabaseType.MYSQL: MySQLConnection,
            DatabaseType.MSSQL: MSSQLConnection
        }

        if config.db_type not in connections:
            raise ValueError(f"Tipo database non supportato: {config.db_type}")

        return connections[config.db_type](config)


class DatabaseManager:
    """Manager principale per operazioni database"""

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.connection = DatabaseFactory.create_connection(config)

    def __enter__(self):
        self.connection.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.connection.disconnect()

    @property
    def is_connected(self) -> bool:
        """Verifica se il manager è connesso"""
        return self.connection.is_connected

    def select(self, query: str, params: Optional[tuple] = None) -> List[Dict]:
        """Esegue una query SELECT"""
        return self.connection.execute_query(query, params)

    def select_one(self, query: str, params: Optional[tuple] = None) -> Optional[Dict]:
        """Esegue una query SELECT e ritorna un solo risultato"""
        results = self.select(query, params)
        return results[0] if results else None

    def insert(self, table: str, data: Dict[str, Any]) -> int:
        """Inserisce un record"""
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?" for _ in data])
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        return self.connection.execute_command(query, tuple(data.values()))

    def update(self, table: str, data: Dict[str, Any], where_clause: str, where_params: Optional[tuple] = None) -> int:
        """Aggiorna record"""
        set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
        query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
        params = tuple(data.values()) + (where_params or ())
        return self.connection.execute_command(query, params)

    def delete(self, table: str, where_clause: str, where_params: Optional[tuple] = None) -> int:
        """Elimina record"""
        query = f"DELETE FROM {table} WHERE {where_clause}"
        return self.connection.execute_command(query, where_params)

    def insert_many(self, table: str, data_list: List[Dict[str, Any]]) -> int:
        """Inserisce multipli record"""
        if not data_list:
            return 0

        columns = ", ".join(data_list[0].keys())
        placeholders = ", ".join(["?" for _ in data_list[0]])
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"

        params_list = [tuple(data.values()) for data in data_list]
        return self.connection.execute_many(query, params_list)

    def execute_raw(self, query: str, params: Optional[tuple] = None) -> Union[List[Dict], int]:
        """Esegue query/comando raw"""
        query_upper = query.strip().upper()
        if query_upper.startswith('SELECT'):
            return self.connection.execute_query(query, params)
        else:
            return self.connection.execute_command(query, params)

    def transaction(self):
        """Ritorna context manager per transazioni"""
        return self.connection.transaction()

    def count(self, table: str, where_clause: str = None, where_params: Optional[tuple] = None) -> int:
        """Conta i record in una tabella"""
        query = f"SELECT COUNT(*) as count FROM {table}"
        if where_clause:
            query += f" WHERE {where_clause}"

        result = self.select_one(query, where_params)
        return result['count'] if result else 0

    def exists(self, table: str, where_clause: str, where_params: Optional[tuple] = None) -> bool:
        """Verifica se esistono record che soddisfano una condizione"""
        return self.count(table, where_clause, where_params) > 0