import json
import pickle
from datetime import datetime, timedelta
from functools import wraps
from flask import g, current_app, request

class RedisCache:
    """
    Redis caching utility for the Quiz Master application.
    Provides methods for caching and retrieving data.
    """
    @staticmethod
    def is_redis_available():
        """Check if Redis is available"""
        return hasattr(g, 'redis_client') and g.redis_client is not None
        
    @staticmethod
    def get(key):
        """Get a value from Redis cache"""
        if not RedisCache.is_redis_available():
            return None
            
        try:
            data = g.redis_client.get(key)
            if data:
                return pickle.loads(data)
            return None
        except Exception as e:
            current_app.logger.warning(f"Redis get error: {e}")
            return None
            
    @staticmethod
    def set(key, value, expire_seconds=3600):
        """Set a value in Redis cache with expiration time"""
        if not RedisCache.is_redis_available():
            return False
            
        try:
            serialized_value = pickle.dumps(value)
            return g.redis_client.setex(key, expire_seconds, serialized_value)
        except Exception as e:
            current_app.logger.warning(f"Redis set error: {e}")
            return False
            
    @staticmethod
    def delete(key):
        """Delete a key from Redis cache"""
        if not RedisCache.is_redis_available():
            return False
            
        try:
            return g.redis_client.delete(key)
        except Exception as e:
            current_app.logger.warning(f"Redis delete error: {e}")
            return False
            
    @staticmethod
    def flush_pattern(pattern):
        """Delete all keys matching pattern from Redis cache"""
        if not RedisCache.is_redis_available():
            return False
            
        try:
            keys = g.redis_client.keys(pattern)
            if keys:
                return g.redis_client.delete(*keys)
            return 0
        except Exception as e:
            current_app.logger.warning(f"Redis flush pattern error: {e}")
            return False

# Decorator for caching view responses
def cached_response(expire_seconds=3600, key_prefix='view'):
    """
    Decorator for caching Flask view responses
    
    Args:
        expire_seconds: Seconds until cache expiration
        key_prefix: Prefix for the cache key
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Don't cache if Redis is not available
            if not RedisCache.is_redis_available():
                return f(*args, **kwargs)
                
            # Create a cache key based on the function name, args, kwargs and query params
            cache_key = f"{key_prefix}:{f.__name__}"
            
            # Add arguments to cache key
            for arg in args:
                cache_key += f":{arg}"
                
            # Add keyword arguments to cache key
            for key, value in sorted(kwargs.items()):
                cache_key += f":{key}={value}"
                
            # Add query parameters to cache key
            for key, value in sorted(request.args.items()):
                cache_key += f":{key}={value}"
                
            # Try to get response from cache
            cached_result = RedisCache.get(cache_key)
            if cached_result is not None:
                current_app.logger.debug(f"Cache hit: {cache_key}")
                return cached_result
                
            # If not in cache, call the original function
            result = f(*args, **kwargs)
            
            # Cache the response
            RedisCache.set(cache_key, result, expire_seconds)
            current_app.logger.debug(f"Cached: {cache_key}")
            
            return result
        return decorated_function
    return decorator

# Function to invalidate cache for a specific model
def invalidate_model_cache(model_name, model_id=None):
    """
    Invalidate cache for a specific model
    
    Args:
        model_name: Name of the model (e.g. 'quiz')
        model_id: Optional ID of the model instance
    """
    if not RedisCache.is_redis_available():
        return
        
    pattern = f"view:*{model_name}*"
    if model_id:
        specific_pattern = f"view:*{model_name}*:{model_id}*"
        RedisCache.flush_pattern(specific_pattern)
    
    # Flush all cache entries related to this model
    RedisCache.flush_pattern(pattern)
    
    # Flush dashboard data which might include this model
    RedisCache.flush_pattern("view:get_user_quiz_dashboard*")