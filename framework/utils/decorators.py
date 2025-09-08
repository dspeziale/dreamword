# framework/utils/decorators.py
import functools
import time
from typing import Callable, Any, Dict, Optional
import asyncio
import logging
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0, exceptions: tuple = (Exception,)):
    """
    Decorator per retry automatico con backoff esponenziale

    Args:
        max_attempts: Numero massimo di tentativi
        delay: Delay iniziale in secondi
        backoff: Moltiplicatore per backoff esponenziale
        exceptions: Tuple di eccezioni da catturare
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay

            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(f"Tentativo {attempt + 1} fallito per {func.__name__}: {e}")
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(f"Tutti i {max_attempts} tentativi falliti per {func.__name__}")

            raise last_exception

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(f"Tentativo {attempt + 1} fallito per {func.__name__}: {e}")
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(f"Tutti i {max_attempts} tentativi falliti per {func.__name__}")

            raise last_exception

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator


def measure_time(log_result: bool = True, return_time: bool = False):
    """
    Decorator per misurare tempo di esecuzione

    Args:
        log_result: Se True, logga il risultato
        return_time: Se True, ritorna (result, execution_time)
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            result = await func(*args, **kwargs)
            end_time = time.time()
            execution_time = end_time - start_time

            if log_result:
                logger.info(f"{func.__name__} eseguita in {execution_time:.4f} secondi")

            return (result, execution_time) if return_time else result

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            execution_time = end_time - start_time

            if log_result:
                logger.info(f"{func.__name__} eseguita in {execution_time:.4f} secondi")

            return (result, execution_time) if return_time else result

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator


def cache_result(ttl_seconds: int = 300, max_size: int = 128, key_func: Optional[Callable] = None):
    """
    Decorator per cache semplice con TTL e limite dimensioni

    Args:
        ttl_seconds: Time to live in secondi
        max_size: Dimensione massima cache
        key_func: Funzione personalizzata per generare chiave cache
    """

    def decorator(func: Callable) -> Callable:
        cache = {}
        access_times = {}  # Per LRU

        def default_key_func(*args, **kwargs):
            return str(args) + str(sorted(kwargs.items()))

        key_generator = key_func or default_key_func

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Genera chiave cache
            try:
                key = key_generator(*args, **kwargs)
            except:
                # Se la generazione della chiave fallisce, esegui senza cache
                return func(*args, **kwargs)

            current_time = time.time()

            # Controlla cache
            if key in cache:
                result, timestamp = cache[key]
                if current_time - timestamp < ttl_seconds:
                    access_times[key] = current_time
                    return result
                else:
                    # Cache scaduta
                    del cache[key]
                    del access_times[key]

            # Esegui funzione
            result = func(*args, **kwargs)

            # Gestione dimensione cache
            if len(cache) >= max_size:
                # Rimuovi elemento meno recentemente usato
                oldest_key = min(access_times.keys(), key=lambda k: access_times[k])
                del cache[oldest_key]
                del access_times[oldest_key]

            # Memorizza risultato
            cache[key] = (result, current_time)
            access_times[key] = current_time

            return result

        # Aggiungi metodi utili al wrapper
        wrapper.cache_clear = lambda: cache.clear() or access_times.clear()
        wrapper.cache_info = lambda: {
            'hits': 0,  # Implementazione semplificata
            'misses': 0,
            'maxsize': max_size,
            'currsize': len(cache)
        }

        return wrapper

    return decorator


def rate_limit(calls_per_second: float = 1.0, per_user: bool = False):
    """
    Decorator per rate limiting

    Args:
        calls_per_second: Numero di chiamate per secondo
        per_user: Se True, applica rate limit per utente
    """
    min_interval = 1.0 / calls_per_second
    last_calls = {}

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Determina chiave per rate limiting
            if per_user:
                # Assume che il primo argomento sia user_id o simile
                key = str(args[0]) if args else "default"
            else:
                key = func.__name__

            current_time = time.time()

            if key in last_calls:
                time_since_last = current_time - last_calls[key]
                if time_since_last < min_interval:
                    sleep_time = min_interval - time_since_last
                    logger.warning(f"Rate limit per {func.__name__}, attesa {sleep_time:.2f}s")
                    time.sleep(sleep_time)

            last_calls[key] = time.time()
            return func(*args, **kwargs)

        return wrapper

    return decorator


def validate_types(**type_hints):
    """
    Decorator per validazione tipi runtime

    Args:
        **type_hints: Dizionario nome_parametro -> tipo_atteso
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import inspect

            # Ottieni signature della funzione
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            # Valida tipi
            for param_name, expected_type in type_hints.items():
                if param_name in bound_args.arguments:
                    value = bound_args.arguments[param_name]
                    if value is not None and not isinstance(value, expected_type):
                        raise TypeError(
                            f"Parametro '{param_name}' deve essere di tipo {expected_type.__name__}, "
                            f"ricevuto {type(value).__name__}"
                        )

            return func(*args, **kwargs)

        return wrapper

    return decorator


def log_calls(log_args: bool = True, log_result: bool = False, log_level: str = "DEBUG"):
    """
    Decorator per loggare chiamate a funzioni

    Args:
        log_args: Se True, logga gli argomenti
        log_result: Se True, logga il risultato
        log_level: Livello di log
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Log chiamata
            if log_args:
                args_str = f"args={args}, kwargs={kwargs}"
                getattr(logger, log_level.lower())(f"Chiamata {func.__name__}({args_str})")
            else:
                getattr(logger, log_level.lower())(f"Chiamata {func.__name__}")

            # Esegui funzione
            result = func(*args, **kwargs)

            # Log risultato
            if log_result:
                result_str = str(result)[:200]  # Limita lunghezza
                getattr(logger, log_level.lower())(f"Risultato {func.__name__}: {result_str}")

            return result

        return wrapper

    return decorator


def async_timeout(seconds: float):
    """
    Decorator per timeout su funzioni async

    Args:
        seconds: Timeout in secondi
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=seconds)
            except asyncio.TimeoutError:
                logger.error(f"Timeout dopo {seconds}s per {func.__name__}")
                raise

        return wrapper

    return decorator


def singleton(cls):
    """
    Decorator per implementare pattern Singleton
    """
    instances = {}

    @functools.wraps(cls)
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance


def deprecated(reason: str = "Questa funzione è deprecata"):
    """
    Decorator per marcare funzioni come deprecate

    Args:
        reason: Motivo della deprecazione
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import warnings
            warnings.warn(
                f"{func.__name__} è deprecata. {reason}",
                DeprecationWarning,
                stacklevel=2
            )
            return func(*args, **kwargs)

        return wrapper

    return decorator


# Esempio di uso combinato
"""
@retry(max_attempts=3, delay=1.0)
@measure_time(log_result=True)
@cache_result(ttl_seconds=60)
@rate_limit(calls_per_second=2.0)
def complex_function(param1: str, param2: int = 42):
    # Funzione che può fallire e beneficia di cache
    time.sleep(0.5)  # Simula operazione lenta
    return f"Risultato: {param1} - {param2}"
"""