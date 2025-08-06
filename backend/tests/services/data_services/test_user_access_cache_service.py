import pytest
import asyncio
from datetime import datetime, timezone

from fakeredis.aioredis import FakeRedis

from services.data_services.user_access_cache_service import UserAccessCacheService

from schemas.user_access import UserAccess
from utils.date_utils import to_utc_isostring

from tests.test_helpers.assert_deep_equal import assert_deep_equal


@pytest.fixture
def user_access_cache_service(redis_client: FakeRedis) -> UserAccessCacheService:
    return UserAccessCacheService(redis_client, ttl=30)  # 30 seconds for testing


@pytest.fixture
def sample_access_token() -> str:
    return "test_access_token"


@pytest.fixture
def sample_user_id() -> str:
    return "test_user_id"


@pytest.fixture
def sample_created_at() -> str:
    result = to_utc_isostring(datetime.now(timezone.utc))
    return str(result)


@pytest.fixture
def sample_updated_at() -> str:
    result = to_utc_isostring(datetime.now(timezone.utc))
    return str(result)


@pytest.fixture
def sample_ip_address() -> str:
    return "192.168.1.100"


@pytest.fixture
def sample_anonymous_user_access(
    sample_access_token: str,
    sample_user_id: str,
    sample_created_at: str,
    sample_updated_at: str,
    sample_ip_address: str,
) -> UserAccess:
    return UserAccess(
        access_token=sample_access_token,
        user_id=sample_user_id,
        is_authenticated=False,
        user_message_count=0,
        created_at=sample_created_at,
        updated_at=sample_updated_at,
        ip_address=sample_ip_address,
    )


@pytest.fixture
def sample_authenticated_user_access(
    sample_access_token: str, sample_user_id: str, sample_created_at: str, sample_updated_at: str
) -> UserAccess:
    return UserAccess(
        access_token=sample_access_token,
        user_id=sample_user_id,
        is_authenticated=True,
        user_message_count=10,
        created_at=sample_created_at,
        updated_at=sample_updated_at,
    )


class TestGetAndSetUserAccess:
    def test_get_user_access_key(self, user_access_cache_service: UserAccessCacheService) -> None:
        user_access_key = user_access_cache_service._get_user_access_key("test_access_token")
        assert user_access_key == "brekkie:user_access:test_access_token"

    @pytest.mark.asyncio
    async def test_set_and_get_user_access(
        self,
        user_access_cache_service: UserAccessCacheService,
        sample_anonymous_user_access: UserAccess,
        sample_access_token: str,
    ) -> None:
        await user_access_cache_service.set_user_access(
            sample_access_token, sample_anonymous_user_access
        )
        user_access = await user_access_cache_service.get_user_access(sample_access_token)
        assert_deep_equal(user_access, sample_anonymous_user_access)

    @pytest.mark.asyncio
    async def test_set_and_get_user_access_with_ttl(
        self,
        user_access_cache_service: UserAccessCacheService,
        sample_anonymous_user_access: UserAccess,
        sample_access_token: str,
    ) -> None:
        await user_access_cache_service.set_user_access(
            sample_access_token, sample_anonymous_user_access, ttl=1
        )
        user_access = await user_access_cache_service.get_user_access(sample_access_token)
        assert_deep_equal(user_access, sample_anonymous_user_access)

        await asyncio.sleep(1.1)

        user_access = await user_access_cache_service.get_user_access(sample_access_token)
        assert user_access is None


