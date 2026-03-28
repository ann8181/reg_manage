"""
Cache Module - 缓存模块
支持 Redis 和内存缓存，提供统一的缓存接口
"""

import time
import json
import hashlib
from abc import ABC, abstractmethod
from typing import Any, Optional, Dict, Callable
from collections import OrderedDict
import threading


class CacheBackend(ABC):
    """缓存后端基类"""
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl: int = -1) -> bool:
        """设置缓存"""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """删除缓存"""
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        pass
    
    @abstractmethod
    def clear(self) -> bool:
        """清空缓存"""
        pass


class MemoryCache(CacheBackend):
    """内存缓存 (LRU 实现)"""
    
    def __init__(self, max_size: int = 1000):
        self._cache: OrderedDict = OrderedDict()
        self._ttl: Dict[str, float] = {}
        self._max_size = max_size
        self._lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key not in self._cache:
                return None
            
            if key in self._ttl:
                if time.time() > self._ttl[key]:
                    del self._cache[key]
                    del self._ttl[key]
                    return None
            
            self._cache.move_to_end(key)
            return self._cache[key]
    
    def set(self, key: str, value: Any, ttl: int = -1) -> bool:
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            else:
                if len(self._cache) >= self._max_size:
                    oldest = next(iter(self._cache))
                    del self._cache[oldest]
                    if oldest in self._ttl:
                        del self._ttl[oldest]
            
            self._cache[key] = value
            
            if ttl > 0:
                self._ttl[key] = time.time() + ttl
            elif key in self._ttl:
                del self._ttl[key]
            
            return True
    
    def delete(self, key: str) -> bool:
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                if key in self._ttl:
                    del self._ttl[key]
                return True
            return False
    
    def exists(self, key: str) -> bool:
        return self.get(key) is not None
    
    def clear(self) -> bool:
        with self._lock:
            self._cache.clear()
            self._ttl.clear()
        return True
    
    def get_many(self, keys: list) -> Dict[str, Any]:
        """批量获取"""
        result = {}
        for key in keys:
            value = self.get(key)
            if value is not None:
                result[key] = value
        return result
    
    def set_many(self, data: Dict[str, Any], ttl: int = -1) -> bool:
        """批量设置"""
        for key, value in data.items():
            self.set(key, value, ttl)
        return True
    
    def keys(self, pattern: str = "*") -> list:
        """获取匹配的 keys"""
        import fnmatch
        with self._lock:
            return fnmatch.filter(self._cache.keys(), pattern)
    
    def size(self) -> int:
        """获取缓存大小"""
        return len(self._cache)


class RedisCache(CacheBackend):
    """Redis 缓存后端"""
    
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0, password: str = None, prefix: str = "cache:"):
        self._prefix = prefix
        self._client = None
        self._connected = False
        
        try:
            import redis
            self._client = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=True,
                socket_connect_timeout=5
            )
            self._client.ping()
            self._connected = True
        except Exception:
            self._connected = False
    
    def _make_key(self, key: str) -> str:
        return f"{self._prefix}{key}"
    
    @property
    def is_connected(self) -> bool:
        return self._connected and self._client is not None
    
    def get(self, key: str) -> Optional[Any]:
        if not self.is_connected:
            return None
        
        try:
            value = self._client.get(self._make_key(key))
            if value is None:
                return None
            return json.loads(value)
        except Exception:
            return None
    
    def set(self, key: str, value: Any, ttl: int = -1) -> bool:
        if not self.is_connected:
            return False
        
        try:
            serialized = json.dumps(value)
            if ttl > 0:
                self._client.setex(self._make_key(key), ttl, serialized)
            else:
                self._client.set(self._make_key(key), serialized)
            return True
        except Exception:
            return False
    
    def delete(self, key: str) -> bool:
        if not self.is_connected:
            return False
        
        try:
            return self._client.delete(self._make_key(key)) > 0
        except Exception:
            return False
    
    def exists(self, key: str) -> bool:
        if not self.is_connected:
            return False
        
        try:
            return self._client.exists(self._make_key(key)) > 0
        except Exception:
            return False
    
    def clear(self) -> bool:
        if not self.is_connected:
            return False
        
        try:
            keys = self._client.keys(f"{self._prefix}*")
            if keys:
                self._client.delete(*keys)
            return True
        except Exception:
            return False
    
    def get_many(self, keys: list) -> Dict[str, Any]:
        if not self.is_connected:
            return {}
        
        try:
            full_keys = [self._make_key(k) for k in keys]
            values = self._client.mget(full_keys)
            result = {}
            for key, value in zip(keys, values):
                if value is not None:
                    try:
                        result[key] = json.loads(value)
                    except Exception:
                        pass
            return result
        except Exception:
            return {}
    
    def set_many(self, data: Dict[str, Any], ttl: int = -1) -> bool:
        if not self.is_connected:
            return False
        
        try:
            pipe = self._client.pipeline()
            for key, value in data.items():
                serialized = json.dumps(value)
                if ttl > 0:
                    pipe.setex(self._make_key(key), ttl, serialized)
                else:
                    pipe.set(self._make_key(key), serialized)
            pipe.execute()
            return True
        except Exception:
            return False
    
    def keys(self, pattern: str = "*") -> list:
        if not self.is_connected:
            return []
        
        try:
            full_pattern = self._make_key(pattern)
            keys = self._client.keys(full_pattern)
            prefix_len = len(self._prefix)
            return [k[prefix_len:] for k in keys]
        except Exception:
            return []
    
    def ttl(self, key: str) -> int:
        if not self.is_connected:
            return -1
        
        try:
            return self._client.ttl(self._make_key(key))
        except Exception:
            return -1


