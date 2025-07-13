from pydantic import BaseModel

from services.redis.redis_client import RedisClient
from services.redis.redis_cache import RedisCache


class IpAddressRateLimitData(BaseModel):
    ip_address: str
    anonymous_access_count: int
    violation_count: int


class IpAddressRateLimitConfig(BaseModel):
    ttl: int
    anonymous_access_limit: int
    violation_limit: int


class IpAddressRateLimiter:
    def __init__(self, redis_client: RedisClient, config: IpAddressRateLimitConfig):
        self.redis_cache = RedisCache[IpAddressRateLimitData](redis_client)
        self.config = config

    def _get_rate_limit_key(self, ip_address: str) -> str:
        return f"brekkie:rate_limit:ip:{ip_address}"

    async def set_rate_limit_data(
        self,
        ip_address: str,
        data: IpAddressRateLimitData,
        ttl: int | None = None,
        keep_ttl: bool = False,
    ) -> None:
        if keep_ttl:
            set_ttl = None
        else:
            set_ttl = ttl if ttl is not None else self.config.ttl
        await self.redis_cache.set_json(
            self._get_rate_limit_key(ip_address), data, set_ttl, keep_ttl
        )

    async def is_anonymous_access_rate_limited(self, ip_address: str) -> bool:
        current_data = await self.redis_cache.get_json(
            self._get_rate_limit_key(ip_address), IpAddressRateLimitData
        )
        return (
            current_data is not None
            and current_data.anonymous_access_count >= self.config.anonymous_access_limit
        )

    async def is_violation_rate_limited(self, ip_address: str) -> bool:
        current_data = await self.redis_cache.get_json(
            self._get_rate_limit_key(ip_address), IpAddressRateLimitData
        )
        return (
            current_data is not None and current_data.violation_count >= self.config.violation_limit
        )

    async def get_current_data(self, ip_address: str) -> IpAddressRateLimitData | None:
        return await self.redis_cache.get_json(
            self._get_rate_limit_key(ip_address), IpAddressRateLimitData
        )

    async def get_current_anonymous_access_count(self, ip_address: str) -> int:
        current_data = await self.redis_cache.get_json(
            self._get_rate_limit_key(ip_address), IpAddressRateLimitData
        )
        return current_data.anonymous_access_count if current_data is not None else 0

    async def get_current_violation_count(self, ip_address: str) -> int:
        current_data = await self.redis_cache.get_json(
            self._get_rate_limit_key(ip_address), IpAddressRateLimitData
        )
        return current_data.violation_count if current_data is not None else 0

    async def increment_anonymous_access_count(self, ip_address: str) -> int:
        current_data = await self.redis_cache.get_json(
            self._get_rate_limit_key(ip_address), IpAddressRateLimitData
        )
        if current_data is None:
            current_data = IpAddressRateLimitData(
                ip_address=ip_address, anonymous_access_count=0, violation_count=0
            )
        current_data.anonymous_access_count += 1
        await self.set_rate_limit_data(ip_address, current_data)
        return current_data.anonymous_access_count

    async def increment_violation_count(self, ip_address: str) -> int:
        current_data = await self.redis_cache.get_json(
            self._get_rate_limit_key(ip_address), IpAddressRateLimitData
        )
        if current_data is None:
            current_data = IpAddressRateLimitData(
                ip_address=ip_address, anonymous_access_count=0, violation_count=0
            )
        current_data.violation_count += 1
        await self.set_rate_limit_data(ip_address, current_data)
        return current_data.violation_count

    async def clear(self, ip_address: str) -> None:
        await self.redis_cache.delete(self._get_rate_limit_key(ip_address))
