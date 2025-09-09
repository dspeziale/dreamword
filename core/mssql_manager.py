import pyodbc
import json
import os
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import logging


class MSSQLCRUD:
    """
    Classe per gestire operazioni CRUD su database Microsoft SQL Server.
    Fornisce un'interfaccia semplice e sicura per interagire con il database.
    """

    def __init__(self, server: str, database: str, username: str = None, password: str = None,
                 driver: str = "ODBC Driver 17 for SQL Server", trusted_connection: bool = False):
        """
        Inizializza la connessione al database MSSQL.

        Args:
            server (str): Nome del server SQL Server
            database (str): Nome del database
            username (str): Username per la connessione (opzionale se trusted_connection=True)
            password (str): Password per la connessione (opzionale se trusted_connection=True)
            driver (str): Driver ODBC da utilizzare
            trusted_connection (bool): Usa Windows Authentication se True
        """
        self.server = server
        self.database = database
        self.username = username
        self.password = password
        self.driver = driver
        self.trusted_connection = trusted_connection

        # Crea la cartella instance per i backup
        self.instance_dir = os.path.join(os.getcwd(), "instance")
        os.makedirs(self.instance_dir, exist_ok=True)

        self.logger = self._setup_logger()
        self._init_connection()

    def _setup_logger(self) -> logging.Logger:
        """Configura il logger per la classe."""
        logger = logging.getLogger(__name__)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    def _init_connection(self):
        """Inizializza la connessione al database con configurazioni ottimali."""
        try:
            if self.trusted_connection:
                # Windows Authentication
                connection_string = (
                    f"DRIVER={{{self.driver}}};"
                    f"SERVER={self.server};"
                    f"DATABASE={self.database};"
                    f"Trusted_Connection=yes;"
                )
            else:
                # SQL Server Authentication
                connection_string = (
                    f"DRIVER={{{self.driver}}};"
                    f"SERVER={self.server};"
                    f"DATABASE={self.database};"
                    f"UID={self.username};"
                    f"PWD={self.password};"
                )

            self.connection = pyodbc.connect(connection_string, timeout=30)
            self.connection.autocommit = False
            self.cursor = self.connection.cursor()

            self.logger.info(f"Connessione al database {self.database} su {self.server} stabilita con successo")

        except pyodbc.Error as e:
            self.logger.error(f"Errore durante l'inizializzazione del database: {e}")
            raise

    def execute_query(self, query: str, params: tuple = None) -> List[Dict]:
        """
        Esegue una query SQL e ritorna i risultati.

        Args:
            query (str): Query SQL da eseguire
            params (tuple): Parametri per la query (opzionale)

        Returns:
            List[Dict]: Lista di dizionari con i risultati
        """
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)

            # Se è una SELECT, ritorna i risultati
            if query.strip().upper().startswith('SELECT'):
                columns = [column[0] for column in self.cursor.description]
                rows = self.cursor.fetchall()
                return [dict(zip(columns, row)) for row in rows]
            else:
                # Per INSERT, UPDATE, DELETE
                affected_rows = self.cursor.rowcount
                self.connection.commit()
                return [{"affected_rows": affected_rows}]

        except pyodbc.Error as e:
            self.logger.error(f"Errore durante l'esecuzione della query: {e}")
            self.connection.rollback()
            raise

    def create_table(self, table_name: str, columns: Dict[str, str],
                     primary_key: str = None, foreign_keys: List[str] = None) -> bool:
        """
        Crea una nuova tabella nel database.

        Args:
            table_name (str): Nome della tabella
            columns (Dict[str, str]): Dizionario colonna -> tipo di dato
            primary_key (str): Nome della colonna chiave primaria
            foreign_keys (List[str]): Lista di definizioni foreign key

        Returns:
            bool: True se la tabella è stata creata con successo
        """
        try:
            # Costruisci la definizione delle colonne
            column_defs = []
            for col_name, col_type in columns.items():
                definition = f"[{col_name}] {col_type}"
                if primary_key and col_name == primary_key:
                    definition += " PRIMARY KEY"
                column_defs.append(definition)

            # Aggiungi foreign keys se specificate
            if foreign_keys:
                column_defs.extend(foreign_keys)

            columns_sql = ", ".join(column_defs)
            query = f"IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='{table_name}' AND xtype='U') CREATE TABLE [{table_name}] ({columns_sql})"

            self.execute_query(query)
            self.logger.info(f"Tabella '{table_name}' creata con successo")
            return True

        except Exception as e:
            self.logger.error(f"Errore durante la creazione della tabella '{table_name}': {e}")
            return False

    def insert(self, table: str, data: Dict[str, Any]) -> Optional[int]:
        """
        Inserisce un record nella tabella specificata.

        Args:
            table (str): Nome della tabella
            data (Dict[str, Any]): Dizionario con i dati da inserire

        Returns:
            Optional[int]: ID del record inserito o None se errore
        """
        if not data:
            self.logger.warning("Nessun dato fornito per l'inserimento")
            return None

        try:
            columns = ', '.join([f'[{key}]' for key in data.keys()])
            placeholders = ', '.join(['?' for _ in data])
            values = tuple(data.values())

            query = f"INSERT INTO [{table}] ({columns}) VALUES ({placeholders}); SELECT SCOPE_IDENTITY()"
            result = self.execute_query(query, values)

            # Esegui una query separata per ottenere l'ID inserito
            self.cursor.execute("SELECT SCOPE_IDENTITY()")
            inserted_id_row = self.cursor.fetchone()
            inserted_id = int(inserted_id_row[0]) if inserted_id_row and inserted_id_row[0] else None

            self.logger.info(f"Record inserito nella tabella '{table}' con ID: {inserted_id}")
            return inserted_id

        except Exception as e:
            self.logger.error(f"Errore durante l'inserimento nella tabella '{table}': {e}")
            return None

    def insert_many(self, table: str, data_list: List[Dict[str, Any]]) -> bool:
        """
        Inserisce multipli record nella tabella specificata.

        Args:
            table (str): Nome della tabella
            data_list (List[Dict[str, Any]]): Lista di dizionari con i dati

        Returns:
            bool: True se tutti i record sono stati inseriti con successo
        """
        if not data_list:
            self.logger.warning("Nessun dato fornito per l'inserimento multiplo")
            return False

        try:
            # Usa le chiavi del primo elemento per definire le colonne
            columns = list(data_list[0].keys())
            columns_str = ', '.join([f'[{col}]' for col in columns])
            placeholders = ', '.join(['?' for _ in columns])

            query = f"INSERT INTO [{table}] ({columns_str}) VALUES ({placeholders})"

            # Prepara i valori per tutti i record
            values_list = []
            for data in data_list:
                values_list.append(tuple(data.get(col) for col in columns))

            self.cursor.executemany(query, values_list)
            self.connection.commit()

            self.logger.info(f"{len(data_list)} record inseriti nella tabella '{table}'")
            return True

        except Exception as e:
            self.logger.error(f"Errore durante l'inserimento multiplo nella tabella '{table}': {e}")
            self.connection.rollback()
            return False

    def select(self, table: str, columns: str = "*", where: str = None,
               params: tuple = None, order_by: str = None, limit: int = None) -> List[Dict]:
        """
        Seleziona record dalla tabella specificata.

        Args:
            table (str): Nome della tabella
            columns (str): Colonne da selezionare (default: "*")
            where (str): Condizione WHERE (opzionale)
            params (tuple): Parametri per la condizione WHERE
            order_by (str): Ordinamento (opzionale)
            limit (int): Limite di risultati (opzionale)

        Returns:
            List[Dict]: Lista di record trovati
        """
        try:
            if limit and not order_by:
                query = f"SELECT TOP {limit} {columns} FROM [{table}]"
            elif limit and order_by:
                query = f"SELECT TOP {limit} {columns} FROM [{table}]"
            else:
                query = f"SELECT {columns} FROM [{table}]"

            if where:
                query += f" WHERE {where}"

            if order_by:
                query += f" ORDER BY {order_by}"

            results = self.execute_query(query, params)
            self.logger.info(f"Trovati {len(results)} record nella tabella '{table}'")
            return results

        except Exception as e:
            self.logger.error(f"Errore durante la selezione dalla tabella '{table}': {e}")
            return []

    def select_by_id(self, table: str, record_id: Union[int, str],
                     id_column: str = "id") -> Optional[Dict]:
        """
        Seleziona un record specifico tramite ID.

        Args:
            table (str): Nome della tabella
            record_id (Union[int, str]): ID del record
            id_column (str): Nome della colonna ID (default: "id")

        Returns:
            Optional[Dict]: Record trovato o None
        """
        results = self.select(table, where=f"[{id_column}] = ?", params=(record_id,))
        return results[0] if results else None

    def update(self, table: str, data: Dict[str, Any], where: str,
               params: tuple = None) -> int:
        """
        Aggiorna record nella tabella specificata.

        Args:
            table (str): Nome della tabella
            data (Dict[str, Any]): Dati da aggiornare
            where (str): Condizione WHERE
            params (tuple): Parametri aggiuntivi per WHERE

        Returns:
            int: Numero di record aggiornati
        """
        if not data:
            self.logger.warning("Nessun dato fornito per l'aggiornamento")
            return 0

        try:
            set_clause = ', '.join([f"[{key}] = ?" for key in data.keys()])
            values = list(data.values())

            if params:
                values.extend(params)

            query = f"UPDATE [{table}] SET {set_clause} WHERE {where}"
            result = self.execute_query(query, tuple(values))

            affected_rows = result[0]['affected_rows']
            self.logger.info(f"{affected_rows} record aggiornati nella tabella '{table}'")
            return affected_rows

        except Exception as e:
            self.logger.error(f"Errore durante l'aggiornamento della tabella '{table}': {e}")
            return 0

    def update_by_id(self, table: str, record_id: Union[int, str],
                     data: Dict[str, Any], id_column: str = "id") -> bool:
        """
        Aggiorna un record specifico tramite ID.

        Args:
            table (str): Nome della tabella
            record_id (Union[int, str]): ID del record
            data (Dict[str, Any]): Dati da aggiornare
            id_column (str): Nome della colonna ID (default: "id")

        Returns:
            bool: True se il record è stato aggiornato
        """
        affected_rows = self.update(table, data, f"[{id_column}] = ?", (record_id,))
        return affected_rows > 0

    def delete(self, table: str, where: str, params: tuple = None) -> int:
        """
        Elimina record dalla tabella specificata.

        Args:
            table (str): Nome della tabella
            where (str): Condizione WHERE
            params (tuple): Parametri per la condizione WHERE

        Returns:
            int: Numero di record eliminati
        """
        try:
            query = f"DELETE FROM [{table}] WHERE {where}"
            result = self.execute_query(query, params)

            affected_rows = result[0]['affected_rows']
            self.logger.info(f"{affected_rows} record eliminati dalla tabella '{table}'")
            return affected_rows

        except Exception as e:
            self.logger.error(f"Errore durante l'eliminazione dalla tabella '{table}': {e}")
            return 0

    def delete_by_id(self, table: str, record_id: Union[int, str],
                     id_column: str = "id") -> bool:
        """
        Elimina un record specifico tramite ID.

        Args:
            table (str): Nome della tabella
            record_id (Union[int, str]): ID del record
            id_column (str): Nome della colonna ID (default: "id")

        Returns:
            bool: True se il record è stato eliminato
        """
        affected_rows = self.delete(table, f"[{id_column}] = ?", (record_id,))
        return affected_rows > 0

    def count(self, table: str, where: str = None, params: tuple = None) -> int:
        """
        Conta i record nella tabella specificata.

        Args:
            table (str): Nome della tabella
            where (str): Condizione WHERE (opzionale)
            params (tuple): Parametri per la condizione WHERE

        Returns:
            int: Numero di record
        """
        query = f"SELECT COUNT(*) as count FROM [{table}]"
        if where:
            query += f" WHERE {where}"

        result = self.execute_query(query, params)
        return result[0]['count'] if result else 0

    def exists(self, table: str, where: str, params: tuple = None) -> bool:
        """
        Verifica se esistono record che soddisfano la condizione.

        Args:
            table (str): Nome della tabella
            where (str): Condizione WHERE
            params (tuple): Parametri per la condizione WHERE

        Returns:
            bool: True se esistono record
        """
        count = self.count(table, where, params)
        return count > 0

    def get_table_info(self, table: str) -> List[Dict]:
        """
        Ottiene informazioni sulla struttura della tabella.

        Args:
            table (str): Nome della tabella

        Returns:
            List[Dict]: Informazioni sulle colonne della tabella
        """
        try:
            query = """
            SELECT 
                COLUMN_NAME as column_name,
                DATA_TYPE as data_type,
                IS_NULLABLE as is_nullable,
                COLUMN_DEFAULT as column_default,
                CHARACTER_MAXIMUM_LENGTH as max_length
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = ?
            ORDER BY ORDINAL_POSITION
            """
            return self.execute_query(query, (table,))
        except Exception as e:
            self.logger.error(f"Errore durante il recupero delle informazioni per la tabella '{table}': {e}")
            return []

    def get_table_names(self) -> List[str]:
        """
        Ottiene l'elenco di tutte le tabelle nel database.

        Returns:
            List[str]: Lista dei nomi delle tabelle
        """
        try:
            query = "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'"
            results = self.execute_query(query)
            return [row['TABLE_NAME'] for row in results]
        except Exception as e:
            self.logger.error(f"Errore durante il recupero dei nomi delle tabelle: {e}")
            return []

    def backup_table(self, table: str, backup_file: str) -> bool:
        """
        Crea un backup di una tabella in formato JSON nella cartella instance.

        Args:
            table (str): Nome della tabella
            backup_file (str): Nome del file di backup (verrà salvato nella cartella instance)

        Returns:
            bool: True se il backup è riuscito
        """
        try:
            # Se non è un percorso assoluto, salva nella cartella instance
            if not os.path.isabs(backup_file):
                backup_path = os.path.join(self.instance_dir, backup_file)
            else:
                backup_path = backup_file

            data = self.select(table)
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str, ensure_ascii=False)

            self.logger.info(f"Backup della tabella '{table}' salvato in '{backup_path}'")
            return True

        except Exception as e:
            self.logger.error(f"Errore durante il backup della tabella '{table}': {e}")
            return False

    def close(self):
        """Chiude la connessione al database."""
        if hasattr(self, 'connection'):
            self.connection.close()
            self.logger.info("Connessione al database chiusa")

    def __enter__(self):
        """Supporto per il context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cleanup automatico quando si esce dal context manager."""
        self.close()


