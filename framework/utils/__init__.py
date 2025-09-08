# framework/utils/__init__.py

"""
Utilities del ModularFramework

Decoratori, validatori, helper functions
"""

from .decorators import (
    retry, measure_time, cache_result, rate_limit,
    validate_types, log_calls, async_timeout,
    singleton, deprecated
)

try:
    from .validators import FrameworkValidators, ValidationError
except ImportError:
    FrameworkValidators = None
    ValidationError = Exception

from .helpers import FrameworkHelpers

__all__ = [
    # Decorators
    'retry', 'measure_time', 'cache_result', 'rate_limit',
    'validate_types', 'log_calls', 'async_timeout',
    'singleton', 'deprecated',

    # Validators
    'FrameworkValidators', 'ValidationError',

    # Helpers
    'FrameworkHelpers'
]