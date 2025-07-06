import pytest

from fakeredis import FakeRedis

from services.data_services.anonymous_access_rate_limiter import AnonymousAccessIpAddressRateLimiter


@pytest.fixture
def rate_limiter(redis_client: FakeRedis):
    return AnonymousAccessIpAddressRateLimiter(redis_client, 30, 3)


class TestAnonymousAccessIpAddressRateLimiter:
    def test_key_format(self, rate_limiter: AnonymousAccessIpAddressRateLimiter):
        assert rate_limiter._get_rate_limit_key("127.0.0.1") == "brekkie:anonymous_access:rate_limit:ip:127.0.0.1"
        

    @pytest.mark.asyncio
    async def test_is_rate_limited(self, rate_limiter: AnonymousAccessIpAddressRateLimiter):
        assert not await rate_limiter.is_rate_limited("127.0.0.1")
        
        await rate_limiter.increment("127.0.0.1")
        assert not await rate_limiter.is_rate_limited("127.0.0.1")
        
        await rate_limiter.increment("127.0.0.1")
        assert not await rate_limiter.is_rate_limited("127.0.0.1")
        
        await rate_limiter.increment("127.0.0.1")
        assert await rate_limiter.is_rate_limited("127.0.0.1")
        
        
    @pytest.mark.asyncio
    async def test_get_current_count(self, rate_limiter: AnonymousAccessIpAddressRateLimiter):
        assert await rate_limiter.get_current_count("127.0.0.1") == 0
        
        await rate_limiter.increment("127.0.0.1")
        assert await rate_limiter.get_current_count("127.0.0.1") == 1
        
        await rate_limiter.increment("127.0.0.1")
        assert await rate_limiter.get_current_count("127.0.0.1") == 2
        
        
    @pytest.mark.asyncio
    async def test_increment(self, rate_limiter: AnonymousAccessIpAddressRateLimiter, redis_client: FakeRedis):
        assert await redis_client.ttl("brekkie:anonymous_access:rate_limit:ip:127.0.0.1") == -2
        
        assert await rate_limiter.increment("127.0.0.1") == 1
        assert await redis_client.ttl("brekkie:anonymous_access:rate_limit:ip:127.0.0.1") == 30
        assert await rate_limiter.get_current_count("127.0.0.1") == 1
        
        assert await rate_limiter.increment("127.0.0.1") == 2
        assert await rate_limiter.get_current_count("127.0.0.1") == 2
        
        assert await rate_limiter.increment("127.0.0.1") == 3
        assert await rate_limiter.get_current_count("127.0.0.1") == 3
        
        

    @pytest.mark.asyncio
    async def test_clear(self, rate_limiter: AnonymousAccessIpAddressRateLimiter, redis_client: FakeRedis):
        assert await redis_client.ttl("brekkie:anonymous_access:rate_limit:ip:127.0.0.1") == -2
        
        await rate_limiter.increment("127.0.0.1")
        assert await redis_client.ttl("brekkie:anonymous_access:rate_limit:ip:127.0.0.1") == 30
        assert await rate_limiter.get_current_count("127.0.0.1") == 1
        
        await rate_limiter.clear("127.0.0.1")
        assert await redis_client.ttl("brekkie:anonymous_access:rate_limit:ip:127.0.0.1") == -2
        assert await rate_limiter.get_current_count("127.0.0.1") == 0