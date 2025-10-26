"""
Tests for the LRU cache wrapper functions.
"""
import pytest
from unittest.mock import MagicMock, patch
import time
from cache2cache.submodule.wrappers import get, put, invalidate, get_capacity, set_capacity, get_stats, clear_all, clear_collection, batch_invalidate, reset_stats

# Mock data for testing
USER_DATA = {"id": "123", "name": "Test User", "email": "test@example.com"}
PRODUCT_DATA = {"product_id": "PROD-001", "name": "Test Product", "price": 99.99}


class TestLRUCacheWrappers:
    """Tests for the LRU cache wrapper functions."""
    
    def setup_method(self):
        """Setup for each test - clear the cache."""
        clear_all()
    
    def test_get_cache_miss_with_fallback(self):
        """Test get function with cache miss and fallback."""
        # Mock fallback function
        fallback = MagicMock(return_value=USER_DATA)
        
        # Get with cache miss - should call fallback
        result = get('users', '123', 'id', fallback, '123')
        
        # Verify results
        assert result == USER_DATA
        fallback.assert_called_once_with('123')
        
        # Second get should be a cache hit
        fallback.reset_mock()
        result2 = get('users', '123', 'id', fallback)
        
        assert result2 == USER_DATA
        fallback.assert_not_called()
    
    def test_get_cache_miss_no_fallback(self):
        """Test get function with cache miss and no fallback."""
        # Get with no fallback should return None
        result = get('users', '123', 'id')
        assert result is None
    
    def test_get_with_different_id_field(self):
        """Test get function with a different ID field."""
        # Mock fallback function
        fallback = MagicMock(return_value=PRODUCT_DATA)
        
        # Get with cache miss - should call fallback
        result = get('products', 'PROD-001', 'product_id', fallback, 'PROD-001')
        
        # Verify results
        assert result == PRODUCT_DATA
        fallback.assert_called_once_with('PROD-001')
    
    def test_put_decorator(self):
        """Test put decorator."""
        # Create a decorated function
        @put('users', 'id')
        def create_user(user_id):
            return {"id": user_id, "name": f"User {user_id}", "created": time.time()}
        
        # Call the decorated function
        user = create_user('456')
        assert user["id"] == '456'
        
        # Verify it was cached
        cached_user = get('users', '456', 'id')
        assert cached_user == user
    
    def test_put_decorator_with_different_id_field(self):
        """Test put decorator with a different ID field."""
        # Create a decorated function
        @put('products', 'product_id')
        def create_product(product_id):
            return {"product_id": product_id, "name": f"Product {product_id}", "created": time.time()}
        
        # Call the decorated function
        product = create_product('PROD-002')
        assert product["product_id"] == 'PROD-002'
        
        # Verify it was cached
        cached_product = get('products', 'PROD-002', 'product_id')
        assert cached_product == product
    
    def test_put_decorator_with_none_result(self):
        """Test put decorator with a function that returns None."""
        # Create a decorated function
        @put('users', 'id')
        def create_user_none():
            return None
        
        # Call the decorated function
        result = create_user_none()
        assert result is None
        
        # No cache entry should be created
        stats = get_stats()
        assert stats["size"] == 0
    
    def test_invalidate_with_doc_id(self):
        """Test invalidate function with document ID."""
        # Add item to cache
        @put('users', 'id')
        def create_user(user_id):
            return {"id": user_id, "name": f"User {user_id}"}
        
        user = create_user('789')
        
        # Verify it's in cache
        assert get('users', '789', 'id') == user
        
        # Invalidate the item
        result = invalidate('users', '789')
        assert result is True
        
        # Verify it's no longer in cache
        assert get('users', '789', 'id') is None
        
        # Invalidating again should return False
        result = invalidate('users', '789')
        assert result is False
    
    def test_invalidate_with_data(self):
        """Test invalidate function with data object."""
        # Add item to cache
        @put('users', 'id')
        def create_user(user_id):
            return {"id": user_id, "name": f"User {user_id}"}
        
        user = create_user('101')
        
        # Verify it's in cache
        assert get('users', '101', 'id') == user
        
        # Invalidate using the user data
        result = invalidate('users', user, 'id')
        assert result is True
        
        # Verify it's no longer in cache
        assert get('users', '101', 'id') is None
    
    def test_invalidate_with_different_id_field(self):
        """Test invalidate function with data object using a different ID field."""
        # Add product to cache
        @put('products', 'product_id')
        def create_product(product_id):
            return {"product_id": product_id, "name": f"Product {product_id}"}
        
        product = create_product('PROD-003')
        
        # Verify it's in cache
        assert get('products', 'PROD-003', 'product_id') == product
        
        # Invalidate using the product data
        result = invalidate('products', product, 'product_id')
        assert result is True
        
        # Verify it's no longer in cache
        assert get('products', 'PROD-003', 'product_id') is None
    
    def test_invalidate_invalid_arguments(self):
        """Test invalidate function with invalid arguments."""
        # Missing id_field when passing a dict
        with pytest.raises(ValueError):
            invalidate('users', {"id": "123"})
        
        # id_field not in data
        result = invalidate('users', {"name": "Alice"}, 'id')
        assert result is False
    
    def test_capacity_functions(self):
        """Test capacity-related functions."""
        # Get initial capacity
        initial_capacity = get_capacity()
        
        # Set new capacity
        set_capacity(50)
        assert get_capacity() == 50
        
        # Set back to initial
        set_capacity(initial_capacity)
        assert get_capacity() == initial_capacity
        
        # Test invalid capacity
        with pytest.raises(ValueError):
            set_capacity(0)
    
    def test_cache_eviction(self):
        """Test cache eviction when capacity is reached."""
        # Set small capacity
        set_capacity(3)
        
        # Add items to fill the cache
        for i in range(3):
            get('users', str(i), 'id', lambda x: {"id": x, "value": i}, str(i))
        
        # All items should be cached
        assert get('users', '0', 'id') is not None
        assert get('users', '1', 'id') is not None
        assert get('users', '2', 'id') is not None
        
        # Add another item, which should evict the oldest one
        get('users', '3', 'id', lambda x: {"id": x, "value": 3}, '3')
        
        # First item should be evicted, others should remain
        assert get('users', '0', 'id') is None
        assert get('users', '1', 'id') is not None
        assert get('users', '2', 'id') is not None
        assert get('users', '3', 'id') is not None
        
        # Set capacity back to a larger value
        set_capacity(1000)
    
    def test_clear_collection(self):
        """Test clearing a collection."""
        # Add items to different collections
        get('users', '1', 'id', lambda x: {"id": x, "name": "User 1"}, '1')
        get('users', '2', 'id', lambda x: {"id": x, "name": "User 2"}, '2')
        get('products', '1', 'id', lambda x: {"id": x, "name": "Product 1"}, '1')
        
        # Clear users collection
        removed = clear_collection('users')
        assert removed == 2
        
        # Verify users are gone but products remain
        assert get('users', '1', 'id') is None
        assert get('users', '2', 'id') is None
        assert get('products', '1', 'id') is not None
        
        # Clearing again should return 0
        removed = clear_collection('users')
        assert removed == 0
    
    def test_batch_invalidate(self):
        """Test batch invalidation."""
        # Add items
        get('users', '1', 'id', lambda x: {"id": x, "name": "User 1"}, '1')
        get('users', '2', 'id', lambda x: {"id": x, "name": "User 2"}, '2')
        get('products', '1', 'id', lambda x: {"id": x, "name": "Product 1"}, '1')
        
        # Batch invalidate
        count = batch_invalidate([
            ('users', '1'),
            ('users', '2'),
            ('products', '1'),
            ('orders', '1')  # Doesn't exist
        ])
        assert count == 3
        
        # Verify all are gone
        assert get('users', '1', 'id') is None
        assert get('users', '2', 'id') is None
        assert get('products', '1', 'id') is None
    
    def test_get_stats(self):
        """Test stats reporting."""
        # Clear the cache and reset stats to start fresh
        clear_all()  # This now also resets the stats
        
        # Add some items and access them
        get('users', '1', 'id', lambda x: {"id": x}, '1')
        get('users', '1', 'id')  # Hit
        get('users', '2', 'id')  # Miss
        
        # Get stats
        stats = get_stats()
        
        # Verify stats - we now expect exactly 1 hit and 2 misses
        assert stats["hits"] == 1, f"Expected 1 hit but got {stats['hits']}"
        assert stats["misses"] == 2, f"Expected 2 misses but got {stats['misses']}" 
        assert stats["hit_ratio"] == 1/3
        assert stats["size"] == 1
        assert stats["collections"] == 1
        assert stats["capacity"] > 0


