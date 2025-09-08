# framework/core/base.py

"""
Classi base per il framework modulare

Definisce interfacce e classi base comuni utilizzate
da tutti i componenti del framework.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from datetime import datetime
import uuid


class BaseComponent(ABC):
    """
    Classe base per tutti i componenti del framework

    Fornisce funzionalità comuni come:
    - Identificazione univoca
    - Configurazione
    - Logging
    - Lifecycle management
    """

    def __init__(self, name: str = None, config: Dict[str, Any] = None):
        """
        Inizializza componente base

        Args:
            name: Nome del componente
            config: Configurazione opzionale
        """
        self.id = str(uuid.uuid4())
        self.name = name or self.__class__.__name__
        self.config = config or {}
        self.created_at = datetime.now()
        self.is_initialized = False
        self.is_active = False

    @abstractmethod
    def initialize(self) -> bool:
        """
        Inizializza il componente

        Returns:
            True se inizializzazione riuscita
        """
        pass

    @abstractmethod
    def cleanup(self):
        """Cleanup risorse del componente"""
        pass

    def get_info(self) -> Dict[str, Any]:
        """
        Ottieni informazioni sul componente

        Returns:
            Dizionario con informazioni del componente
        """
        return {
            "id": self.id,
            "name": self.name,
            "class": self.__class__.__name__,
            "created_at": self.created_at.isoformat(),
            "is_initialized": self.is_initialized,
            "is_active": self.is_active,
            "config": self.config
        }

    def __repr__(self):
        return f"{self.__class__.__name__}(name='{self.name}', id='{self.id[:8]}...', active={self.is_active})"


class Singleton:
    """
    Metaclass per implementare pattern Singleton

    Usage:
        class MyClass(metaclass=Singleton):
            pass
    """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class ConfigurableComponent(BaseComponent):
    """
    Componente con supporto configurazione avanzata

    Estende BaseComponent con:
    - Validazione configurazione
    - Configurazione dinamica
    - Schema configurazione
    """

    def __init__(self, name: str = None, config: Dict[str, Any] = None):
        super().__init__(name, config)
        self._config_schema = self.get_config_schema()
        self._validate_config()

    def get_config_schema(self) -> Dict[str, Any]:
        """
        Schema di configurazione del componente

        Returns:
            Dizionario con schema di validazione
        """
        return {
            "type": "object",
            "properties": {},
            "required": []
        }

    def _validate_config(self):
        """Valida configurazione contro schema"""
        # Implementazione base - può essere estesa con jsonschema
        schema = self._config_schema
        required = schema.get("required", [])

        for field in required:
            if field not in self.config:
                raise ValueError(f"Campo obbligatorio mancante: {field}")

    def update_config(self, new_config: Dict[str, Any]):
        """
        Aggiorna configurazione del componente

        Args:
            new_config: Nuova configurazione
        """
        old_config = self.config.copy()
        self.config.update(new_config)

        try:
            self._validate_config()
            self.on_config_updated(old_config, self.config)
        except Exception as e:
            # Rollback configurazione
            self.config = old_config
            raise ValueError(f"Configurazione non valida: {e}")

    def on_config_updated(self, old_config: Dict[str, Any], new_config: Dict[str, Any]):
        """
        Callback chiamato quando configurazione è aggiornata

        Args:
            old_config: Configurazione precedente
            new_config: Nuova configurazione
        """
        pass


class EventEmitter(BaseComponent):
    """
    Componente con supporto eventi

    Fornisce sistema di eventi pub/sub interno
    """

    def __init__(self, name: str = None, config: Dict[str, Any] = None):
        super().__init__(name, config)
        self._event_handlers: Dict[str, List[callable]] = {}

    def on(self, event_name: str, handler: callable):
        """
        Registra handler per evento

        Args:
            event_name: Nome evento
            handler: Funzione handler
        """
        if event_name not in self._event_handlers:
            self._event_handlers[event_name] = []

        self._event_handlers[event_name].append(handler)

    def off(self, event_name: str, handler: callable = None):
        """
        Rimuove handler per evento

        Args:
            event_name: Nome evento
            handler: Handler specifico (None = tutti)
        """
        if event_name not in self._event_handlers:
            return

        if handler is None:
            # Rimuovi tutti gli handler
            self._event_handlers[event_name] = []
        else:
            # Rimuovi handler specifico
            if handler in self._event_handlers[event_name]:
                self._event_handlers[event_name].remove(handler)

    def emit(self, event_name: str, *args, **kwargs):
        """
        Emette evento

        Args:
            event_name: Nome evento
            *args: Argomenti posizionali
            **kwargs: Argomenti keyword
        """
        if event_name not in self._event_handlers:
            return

        for handler in self._event_handlers[event_name]:
            try:
                handler(*args, **kwargs)
            except Exception as e:
                # Log errore ma continua con altri handler
                print(f"Errore in event handler {handler}: {e}")

    def list_events(self) -> List[str]:
        """
        Lista eventi registrati

        Returns:
            Lista nomi eventi
        """
        return list(self._event_handlers.keys())

    def get_event_handlers(self, event_name: str) -> List[callable]:
        """
        Ottieni handler per evento

        Args:
            event_name: Nome evento

        Returns:
            Lista handler
        """
        return self._event_handlers.get(event_name, [])


class ServiceComponent(ConfigurableComponent, EventEmitter):
    """
    Componente servizio completo

    Combina configurazione e eventi per servizi del framework
    """

    def __init__(self, name: str = None, config: Dict[str, Any] = None):
        ConfigurableComponent.__init__(self, name, config)
        EventEmitter.__init__(self, name, config)
        self._status = "stopped"
        self._error_count = 0
        self._last_error = None

    @property
    def status(self) -> str:
        """Stato corrente del servizio"""
        return self._status

    @property
    def is_running(self) -> bool:
        """True se servizio è in esecuzione"""
        return self._status == "running"

    def start(self) -> bool:
        """
        Avvia servizio

        Returns:
            True se avviato con successo
        """
        if self._status == "running":
            return True

        try:
            self._status = "starting"
            self.emit("service.starting")

            # Inizializza se necessario
            if not self.is_initialized:
                if not self.initialize():
                    self._status = "error"
                    return False

            # Template method per logica specifica
            if self._do_start():
                self._status = "running"
                self.is_active = True
                self.emit("service.started")
                return True
            else:
                self._status = "error"
                self.emit("service.error", "Start failed")
                return False

        except Exception as e:
            self._status = "error"
            self._last_error = str(e)
            self._error_count += 1
            self.emit("service.error", e)
            return False

    def stop(self) -> bool:
        """
        Ferma servizio

        Returns:
            True se fermato con successo
        """
        if self._status == "stopped":
            return True

        try:
            self._status = "stopping"
            self.emit("service.stopping")

            # Template method per logica specifica
            if self._do_stop():
                self._status = "stopped"
                self.is_active = False
                self.emit("service.stopped")
                return True
            else:
                self._status = "error"
                self.emit("service.error", "Stop failed")
                return False

        except Exception as e:
            self._status = "error"
            self._last_error = str(e)
            self._error_count += 1
            self.emit("service.error", e)
            return False

    def restart(self) -> bool:
        """
        Riavvia servizio

        Returns:
            True se riavviato con successo
        """
        if not self.stop():
            return False
        return self.start()

    def _do_start(self) -> bool:
        """
        Template method per logica di start specifica

        Returns:
            True se start riuscito
        """
        return True

    def _do_stop(self) -> bool:
        """
        Template method per logica di stop specifica

        Returns:
            True se stop riuscito
        """
        return True

    def get_info(self) -> Dict[str, Any]:
        """Informazioni estese del servizio"""
        info = super().get_info()
        info.update({
            "status": self._status,
            "is_running": self.is_running,
            "error_count": self._error_count,
            "last_error": self._last_error
        })
        return info

    def cleanup(self):
        """Cleanup del servizio"""
        if self.is_running:
            self.stop()

        # Cleanup eventi
        self._event_handlers.clear()


class FrameworkRegistry:
    """
    Registry globale per componenti del framework

    Permette registrazione e discovery di componenti
    """

    def __init__(self):
        self._components: Dict[str, BaseComponent] = {}
        self._types: Dict[str, List[str]] = {}

    def register(self, component: BaseComponent, component_type: str = None):
        """
        Registra componente

        Args:
            component: Istanza del componente
            component_type: Tipo del componente (opzionale)
        """
        self._components[component.name] = component

        if component_type:
            if component_type not in self._types:
                self._types[component_type] = []
            self._types[component_type].append(component.name)

    def unregister(self, name: str):
        """
        Rimuove componente dal registry

        Args:
            name: Nome del componente
        """
        if name in self._components:
            del self._components[name]

        # Rimuovi dai tipi
        for type_name, components in self._types.items():
            if name in components:
                components.remove(name)

    def get(self, name: str) -> Optional[BaseComponent]:
        """
        Ottieni componente per nome

        Args:
            name: Nome del componente

        Returns:
            Istanza del componente o None
        """
        return self._components.get(name)

    def get_by_type(self, component_type: str) -> List[BaseComponent]:
        """
        Ottieni componenti per tipo

        Args:
            component_type: Tipo componente

        Returns:
            Lista componenti del tipo
        """
        names = self._types.get(component_type, [])
        return [self._components[name] for name in names if name in self._components]

    def list_all(self) -> List[str]:
        """Lista nomi di tutti i componenti"""
        return list(self._components.keys())

    def list_types(self) -> List[str]:
        """Lista tutti i tipi registrati"""
        return list(self._types.keys())


# Registry globale singleton
_global_registry = FrameworkRegistry()


def get_registry() -> FrameworkRegistry:
    """Ottieni registry globale"""
    return _global_registry


# Utility classes
class Result:
    """
    Classe per risultati di operazioni

    Pattern Result per gestione errori funzionale
    """

    def __init__(self, success: bool, data: Any = None, error: str = None):
        self.success = success
        self.data = data
        self.error = error

    @classmethod
    def ok(cls, data: Any = None):
        """Crea risultato di successo"""
        return cls(True, data=data)

    @classmethod
    def fail(cls, error: str, data: Any = None):
        """Crea risultato di errore"""
        return cls(False, data=data, error=error)

    def is_ok(self) -> bool:
        """True se operazione riuscita"""
        return self.success

    def is_error(self) -> bool:
        """True se operazione fallita"""
        return not self.success

    def unwrap(self) -> Any:
        """
        Estrae dati o solleva eccezione

        Returns:
            Dati se successo

        Raises:
            Exception se errore
        """
        if self.success:
            return self.data
        else:
            raise Exception(self.error or "Operation failed")

    def unwrap_or(self, default: Any) -> Any:
        """
        Estrae dati o restituisce default

        Args:
            default: Valore di default

        Returns:
            Dati se successo, default se errore
        """
        return self.data if self.success else default

    def __repr__(self):
        if self.success:
            return f"Result.ok({self.data})"
        else:
            return f"Result.fail('{self.error}')"