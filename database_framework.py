# database_framework.py

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
import sqlite3
import logging
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum

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
            raise

    def disconnect(self):
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.info("Disconnesso da SQLite")

    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict]:
        cursor = self._connection.cursor()
        try:
            cursor.execute(query, params or ())
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Errore query SQLite: {e}")
            raise
        finally:
            cursor.close()

    def execute_command(self, command: str, params: Optional[tuple] = None) -> int:
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
        cursor = self._connection.cursor()
        try:
            cursor.executemany(command, params_list)
            self._connection.commit()
            return cursor.rowcount
        except Exception as e:
            logger.error(f"Errore executemany SQLite: {e}")
            self._connection.rollback()
            raise
        finally:
            cursor.close()

    def begin_transaction(self):
        self._connection.execute("BEGIN")

    def commit(self):
        self._connection.commit()

    def rollback(self):
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
            raise

    def disconnect(self):
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.info("Disconnesso da MySQL")

    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict]:
        cursor = self._connection.cursor(dictionary=True)
        try:
            cursor.execute(query, params or ())
            return cursor.fetchall()
        except Exception as e:
            logger.error(f"Errore query MySQL: {e}")
            raise
        finally:
            cursor.close()

    def execute_command(self, command: str, params: Optional[tuple] = None) -> int:
        cursor = self._connection.cursor()
        try:
            cursor.execute(command, params or ())
            self._connection.commit()
            return cursor.rowcount
        except Exception as e:
            logger.error(f"Errore comando MySQL: {e}")
            self._connection.rollback()
            raise
        finally:
            cursor.close()

    def execute_many(self, command: str, params_list: List[tuple]) -> int:
        cursor = self._connection.cursor()
        try:
            cursor.executemany(command, params_list)
            self._connection.commit()
            return cursor.rowcount
        except Exception as e:
            logger.error(f"Errore executemany MySQL: {e}")
            self._connection.rollback()
            raise
        finally:
            cursor.close()

    def begin_transaction(self):
        self._connection.start_transaction()

    def commit(self):
        self._connection.commit()

    def rollback(self):
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
            raise

    def disconnect(self):
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.info("Disconnesso da SQL Server")

    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict]:
        cursor = self._connection.cursor()
        try:
            cursor.execute(query, params or ())
            columns = [column[0] for column in cursor.description]
            rows = cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            logger.error(f"Errore query SQL Server: {e}")
            raise
        finally:
            cursor.close()

    def execute_command(self, command: str, params: Optional[tuple] = None) -> int:
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
        self._connection.autocommit = False

    def commit(self):
        self._connection.commit()

    def rollback(self):
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

    def select(self, query: str, params: Optional[tuple] = None) -> List[Dict]:
        """Esegue una query SELECT"""
        return self.connection.execute_query(query, params)

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


# Esporta tutte le classi e funzioni pubbliche
__all__ = [
    'DatabaseType',
    'DatabaseConfig',
    'DatabaseConnection',
    'SQLiteConnection',
    'MySQLConnection',
    'MSSQLConnection',
    'DatabaseFactory',
    'DatabaseManager',
    'DatabaseError',
    'ConnectionError',
    'DuplicateKeyError',
    'ConstraintViolationError'
]

# Esempio di utilizzo
if __name__ == "__main__":

    # Configurazione per SQLite
    sqlite_config = DatabaseConfig(
        db_type=DatabaseType.SQLITE,
        file_path="test.db"
    )

    # Configurazione per MySQL
    mysql_config = DatabaseConfig(
        db_type=DatabaseType.MYSQL,
        host="localhost",
        port=3306,
        database="test_db",
        username="user",
        password="password"
    )

    # Configurazione per SQL Server
    mssql_config = DatabaseConfig(
        db_type=DatabaseType.MSSQL,
        host="localhost",
        port=1433,
        database="test_db",
        username="sa",
        password="password"
    )

    # Esempio con SQLite
    with DatabaseManager(sqlite_config) as db:

        # Crea tabella di esempio
        db.execute_raw("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE,
                age INTEGER
            )
        """)

        # Insert singolo
        user_id = db.insert("users", {
            "name": "Mario Rossi",
            "email": "mario@example.com",
            "age": 30
        })
        print(f"Inserito utente con ID: {user_id}")

        # Insert multipli
        users_data = [
            {"name": "Luigi Verdi", "email": "luigi@example.com", "age": 25},
            {"name": "Anna Bianchi", "email": "anna@example.com", "age": 35},
        ]
        inserted_count = db.insert_many("users", users_data)
        print(f"Inseriti {inserted_count} utenti")

        # Select
        users = db.select("SELECT * FROM users WHERE age > ?", (20,))
        print("Utenti trovati:", users)

        # Update
        updated = db.update("users",
                            {"age": 31},
                            "email = ?",
                            ("mario@example.com",))
        print(f"Aggiornati {updated} record")

        # Uso di transazioni
        try:
            with db.transaction():
                db.insert("users", {"name": "Test User", "email": "test@example.com", "age": 25})
                db.update("users", {"age": 26}, "email = ?", ("test@example.com",))
                # Se tutto va bene, viene fatto commit automatico
        except Exception as e:
            print(f"Errore in transazione: {e}")
            # Rollback automatico in caso di errore