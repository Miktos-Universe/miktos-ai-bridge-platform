"""
Advanced Cache Manager for Miktos AI Platform
Priority 3: Real-time Features & Optimization

Provides intelligent multi-tier caching with semantic similarity,
LRU eviction, and automatic cache warming for optimal performance.
"""

import asyncio
import logging
import hashlib
import json
import pickle
import time
from typing import Any, Dict, List, Optional, Union, Callable, Set
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import OrderedDict
import threading
import weakref
import numpy as np
from pathlib import Path

try:
    import redis  # type: ignore
    from redis import Redis  # type: ignore
    REDIS_AVAILABLE = True
except ImportError:
    # Create dummy redis module for type checking
    class _DummyRedis:
        @staticmethod
        def from_url(*args, **kwargs):
            return None
    
    redis = _DummyRedis()  # type: ignore
    Redis = None  # type: ignore
    REDIS_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    value: Any
    created_at: datetime
    last_accessed: datetime
    access_count: int
    ttl_seconds: Optional[int]
    size_bytes: int
    tags: Set[str]
    similarity_vector: Optional[np.ndarray] = None


@dataclass
class CacheStats:
    """Cache statistics"""
    total_requests: int
    cache_hits: int
    cache_misses: int
    hit_rate: float
    total_size_bytes: int
    entry_count: int
    evictions: int
    last_cleanup: datetime


class MemoryCache:
    """High-performance in-memory cache with LRU eviction"""
    
    def __init__(self, max_size: int = 1000, max_memory_mb: int = 512):
        self.max_size = max_size
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.cache = OrderedDict()
        self.lock = threading.RLock()
        self.stats = CacheStats(
            total_requests=0,
            cache_hits=0,
            cache_misses=0,
            hit_rate=0.0,
            total_size_bytes=0,
            entry_count=0,
            evictions=0,
            last_cleanup=datetime.now()
        )
    
    def get(self, key: str) -> Optional[Any]:
        """Get item from cache"""
        with self.lock:
            self.stats.total_requests += 1
            
            if key in self.cache:
                entry = self.cache[key]
                
                # Check TTL
                if entry.ttl_seconds:
                    age = (datetime.now() - entry.created_at).total_seconds()
                    if age > entry.ttl_seconds:
                        del self.cache[key]
                        self.stats.cache_misses += 1
                        self._update_stats()
                        return None
                
                # Update access info and move to end (most recently used)
                entry.last_accessed = datetime.now()
                entry.access_count += 1
                self.cache.move_to_end(key)
                
                self.stats.cache_hits += 1
                self._update_stats()
                return entry.value
            
            self.stats.cache_misses += 1
            self._update_stats()
            return None
    
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None, 
            tags: Optional[Set[str]] = None) -> bool:
        """Set item in cache"""
        with self.lock:
            # Calculate size
            try:
                size_bytes = len(pickle.dumps(value))
            except:
                size_bytes = 1024  # Fallback estimate
            
            # Check if single item exceeds memory limit
            if size_bytes > self.max_memory_bytes:
                logger.warning(f"Cache item too large: {size_bytes} bytes")
                return False
            
            # Create entry
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=datetime.now(),
                last_accessed=datetime.now(),
                access_count=0,
                ttl_seconds=ttl_seconds,
                size_bytes=size_bytes,
                tags=tags or set()
            )
            
            # Remove old entry if exists
            if key in self.cache:
                old_entry = self.cache[key]
                self.stats.total_size_bytes -= old_entry.size_bytes
                del self.cache[key]
            
            # Add new entry
            self.cache[key] = entry
            self.stats.total_size_bytes += size_bytes
            
            # Evict if necessary
            self._evict_if_needed()
            
            self._update_stats()
            return True
    
    def delete(self, key: str) -> bool:
        """Delete item from cache"""
        with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                self.stats.total_size_bytes -= entry.size_bytes
                del self.cache[key]
                self._update_stats()
                return True
            return False
    
    def clear_by_tags(self, tags: Set[str]) -> int:
        """Clear all entries with any of the specified tags"""
        with self.lock:
            keys_to_remove = []
            for key, entry in self.cache.items():
                if entry.tags.intersection(tags):
                    keys_to_remove.append(key)
            
            removed_count = 0
            for key in keys_to_remove:
                if self.delete(key):
                    removed_count += 1
            
            return removed_count
    
    def cleanup_expired(self) -> int:
        """Remove expired entries"""
        with self.lock:
            current_time = datetime.now()
            keys_to_remove = []
            
            for key, entry in self.cache.items():
                if entry.ttl_seconds:
                    age = (current_time - entry.created_at).total_seconds()
                    if age > entry.ttl_seconds:
                        keys_to_remove.append(key)
            
            removed_count = 0
            for key in keys_to_remove:
                entry = self.cache[key]
                self.stats.total_size_bytes -= entry.size_bytes
                del self.cache[key]
                removed_count += 1
            
            self.stats.last_cleanup = current_time
            self._update_stats()
            return removed_count
    
    def _evict_if_needed(self):
        """Evict entries if cache limits exceeded"""
        # Evict by count
        while len(self.cache) > self.max_size:
            key, entry = self.cache.popitem(last=False)  # Remove least recently used
            self.stats.total_size_bytes -= entry.size_bytes
            self.stats.evictions += 1
        
        # Evict by memory
        while self.stats.total_size_bytes > self.max_memory_bytes and self.cache:
            key, entry = self.cache.popitem(last=False)
            self.stats.total_size_bytes -= entry.size_bytes
            self.stats.evictions += 1
    
    def _update_stats(self):
        """Update cache statistics"""
        self.stats.entry_count = len(self.cache)
        if self.stats.total_requests > 0:
            self.stats.hit_rate = self.stats.cache_hits / self.stats.total_requests
    
    def get_stats(self) -> CacheStats:
        """Get cache statistics"""
        with self.lock:
            return CacheStats(**asdict(self.stats))


