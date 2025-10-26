"""
Two-layer LRU Cache singleton implementation.

This module provides a Least Recently Used (LRU) cache implementation
as a singleton class that supports a two-layer key structure:
collection_id -> document_id -> value.
"""
from collections import OrderedDict
from threading import RLock
from typing import Any, Dict, List, Optional, TypeVar, Generic, Union, Tuple, Set

T = TypeVar('T')
C = TypeVar('C')  # Collection ID type
D = TypeVar('D')  # Document ID type
V = TypeVar('V')  # Value type

class LRUCache(Generic[C, D, V]):
    """
    A thread-safe two-layer LRU cache implemented as a singleton.
    
    This cache organizes data in a collection -> document -> value structure:
    - The first layer is the collection ID
    - The second layer is the document ID
    - Together, they map to a value
    
    No matter where or how this class is instantiated, it will always return
    a reference to the same instance, maintaining a single shared cache across
    your application.
    
    Attributes:
        capacity (int): Maximum number of items to store in the cache.
        _cache (Dict[C, Dict[D, V]]): Internal two-layer cache structure.
        _access_order (OrderedDict): Tracks the LRU order of (collection, document) pairs.
    """
    
    # Class variable to store the singleton instance
    _instance: Optional['LRUCache'] = None
    
    # Class lock for thread safety during instantiation
    _lock = RLock()
    
    def __new__(cls, capacity: int = 1000) -> 'LRUCache':
        """
        Create or return the singleton instance of LRUCache.
        
        Args:
            capacity: Maximum number of items to store in the cache.
                     Only used when creating the instance for the first time.
        
        Returns:
            The singleton LRUCache instance.
        """
        with cls._lock:
            if cls._instance is None:
                # Create a new instance only if one doesn't exist
                cls._instance = super(LRUCache, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self, capacity: int = 1000) -> None:
        """
        Initialize the LRUCache with the specified capacity.
        
        This will only run once for the singleton instance.
        
        Args:
            capacity: Maximum number of items to store in the cache.
        """
        # Skip initialization if already initialized
        with self._lock:
            if getattr(self, '_initialized', False):
                return
            
            self.capacity = capacity
            self._cache: Dict[C, Dict[D, V]] = {}
            self._access_order: OrderedDict[Tuple[C, D], None] = OrderedDict()
            self._hit_count = 0
            self._miss_count = 0
            self._initialized = True
    
    def get(self, collection_id: C, document_id: D) -> Optional[V]:
        """
        Retrieve an item from the cache.
        
        If the item exists, it will be moved to the most recently used position.
        
        Args:
            collection_id: The collection identifier.
            document_id: The document identifier within the collection.
        
        Returns:
            The cached value, or None if the key pair is not in the cache.
        """
        with self._lock:
            if collection_id in self._cache and document_id in self._cache[collection_id]:
                # Update access order to mark as most recently used
                key_pair = (collection_id, document_id)
                self._access_order.pop(key_pair, None)
                self._access_order[key_pair] = None
                
                self._hit_count += 1
                return self._cache[collection_id][document_id]
            
            self._miss_count += 1
            return None
    
    def put(self, collection_id: C, document_id: D, value: V) -> None:
        """
        Add or update an item in the cache.
        
        If the item already exists, it will be updated and moved to the
        most recently used position. If the cache is at capacity, the
        least recently used item will be removed.
        
        Args:
            collection_id: The collection identifier.
            document_id: The document identifier within the collection.
            value: The value to store.
        """
        with self._lock:
            # Create collection dictionary if it doesn't exist
            if collection_id not in self._cache:
                self._cache[collection_id] = {}
                
            key_pair = (collection_id, document_id)
            
            # Check if we're updating an existing entry
            updating_existing = (collection_id in self._cache and 
                                document_id in self._cache[collection_id])
            
            # If not updating and we're at capacity, remove the LRU item
            if not updating_existing and len(self._access_order) >= self.capacity:
                lru_pair = next(iter(self._access_order))
                lru_collection, lru_document = lru_pair
                
                # Remove from access order and cache
                self._access_order.pop(lru_pair)
                self._cache[lru_collection].pop(lru_document)
                
                # Clean up empty collections
                if not self._cache[lru_collection]:
                    self._cache.pop(lru_collection)
            
            # Update access order (remove if exists, then add to end)
            self._access_order.pop(key_pair, None)
            self._access_order[key_pair] = None
            
            # Store the value
            self._cache[collection_id][document_id] = value
    
    def remove(self, collection_id: C, document_id: D) -> bool:
        """
        Remove an item from the cache if it exists.
        
        Args:
            collection_id: The collection identifier.
            document_id: The document identifier within the collection.
            
        Returns:
            True if the item was in the cache, False otherwise.
        """
        with self._lock:
            if (collection_id in self._cache and 
                document_id in self._cache[collection_id]):
                
                # Remove from cache
                self._cache[collection_id].pop(document_id)
                
                # Clean up empty collections
                if not self._cache[collection_id]:
                    self._cache.pop(collection_id)
                
                # Remove from access order
                self._access_order.pop((collection_id, document_id), None)
                
                return True
            return False
    
    def remove_collection(self, collection_id: C) -> int:
        """
        Remove an entire collection from the cache.
        
        Args:
            collection_id: The collection identifier to remove.
            
        Returns:
            The number of documents removed from the collection.
        """
        with self._lock:
            if collection_id in self._cache:
                # Get all document IDs in this collection
                document_ids = list(self._cache[collection_id].keys())
                count = len(document_ids)
                
                # Remove each (collection_id, document_id) from access order
                for doc_id in document_ids:
                    self._access_order.pop((collection_id, doc_id), None)
                
                # Remove the entire collection
                self._cache.pop(collection_id)
                
                return count
            return 0
    
    def clear(self) -> None:
        """
        Clear all items from the cache.
        """
        with self._lock:
            self._cache.clear()
            self._access_order.clear()
    
    def contains(self, collection_id: C, document_id: D) -> bool:
        """
        Check if a specific item exists in the cache.
        
        Args:
            collection_id: The collection identifier.
            document_id: The document identifier within the collection.
            
        Returns:
            True if the item exists in the cache, False otherwise.
        """
        with self._lock:
            return (collection_id in self._cache and 
                   document_id in self._cache[collection_id])
    
    def collection_exists(self, collection_id: C) -> bool:
        """
        Check if a collection exists in the cache.
        
        Args:
            collection_id: The collection identifier.
            
        Returns:
            True if the collection exists in the cache, False otherwise.
        """
        with self._lock:
            return collection_id in self._cache
    
    def get_document_ids(self, collection_id: C) -> List[D]:
        """
        Get all document IDs in a specific collection.
        
        Args:
            collection_id: The collection identifier.
            
        Returns:
            A list of document IDs in the collection, or an empty list if the
            collection doesn't exist.
        """
        with self._lock:
            if collection_id in self._cache:
                return list(self._cache[collection_id].keys())
            return []
    
    def get_collection_ids(self) -> List[C]:
        """
        Get all collection IDs in the cache.
        
        Returns:
            A list of all collection IDs in the cache.
        """
        with self._lock:
            return list(self._cache.keys())
    
    def get_collection(self, collection_id: C) -> Dict[D, V]:
        """
        Get all documents in a specific collection.
        
        Args:
            collection_id: The collection identifier.
            
        Returns:
            A dictionary of document_id -> value for the collection,
            or an empty dictionary if the collection doesn't exist.
        """
        with self._lock:
            if collection_id in self._cache:
                # Return a copy to prevent external modification
                return dict(self._cache[collection_id])
            return {}
    
    def get_all(self) -> Dict[C, Dict[D, V]]:
        """
        Get a copy of all items in the cache.
        
        Returns:
            A nested dictionary containing all items in the cache.
        """
        with self._lock:
            result = {}
            for collection_id, documents in self._cache.items():
                result[collection_id] = dict(documents)
            return result
    
    def resize(self, new_capacity: int) -> None:
        """
        Resize the cache capacity.
        
        If the new capacity is smaller than the current number of items,
        the least recently used items will be removed.
        
        Args:
            new_capacity: The new maximum capacity for the cache.
        
        Raises:
            ValueError: If the new capacity is less than 1.
        """
        if new_capacity < 1:
            raise ValueError("Cache capacity must be at least 1")
        
        with self._lock:
            old_capacity = self.capacity
            self.capacity = new_capacity
            
            # If reducing capacity, remove least recently used items
            if new_capacity < old_capacity:
                while len(self._access_order) > new_capacity:
                    # Get and remove the least recently used item
                    lru_pair = next(iter(self._access_order))
                    lru_collection, lru_document = lru_pair
                    
                    # Remove from access order and cache
                    self._access_order.pop(lru_pair)
                    self._cache[lru_collection].pop(lru_document)
                    
                    # Clean up empty collections
                    if not self._cache[lru_collection]:
                        self._cache.pop(lru_collection)
    
    def get_stats(self) -> Dict[str, Union[int, float]]:
        """
        Get cache statistics.
        
        Returns:
            A dictionary containing hit count, miss count, hit ratio,
            current size, and capacity.
        """
        with self._lock:
            total = self._hit_count + self._miss_count
            hit_ratio = self._hit_count / total if total > 0 else 0.0
            
            # Count collections and total items
            collections_count = len(self._cache)
            total_items = len(self._access_order)
            
            return {
                "hits": self._hit_count,
                "misses": self._miss_count,
                "hit_ratio": hit_ratio,
                "size": total_items,
                "collections": collections_count,
                "capacity": self.capacity
            }
    
    def touch(self, collection_id: C, document_id: D) -> bool:
        """
        Update the access time of an item without retrieving it.
        
        This is useful when you want to prevent an item from being evicted
        but don't need its value.
        
        Args:
            collection_id: The collection identifier.
            document_id: The document identifier within the collection.
            
        Returns:
            True if the item exists and was touched, False otherwise.
        """
        with self._lock:
            if self.contains(collection_id, document_id):
                # Move to most recently used position
                key_pair = (collection_id, document_id)
                self._access_order.pop(key_pair)
                self._access_order[key_pair] = None
                return True
            return False
    
    def __len__(self) -> int:
        """
        Get the current number of items in the cache.
        
        Returns:
            The number of items currently in the cache.
        """
        with self._lock:
            return len(self._access_order)
    
    def __str__(self) -> str:
        """
        Get a string representation of the cache.
        
        Returns:
            A string showing the capacity and current size of the cache.
        """
        with self._lock:
            return (f"LRUCache(size={len(self._access_order)}, "
                    f"collections={len(self._cache)}, "
                    f"capacity={self.capacity})")
    
    def __repr__(self) -> str:
        """
        Get a detailed string representation of the cache.
        
        Returns:
            A detailed string representation of the cache.
        """
        with self._lock:
            stats = self.get_stats()
            return (f"LRUCache(size={stats['size']}, "
                    f"collections={stats['collections']}, "
                    f"capacity={self.capacity}, "
                    f"hit_ratio={stats['hit_ratio']:.2f})")


# Create an alias for backward compatibility and common use
lru_cache = LRUCache

# For type hinting convenience
def create_lru_cache(capacity: int = 1000) -> LRUCache:
    """
    Create or get the singleton LRU cache instance.
    
    This is just a convenience function that returns the singleton instance.
    It's equivalent to calling LRUCache(capacity).
    
    Args:
        capacity: Maximum number of items to store in the cache.
                 Only used when creating the instance for the first time.
    
    Returns:
        The singleton LRUCache instance.
    """
    return LRUCache(capacity)
