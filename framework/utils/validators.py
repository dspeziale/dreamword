import re
import ipaddress
from typing import Any, Optional, Union, List
from email_validator import validate_email, EmailNotValidError
import validators
from datetime import datetime


class ValidationError(Exception):
    """Eccezione per errori di validazione"""
    pass


class FrameworkValidators:
    """Collezione di validatori per il framework"""

    @staticmethod
    def validate_email_address(email: str) -> bool:
        """Valida indirizzo email"""
        try:
            validate_email(email)
            return True
        except EmailNotValidError:
            return False

    @staticmethod
    def validate_url(url: str, public: bool = False) -> bool:
        """Valida URL"""
        try:
            result = validators.url(url, public=public)
            return result is True
        except:
            return False

    @staticmethod
    def validate_ip_address(ip: str, version: Optional[int] = None) -> bool:
        """Valida indirizzo IP"""
        try:
            ip_obj = ipaddress.ip_address(ip)
            if version:
                return ip_obj.version == version
            return True
        except ValueError:
            return False

    @staticmethod
    def validate_port(port: Union[str, int]) -> bool:
        """Valida porta di rete"""
        try:
            port_int = int(port)
            return 1 <= port_int <= 65535
        except (ValueError, TypeError):
            return False

    @staticmethod
    def validate_database_name(name: str) -> bool:
        """Valida nome database"""
        # Lettere, numeri, underscore, non inizia con numero
        pattern = r'^[a-zA-Z_][a-zA-Z0-9_]*$'
        return bool(re.match(pattern, name)) and len(name) <= 64

    @staticmethod
    def validate_plugin_name(name: str) -> bool:
        """Valida nome plugin"""
        # Lettere, numeri, underscore, trattino
        pattern = r'^[a-zA-Z][a-zA-Z0-9_-]*$'
        return bool(re.match(pattern, name)) and len(name) <= 50

    @staticmethod
    def validate_json_structure(data: Any, required_keys: List[str]) -> bool:
        """Valida struttura JSON"""
        if not isinstance(data, dict):
            return False

        for key in required_keys:
            if key not in data:
                return False

        return True

    @staticmethod
    def validate_password_strength(password: str) -> dict:
        """Valida forza password"""
        result = {
            'valid': True,
            'score': 0,
            'issues': []
        }

        if len(password) < 8:
            result['issues'].append('Minimo 8 caratteri')
            result['valid'] = False
        else:
            result['score'] += 1

        if not re.search(r'[A-Z]', password):
            result['issues'].append('Manca lettera maiuscola')
        else:
            result['score'] += 1

        if not re.search(r'[a-z]', password):
            result['issues'].append('Manca lettera minuscola')
        else:
            result['score'] += 1

        if not re.search(r'[0-9]', password):
            result['issues'].append('Manca numero')
        else:
            result['score'] += 1

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            result['issues'].append('Manca carattere speciale')
        else:
            result['score'] += 1

        if result['issues']:
            result['valid'] = False

        return result