class TestLRUCacheIntegration:
    """Integration tests for LRU cache wrappers."""
    
    def setup_method(self):
        """Setup for each test - clear the cache."""
        clear_all()
    
    def test_full_workflow(self):
        """Test a full workflow with put, get, and invalidate."""
        # Create a decorated function
        @put('users', 'id')
        def create_user(user_id, name, email):
            return {
                "id": user_id,
                "name": name,
                "email": email,
                "created": time.time()
            }
        
        # Create a fallback function for get
        def get_user_fallback(user_id):
            return {
                "id": user_id,
                "name": f"Fallback User {user_id}",
                "email": f"fallback-{user_id}@example.com",
                "created": time.time()
            }
        
        # 1. Create a user (put)
        user = create_user('123', 'Test User', 'test@example.com')
        
        # 2. Retrieve the user (get - hit)
        cached_user = get('users', '123', 'id')
        assert cached_user == user
        
        # 3. Invalidate the user
        result = invalidate('users', '123')
        assert result is True
        
        # 4. Retrieve again (get - miss with fallback)
        new_user = get('users', '123', 'id', get_user_fallback, '123')
        assert new_user != user
        assert new_user["name"] == "Fallback User 123"
        
        # 5. Update the user
        updated_user = {
            "id": "123",
            "name": "Updated User",
            "email": "updated@example.com",
            "updated": time.time()
        }
        
        # 6. Invalidate with user data
        result = invalidate('users', updated_user, 'id')
        assert result is True
        
        # 7. Verify it's no longer in cache
        assert get('users', '123', 'id') is None
    
    def test_multiple_collections(self):
        """Test using multiple collections with different ID fields."""
        # Create decorated functions
        @put('users', 'id')
        def create_user(user_id):
            return {"id": user_id, "type": "user"}
        
        @put('products', 'product_id')
        def create_product(prod_id):
            return {"product_id": prod_id, "type": "product"}
        
        # Create items in different collections
        user = create_user('U1')
        product = create_product('P1')
        
        # Retrieve items
        assert get('users', 'U1', 'id') == user
        assert get('products', 'P1', 'product_id') == product
        
        # Invalidate with data
        invalidate('users', user, 'id')
        invalidate('products', product, 'product_id')
        
        # Verify they're gone
        assert get('users', 'U1', 'id') is None
        assert get('products', 'P1', 'product_id') is None
    
    def test_fallback_with_invalid_id(self):
        """Test fallback function that returns an item with a different ID."""
        # Clear the cache to start fresh
        clear_all()
        
        # Fallback function returns item with ID that doesn't match request
        def wrong_id_fallback(user_id):
            return {"id": "wrong-id", "name": "Wrong ID User"}
        
        # Get with fallback
        result = get('users', '123', 'id', wrong_id_fallback, '123')
        
        # Should return the result
        assert result["id"] == "wrong-id"
        
        # Verify it wasn't cached with requested ID
        assert get('users', '123', 'id') is None
        # But should be cached with the actual ID from the result
        assert get('users', 'wrong-id', 'id') is not None


if __name__ == "__main__":
    pytest.main()
