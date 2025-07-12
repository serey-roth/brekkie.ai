import pytest

from fakeredis import FakeRedis

from services.data_services.ip_address_rate_limiter import IpAddressRateLimiter, IpAddressRateLimitConfig


@pytest.fixture
def rate_limiter(redis_client: FakeRedis):
    return IpAddressRateLimiter(redis_client, IpAddressRateLimitConfig(ttl=30, anonymous_access_limit=3, violation_limit=1)) # type: ignore


class TestIpAddressRateLimiter:
    def test_key_format(self, rate_limiter: IpAddressRateLimiter):
        assert rate_limiter._get_rate_limit_key("127.0.0.1") == "brekkie:rate_limit:ip:127.0.0.1"
        

    @pytest.mark.asyncio
    async def test_is_rate_limited(self, rate_limiter: IpAddressRateLimiter):
        assert not await rate_limiter.is_anonymous_access_rate_limited("127.0.0.1")
        
        await rate_limiter.increment_anonymous_access_count("127.0.0.1")
        assert not await rate_limiter.is_anonymous_access_rate_limited("127.0.0.1")
        
        await rate_limiter.increment_anonymous_access_count("127.0.0.1")
        assert not await rate_limiter.is_anonymous_access_rate_limited("127.0.0.1")
        
        await rate_limiter.increment_anonymous_access_count("127.0.0.1")
        assert await rate_limiter.is_anonymous_access_rate_limited("127.0.0.1")
        
        
    @pytest.mark.asyncio
    async def test_get_current_count(self, rate_limiter: IpAddressRateLimiter):
        assert await rate_limiter.get_current_anonymous_access_count("127.0.0.1") == 0
        
        await rate_limiter.increment_anonymous_access_count("127.0.0.1")
        assert await rate_limiter.get_current_anonymous_access_count("127.0.0.1") == 1
        
        await rate_limiter.increment_anonymous_access_count("127.0.0.1")
        assert await rate_limiter.get_current_anonymous_access_count("127.0.0.1") == 2
        
        
    @pytest.mark.asyncio
    async def test_increment(self, rate_limiter: IpAddressRateLimiter, redis_client: FakeRedis):
        key = rate_limiter._get_rate_limit_key("127.0.0.1")
        assert await redis_client.ttl(key) == -2
        
        assert await rate_limiter.increment_anonymous_access_count("127.0.0.1") == 1
        assert await redis_client.ttl(key) == 30
        assert await rate_limiter.get_current_anonymous_access_count("127.0.0.1") == 1
        
        assert await rate_limiter.increment_anonymous_access_count("127.0.0.1") == 2
        assert await rate_limiter.get_current_anonymous_access_count("127.0.0.1") == 2
        
        assert await rate_limiter.increment_anonymous_access_count("127.0.0.1") == 3
        assert await rate_limiter.get_current_anonymous_access_count("127.0.0.1") == 3
        
        

    @pytest.mark.asyncio
    async def test_clear(self, rate_limiter: IpAddressRateLimiter, redis_client: FakeRedis):
        key = rate_limiter._get_rate_limit_key("127.0.0.1")
        assert await redis_client.ttl(key) == -2
        
        await rate_limiter.increment_anonymous_access_count("127.0.0.1")
        assert await redis_client.ttl(key) == 30
        assert await rate_limiter.get_current_anonymous_access_count("127.0.0.1") == 1
        
        await rate_limiter.clear("127.0.0.1")
        assert await redis_client.ttl("brekkie:rate_limit:ip:127.0.0.1") == -2
        assert await rate_limiter.get_current_anonymous_access_count("127.0.0.1") == 0