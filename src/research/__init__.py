"""
Research Module

DHIN (Dynamic Hierarchical Information Network) research and advanced modeling.

This module contains:
- graph_builder: Transforms time-series data into graph structures
- config: Shared configuration for research components
"""

from .graph_builder import DHINBuilder
from . import config

__all__ = ['DHINBuilder', 'config']

