# framework/config.py
"""
Configurazione del framework per gestire directory instance
"""

import os
from pathlib import Path


class FrameworkConfig:
    """Configurazione centrale del framework"""

    def __init__(self, base_dir: str = None):
        # Directory base del progetto
        if base_dir is None:
            base_dir = os.getcwd()

        self.base_dir = Path(base_dir)
        self.instance_dir = self.base_dir / "instance"

        # Sottodirectory in instance
        self.logs_dir = self.instance_dir / "logs"
        self.database_dir = self.instance_dir / "database"
        self.temp_dir = self.instance_dir / "temp"

        # Crea le directory se non esistono
        self._create_directories()

    def _create_directories(self):
        """Crea le directory necessarie"""
        directories = [
            self.instance_dir,
            self.logs_dir,
            self.database_dir,
            self.temp_dir
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def get_database_path(self, db_name: str) -> str:
        """Ritorna il path completo per un database"""
        if not db_name.endswith('.db'):
            db_name += '.db'
        return str(self.database_dir / db_name)

    def get_log_path(self, log_name: str) -> str:
        """Ritorna il path completo per un file di log"""
        if not log_name.endswith('.log'):
            log_name += '.log'
        return str(self.logs_dir / log_name)

    def get_temp_path(self, file_name: str) -> str:
        """Ritorna il path completo per un file temporaneo"""
        return str(self.temp_dir / file_name)

    def cleanup_temp(self):
        """Pulisce i file temporanei"""
        try:
            for file_path in self.temp_dir.glob("*"):
                if file_path.is_file():
                    file_path.unlink()
        except Exception as e:
            print(f"Errore pulizia temp: {e}")


# Istanza globale della configurazione
_config = None


def get_config() -> FrameworkConfig:
    """Ottiene l'istanza globale della configurazione"""
    global _config
    if _config is None:
        _config = FrameworkConfig()
    return _config


def set_base_directory(base_dir: str):
    """Imposta una directory base personalizzata"""
    global _config
    _config = FrameworkConfig(base_dir)