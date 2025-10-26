"""
LRU Cache wrapper functions.

This module provides simplified wrapper functions for the two-layer LRU cache:
- lru_cache.get: Retrieves a value from the cache or executes a fallback function
- lru_cache.put: Decorator for functions that add values to the cache
- lru_cache.invalidate: Removes a specific item from the cache
"""
import functools
from typing import Any, Callable, Dict, Optional, TypeVar, cast, Union, Tuple, overload

# Import the singleton LRU cache implementation
from .lru_cache import LRUCache

# Type variables for generic typing
T = TypeVar('T')
R = TypeVar('R')


def get(collection: str, doc_id: str, id_field: str, 
        fallback_func: Optional[Callable[..., Any]] = None, 
        *args, **kwargs) -> Union[Any, None]:
    """
    Retrieve a value from the cache or execute a fallback function.
    
    Args:
        collection: The collection identifier.
        doc_id: The document identifier within the collection.
        id_field: The field name containing the document ID in the result.
        fallback_func: Optional function to call if cache miss.
        *args: Arguments to pass to the fallback function.
        **kwargs: Keyword arguments to pass to the fallback function.
    
    Returns:
        The cached value if found, otherwise the result of the fallback function,
        or None if no fallback function is provided and the item is not in cache.
    
    Examples:
        # Simple get with fallback
        user = lru_cache.get('users', '123', 'id', get_user_from_db, 123)
        
        # Get with keyword arguments for fallback
        order = lru_cache.get('orders', 'ORD-123', 'order_id', 
                             get_order_from_db, customer_id=42)
    """
    # Get the singleton cache instance
    cache = LRUCache()
    
    # Try to get the value from cache
    value = cache.get(collection, doc_id)
    
    if value is not None:
        return value
    
    # If value not in cache and fallback function provided
    if fallback_func is not None:
        # Execute the fallback function to get the value
        result = fallback_func(*args, **kwargs)
        
        if result is not None:
            # Check if the result has the expected ID field
            if isinstance(result, dict) and id_field in result:
                # Get the actual ID from the result
                actual_id = str(result[id_field])
                
                # Cache the result with the actual ID from the result
                cache.put(collection, actual_id, result)
                
                # If the ID doesn't match what we were looking for, don't cache with the requested ID
                # But still return the result
                if actual_id != doc_id:
                    return result
                
            # For the case where we don't have a dict with id_field or the IDs match
            cache.put(collection, doc_id, result)
        
        return result
    
    return None


def put(collection: str, id_field: str) -> Callable[[Callable[..., R]], Callable[..., R]]:
    """
    Decorator that adds the result of a function to the cache.
    
    This decorator wraps a function, executing it normally, but also
    storing its result in the cache. The function must return a value
    with the specified ID field, which is used as the document ID.
    
    Args:
        collection: The collection identifier.
        id_field: The field name containing the document ID in the result.
    
    Returns:
        A decorator function that will cache the result of the decorated function.
    
    Examples:
        @lru_cache.put('users', 'id')
        def create_user(name, email):
            # Create user in database
            user = db.users.insert({"name": name, "email": email})
            return user  # user contains 'id' field
    """
    def decorator(func: Callable[..., R]) -> Callable[..., R]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> R:
            # Execute the original function
            result = func(*args, **kwargs)
            
            # If result exists and has the expected ID field
            if result is not None:
                # Get the singleton cache instance
                cache = LRUCache()
                
                # Handle different result types
                if isinstance(result, dict) and id_field in result:
                    # For dictionary results with the ID field
                    doc_id = str(result[id_field])
                    cache.put(collection, doc_id, result)
                elif hasattr(result, id_field):
                    # For object results with the ID field as an attribute
                    doc_id = str(getattr(result, id_field))
                    cache.put(collection, doc_id, result)
            
            return result
        return wrapper
    
    return decorator


@overload
def invalidate(collection: str, doc_id: str) -> bool:
    ...

@overload
def invalidate(collection: str, data: Dict[str, Any], id_field: str) -> bool:
    ...

def invalidate(collection: str, doc_id_or_data: Union[str, Dict[str, Any]], id_field: Optional[str] = None) -> bool:
    """
    Remove a specific item from the cache.
    
    This function can be used in two ways:
    1. Directly with a document ID
    2. With a data object containing the document ID in a specified field
    
    Args:
        collection: The collection identifier.
        doc_id_or_data: Either the document ID string or a dictionary containing the ID.
        id_field: The field name containing the document ID (required when passing data).
    
    Returns:
        True if the item was in the cache and was removed,
        False if the item was not in the cache.
    
    Examples:
        # Method 1: Direct invalidation with document ID
        lru_cache.invalidate('users', '123')
        
        # Method 2: Invalidation using data object
        user_data = {'id': '123', 'name': 'Alice'}
        lru_cache.invalidate('users', user_data, 'id')
        
        # Use with update operations
        def update_user(user_id, new_data):
            # Update in database
            updated_user = db.users.update(user_id, new_data)
            # Invalidate the cache using the updated user data
            lru_cache.invalidate('users', updated_user, 'id')
    """
    # Get the singleton cache instance
    cache = LRUCache()
    
    # Handle different argument types
    if isinstance(doc_id_or_data, str):
        # If directly provided a document ID
        doc_id = doc_id_or_data
    elif isinstance(doc_id_or_data, dict) and id_field is not None:
        # If provided a dictionary with the ID field
        if id_field not in doc_id_or_data:
            return False  # ID field not in data
        doc_id = str(doc_id_or_data[id_field])
    elif hasattr(doc_id_or_data, id_field or '') and id_field is not None:
        # If provided an object with the ID as an attribute
        doc_id = str(getattr(doc_id_or_data, id_field))
    else:
        raise ValueError("Invalid arguments. Either provide a document ID string or "
                         "a data object with an id_field parameter.")
    
    # Remove the item from the cache
    return cache.remove(collection, doc_id)


# Reset the cache stats (useful for testing)
def reset_stats() -> None:
    """
    Reset the hit/miss statistics of the LRU cache.
    
    This is particularly useful for testing.
    """
    cache = LRUCache()
    cache._hit_count = 0
    cache._miss_count = 0


# Provide shorthand access to the cache capacity
def get_capacity() -> int:
    """Get the current capacity of the LRU cache."""
    return LRUCache().capacity


def set_capacity(capacity: int) -> None:
    """Set the capacity of the LRU cache."""
    LRUCache().resize(capacity)


def get_stats() -> Dict[str, Union[int, float]]:
    """Get statistics about the LRU cache usage."""
    return LRUCache().get_stats()


def clear_all() -> None:
    """
    Clear all items from the cache and reset statistics.
    """
    cache = LRUCache()
    cache.clear()
    reset_stats()  # Reset hit/miss counts


def clear_collection(collection: str) -> int:
    """
    Clear all items from a specific collection.
    
    Args:
        collection: The collection identifier.
    
    Returns:
        The number of items removed.
    """
    return LRUCache().remove_collection(collection)


# Additional utility function for batch operations
def batch_invalidate(items: list[Tuple[str, str]]) -> int:
    """
    Invalidate multiple items in a batch operation.
    
    Args:
        items: List of (collection, doc_id) tuples to invalidate.
    
    Returns:
        The number of items successfully invalidated.
    """
    cache = LRUCache()
    count = 0
    
    for collection, doc_id in items:
        if cache.remove(collection, doc_id):
            count += 1
    
    return count
