from django.core.cache import cache
from functools import wraps
import hashlib
import json

def cache_key_generator(*args, **kwargs):
    """Generate a cache key from function arguments."""
    key_parts = [str(arg) for arg in args]
    key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
    key_string = "|".join(key_parts)
    return hashlib.md5(key_string.encode()).hexdigest()

def cache_response(timeout=300):
    """
    Cache decorator for views and functions.
    Usage:
        @cache_response(timeout=300)
        def my_view(request):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{func.__name__}:{cache_key_generator(*args, **kwargs)}"
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # If not in cache, execute function
            result = func(*args, **kwargs)
            
            # Store in cache
            cache.set(cache_key, result, timeout)
            return result
        return wrapper
    return decorator

def cache_product_list(timeout=300):
    """
    Specialized cache decorator for product listing views.
    Handles pagination and filtering parameters.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract pagination and filter parameters
            page = kwargs.get('page', 1)
            filters = kwargs.get('filters', {})
            
            # Generate cache key
            cache_key = f"product_list:{page}:{json.dumps(filters, sort_keys=True)}"
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # If not in cache, execute function
            result = func(*args, **kwargs)
            
            # Store in cache
            cache.set(cache_key, result, timeout)
            return result
        return wrapper
    return decorator

def cache_product_details(timeout=300):
    """
    Specialized cache decorator for product detail views.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            product_id = kwargs.get('product_id')
            cache_key = f"product_details:{product_id}"
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # If not in cache, execute function
            result = func(*args, **kwargs)
            
            # Store in cache
            cache.set(cache_key, result, timeout)
            return result
        return wrapper
    return decorator

def invalidate_product_cache(product_id=None):
    """
    Invalidate product-related cache entries.
    If product_id is provided, only invalidate that product's cache.
    Otherwise, invalidate all product-related cache.
    """
    if product_id:
        # Invalidate specific product cache
        cache.delete(f"product_details:{product_id}")
    else:
        # Invalidate all product-related cache
        cache.delete_pattern("product_list:*")
        cache.delete_pattern("product_details:*")

def cache_search_results(timeout=300):
    """
    Specialized cache decorator for search results.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            query = kwargs.get('query', '')
            filters = kwargs.get('filters', {})
            
            # Generate cache key
            cache_key = f"search_results:{query}:{json.dumps(filters, sort_keys=True)}"
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # If not in cache, execute function
            result = func(*args, **kwargs)
            
            # Store in cache
            cache.set(cache_key, result, timeout)
            return result
        return wrapper
    return decorator

def invalidate_search_cache(query=None):
    """
    Invalidate search-related cache entries.
    If query is provided, only invalidate that search's cache.
    Otherwise, invalidate all search-related cache.
    """
    if query:
        cache.delete(f"search_results:{query}:*")
    else:
        cache.delete_pattern("search_results:*") 