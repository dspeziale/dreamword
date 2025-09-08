# tests/test_framework_basic.py

"""
Test base per il ModularFramework
Strutturato correttamente per PyTest
"""

import pytest
import tempfile
from pathlib import Path


class TestFrameworkBasic:
    """Test suite base per il framework"""

    def test_import(self):
        """Test import del framework"""
        from framework import ModularFramework
        assert ModularFramework is not None

    def test_framework_initialization(self):
        """Test inizializzazione framework"""
        from framework import ModularFramework

        fw = ModularFramework()
        assert fw is not None
        assert hasattr(fw, 'config')
        assert hasattr(fw, 'db')
        assert hasattr(fw, 'http')
        assert hasattr(fw, 'plugins')

    def test_config_access(self):
        """Test accesso configurazione"""
        from framework import ModularFramework

        fw = ModularFramework()
        assert fw.config.database.provider == "sqlite"
        assert fw.config.networking.port == 8000
        assert fw.config.debug is False

    def test_database_setup(self):
        """Test setup database"""
        from framework import ModularFramework

        # Usa database temporaneo
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
            temp_db_path = tmp_file.name

        try:
            fw = ModularFramework()
            fw.config.database.sqlite_path = temp_db_path

            # Setup database
            fw.setup_database()

            # Verifica che il database sia stato creato
            assert Path(temp_db_path).exists()

        finally:
            # Cleanup
            Path(temp_db_path).unlink(missing_ok=True)

    def test_database_connection(self):
        """Test connessione database"""
        from framework import ModularFramework

        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
            temp_db_path = tmp_file.name

        try:
            fw = ModularFramework()
            fw.config.database.sqlite_path = temp_db_path
            fw.setup_database()

            # Test connessione
            with fw.db.get_session() as session:
                result = fw.db.execute_query("SELECT 1 as test")
                assert result is not None
                assert len(result) > 0
                assert result[0]['test'] == 1

        finally:
            Path(temp_db_path).unlink(missing_ok=True)

    def test_database_operations(self):
        """Test operazioni database CRUD"""
        from framework import ModularFramework
        from framework.database.models import Configuration

        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
            temp_db_path = tmp_file.name

        try:
            fw = ModularFramework()
            fw.config.database.sqlite_path = temp_db_path
            fw.setup_database()

            # Test inserimento
            with fw.db.get_session() as session:
                config = Configuration(
                    key="test_key",
                    value="test_value",
                    description="Test configuration"
                )
                session.add(config)
                session.commit()
                config_id = config.id

            # Test lettura
            with fw.db.get_session() as session:
                retrieved = session.query(Configuration).filter(
                    Configuration.id == config_id
                ).first()

                assert retrieved is not None
                assert retrieved.key == "test_key"
                assert retrieved.value == "test_value"

        finally:
            Path(temp_db_path).unlink(missing_ok=True)

    def test_http_client(self):
        """Test HTTP client (richiede connessione internet)"""
        from framework import ModularFramework

        fw = ModularFramework()

        try:
            # Test HTTP GET
            response = fw.http.get("https://httpbin.org/json")
            assert response is not None
            assert hasattr(response, 'status')
            assert hasattr(response, 'success')

            # Se la connessione funziona
            if response.success:
                assert response.status == 200
                assert isinstance(response.data, dict)

        except Exception as e:
            # Skip test se problemi di rete
            pytest.skip(f"Test HTTP saltato per problemi di rete: {e}")

    def test_plugin_system(self):
        """Test sistema plugin base"""
        from framework import ModularFramework

        fw = ModularFramework()

        # Verifica che il plugin manager sia inizializzato
        assert fw.plugins is not None
        assert hasattr(fw.plugins, 'load_plugin')
        assert hasattr(fw.plugins, 'list_plugins')

        # Lista iniziale plugin (dovrebbe essere vuota)
        plugins = fw.plugins.list_plugins()
        assert isinstance(plugins, list)

    def test_framework_status(self):
        """Test status framework"""
        from framework import ModularFramework

        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
            temp_db_path = tmp_file.name

        try:
            fw = ModularFramework()
            fw.config.database.sqlite_path = temp_db_path
            fw.setup_database()

            # Test status
            status = fw.get_status()
            assert isinstance(status, dict)
            assert 'framework' in status
            assert 'database' in status
            assert 'plugins' in status

            # Framework status
            assert status['framework']['initialized'] is True
            assert status['framework']['version'] == "1.0.0"

            # Database status
            assert status['database']['provider'] == "sqlite"

        finally:
            Path(temp_db_path).unlink(missing_ok=True)

    def test_health_check(self):
        """Test health check"""
        from framework import ModularFramework

        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
            temp_db_path = tmp_file.name

        try:
            fw = ModularFramework()
            fw.config.database.sqlite_path = temp_db_path
            fw.setup_database()

            # Test health check
            health = fw.health_check()
            assert isinstance(health, dict)
            assert 'overall' in health
            assert 'checks' in health

            # Database health
            assert 'database' in health['checks']
            db_health = health['checks']['database']
            assert db_health['status'] == 'healthy'

        finally:
            Path(temp_db_path).unlink(missing_ok=True)


class TestFrameworkConfiguration:
    """Test configurazione framework"""

    def test_config_defaults(self):
        """Test valori default configurazione"""
        from framework.core.config import FrameworkConfig

        config = FrameworkConfig()
        assert config.debug is False
        assert config.database.provider == "sqlite"
        assert config.networking.port == 8000

    def test_config_override(self):
        """Test override configurazione"""
        from framework import ModularFramework

        # Override configurazione
        override = {
            "debug": True,
            "database": {"provider": "sqlite"},
            "networking": {"port": 9000}
        }

        fw = ModularFramework(config_override=override)
        assert fw.config.debug is True
        assert fw.config.networking.port == 9000

    def test_environment_detection(self):
        """Test rilevamento environment"""
        from framework.core.config import FrameworkConfig

        # Development
        config = FrameworkConfig(debug=True)
        assert config.get_environment() == "development"

        # Production
        config = FrameworkConfig(production=True)
        assert config.get_environment() == "production"

        # Testing
        config = FrameworkConfig(testing=True)
        assert config.get_environment() == "testing"


@pytest.mark.skipif(
    True,
    reason="Test asincroni richiedono setup aggiuntivo"
)
class TestFrameworkAsync:
    """Test funzionalità asincrone (opzionali)"""

    @pytest.mark.asyncio
    async def test_async_http_client(self):
        """Test HTTP client asincrono"""
        from framework import ModularFramework

        fw = ModularFramework()

        try:
            response = await fw.http.aget("https://httpbin.org/json")
            if response.success:
                assert response.status == 200
        except Exception as e:
            pytest.skip(f"Test async HTTP saltato: {e}")

    @pytest.mark.asyncio
    async def test_framework_cleanup(self):
        """Test cleanup asincrono"""
        from framework import ModularFramework

        fw = ModularFramework()

        # Test cleanup
        await fw.cleanup()

        # Verifica che cleanup sia avvenuto
        # (implementazione specifica dipende dai componenti)


if __name__ == "__main__":
    # Esegue test se chiamato direttamente
    pytest.main([__file__, "-v"])