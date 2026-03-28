"""
Cache 模块测试
"""
import pytest
import time
from modules.cache import (
    CacheModule,
    MemoryCache,
    RedisCache,
    CacheBackend
)


class TestMemoryCache:
    """测试内存缓存"""

    def test_set_and_get(self):
        """测试设置和获取"""
        cache = MemoryCache()
        
        cache.set("key1", "value1")
        result = cache.get("key1")
        
        assert result == "value1"

    def test_get_nonexistent(self):
        """测试获取不存在的 key"""
        cache = MemoryCache()
        
        result = cache.get("nonexistent")
        
        assert result is None

    def test_delete(self):
        """测试删除"""
        cache = MemoryCache()
        
        cache.set("key1", "value1")
        result = cache.delete("key1")
        
        assert result is True
        assert cache.get("key1") is None

    def test_delete_nonexistent(self):
        """测试删除不存在的 key"""
        cache = MemoryCache()
        
        result = cache.delete("nonexistent")
        
        assert result is False

    def test_exists(self):
        """测试 exists"""
        cache = MemoryCache()
        
        cache.set("key1", "value1")
        
        assert cache.exists("key1") is True
        assert cache.exists("nonexistent") is False

    def test_clear(self):
        """测试清空"""
        cache = MemoryCache()
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.clear()
        
        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_ttl(self):
        """测试 TTL"""
        cache = MemoryCache()
        
        cache.set("key1", "value1", ttl=1)
        assert cache.get("key1") == "value1"
        
        time.sleep(1.1)
        assert cache.get("key1") is None

    def test_lru_eviction(self):
        """测试 LRU 淘汰"""
        cache = MemoryCache(max_size=3)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        cache.set("key4", "value4")
        
        assert cache.get("key1") is None
        assert cache.get("key4") == "value4"

    def test_lru_update(self):
        """测试 LRU 更新后不会被淘汰"""
        cache = MemoryCache(max_size=3)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        
        cache.get("key1")
        cache.set("key4", "value4")
        
        assert cache.get("key1") == "value1"
        assert cache.get("key2") is None

    def test_get_many(self):
        """测试批量获取"""
        cache = MemoryCache()
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        result = cache.get_many(["key1", "key2", "key3"])
        
        assert len(result) == 2
        assert result["key1"] == "value1"
        assert result["key2"] == "value2"

    def test_set_many(self):
        """测试批量设置"""
        cache = MemoryCache()
        
        cache.set_many({"key1": "value1", "key2": "value2"})
        
        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"

    def test_keys_pattern(self):
        """测试 keys 模式匹配"""
        cache = MemoryCache()
        
        cache.set("user:1", "data1")
        cache.set("user:2", "data2")
        cache.set("order:1", "data3")
        
        user_keys = cache.keys("user:*")
        
        assert len(user_keys) == 2


class TestCacheModule:
    """测试缓存模块"""

    def test_create_module(self, cache):
        """测试创建模块"""
        assert cache is not None
        assert cache.backend is not None

    def test_set_and_get(self, cache):
        """测试设置和获取"""
        cache.set("key1", "value1")
        
        result = cache.get("key1")
        
        assert result == "value1"

    def test_delete(self, cache):
        """测试删除"""
        cache.set("key1", "value1")
        cache.delete("key1")
        
        assert cache.get("key1") is None

    def test_clear(self, cache):
        """测试清空"""
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.clear()
        
        assert cache.get("key1") is None

    def test_exists(self, cache):
        """测试 exists"""
        cache.set("key1", "value1")
        
        assert cache.exists("key1") is True
        assert cache.exists("nonexistent") is False

    def test_get_many(self, cache):
        """测试批量获取"""
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        result = cache.get_many(["key1", "key2", "key3"])
        
        assert len(result) == 2

    def test_set_many(self, cache):
        """测试批量设置"""
        cache.set_many({"key1": "value1", "key2": "value2"})
        
        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"

    def test_invalidate(self, cache):
        """测试使缓存失效"""
        cache.set("user:1", "data1")
        cache.set("user:2", "data2")
        cache.set("order:1", "data3")
        
        count = cache.invalidate("user:*")
        
        assert count == 2
        assert cache.get("user:1") is None
        assert cache.get("order:1") == "data3"


class TestCacheModuleKernelIntegration:
    """测试 CacheModule 与 Kernel 集成"""

    def test_kernel_cache_property(self, running_kernel):
        """测试 kernel.cache 属性"""
        assert running_kernel.cache is not None
        assert running_kernel.cache.__class__.__name__ == "CacheModule"

    def test_cache_backend_is_memory(self, running_kernel):
        """测试默认后端是内存"""
        assert running_kernel.cache.backend.__class__.__name__ == "MemoryCache"


class TestCacheDecorator:
    """测试缓存装饰器"""

    def test_memorize_decorator(self, cache):
        """测试 memorize 装饰器"""
        call_count = 0
        
        @cache.memorize(ttl=10)
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        result1 = expensive_function(5)
        result2 = expensive_function(5)
        
        assert result1 == 10
        assert result2 == 10
        assert call_count == 1

    def test_memorize_different_args(self, cache):
        """测试不同参数不共享缓存"""
        call_count = 0
        
        @cache.memorize(ttl=10)
        def add(x, y):
            nonlocal call_count
            call_count += 1
            return x + y
        
        result1 = add(1, 2)
        result2 = add(2, 3)
        
        assert result1 == 3
        assert result2 == 5
        assert call_count == 2