class RedisCache:
    """Redis-based distributed cache backend"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379", prefix: str = "miktos:"):
        self.redis_url = redis_url
        self.prefix = prefix
        self.client: Optional[Any] = None  # Use Any to avoid import issues
        self.connected = False
        
        if REDIS_AVAILABLE:
            try:
                self.client = redis.from_url(redis_url, decode_responses=False)
                if self.client is not None:
                    self.client.ping()
                    self.connected = True
                    logger.info("Connected to Redis cache backend")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}")
                self.connected = False
    
    def _make_key(self, key: str) -> str:
        """Create prefixed cache key"""
        return f"{self.prefix}{key}"
    
    async def get(self, key: str) -> Optional[Any]:
        """Get item from Redis cache"""
        if not self.connected or self.client is None:
            return None
        
        try:
            redis_key = self._make_key(key)
            data = self.client.get(redis_key)
            if data:
                return pickle.loads(data)
            return None
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> bool:
        """Set item in Redis cache"""
        if not self.connected or self.client is None:
            return False
        
        try:
            redis_key = self._make_key(key)
            data = pickle.dumps(value)
            
            if ttl_seconds:
                self.client.setex(redis_key, ttl_seconds, data)
            else:
                self.client.set(redis_key, data)
            
            return True
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete item from Redis cache"""
        if not self.connected or self.client is None:
            return False
        
        try:
            redis_key = self._make_key(key)
            result = self.client.delete(redis_key)
            return result > 0
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False


class SemanticCacheLayer:
    """Semantic similarity-based cache layer"""
    
    def __init__(self, similarity_threshold: float = 0.85):
        self.similarity_threshold = similarity_threshold
        self.model = None
        self.embeddings_cache = {}
        self.semantic_index = {}
        
        if TRANSFORMERS_AVAILABLE:
            try:
                self.model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("Semantic cache layer initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize semantic model: {e}")
    
    def _get_embedding(self, text: str) -> Optional[np.ndarray]:
        """Get text embedding for semantic similarity"""
        if not self.model:
            return None
        
        try:
            if text not in self.embeddings_cache:
                embedding = self.model.encode([text])[0]
                self.embeddings_cache[text] = embedding
            return self.embeddings_cache[text]
        except Exception as e:
            logger.error(f"Failed to get embedding: {e}")
            return None
    
    def find_similar_keys(self, query: str, max_results: int = 5) -> List[str]:
        """Find semantically similar cache keys"""
        if not self.model:
            return []
        
        query_embedding = self._get_embedding(query)
        if query_embedding is None:
            return []
        
        similarities = []
        for key, embedding in self.semantic_index.items():
            try:
                similarity = np.dot(query_embedding, embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(embedding)
                )
                if similarity >= self.similarity_threshold:
                    similarities.append((key, similarity))
            except Exception:
                continue
        
        # Sort by similarity and return top results
        similarities.sort(key=lambda x: x[1], reverse=True)
        return [key for key, _ in similarities[:max_results]]
    
    def index_key(self, key: str, text_content: str):
        """Add key to semantic index"""
        if not self.model:
            return
        
        embedding = self._get_embedding(text_content)
        if embedding is not None:
            self.semantic_index[key] = embedding


