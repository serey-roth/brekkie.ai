import pytest
import asyncio

from fakeredis.aioredis import FakeRedis

from services.data_services.user_access_cache_service import UserAccessCacheService

from schemas.user_access import UserAccessData

from tests.utils.assert_deep_equal import assert_deep_equal


@pytest.fixture
def user_access_cache_service(redis_client: FakeRedis):
    return UserAccessCacheService(redis_client, ttl=30) # 30 seconds for testing


@pytest.fixture
def sample_access_token():
    return "test_access_token"


@pytest.fixture
def sample_user_id():
    return "test_user_id"


@pytest.fixture
def sample_anonymous_user_access_data(sample_access_token: str, sample_user_id: str):
    return UserAccessData(
        access_token=sample_access_token,
        user_id=sample_user_id,
        email=None,
        name=None,
        is_authenticated=False,
        user_message_count=0,
    )
    
@pytest.fixture
def sample_authenticated_user_access_data(sample_access_token: str, sample_user_id: str):
    return UserAccessData(
        access_token=sample_access_token,
        user_id=sample_user_id,
        email="test@test.com",
        name="test",
        is_authenticated=True,
        user_message_count=10,
    )


class TestUserAccessCacheService:
    def test_get_user_access_key(self, user_access_cache_service: UserAccessCacheService):
        user_access_key = user_access_cache_service._get_user_access_key("test_access_token")
        assert user_access_key == "brekkie:user_access:test_access_token"
        
        
    @pytest.mark.asyncio
    async def test_set_and_get_user_access_data(self, user_access_cache_service: UserAccessCacheService, sample_anonymous_user_access_data: UserAccessData, sample_access_token: str):
        await user_access_cache_service.set_user_access(sample_access_token, sample_anonymous_user_access_data)
        user_access_data = await user_access_cache_service.get_user_access(sample_access_token)
        assert_deep_equal(user_access_data, sample_anonymous_user_access_data)
        

    @pytest.mark.asyncio
    async def test_set_and_get_user_access_data_with_ttl(self, user_access_cache_service: UserAccessCacheService, sample_anonymous_user_access_data: UserAccessData, sample_access_token: str):
        await user_access_cache_service.set_user_access(sample_access_token, sample_anonymous_user_access_data, ttl=1)
        user_access_data = await user_access_cache_service.get_user_access(sample_access_token)
        assert_deep_equal(user_access_data, sample_anonymous_user_access_data)
        
        await asyncio.sleep(1.1)
        
        user_access_data = await user_access_cache_service.get_user_access(sample_access_token)
        assert user_access_data is None
        
        
    @pytest.mark.asyncio
    async def test_create_user_access(self, user_access_cache_service: UserAccessCacheService, sample_access_token: str, sample_user_id: str):
        user_access_data = await user_access_cache_service.create_user_access(sample_access_token, sample_user_id, email="test@test.com", name="test", is_authenticated=True)
        assert_deep_equal(user_access_data, UserAccessData(
            access_token=sample_access_token,
            user_id=sample_user_id,
            email="test@test.com",
            name="test",
            is_authenticated=False,
            user_message_count=0,
        ))
        
        
    @pytest.mark.asyncio
    async def test_create_user_access_with_ttl(self, user_access_cache_service: UserAccessCacheService, sample_access_token: str, sample_user_id: str):
        user_access_data = await user_access_cache_service.create_user_access(sample_access_token, sample_user_id, email="test@test.com", name="test", is_authenticated=True, ttl=1)
        assert_deep_equal(user_access_data, UserAccessData(
            access_token=sample_access_token,
            user_id=sample_user_id,
            email="test@test.com",
            name="test",
            is_authenticated=False,
            user_message_count=0,
        ))
        
        await asyncio.sleep(1.1)
        
        user_access_data = await user_access_cache_service.get_user_access(sample_access_token)
        assert user_access_data is None
        
        
    @pytest.mark.asyncio
    async def test_create_anonymous_access(self, user_access_cache_service: UserAccessCacheService):
        user_access_data = await user_access_cache_service.create_anonymous_access()
        assert user_access_data.access_token is not None
        assert user_access_data.user_id is not None
        assert user_access_data.is_authenticated is False
        assert user_access_data.user_message_count == 0
        
        user_access_data = await user_access_cache_service.get_user_access(user_access_data.access_token)
        assert_deep_equal(user_access_data, user_access_data)
        
        
    @pytest.mark.asyncio
    async def test_promote_to_authenticated(self, user_access_cache_service: UserAccessCacheService, sample_access_token: str, sample_user_id: str, sample_anonymous_user_access_data: UserAccessData):
        await user_access_cache_service.set_user_access(sample_access_token, sample_anonymous_user_access_data)
        await user_access_cache_service.promote_to_authenticated(sample_access_token, sample_user_id, "test@test.com", "test")
        user_access_data = await user_access_cache_service.get_user_access(sample_access_token)
        assert_deep_equal(user_access_data, UserAccessData(
            access_token=sample_access_token,
            user_id=sample_user_id,
            email="test@test.com",
            name="test",
            is_authenticated=True,
            user_message_count=0,
        ))
        
        
    @pytest.mark.asyncio
    async def test_increment_user_message_count(self, user_access_cache_service: UserAccessCacheService, sample_access_token: str, sample_user_id: str, sample_anonymous_user_access_data: UserAccessData):
        await user_access_cache_service.set_user_access(sample_access_token, sample_anonymous_user_access_data)
        await user_access_cache_service.increment_user_message_count(sample_access_token)
        user_access_data = await user_access_cache_service.get_user_access(sample_access_token)
        assert_deep_equal(user_access_data, UserAccessData(
            access_token=sample_access_token,
            user_id=sample_user_id,
            email=None,
            name=None,
            is_authenticated=False,
            user_message_count=1,
        ))
        
        
    @pytest.mark.asyncio
    async def test_increment_user_message_count_for_non_existent_user_access(self, user_access_cache_service: UserAccessCacheService, sample_access_token: str):
        with pytest.raises(ValueError):
            await user_access_cache_service.increment_user_message_count(sample_access_token)
            
            
    @pytest.mark.asyncio
    async def test_is_authenticated(self, user_access_cache_service: UserAccessCacheService, sample_access_token: str, sample_user_id: str, sample_anonymous_user_access_data: UserAccessData):
        await user_access_cache_service.set_user_access(sample_access_token, sample_anonymous_user_access_data)
        assert not await user_access_cache_service.is_authenticated(sample_access_token)
        
        await user_access_cache_service.promote_to_authenticated(sample_access_token, sample_user_id, "test@test.com", "test")
        assert await user_access_cache_service.is_authenticated(sample_access_token)
        
        
    @pytest.mark.asyncio
    async def test_is_authenticated_for_non_existent_user_access(self, user_access_cache_service: UserAccessCacheService, sample_access_token: str):
        assert not await user_access_cache_service.is_authenticated(sample_access_token)
        

    @pytest.mark.asyncio
    async def test_is_expired(self, user_access_cache_service: UserAccessCacheService, sample_access_token: str, sample_user_id: str, sample_anonymous_user_access_data: UserAccessData):
        await user_access_cache_service.set_user_access(sample_access_token, sample_anonymous_user_access_data, ttl=1)
        assert not await user_access_cache_service.is_expired(sample_access_token)
        
        await asyncio.sleep(1.1)
        
        assert await user_access_cache_service.is_expired(sample_access_token)
    
        
        
        
        
    
    
    
        
        
        
        
        