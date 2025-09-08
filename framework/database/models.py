# framework/database/models.py
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Float, JSON
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class BaseModel(Base):
    """Modello base con campi comuni"""
    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class LogEntry(BaseModel):
    """Tabella per log applicazione"""
    __tablename__ = "log_entries"

    level = Column(String(10), nullable=False)
    message = Column(Text, nullable=False)
    module = Column(String(100))
    function = Column(String(100))
    line_number = Column(Integer)
    extra_data = Column(JSON)


class Configuration(BaseModel):
    """Tabella per configurazioni dinamiche"""
    __tablename__ = "configurations"

    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    category = Column(String(50), default='general')


class PluginData(BaseModel):
    """Tabella per dati dei plugin"""
    __tablename__ = "plugin_data"

    plugin_name = Column(String(100), nullable=False, index=True)
    key = Column(String(100), nullable=False)
    value = Column(Text)
    data_type = Column(String(20), default='string')  # string, json, binary
    expires_at = Column(DateTime(timezone=True))


class SessionData(BaseModel):
    """Tabella per sessioni utente"""
    __tablename__ = "sessions"

    session_id = Column(String(255), unique=True, nullable=False, index=True)
    user_id = Column(String(100))
    data = Column(JSON)
    expires_at = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)


class ApiKey(BaseModel):
    """Tabella per chiavi API"""
    __tablename__ = "api_keys"

    key_name = Column(String(100), nullable=False)
    key_hash = Column(String(255), unique=True, nullable=False)
    permissions = Column(JSON)  # Lista di permessi
    expires_at = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)
    last_used = Column(DateTime(timezone=True))