# Esempio di utilizzo della classe
if __name__ == "__main__":
    # Esempio con Windows Authentication
    # with MSSQLCRUD("localhost\\SQLEXPRESS", "TestDB", trusted_connection=True) as db:

    # Esempio con SQL Server Authentication
    with MSSQLCRUD("localhost\\SQLEXPRESS", "TestDB", "username", "password") as db:

        # Mostra i percorsi che verranno utilizzati per i backup
        print(f"Cartella instance per backup: {db.instance_dir}")

        # Crea una tabella di esempio
        db.create_table(
            "users",
            {
                "id": "INT IDENTITY(1,1)",
                "name": "NVARCHAR(100) NOT NULL",
                "email": "NVARCHAR(255) UNIQUE NOT NULL",
                "age": "INT",
                "created_at": "DATETIME2 DEFAULT GETDATE()"
            },
            primary_key="id"
        )

        # Controlla se gli utenti esistono già
        existing_users = db.select("users", where="email IN (?, ?)",
                                   params=("mario.rossi@email.com", "luigi.bianchi@email.com"))

        if not existing_users:
            # Inserisce alcuni utenti
            user1_id = db.insert("users", {
                "name": "Mario Rossi",
                "email": "mario.rossi@email.com",
                "age": 30
            })

            user2_id = db.insert("users", {
                "name": "Luigi Bianchi",
                "email": "luigi.bianchi@email.com",
                "age": 25
            })
            print(f"Utenti inseriti con ID: {user1_id}, {user2_id}")
        else:
            print("Utenti già esistenti nel database")
            user1_id = existing_users[0]['id'] if len(existing_users) > 0 else None

        # Seleziona tutti gli utenti
        all_users = db.select("users")
        print("Tutti gli utenti:", all_users)

        # Seleziona un utente per ID
        if user1_id:
            user = db.select_by_id("users", user1_id)
            print("Utente trovato:", user)

            # Aggiorna un utente
            updated = db.update_by_id("users", user1_id, {"age": 31})
            print(f"Utente aggiornato: {updated}")

        # Conta gli utenti
        user_count = db.count("users")
        print(f"Numero totale di utenti: {user_count}")

        # Backup della tabella
        backup_success = db.backup_table("users", "users_backup_mssql.json")
        if backup_success:
            backup_path = os.path.join(db.instance_dir, "users_backup_mssql.json")
            print(f"File di backup salvato in: {backup_path}")

    print("Operazioni MSSQL completate con successo!")