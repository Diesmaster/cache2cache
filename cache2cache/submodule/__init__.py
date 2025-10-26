"""
Submodule for LRU Cache implementation.

This module provides a two-layer LRU Cache implementation and wrapper functions
for easy integration with applications.
"""

# Import from lru_cache.py
from .lru_cache import LRUCache, lru_cache, create_lru_cache

# Import from wrappers.py
from .wrappers import get, put, invalidate, get_capacity, set_capacity, get_stats, clear_all, clear_collection, batch_invalidate

# Define what should be available when importing from this module
__all__ = [
    # Core LRU Cache implementation
    "LRUCache", 
    "lru_cache",
    "create_lru_cache",
    
    # Wrapper functions
    "get",
    "put",
    "invalidate",
    "get_capacity",
    "set_capacity",
    "get_stats",
    "clear_all",
    "clear_collection",
    "batch_invalidate"
]