class CacheWarmer:
    """Intelligent cache warming system"""
    
    def __init__(self, cache_manager):
        self.cache_manager = cache_manager
        self.popular_items = {}
        self.access_patterns = {}
        self.warming_tasks = set()
    
    def record_access(self, key: str, context: Dict[str, Any]):
        """Record cache access for pattern analysis"""
        current_time = datetime.now()
        
        if key not in self.popular_items:
            self.popular_items[key] = {
                'access_count': 0,
                'last_access': current_time,
                'contexts': []
            }
        
        item = self.popular_items[key]
        item['access_count'] += 1
        item['last_access'] = current_time
        item['contexts'].append(context)
        
        # Keep only recent contexts
        cutoff_time = current_time - timedelta(hours=24)
        item['contexts'] = [
            ctx for ctx in item['contexts']
            if ctx.get('timestamp', current_time) > cutoff_time
        ]
    
    async def warm_popular_items(self, top_n: int = 20):
        """Warm cache with popular items"""
        # Sort by access count and recency
        popular = sorted(
            self.popular_items.items(),
            key=lambda x: (x[1]['access_count'], x[1]['last_access']),
            reverse=True
        )
        
        for key, data in popular[:top_n]:
            if key not in self.warming_tasks:
                self.warming_tasks.add(key)
                asyncio.create_task(self._warm_item(key, data))
    
    async def _warm_item(self, key: str, data: Dict[str, Any]):
        """Warm a specific cache item"""
        try:
            # This would be implemented based on the specific item type
            # For now, we'll just log the warming attempt
            logger.info(f"Warming cache item: {key}")
            
            # Simulate cache warming
            await asyncio.sleep(0.1)
            
        except Exception as e:
            logger.error(f"Failed to warm cache item {key}: {e}")
        finally:
            self.warming_tasks.discard(key)


