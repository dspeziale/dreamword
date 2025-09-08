# framework/database/mssql_manager.py
import pyodbc
import logging
from typing import List, Dict, Any, Optional
from contextlib import contextmanager


class MSSQLManager:
    """Gestione database Microsoft SQL Server"""

    def __init__(self, server: str, database: str, username: str = None, password: str = None,
                 trusted_connection: bool = True):
        self.server = server
        self.database = database
        self.username = username
        self.password = password
        self.trusted_connection = trusted_connection
        self.logger = logging.getLogger(__name__)

        # Costruisce connection string
        if trusted_connection:
            self.conn_string = (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={server};"
                f"DATABASE={database};"
                f"Trusted_Connection=yes;"
            )
        else:
            self.conn_string = (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={server};"
                f"DATABASE={database};"
                f"UID={username};"
                f"PWD={password};"
            )

    @contextmanager
    def get_connection(self):
        """Context manager per gestire le connessioni MSSQL"""
        conn = None
        try:
            conn = pyodbc.connect(self.conn_string)
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            self.logger.error(f"Errore database MSSQL: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Esegue una query SELECT"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)

            # Ottiene nomi colonne
            columns = [column[0] for column in cursor.description]

            # Converte risultati in lista di dizionari
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))

            return results

    def execute_non_query(self, query: str, params: tuple = ()) -> int:
        """Esegue INSERT, UPDATE, DELETE"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount

    def execute_stored_procedure(self, proc_name: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Esegue una stored procedure"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"EXEC {proc_name} {','.join(['?' for _ in params])}", params)

            if cursor.description:  # Se restituisce risultati
                columns = [column[0] for column in cursor.description]
                results = []
                for row in cursor.fetchall():
                    results.append(dict(zip(columns, row)))
                return results
            else:
                conn.commit()
                return []