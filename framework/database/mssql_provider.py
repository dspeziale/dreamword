# framework/database/mssql_provider.py

"""
Provider MSSQL per ModularFramework

Implementa DatabaseProvider per SQL Server
"""

import urllib.parse
from typing import Dict, Any
from .manager import DatabaseProvider


class MSSQLProvider(DatabaseProvider):
    """Provider per Microsoft SQL Server"""

    def __init__(self, config):
        """
        Inizializza provider MSSQL

        Args:
            config: Configurazione database
        """
        self.config = config
        self._validate_config()

    def _validate_config(self):
        """Valida configurazione MSSQL"""
        required_fields = ['mssql_server', 'mssql_database']

        for field in required_fields:
            if not getattr(self.config, field, None):
                raise ValueError(f"Campo obbligatorio mancante per MSSQL: {field}")

        # Se non usa trusted connection, verifica username/password
        if not self.config.mssql_trusted_connection:
            if not self.config.mssql_username:
                raise ValueError("mssql_username è obbligatorio quando trusted_connection=False")
            if not self.config.mssql_password:
                raise ValueError("mssql_password è obbligatorio quando trusted_connection=False")

    def get_connection_string(self) -> str:
        """
        Genera stringa di connessione MSSQL

        Returns:
            Connection string per SQLAlchemy
        """
        if self.config.mssql_trusted_connection:
            # Autenticazione Windows
            connection_string = (
                f"mssql+pyodbc://@{self.config.mssql_server}"
                f":{self.config.mssql_port}/{self.config.mssql_database}"
                f"?driver={urllib.parse.quote_plus(self.config.mssql_driver)}"
                f"&trusted_connection=yes"
                f"&autocommit=true"
            )
        else:
            # Autenticazione SQL Server
            username = urllib.parse.quote_plus(self.config.mssql_username)
            password = urllib.parse.quote_plus(self.config.mssql_password)

            connection_string = (
                f"mssql+pyodbc://{username}:{password}@"
                f"{self.config.mssql_server}:{self.config.mssql_port}/"
                f"{self.config.mssql_database}"
                f"?driver={urllib.parse.quote_plus(self.config.mssql_driver)}"
                f"&autocommit=true"
            )

        return connection_string

    def get_engine_options(self) -> Dict[str, Any]:
        """
        Opzioni specifiche per engine MSSQL

        Returns:
            Dizionario con opzioni engine
        """
        return {
            # Pool connessioni
            "pool_size": self.config.pool_size,
            "max_overflow": self.config.max_overflow,
            "pool_timeout": self.config.pool_timeout,
            "pool_recycle": self.config.pool_recycle,
            "pool_pre_ping": True,

            # Opzioni connessione
            "connect_args": {
                "timeout": 30,
                "autocommit": False,
                "check_same_thread": False,
            },

            # Echo opzioni
            "echo": self.config.echo,
            "echo_pool": self.config.echo_pool,

            # Altre opzioni
            "isolation_level": "READ_COMMITTED",
        }

    def get_dialect_options(self) -> Dict[str, Any]:
        """
        Opzioni specifiche del dialetto MSSQL

        Returns:
            Opzioni dialetto
        """
        return {
            "json_serializer": None,
            "json_deserializer": None,
            "use_setinputsizes": False,
            "fast_executemany": True,  # Migliora performance INSERT
        }

    def supports_feature(self, feature: str) -> bool:
        """
        Verifica se una feature è supportata

        Args:
            feature: Nome della feature

        Returns:
            True se supportata
        """
        # Features supportate da SQL Server
        supported_features = {
            "transactions": True,
            "foreign_keys": True,
            "indexes": True,
            "triggers": True,
            "views": True,
            "stored_procedures": True,
            "functions": True,
            "json": True,  # SQL Server 2016+
            "full_text_search": True,
            "window_functions": True,
            "cte": True,  # Common Table Expressions
            "merge": True,  # MERGE statement
            "sequences": True,
            "partitioning": True,
            "compression": True,
            "encryption": True,
            "always_encrypted": True,
            "temporal_tables": True,  # SQL Server 2016+
            "graph": True,  # SQL Server 2017+
            "columnstore": True,
            "in_memory": True,
        }

        return supported_features.get(feature, False)

    def get_database_info(self) -> Dict[str, Any]:
        """
        Informazioni sul database (richiede connessione attiva)

        Returns:
            Dizionario con informazioni database
        """
        return {
            "provider": "mssql",
            "server": self.config.mssql_server,
            "port": self.config.mssql_port,
            "database": self.config.mssql_database,
            "driver": self.config.mssql_driver,
            "trusted_connection": self.config.mssql_trusted_connection,
            "username": self.config.mssql_username if not self.config.mssql_trusted_connection else None,
        }

    def get_maintenance_queries(self) -> Dict[str, str]:
        """
        Query di manutenzione SQL Server

        Returns:
            Dizionario con query di manutenzione
        """
        db_name = self.config.mssql_database

        return {
            # Statistiche database
            "database_size": f"""
                SELECT 
                    DB_NAME() as database_name,
                    SUM(CAST(FILEPROPERTY(name, 'SpaceUsed') AS bigint) * 8192.) / 1024 / 1024 AS used_space_mb,
                    SUM(size * 8192.) / 1024 / 1024 AS allocated_space_mb
                FROM sys.database_files
            """,

            # Informazioni tabelle
            "table_info": """
                SELECT 
                    t.name AS table_name,
                    p.rows AS row_count,
                    SUM(a.total_pages) * 8 AS total_space_kb,
                    SUM(a.used_pages) * 8 AS used_space_kb
                FROM sys.tables t
                INNER JOIN sys.indexes i ON t.object_id = i.object_id
                INNER JOIN sys.partitions p ON i.object_id = p.object_id AND i.index_id = p.index_id
                INNER JOIN sys.allocation_units a ON p.partition_id = a.container_id
                WHERE t.is_ms_shipped = 0
                GROUP BY t.name, p.rows
                ORDER BY used_space_kb DESC
            """,

            # Statistiche indici
            "index_usage": """
                SELECT 
                    OBJECT_NAME(s.object_id) AS table_name,
                    i.name AS index_name,
                    s.user_seeks,
                    s.user_scans,
                    s.user_lookups,
                    s.user_updates
                FROM sys.dm_db_index_usage_stats s
                INNER JOIN sys.indexes i ON s.object_id = i.object_id AND s.index_id = i.index_id
                WHERE s.database_id = DB_ID()
                ORDER BY s.user_seeks + s.user_scans + s.user_lookups DESC
            """,

            # Check integrità
            "integrity_check": f"DBCC CHECKDB('{db_name}') WITH NO_INFOMSGS",

            # Aggiorna statistiche
            "update_statistics": f"EXEC sp_updatestats",

            # Riorganizza indici
            "reorg_indexes": """
                DECLARE @sql NVARCHAR(MAX) = ''
                SELECT @sql = @sql + 
                    'ALTER INDEX ' + i.name + ' ON ' + OBJECT_SCHEMA_NAME(i.object_id) + '.' + OBJECT_NAME(i.object_id) + ' REORGANIZE;' + CHAR(13)
                FROM sys.indexes i
                WHERE i.index_id > 0 AND i.is_disabled = 0 AND i.is_hypothetical = 0
                EXEC sp_executesql @sql
            """,

            # Spazio libero
            "free_space": """
                SELECT 
                    name,
                    size/128.0 AS current_size_mb,
                    size/128.0 - CAST(FILEPROPERTY(name, 'SpaceUsed') AS int)/128.0 AS free_space_mb
                FROM sys.database_files
            """,
        }

    def optimize_database(self) -> Dict[str, Any]:
        """
        Ottimizza database SQL Server

        Returns:
            Risultati ottimizzazione
        """
        db_name = self.config.mssql_database

        return {
            "commands": [
                f"EXEC sp_updatestats",  # Aggiorna statistiche
                f"DBCC FREEPROCCACHE",  # Pulisce cache piani
                f"DBCC DROPCLEANBUFFERS",  # Pulisce buffer (solo development!)
                # Ricompila stored procedures
                f"EXEC sp_recompile N'{db_name}'",
            ],
            "maintenance_plan": [
                "UPDATE STATISTICS per tutte le tabelle",
                "REORGANIZE INDEXES per indici frammentati < 30%",
                "REBUILD INDEXES per indici frammentati > 30%",
                "SHRINK LOG FILE se necessario",
                "BACKUP DATABASE",
            ],
            "description": "Piano di ottimizzazione SQL Server"
        }

    def get_backup_command(self, backup_path: str) -> str:
        """
        Comando per backup database

        Args:
            backup_path: Path di destinazione backup

        Returns:
            Comando SQL per backup
        """
        db_name = self.config.mssql_database
        return f"""
            BACKUP DATABASE [{db_name}] 
            TO DISK = '{backup_path}'
            WITH FORMAT, INIT, COMPRESSION, 
            NAME = '{db_name} Full Backup',
            SKIP, NOREWIND, NOUNLOAD, STATS = 10
        """

    def get_restore_command(self, backup_path: str, target_db: str = None) -> str:
        """
        Comando per restore database

        Args:
            backup_path: Path del backup
            target_db: Nome database destinazione (opzionale)

        Returns:
            Comando SQL per restore
        """
        target_db = target_db or self.config.mssql_database

        return f"""
            RESTORE DATABASE [{target_db}]
            FROM DISK = '{backup_path}'
            WITH REPLACE, STATS = 10
        """

    def validate_connection_string(self, connection_string: str) -> bool:
        """
        Valida stringa di connessione

        Args:
            connection_string: Stringa da validare

        Returns:
            True se valida
        """
        try:
            # MSSQL connection string contiene mssql+pyodbc://
            if not connection_string.startswith("mssql+pyodbc://"):
                return False

            # Verifica presenza componenti essenziali
            required_components = ["driver=", "database"]
            return all(comp in connection_string for comp in required_components)

        except Exception:
            return False

    def get_connection_test_query(self) -> str:
        """
        Query per testare connessione

        Returns:
            Query SQL di test
        """
        return "SELECT 1 AS test, @@VERSION AS version, DB_NAME() AS database_name"

    def get_server_info_queries(self) -> Dict[str, str]:
        """
        Query per informazioni server

        Returns:
            Dizionario con query informative
        """
        return {
            "version": "SELECT @@VERSION AS version",
            "server_name": "SELECT @@SERVERNAME AS server_name",
            "edition": "SELECT SERVERPROPERTY('Edition') AS edition",
            "product_version": "SELECT SERVERPROPERTY('ProductVersion') AS product_version",
            "collation": "SELECT SERVERPROPERTY('Collation') AS collation",
            "instance_name": "SELECT SERVERPROPERTY('InstanceName') AS instance_name",
            "is_clustered": "SELECT SERVERPROPERTY('IsClustered') AS is_clustered",
            "machine_name": "SELECT SERVERPROPERTY('MachineName') AS machine_name",
        }