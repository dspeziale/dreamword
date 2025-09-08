# ==============================================================================
# tests/conftest.py - Configurazione test
# ==============================================================================

import pytest
import tempfile
import asyncio
from pathlib import Path
from framework import ModularFramework


@pytest.fixture
def temp_db():
    """Fixture per database temporaneo"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        yield f.name

    # Cleanup
    Path(f.name).unlink(missing_ok=True)


@pytest.fixture
def framework_instance(temp_db):
    """Fixture per istanza framework con DB temporaneo"""
    fw = ModularFramework()
    fw.config.database.sqlite_path = temp_db
    fw.setup_database()
    return fw


@pytest.fixture
def event_loop():
    """Fixture per event loop asyncio"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
