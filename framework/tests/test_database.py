import pytest
import tempfile
from pathlib import Path
from framework import ModularFramework
from framework.database.models import Configuration, LogEntry


class TestDatabase:
    """Test suite per database"""

    def test_framework_initialization(self, framework_instance):
        """Test inizializzazione framework"""
        assert framework_instance is not None
        assert framework_instance.db is not None

    def test_database_connection(self, framework_instance):
        """Test connessione database"""
        with framework_instance.db.get_session() as session:
            result = framework_instance.db.execute_query("SELECT 1 as test")
            assert result is not None
            assert result[0]['test'] == 1

    def test_configuration_crud(self, framework_instance):
        """Test CRUD configurazioni"""
        # Create
        with framework_instance.db.get_session() as session:
            config = Configuration(
                key="test_key",
                value="test_value",
                description="Test configuration"
            )
            session.add(config)
            session.commit()
            config_id = config.id

        # Read
        with framework_instance.db.get_session() as session:
            retrieved = session.query(Configuration).filter(
                Configuration.key == "test_key"
            ).first()

            assert retrieved is not None
            assert retrieved.value == "test_value"
            assert retrieved.key == "test_key"

        # Update
        with framework_instance.db.get_session() as session:
            session.query(Configuration).filter(
                Configuration.key == "test_key"
            ).update({"value": "updated_value"})
            session.commit()

        # Verify update
        with framework_instance.db.get_session() as session:
            updated = session.query(Configuration).filter(
                Configuration.key == "test_key"
            ).first()
            assert updated.value == "updated_value"

        # Delete
        with framework_instance.db.get_session() as session:
            session.query(Configuration).filter(
                Configuration.key == "test_key"
            ).delete()
            session.commit()

        # Verify deletion
        with framework_instance.db.get_session() as session:
            deleted = session.query(Configuration).filter(
                Configuration.key == "test_key"
            ).first()
            assert deleted is None

    def test_transaction_rollback(self, framework_instance):
        """Test rollback transazioni"""
        with pytest.raises(Exception):
            with framework_instance.db.get_session() as session:
                # Inserisci record valido
                config1 = Configuration(
                    key="rollback_test1",
                    value="value1"
                )
                session.add(config1)
                session.flush()

                # Forza errore con chiave duplicata
                config2 = Configuration(
                    key="rollback_test1",  # Chiave duplicata
                    value="value2"
                )
                session.add(config2)
                # Il commit dovrebbe fallire

        # Verifica che nessun record sia stato inserito
        with framework_instance.db.get_session() as session:
            count = session.query(Configuration).filter(
                Configuration.key == "rollback_test1"
            ).count()
            assert count == 0