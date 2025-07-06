from services.redis.redis_client import RedisClient
from services.redis.redis_cache import RedisCache


class AnonymousAccessIpAddressRateLimiter:
    def __init__(self, redis_client: RedisClient, ttl: int, limit: int):
        self.redis_cache = RedisCache[str](redis_client)
        self.ttl = ttl
        self.limit = limit
        
    
    def _get_rate_limit_key(self, ip_address: str) -> str:
        return f"brekkie:anonymous_access:rate_limit:ip:{ip_address}"
    
    
    async def is_rate_limited(self, ip_address: str) -> bool:
        current_count = await self.redis_cache.get(self._get_rate_limit_key(ip_address))
        return current_count is not None and int(current_count) >= self.limit
    
    
    async def get_current_count(self, ip_address: str) -> int:
        current_count = await self.redis_cache.get(self._get_rate_limit_key(ip_address))
        return int(current_count) if current_count is not None else 0

        
    async def increment(self, ip_address: str) -> int:
        key = self._get_rate_limit_key(ip_address)
        count = await self.redis_cache.incr(key)
        if count == 1:
            await self.redis_cache.expire(key, self.ttl)
        return count
    
    
    async def clear(self, ip_address: str) -> None:
        await self.redis_cache.delete(self._get_rate_limit_key(ip_address))
