"""
Utils Package
Contains common utility functions used across the project
UPDATED: Now exports logging functions
"""

from .time_utils import hours_to_hhmm, convert_planned_mhrs, time_to_hours
from .validation import validate_required_columns, check_column_exists
from .formatters import clean_string, format_percentage
from .logger import (
    WorkpackLogger,
    get_logger,
    info,
    debug,
    warning,
    error,
    critical
)

__all__ = [
    # Time utilities
    'hours_to_hhmm',
    'convert_planned_mhrs',
    'time_to_hours',

    # Validation utilities
    'validate_required_columns',
    'check_column_exists',

    # Formatter utilities
    'clean_string',
    'format_percentage',

    # Logging utilities
    'WorkpackLogger',
    'get_logger',
    'info',
    'debug',
    'warning',
    'error',
    'critical',
]