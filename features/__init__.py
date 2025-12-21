"""
Features Package
Contains feature-specific processing modules
UPDATED: Removed type coefficient module
"""

from .special_code import calculate_special_code_distribution

__all__ = [
    'calculate_special_code_distribution',
]