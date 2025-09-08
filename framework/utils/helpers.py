import hashlib
import secrets
import string
import json
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
import os
from pathlib import Path


class FrameworkHelpers:
    """Collezione di funzioni helper"""

    @staticmethod
    def generate_random_string(length: int = 32, include_symbols: bool = False) -> str:
        """Genera stringa casuale"""
        characters = string.ascii_letters + string.digits
        if include_symbols:
            characters += "!@#$%^&*"

        return ''.join(secrets.choice(characters) for _ in range(length))

    @staticmethod
    def generate_api_key() -> str:
        """Genera chiave API"""
        return f"fw_{FrameworkHelpers.generate_random_string(40)}"

    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> tuple:
        """Hash password con salt"""
        if salt is None:
            salt = secrets.token_hex(16)

        # Hash con PBKDF2
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # 100k iterazioni
        )

        return password_hash.hex(), salt

    @staticmethod
    def verify_password(password: str, password_hash: str, salt: str) -> bool:
        """Verifica password"""
        computed_hash, _ = FrameworkHelpers.hash_password(password, salt)
        return secrets.compare_digest(computed_hash, password_hash)

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitizza nome file"""
        # Rimuovi caratteri pericolosi
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')

        # Limita lunghezza
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:255 - len(ext)] + ext

        return filename

    @staticmethod
    def format_bytes(bytes_value: int) -> str:
        """Formatta byte in formato leggibile"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} PB"

    @staticmethod
    def deep_merge_dict(dict1: dict, dict2: dict) -> dict:
        """Merge profondo di dizionari"""
        result = dict1.copy()

        for key, value in dict2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = FrameworkHelpers.deep_merge_dict(result[key], value)
            else:
                result[key] = value

        return result

    @staticmethod
    def flatten_dict(d: dict, parent_key: str = '', sep: str = '.') -> dict:
        """Appiattisce dizionario annidato"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(FrameworkHelpers.flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)

    @staticmethod
    def safe_json_loads(json_str: str, default: Any = None) -> Any:
        """Parse JSON sicuro"""
        try:
            return json.loads(json_str)
        except (json.JSONDecodeError, TypeError):
            return default

    @staticmethod
    def chunks(lst: List[Any], chunk_size: int) -> List[List[Any]]:
        """Divide lista in chunk"""
        for i in range(0, len(lst), chunk_size):
            yield lst[i:i + chunk_size]

    @staticmethod
    def is_port_open(host: str, port: int, timeout: float = 3.0) -> bool:
        """Controlla se porta è aperta"""
        import socket

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(timeout)
                result = sock.connect_ex((host, port))
                return result == 0
        except socket.gaierror:
            return False