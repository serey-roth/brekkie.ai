import pytest
import pytest_asyncio
import asyncio
import json
from datetime import timedelta
from typing import Any

from fakeredis.aioredis import FakeRedis

from services.redis.redis_cache import RedisCache
from tests.utils.assert_deep_equal import assert_deep_equal


pytestmark = pytest.mark.asyncio


class DummyModel:
    def __init__(self, **kwargs): self.__dict__.update(kwargs)
    def __eq__(self, other): return isinstance(other, DummyModel) and self.__dict__ == other.__dict__


@pytest_asyncio.fixture
async def redis_cache(redis_client: FakeRedis) -> RedisCache:
    await redis_client.flushall()
    return RedisCache(redis_client)


class TestRedisCache:
    async def test_set_and_get_json(self, redis_cache: RedisCache):
        key = "test:json"
        data = {"id": "1", "value": "test"}
        await redis_cache.set_json(key, data)
        
        result = await redis_cache.get_json(key, dict)
        assert_deep_equal(result, data)


    async def test_set_json_with_ttl(self, redis_cache):
        key = "test:ttl"
        data = {"id": "2", "value": "temp"}
        await redis_cache.set_json(key, data, ttl=1)

        assert await redis_cache.get_json(key, dict) is not None
        await asyncio.sleep(1.5)
        assert await redis_cache.get_json(key, dict) is None
        
        
    async def test_set_and_get_json_with_model(self, redis_cache: RedisCache):
        key = "test:json:model"
        data = {"id": "1", "value": "test"}
        await redis_cache.set_json(key, data)
        
        result = await redis_cache.get_json(key, DummyModel)
        assert_deep_equal(result, DummyModel(**data))
        
        
    async def test_set_json_keep_ttl(self, redis_cache: RedisCache):
        key = "keep:ttl"
        data = {"id": "1", "value": "test"}
        await redis_cache.set_json(key, data, ttl=5)
        assert await redis_cache.get_json(key, dict) is not None
        await asyncio.sleep(1)
        await redis_cache.set_json(key, data, keep_ttl=True)
        await asyncio.sleep(6)
        assert await redis_cache.get_json(key, dict) is None
        
    
    async def test_fails_if_set_json_keep_ttl_with_ttl(self, redis_cache: RedisCache):
        key = "keep:ttl"
        data = {"id": "1", "value": "test"}
        with pytest.raises(ValueError):
            await redis_cache.set_json(key, data, ttl=5, keep_ttl=True)
            
        
    async def test_get_non_existent_key(self, redis_cache: RedisCache):
        key = "non:existent:key"
        result = await redis_cache.get_json(key, dict)
        assert result is None


    async def test_get_all_json_by_keys(self, redis_cache):
        keys = ["k1", "k2", "k3"]
        
        items = await redis_cache.get_all_json_by_keys(keys, DummyModel)
        assert len(items) == 0
        
        items = [{"id": k, "val": k.upper()} for k in keys]
        for key, item in zip(keys, items):
            await redis_cache.set_json(key, item)

        results = await redis_cache.get_all_json_by_keys(keys, DummyModel)
        assert len(results) == 3
        assert all(isinstance(r, DummyModel) for r in results)


    async def test_get_all_json_by_pattern(self, redis_cache):
        await redis_cache.set_json("p:1", {"id": "1"})
        await redis_cache.set_json("p:2", {"id": "2"})
        await redis_cache.set_json("p:3", {"id": "3"})

        results = await redis_cache.get_all_json_by_pattern("p:*", DummyModel)
        assert len(results) == 3
        assert all(isinstance(r, DummyModel) for r in results)


    async def test_exists(self, redis_cache: RedisCache):
        key = "exists:key"
        assert await redis_cache.exists(key) is False
        
        await redis_cache.set_json(key, {"id": "1", "value": "test"})
        assert await redis_cache.exists(key) is True


    async def test_delete(self, redis_cache):
        key = "delete:key"
        await redis_cache.set_json(key, {"id": "1", "value": "test"})
        assert await redis_cache.exists(key) is True
        
        await redis_cache.delete(key)
        
        assert await redis_cache.exists(key) is False


    async def test_incr_and_decr(self, redis_cache: RedisCache):
        key = "counter"
        val = await redis_cache.incr(key)
        assert val == 1
        val = await redis_cache.incr(key)
        assert val == 2
        val = await redis_cache.decr(key)
        assert val == 1


    async def test_delete_by_pattern(self, redis_cache: RedisCache):
        keys = ["1", "2", "3"]
        for key in keys:
            await redis_cache.set_json(f"p:{key}", {"id": key})
            
        assert await redis_cache.exists("p:1") is True
        assert await redis_cache.exists("p:2") is True 
        assert await redis_cache.exists("p:3") is True

        await redis_cache.delete_by_pattern("p:*")
        assert await redis_cache.exists("p:1") is False
        assert await redis_cache.exists("p:2") is False
        assert await redis_cache.exists("p:3") is False