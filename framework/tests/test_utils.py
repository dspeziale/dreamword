import pytest
from framework.utils import (
    FrameworkValidators, FrameworkHelpers, ValidationError,
    retry, measure_time, cache_result
)
import time


class TestValidators:
    """Test validatori"""

    def test_email_validation(self):
        """Test validazione email"""
        assert FrameworkValidators.validate_email_address("test@example.com") is True
        assert FrameworkValidators.validate_email_address("invalid-email") is False

    def test_url_validation(self):
        """Test validazione URL"""
        assert FrameworkValidators.validate_url("https://example.com") is True
        assert FrameworkValidators.validate_url("not-a-url") is False

    def test_port_validation(self):
        """Test validazione porta"""
        assert FrameworkValidators.validate_port(80) is True
        assert FrameworkValidators.validate_port("8080") is True
        assert FrameworkValidators.validate_port(70000) is False
        assert FrameworkValidators.validate_port("invalid") is False

    def test_password_strength(self):
        """Test forza password"""
        weak = FrameworkValidators.validate_password_strength("123")
        assert weak['valid'] is False
        assert len(weak['issues']) > 0

        strong = FrameworkValidators.validate_password_strength("StrongP@ss123")
        assert strong['valid'] is True
        assert strong['score'] == 5


class TestHelpers:
    """Test helper functions"""

    def test_random_string_generation(self):
        """Test generazione stringa casuale"""
        str1 = FrameworkHelpers.generate_random_string(10)
        str2 = FrameworkHelpers.generate_random_string(10)

        assert len(str1) == 10
        assert len(str2) == 10
        assert str1 != str2  # Dovrebbero essere diverse

    def test_api_key_generation(self):
        """Test generazione API key"""
        key = FrameworkHelpers.generate_api_key()
        assert key.startswith("fw_")
        assert len(key) == 43  # fw_ + 40 caratteri

    def test_password_hashing(self):
        """Test hash password"""
        password = "test_password"
        hash1, salt1 = FrameworkHelpers.hash_password(password)
        hash2, salt2 = FrameworkHelpers.hash_password(password)

        # Hash diversi con salt diversi
        assert hash1 != hash2
        assert salt1 != salt2

        # Verifica funziona
        assert FrameworkHelpers.verify_password(password, hash1, salt1) is True
        assert FrameworkHelpers.verify_password("wrong", hash1, salt1) is False

    def test_dict_operations(self):
        """Test operazioni dizionari"""
        dict1 = {"a": 1, "b": {"c": 2}}
        dict2 = {"b": {"d": 3}, "e": 4}

        merged = FrameworkHelpers.deep_merge_dict(dict1, dict2)
        expected = {"a": 1, "b": {"c": 2, "d": 3}, "e": 4}
        assert merged == expected

        # Test flatten
        flattened = FrameworkHelpers.flatten_dict(merged)
        assert "b.c" in flattened
        assert "b.d" in flattened


class TestDecorators:
    """Test decoratori"""

    def test_cache_decorator(self):
        """Test decorator cache"""
        call_count = 0

        @cache_result(ttl_seconds=1)
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        # Prima chiamata
        result1 = expensive_function(5)
        assert result1 == 10
        assert call_count == 1

        # Seconda chiamata (dovrebbe usare cache)
        result2 = expensive_function(5)
        assert result2 == 10
        assert call_count == 1  # Non dovrebbe essere incrementato

        # Attendi scadenza cache
        time.sleep(1.1)
        result3 = expensive_function(5)
        assert result3 == 10
        assert call_count == 2  # Dovrebbe essere incrementato

    def test_retry_decorator(self):
        """Test decorator retry"""
        attempt_count = 0

        @retry(max_attempts=3, delay=0.1)
        def flaky_function():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise Exception("Flaky error")
            return "success"

        result = flaky_function()
        assert result == "success"
        assert attempt_count == 3

    def test_measure_time_decorator(self):
        """Test decorator timing"""

        @measure_time(return_time=True)
        def slow_function():
            time.sleep(0.1)
            return "done"

        result, execution_time = slow_function()
        assert result == "done"
        assert execution_time >= 0.1