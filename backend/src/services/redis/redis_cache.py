from typing import TypeVar, Generic, Type
from services.redis.redis_client import RedisClient
import json

T = TypeVar("T", bound=dict)

class RedisCache(Generic[T]):
    def __init__(self, redis_client: RedisClient):
        self.redis = redis_client
        
        
    async def set(self, key: str, value: str, ttl: int | None = None, keep_ttl: bool = False) -> None:
        if ttl is not None and keep_ttl:
            raise ValueError("ttl and keep_ttl cannot be used together")
        
        if keep_ttl:
            await self.redis.set(key, value, keepttl=True)
        elif ttl is not None:
            await self.redis.set(key, value, ex=ttl)
        else:
            await self.redis.set(key, value)
            
            
    async def get(self, key: str) -> str | None:
        return await self.redis.get(key)
        

    async def set_json(self, key: str, value: T, ttl: int | None = None, keep_ttl: bool = False) -> None:
        if ttl is not None and keep_ttl:
            raise ValueError("ttl and keep_ttl cannot be used together")
        
        json_value = json.dumps(value)
        if keep_ttl:
            await self.redis.set(key, json_value, keepttl=True) # redis will use the ttl from the previous value
        elif ttl is not None:
            await self.redis.set(key, json_value, ex=ttl) # redis will reset ttl when value is updated
        else:
            await self.redis.set(key, json_value)


    async def get_json(self, key: str, model: Type[T]) -> T | None:
        raw = await self.redis.get(key)
        if raw:
            parsed = json.loads(raw)
            return model(**parsed) if callable(model) else parsed  # model can be dict or pydantic class
        return None


    async def delete(self, key: str) -> None:
        await self.redis.delete(key)


    async def exists(self, key: str) -> bool:
        return await self.redis.exists(key) > 0


    async def incr(self, key: str) -> int:
        return await self.redis.incr(key)


    async def decr(self, key: str) -> int:
        return await self.redis.decr(key)
    
    
    async def get_all_json_by_keys(self, keys: list[str], model: Type[T]) -> list[T]:
        if not keys:
            return []
        values = await self.redis.mget(*keys)
        return [model(**json.loads(v)) for v in values if v]


    async def get_all_json_by_pattern(self, pattern: str, model: Type[T]) -> list[T]:
        cursor = 0
        keys = []

        while True:
            cursor, batch = await self.redis.scan(cursor=cursor, match=pattern, count=100)
            keys.extend(batch)
            if cursor == 0:
                break

        return await self.get_all_json_by_keys(keys, model)


    async def get_ttl(self, key: str) -> int | None:
        return await self.redis.ttl(key)
    
    
    async def delete_by_pattern(self, pattern: str) -> None:
        cursor = 0
        while True:
            cursor, batch = await self.redis.scan(cursor=cursor, match=pattern, count=100)
            if batch:
                await self.redis.delete(*batch)
            if cursor == 0:
                break
            
    
    async def expire(self, key: str, ttl: int) -> None:
        await self.redis.expire(key, ttl)
        