class CacheModule:
    """
    缓存模块
    提供统一的缓存接口，支持内存缓存和 Redis
    """
    
    def __init__(self, kernel):
        self.kernel = kernel
        self._memory = MemoryCache(max_size=1000)
        self._redis: Optional[RedisCache] = None
        self._backend = "memory"
        self._logger = kernel.get_logger("cache")
        self._logger.info("CacheModule initialized with memory backend")
    
    def set_backend(self, backend: str = "memory"):
        """设置缓存后端"""
        if backend == "redis":
            self._backend = "redis"
            self._logger.info("Switched to Redis backend")
        else:
            self._backend = "memory"
            self._logger.info("Switched to memory backend")
    
    def set_redis(self, host: str = "localhost", port: int = 6379, db: int = 0, password: str = None, prefix: str = "cache:"):
        """配置 Redis"""
        self._redis = RedisCache(host, port, db, password, prefix)
        if self._redis.is_connected:
            self._logger.info(f"Redis connected: {host}:{port}")
        else:
            self._logger.warning("Redis connection failed, falling back to memory")
    
    @property
    def backend(self) -> CacheBackend:
        """获取当前后端"""
        if self._backend == "redis" and self._redis and self._redis.is_connected:
            return self._redis
        return self._memory
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        return self.backend.get(key)
    
    def set(self, key: str, value: Any, ttl: int = -1) -> bool:
        """设置缓存"""
        return self.backend.set(key, value, ttl)
    
    def delete(self, key: str) -> bool:
        """删除缓存"""
        return self.backend.delete(key)
    
    def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        return self.backend.exists(key)
    
    def clear(self) -> bool:
        """清空缓存"""
        return self.backend.clear()
    
    def get_many(self, keys: list) -> Dict[str, Any]:
        """批量获取"""
        return self.backend.get_many(keys)
    
    def set_many(self, data: Dict[str, Any], ttl: int = -1) -> bool:
        """批量设置"""
        return self.backend.set_many(data, ttl)
    
    def keys(self, pattern: str = "*") -> list:
        """获取匹配的 keys"""
        return self.backend.keys(pattern)
    
    def memorize(self, ttl: int = 300):
        """装饰器：缓存函数结果"""
        def decorator(func: Callable):
            def wrapper(*args, **kwargs):
                key_parts = [func.__name__]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = hashlib.md5(":".join(key_parts).encode()).hexdigest()
                
                result = self.get(cache_key)
                if result is not None:
                    return result
                
                result = func(*args, **kwargs)
                self.set(cache_key, result, ttl)
                return result
            return wrapper
        return decorator
    
    def invalidate(self, pattern: str = "*"):
        """使匹配的缓存失效"""
        keys = self.keys(pattern)
        for key in keys:
            self.delete(key)
        return len(keys)
    
    def stop(self):
        """停止模块"""
        self._logger.info("CacheModule stopped")
