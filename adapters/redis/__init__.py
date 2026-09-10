"""
==============================================================================
Redis Adaptör Paketi
==============================================================================
"""

from adapters.redis.redis_client import get_redis_client, InMemoryCacheFallback

__all__ = ["get_redis_client", "InMemoryCacheFallback"]
