# config.py
"""
Configurazioni per l'applicazione
"""

import os
from framework import DatabaseConfig, DatabaseType

# Configurazioni database
DATABASE_CONFIGS = {
    'development': DatabaseConfig(
        db_type=DatabaseType.SQLITE,
        file_path='app_development.db'
    ),

    'testing': DatabaseConfig(
        db_type=DatabaseType.SQLITE,
        file_path=':memory:'
    ),

    'production': DatabaseConfig(
        db_type=DatabaseType.SQLITE,
        file_path='app_production.db'
    ),

    # Esempio configurazione MySQL
    'mysql_production': DatabaseConfig(
        db_type=DatabaseType.MYSQL,
        host=os.getenv('MYSQL_HOST', 'localhost'),
        port=int(os.getenv('MYSQL_PORT', 3306)),
        database=os.getenv('MYSQL_DATABASE', 'app_db'),
        username=os.getenv('MYSQL_USER', 'user'),
        password=os.getenv('MYSQL_PASSWORD', 'password')
    ),

    # Esempio configurazione SQL Server
    'mssql_production': DatabaseConfig(
        db_type=DatabaseType.MSSQL,
        host=os.getenv('MSSQL_HOST', 'localhost'),
        port=int(os.getenv('MSSQL_PORT', 1433)),
        database=os.getenv('MSSQL_DATABASE', 'app_db'),
        username=os.getenv('MSSQL_USER', 'sa'),
        password=os.getenv('MSSQL_PASSWORD', 'password')
    )
}

# Configurazione attiva
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
DATABASE_CONFIG = DATABASE_CONFIGS[ENVIRONMENT]

# Altre configurazioni
APP_NAME = "Database Framework Demo"
VERSION = "1.0.0"
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'

# Logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'