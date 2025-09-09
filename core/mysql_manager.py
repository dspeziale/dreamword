import mysql.connector
from mysql.connector import Error
import json
import os
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import logging


class MySQLCRUD:
    """
    Classe per gestire operazioni CRUD su database MySQL/MariaDB.
    Fornisce un'interfaccia semplice e sicura per interagire con il database.
    """

    def __init__(self, host: str, database: str, username: str, password: str,
                 port: int = 3306, charset: str = 'utf8mb4'):
        """
        Inizializza la connessione al database MySQL.

        Args:
            host (str): Host del server MySQL
            database (str): Nome del database
            username (str): Username per la connessione
            password (str): Password per la connessione
            port (int): Porta del server MySQL (default: 3306)
            charset (str): Charset per la connessione (default: utf8mb4)
        """
        self.host = host
        self.database = database
        self.username = username
        self.password = password
        self.port = port
        self.charset = charset

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
            self.connection = mysql.connector.connect(
                host=self.host,
                database=self.database,
                user=self.username,
                password=self.password,
                port=self.port,
                charset=self.charset,
                autocommit=False,
                connection_timeout=30,
                buffered=True
            )
            self.cursor = self.connection.cursor(dictionary=True)

            self.logger.info(
                f"Connessione al database {self.database} su {self.host}:{self.port} stabilita con successo")

        except Error as e:
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
                results = self.cursor.fetchall()
                return results if results else []
            else:
                # Per INSERT, UPDATE, DELETE
                affected_rows = self.cursor.rowcount
                last_insert_id = self.cursor.lastrowid
                self.connection.commit()
                return [{"affected_rows": affected_rows, "lastrowid": last_insert_id}]

        except Error as e:
            self.logger.error(f"Errore durante l'esecuzione della query: {e}")
            self.connection.rollback()
            raise

    def create_table(self, table_name: str, columns: Dict[str, str],
                     primary_key: str = None, foreign_keys: List[str] = None,
                     engine: str = "InnoDB", charset: str = "utf8mb4") -> bool:
        """
        Crea una nuova tabella nel database.

        Args:
            table_name (str): Nome della tabella
            columns (Dict[str, str]): Dizionario colonna -> tipo di dato
            primary_key (str): Nome della colonna chiave primaria
            foreign_keys (List[str]): Lista di definizioni foreign key
            engine (str): Engine MySQL da utilizzare (default: InnoDB)
            charset (str): Charset per la tabella (default: utf8mb4)

        Returns:
            bool: True se la tabella è stata creata con successo
        """
        try:
            # Costruisci la definizione delle colonne
            column_defs = []
            for col_name, col_type in columns.items():
                definition = f"`{col_name}` {col_type}"
                if primary_key and col_name == primary_key:
                    definition += " PRIMARY KEY"
                column_defs.append(definition)

            # Aggiungi foreign keys se specificate
            if foreign_keys:
                column_defs.extend(foreign_keys)

            columns_sql = ", ".join(column_defs)
            query = f"""
            CREATE TABLE IF NOT EXISTS `{table_name}` (
                {columns_sql}
            ) ENGINE={engine} DEFAULT CHARSET={charset}
            """

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
            columns = ', '.join([f'`{key}`' for key in data.keys()])
            placeholders = ', '.join(['%s' for _ in data])
            values = tuple(data.values())

            query = f"INSERT INTO `{table}` ({columns}) VALUES ({placeholders})"
            result = self.execute_query(query, values)

            inserted_id = result[0]['lastrowid']
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
            columns_str = ', '.join([f'`{col}`' for col in columns])
            placeholders = ', '.join(['%s' for _ in columns])

            query = f"INSERT INTO `{table}` ({columns_str}) VALUES ({placeholders})"

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
            query = f"SELECT {columns} FROM `{table}`"

            if where:
                query += f" WHERE {where}"

            if order_by:
                query += f" ORDER BY {order_by}"

            if limit:
                query += f" LIMIT {limit}"

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
        results = self.select(table, where=f"`{id_column}` = %s", params=(record_id,))
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
            set_clause = ', '.join([f"`{key}` = %s" for key in data.keys()])
            values = list(data.values())

            if params:
                values.extend(params)

            query = f"UPDATE `{table}` SET {set_clause} WHERE {where}"
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
        affected_rows = self.update(table, data, f"`{id_column}` = %s", (record_id,))
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
            query = f"DELETE FROM `{table}` WHERE {where}"
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
        affected_rows = self.delete(table, f"`{id_column}` = %s", (record_id,))
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
        query = f"SELECT COUNT(*) as count FROM `{table}`"
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
            query = f"DESCRIBE `{table}`"
            return self.execute_query(query)
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
            query = "SHOW TABLES"
            results = self.execute_query(query)
            # Il nome della colonna varia in base al database
            key = f"Tables_in_{self.database}"
            return [row[key] for row in results]
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

    def create_index(self, table: str, index_name: str, columns: List[str], unique: bool = False) -> bool:
        """
        Crea un indice sulla tabella specificata.

        Args:
            table (str): Nome della tabella
            index_name (str): Nome dell'indice
            columns (List[str]): Lista delle colonne per l'indice
            unique (bool): Se True, crea un indice unico

        Returns:
            bool: True se l'indice è stato creato con successo
        """
        try:
            unique_keyword = "UNIQUE" if unique else ""
            columns_str = ', '.join([f"`{col}`" for col in columns])
            query = f"CREATE {unique_keyword} INDEX `{index_name}` ON `{table}` ({columns_str})"

            self.execute_query(query)
            self.logger.info(f"Indice '{index_name}' creato con successo sulla tabella '{table}'")
            return True

        except Exception as e:
            self.logger.error(f"Errore durante la creazione dell'indice '{index_name}': {e}")
            return False

    def close(self):
        """Chiude la connessione al database."""
        if hasattr(self, 'cursor') and self.cursor:
            self.cursor.close()
        if hasattr(self, 'connection') and self.connection.is_connected():
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
    # Esempio pratico di utilizzo
    with MySQLCRUD("localhost", "testdb", "username", "password") as db:

        # Mostra i percorsi che verranno utilizzati per i backup
        print(f"Cartella instance per backup: {db.instance_dir}")

        # Crea una tabella di esempio
        db.create_table(
            "users",
            {
                "id": "INT AUTO_INCREMENT",
                "name": "VARCHAR(100) NOT NULL",
                "email": "VARCHAR(255) UNIQUE NOT NULL",
                "age": "INT",
                "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            },
            primary_key="id"
        )

        # Controlla se gli utenti esistono già
        existing_users = db.select("users", where="email IN (%s, %s)",
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

        # Crea un indice sulla colonna email
        db.create_index("users", "idx_email", ["email"], unique=True)

        # Backup della tabella
        backup_success = db.backup_table("users", "users_backup_mysql.json")
        if backup_success:
            backup_path = os.path.join(db.instance_dir, "users_backup_mysql.json")
            print(f"File di backup salvato in: {backup_path}")

    print("Operazioni MySQL completate con successo!")