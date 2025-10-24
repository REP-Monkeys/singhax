"""Adapters package."""

from .insurer.base import InsurerAdapter
from .insurer.mock import MockInsurerAdapter

__all__ = [
    "InsurerAdapter",
    "MockInsurerAdapter",
]
