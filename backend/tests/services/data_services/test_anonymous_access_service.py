from datetime import datetime, timezone
import pytest
from unittest.mock import patch

from fakeredis import FakeRedis

from schemas.api_error import RateLimitError
from schemas.user_access import UserAccessData

from services.data_services.anonymous_access_rate_limiter import AnonymousAccessIpAddressRateLimiter
from services.data_services.anonymous_access_service import AnonymousAccessService
from services.data_services.user_access_cache_service import UserAccessCacheService

from utils.date_utils import to_utc_isostring

from tests.test_helpers.assert_deep_equal import assert_deep_equal


@pytest.fixture
def user_access_cache_service(redis_client: FakeRedis):
    return UserAccessCacheService(redis_client, 30)


@pytest.fixture
def rate_limiter(redis_client: FakeRedis):
    return AnonymousAccessIpAddressRateLimiter(redis_client, 30, 3)


@pytest.fixture
def anonymous_access_service(user_access_cache_service: UserAccessCacheService, rate_limiter: AnonymousAccessIpAddressRateLimiter):
    return AnonymousAccessService(user_access_cache_service, rate_limiter)


class TestAnonymousAccessService:
    @pytest.mark.asyncio
    async def test_existing_user_access(self, anonymous_access_service: AnonymousAccessService, user_access_cache_service: UserAccessCacheService):
        now = to_utc_isostring(datetime.now(timezone.utc))
        access_token = "sample_access_token"
        user_id = "sample_user_id"
        await user_access_cache_service.set_user_access(access_token, UserAccessData(
            access_token=access_token,
            user_id=user_id,
            email=None,
            name=None,
            is_authenticated=False,
            user_message_count=0,
            created_at=now,
            updated_at=now,
        ))
        
        user_access_data = await anonymous_access_service.get_or_create_user_access("127.0.0.1", access_token)
        assert_deep_equal(user_access_data, UserAccessData(
            access_token=access_token,
            user_id=user_id,
            email=None,
            name=None,
            is_authenticated=False,
            user_message_count=0,
            created_at=now,
            updated_at=now,
        ))
        
        
    @pytest.mark.asyncio
    async def test_no_token_and_under_rate_limit(self, anonymous_access_service: AnonymousAccessService, user_access_cache_service: UserAccessCacheService, rate_limiter: AnonymousAccessIpAddressRateLimiter):
        ip_address = "127.0.0.1"
        with patch("services.data_services.user_access_cache_service.datetime") as mock_datetime:
            now = datetime.now(timezone.utc)
            mock_datetime.now.return_value = now
            
            user_access_data = await anonymous_access_service.get_or_create_user_access(ip_address)
            assert user_access_data.access_token is not None
            assert user_access_data.user_id is not None
            assert user_access_data.email is None
            assert user_access_data.name is None
            assert user_access_data.is_authenticated is False
            assert user_access_data.user_message_count == 0
            assert user_access_data.created_at == to_utc_isostring(now)
            assert user_access_data.updated_at == to_utc_isostring(now)
            
            assert not await rate_limiter.is_rate_limited(ip_address)
            assert await rate_limiter.get_current_count(ip_address) == 1
            
            
    @pytest.mark.asyncio
    async def test_no_token_and_over_rate_limit(self, anonymous_access_service: AnonymousAccessService, user_access_cache_service: UserAccessCacheService, rate_limiter: AnonymousAccessIpAddressRateLimiter):
        ip_address = "127.0.0.1"
        await rate_limiter.increment(ip_address)
        await rate_limiter.increment(ip_address)
        await rate_limiter.increment(ip_address)
        
        with pytest.raises(RateLimitError):
            await anonymous_access_service.get_or_create_user_access(ip_address)
            
        
    @pytest.mark.asyncio
    async def test_invalid_token_and_under_rate_limit(self, anonymous_access_service: AnonymousAccessService, user_access_cache_service: UserAccessCacheService, rate_limiter: AnonymousAccessIpAddressRateLimiter):
        ip_address = "127.0.0.1"
        access_token = "sample_access_token"
        
        with patch("services.data_services.user_access_cache_service.datetime") as mock_datetime:
            now = datetime.now(timezone.utc)
            mock_datetime.now.return_value = now
            
            user_access_data = await anonymous_access_service.get_or_create_user_access(ip_address, access_token)
            assert user_access_data.access_token is not None
            assert user_access_data.user_id is not None
            assert user_access_data.email is None
            assert user_access_data.name is None
            assert user_access_data.is_authenticated is False
            assert user_access_data.user_message_count == 0
            assert user_access_data.created_at == to_utc_isostring(now)
            assert user_access_data.updated_at == to_utc_isostring(now)
            
            assert not await rate_limiter.is_rate_limited(ip_address)
            assert await rate_limiter.get_current_count(ip_address) == 1
        
        
    @pytest.mark.asyncio
    async def test_invalid_token_and_over_rate_limit(self, anonymous_access_service: AnonymousAccessService, user_access_cache_service: UserAccessCacheService, rate_limiter: AnonymousAccessIpAddressRateLimiter):
        ip_address = "127.0.0.1"
        access_token = "sample_access_token"
        
        await rate_limiter.increment(ip_address)
        await rate_limiter.increment(ip_address)
        await rate_limiter.increment(ip_address)
        
        with pytest.raises(RateLimitError):
            await anonymous_access_service.get_or_create_user_access(ip_address, access_token)
            
            