class CacheManager:
    """Advanced multi-tier cache manager"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config.get('caching', {})
        
        # Initialize cache backends
        self.memory_cache = MemoryCache(
            max_size=self.config.get('memory_cache', {}).get('max_entries', 1000),
            max_memory_mb=self.config.get('memory_cache', {}).get('max_memory_mb', 512)
        )
        
        self.redis_cache = None
        redis_config = self.config.get('redis', {})
        if redis_config.get('enabled', False) and REDIS_AVAILABLE:
            self.redis_cache = RedisCache(
                redis_url=redis_config.get('url', 'redis://localhost:6379'),
                prefix=redis_config.get('prefix', 'miktos:')
            )
        
        # Initialize semantic layer
        self.semantic_cache = None
        semantic_config = self.config.get('semantic_similarity', {})
        if semantic_config.get('enabled', False):
            self.semantic_cache = SemanticCacheLayer(
                similarity_threshold=semantic_config.get('threshold', 0.85)
            )
        
        # Initialize cache warmer
        self.cache_warmer = CacheWarmer(self)
        
        # Cache configuration
        self.default_ttl = self.config.get('default_ttl', 3600)
        self.enable_statistics = self.config.get('enable_statistics', True)
        
        # Performance monitoring integration
        self.performance_monitor = None
        
        # Start background tasks
        self._start_background_tasks()
    
    def set_performance_monitor(self, monitor):
        """Set performance monitor for integration"""
        self.performance_monitor = monitor
    
    async def get(self, key: str, namespace: str = "default") -> Optional[Any]:
        """Get item from cache with multi-tier lookup"""
        cache_key = f"{namespace}:{key}"
        start_time = time.time()
        
        # Try memory cache first
        value = self.memory_cache.get(cache_key)
        if value is not None:
            self._record_cache_hit("memory", time.time() - start_time)
            self.cache_warmer.record_access(cache_key, {"source": "memory"})
            return value
        
        # Try Redis cache
        if self.redis_cache:
            value = await self.redis_cache.get(cache_key)
            if value is not None:
                # Populate memory cache
                self.memory_cache.set(cache_key, value, ttl_seconds=self.default_ttl)
                self._record_cache_hit("redis", time.time() - start_time)
                self.cache_warmer.record_access(cache_key, {"source": "redis"})
                return value
        
        # Try semantic similarity if enabled
        if self.semantic_cache and isinstance(key, str):
            similar_keys = self.semantic_cache.find_similar_keys(key)
            for similar_key in similar_keys:
                similar_cache_key = f"{namespace}:{similar_key}"
                value = self.memory_cache.get(similar_cache_key)
                if value is not None:
                    # Cache under the requested key too
                    await self.set(key, value, namespace=namespace)
                    self._record_cache_hit("semantic", time.time() - start_time)
                    return value
        
        self._record_cache_miss(time.time() - start_time)
        return None
    
    async def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None,
                  namespace: str = "default", tags: Optional[Set[str]] = None) -> bool:
        """Set item in cache across all tiers"""
        cache_key = f"{namespace}:{key}"
        ttl = ttl_seconds or self.default_ttl
        
        # Set in memory cache
        success = self.memory_cache.set(cache_key, value, ttl_seconds=ttl, tags=tags)
        
        # Set in Redis cache
        if self.redis_cache:
            await self.redis_cache.set(cache_key, value, ttl_seconds=ttl)
        
        # Index in semantic cache if applicable
        if self.semantic_cache and isinstance(key, str):
            text_content = str(value) if not isinstance(value, str) else value
            self.semantic_cache.index_key(key, text_content)
        
        return success
    
    async def delete(self, key: str, namespace: str = "default") -> bool:
        """Delete item from all cache tiers"""
        cache_key = f"{namespace}:{key}"
        
        # Delete from memory cache
        memory_deleted = self.memory_cache.delete(cache_key)
        
        # Delete from Redis cache
        redis_deleted = False
        if self.redis_cache:
            redis_deleted = await self.redis_cache.delete(cache_key)
        
        # Remove from semantic index
        if self.semantic_cache and key in self.semantic_cache.semantic_index:
            del self.semantic_cache.semantic_index[key]
        
        return memory_deleted or redis_deleted
    
    async def clear_namespace(self, namespace: str) -> int:
        """Clear all items in a namespace"""
        # This is a simplified implementation
        # In a real system, you'd need more sophisticated namespace handling
        removed_count = 0
        
        # Clear from memory cache (approximate)
        keys_to_remove = [k for k in self.memory_cache.cache.keys() if k.startswith(f"{namespace}:")]
        for key in keys_to_remove:
            if self.memory_cache.delete(key):
                removed_count += 1
        
        return removed_count
    
    async def clear_by_tags(self, tags: Set[str]) -> int:
        """Clear all items with specified tags"""
        return self.memory_cache.clear_by_tags(tags)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        memory_stats = self.memory_cache.get_stats()
        
        stats = {
            'memory_cache': asdict(memory_stats),
            'redis_connected': self.redis_cache.connected if self.redis_cache else False,
            'semantic_enabled': self.semantic_cache is not None,
            'total_namespaces': len(set(k.split(':')[0] for k in self.memory_cache.cache.keys())),
        }
        
        if self.semantic_cache:
            stats['semantic_index_size'] = len(self.semantic_cache.semantic_index)
        
        return stats
    
    def _record_cache_hit(self, source: str, duration: float):
        """Record cache hit for monitoring"""
        if self.performance_monitor:
            self.performance_monitor.record_cache_operation(f"{source}_get", True, duration)
    
    def _record_cache_miss(self, duration: float):
        """Record cache miss for monitoring"""
        if self.performance_monitor:
            self.performance_monitor.record_cache_operation("get", False, duration)
    
    def _start_background_tasks(self):
        """Start background maintenance tasks"""
        async def cleanup_task():
            while True:
                try:
                    # Cleanup expired entries
                    expired_count = self.memory_cache.cleanup_expired()
                    if expired_count > 0:
                        logger.debug(f"Cleaned up {expired_count} expired cache entries")
                    
                    # Warm popular items
                    if self.config.get('warming', {}).get('enabled', False):
                        await self.cache_warmer.warm_popular_items()
                    
                    await asyncio.sleep(300)  # Run every 5 minutes
                    
                except Exception as e:
                    logger.error(f"Cache cleanup task error: {e}")
                    await asyncio.sleep(60)
        
        asyncio.create_task(cleanup_task())


# Convenience functions for common cache patterns
async def cached_function(cache_manager: CacheManager, namespace: str = "functions",
                         ttl_seconds: int = 3600):
    """Decorator for caching function results"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            key_parts = [func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = ":".join(key_parts)
            
            # Try to get from cache
            cached_result = await cache_manager.get(cache_key, namespace)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            await cache_manager.set(cache_key, result, ttl_seconds=ttl_seconds, namespace=namespace)
            
            return result
        return wrapper
    return decorator
