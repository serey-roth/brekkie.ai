from datetime import datetime, timezone
import pytest
from unittest.mock import patch

from fakeredis import FakeRedis

from schemas.api_error import RateLimitError
from schemas.user_access import UserAccessData

from services.data_services.ip_address_rate_limiter import IpAddressRateLimiter, IpAddressRateLimitConfig
from services.data_services.anonymous_access_service import AnonymousAccessService
from services.data_services.user_access_cache_service import UserAccessCacheService

from utils.date_utils import to_utc_isostring

from tests.test_helpers.assert_deep_equal import assert_deep_equal


@pytest.fixture
def user_access_cache_service(redis_client: FakeRedis):
    return UserAccessCacheService(redis_client, 30) # type: ignore


@pytest.fixture
def ip_address_rate_limiter(redis_client: FakeRedis):
    return IpAddressRateLimiter(redis_client, IpAddressRateLimitConfig(ttl=30, anonymous_access_limit=1, violation_limit=1)) # type: ignore


@pytest.fixture
def anonymous_access_service(user_access_cache_service: UserAccessCacheService, ip_address_rate_limiter: IpAddressRateLimiter):
    return AnonymousAccessService(user_access_cache_service, ip_rate_limiter=ip_address_rate_limiter)


@pytest.fixture
def sample_ip_address():
    return "192.168.1.100"


class TestAnonymousAccessService:
    @pytest.mark.asyncio
    async def test_existing_user_access(self, anonymous_access_service: AnonymousAccessService, user_access_cache_service: UserAccessCacheService, sample_ip_address: str):
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
            ip_address=sample_ip_address,
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
            ip_address=sample_ip_address,
        ))
        
        
    @pytest.mark.asyncio
    async def test_no_token_and_under_rate_limit(self, anonymous_access_service: AnonymousAccessService, user_access_cache_service: UserAccessCacheService, ip_address_rate_limiter: IpAddressRateLimiter, sample_ip_address: str):
        with patch("services.data_services.user_access_cache_service.datetime") as mock_datetime:
            now = datetime.now(timezone.utc)
            mock_datetime.now.return_value = now
            
            user_access_data = await anonymous_access_service.get_or_create_user_access(sample_ip_address)
            assert user_access_data.access_token is not None
            assert user_access_data.user_id is not None
            assert user_access_data.email is None
            assert user_access_data.name is None
            assert user_access_data.is_authenticated is False
            assert user_access_data.user_message_count == 0
            assert user_access_data.created_at == to_utc_isostring(now)
            assert user_access_data.updated_at == to_utc_isostring(now)
            assert user_access_data.ip_address == sample_ip_address
            
            # After the call, the rate limiter should be at the limit (1)
            assert await ip_address_rate_limiter.is_anonymous_access_rate_limited(sample_ip_address)
            assert await ip_address_rate_limiter.get_current_anonymous_access_count(sample_ip_address) == 1
            
            
    @pytest.mark.asyncio
    async def test_no_token_and_over_rate_limit(self, anonymous_access_service: AnonymousAccessService, user_access_cache_service: UserAccessCacheService, ip_address_rate_limiter: IpAddressRateLimiter, sample_ip_address: str):
        await ip_address_rate_limiter.increment_anonymous_access_count(sample_ip_address)
        await ip_address_rate_limiter.increment_anonymous_access_count(sample_ip_address)
        
        with pytest.raises(RateLimitError):
            await anonymous_access_service.get_or_create_user_access(sample_ip_address)
            
        await ip_address_rate_limiter.clear(sample_ip_address)
        
    @pytest.mark.asyncio
    async def test_invalid_token_and_under_rate_limit(self, anonymous_access_service: AnonymousAccessService, user_access_cache_service: UserAccessCacheService, ip_address_rate_limiter: IpAddressRateLimiter):
        access_token = "sample_access_token"
        ip_address = "127.0.0.1"
        
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
            assert user_access_data.ip_address == ip_address
            
            # After the call, the rate limiter should be at the limit (1)
            assert await ip_address_rate_limiter.is_anonymous_access_rate_limited(ip_address)
            assert await ip_address_rate_limiter.get_current_anonymous_access_count(ip_address) == 1
            
            await ip_address_rate_limiter.clear(ip_address)
        
        
    @pytest.mark.asyncio
    async def test_invalid_token_and_over_rate_limit_with_token(self, anonymous_access_service: AnonymousAccessService, ip_address_rate_limiter: IpAddressRateLimiter):
        access_token = "sample_access_token"
        
        await ip_address_rate_limiter.increment_anonymous_access_count("127.0.0.1")
        await ip_address_rate_limiter.increment_anonymous_access_count("127.0.0.1")
        
        with pytest.raises(RateLimitError):
            await anonymous_access_service.get_or_create_user_access("127.0.0.1", access_token)
            
        await ip_address_rate_limiter.clear("127.0.0.1")