class TestCreateUserAccess:
    @pytest.mark.asyncio
    async def test_create_user_access(
        self,
        user_access_cache_service: UserAccessCacheService,
        sample_access_token: str,
        sample_user_id: str,
        sample_created_at: str,
        sample_updated_at: str,
        sample_ip_address: str,
    ) -> None:
        user_access = await user_access_cache_service.create_user_access(
            sample_access_token,
            sample_user_id,
            is_authenticated=True,
            created_at=sample_created_at,
            updated_at=sample_updated_at,
            ip_address=sample_ip_address,
        )
        assert_deep_equal(
            user_access,
            UserAccess(
                access_token=sample_access_token,
                user_id=sample_user_id,
                is_authenticated=True,
                user_message_count=0,
                created_at=sample_created_at,
                updated_at=sample_updated_at,
                ip_address=sample_ip_address,
            ),
        )

    @pytest.mark.asyncio
    async def test_create_user_access_with_ttl(
        self,
        user_access_cache_service: UserAccessCacheService,
        sample_access_token: str,
        sample_user_id: str,
        sample_created_at: str,
        sample_updated_at: str,
        sample_ip_address: str,
    ) -> None:
        user_access = await user_access_cache_service.create_user_access(
            sample_access_token,
            sample_user_id,
            is_authenticated=True,
            created_at=sample_created_at,
            updated_at=sample_updated_at,
            ip_address=sample_ip_address,
            ttl=1,
        )
        assert_deep_equal(
            user_access,
            UserAccess(
                access_token=sample_access_token,
                user_id=sample_user_id,
                is_authenticated=True,
                user_message_count=0,
                created_at=sample_created_at,
                updated_at=sample_updated_at,
                ip_address=sample_ip_address,
            ),
        )

        await asyncio.sleep(1.1)

        user_access = await user_access_cache_service.get_user_access(sample_access_token)
        assert user_access is None

    @pytest.mark.asyncio
    async def test_create_anonymous_access(
        self,
        user_access_cache_service: UserAccessCacheService,
        sample_access_token: str,
        sample_user_id: str,
        sample_created_at: str,
        sample_updated_at: str,
        sample_ip_address: str,
    ) -> None:
        user_access = await user_access_cache_service.create_user_access(
            sample_access_token,
            sample_user_id,
            is_authenticated=False,
            created_at=sample_created_at,
            updated_at=sample_updated_at,
            ip_address=sample_ip_address,
        )
        assert user_access.access_token is not None
        assert user_access.user_id is not None
        assert user_access.is_authenticated is False
        assert user_access.user_message_count == 0
        assert user_access.created_at is not None
        assert user_access.updated_at is not None
        assert user_access.ip_address == sample_ip_address

        user_access = await user_access_cache_service.get_user_access(user_access.access_token)
        assert_deep_equal(user_access, user_access)

    @pytest.mark.asyncio
    async def test_create_authenticated_access(
        self,
        user_access_cache_service: UserAccessCacheService,
        sample_access_token: str,
        sample_user_id: str,
        sample_created_at: str,
        sample_ip_address: str,
    ) -> None:
        updated_at = to_utc_isostring(datetime.now(timezone.utc))
        await user_access_cache_service.create_user_access(
            sample_access_token,
            sample_user_id,
            is_authenticated=True,
            created_at=sample_created_at,
            updated_at=updated_at,
            ip_address=sample_ip_address,
        )

        user_access = await user_access_cache_service.get_user_access(sample_access_token)
        assert_deep_equal(
            user_access,
            UserAccess(
                access_token=sample_access_token,
                user_id=sample_user_id,
                is_authenticated=True,
                user_message_count=0,
                created_at=sample_created_at,
                updated_at=updated_at,
                ip_address=sample_ip_address,
            ),
        )


class TestIncrementUserMessageCount:
    @pytest.mark.asyncio
    async def test_increment_user_message_count(
        self,
        user_access_cache_service: UserAccessCacheService,
        sample_access_token: str,
        sample_user_id: str,
        sample_created_at: str,
        sample_updated_at: str,
        sample_anonymous_user_access: UserAccess,
        sample_ip_address: str,
    ) -> None:
        await user_access_cache_service.set_user_access(
            sample_access_token, sample_anonymous_user_access
        )
        user_access = await user_access_cache_service.increment_user_message_count(
            sample_access_token
        )
        assert_deep_equal(
            user_access,
            UserAccess(
                access_token=sample_access_token,
                user_id=sample_user_id,
                is_authenticated=False,
                user_message_count=1,
                created_at=sample_created_at,
                updated_at=sample_updated_at,
                ip_address=sample_ip_address,
            ),
        )

    @pytest.mark.asyncio
    async def test_increment_user_message_count_for_non_existent_user_access(
        self, user_access_cache_service: UserAccessCacheService, sample_access_token: str
    ) -> None:
        with pytest.raises(ValueError):
            await user_access_cache_service.increment_user_message_count(sample_access_token)

    @pytest.mark.asyncio
    async def test_is_authenticated(
        self,
        user_access_cache_service: UserAccessCacheService,
        sample_access_token: str,
        sample_anonymous_user_access: UserAccess,
        sample_authenticated_user_access: UserAccess,
    ) -> None:
        await user_access_cache_service.set_user_access(
            sample_access_token, sample_anonymous_user_access
        )
        assert not await user_access_cache_service.is_authenticated(sample_access_token)

        await user_access_cache_service.set_user_access(
            sample_access_token, sample_authenticated_user_access
        )
        assert await user_access_cache_service.is_authenticated(sample_access_token)

    @pytest.mark.asyncio
    async def test_is_authenticated_for_non_existent_user_access(
        self, user_access_cache_service: UserAccessCacheService, sample_access_token: str
    ) -> None:
        assert not await user_access_cache_service.is_authenticated(sample_access_token)


class TestIsExpired:
    @pytest.mark.asyncio
    async def test_is_expired(
        self,
        user_access_cache_service: UserAccessCacheService,
        sample_access_token: str,
        sample_anonymous_user_access: UserAccess,
    ) -> None:
        await user_access_cache_service.set_user_access(
            sample_access_token, sample_anonymous_user_access, ttl=1
        )
        assert not await user_access_cache_service.has_expired(sample_access_token)

        await asyncio.sleep(1.1)

        assert await user_access_cache_service.has_expired(sample_access_token)
