from uuid import uuid4
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from unittest.mock import MagicMock

from sqlalchemy.ext.asyncio import AsyncSession

from src.database.schema import DBUser

from src.services.data_services.user_service import UserService

from src.repositories.user_repository import UserRepository

from src.schemas.users import CreateUserParams, UpdateUserParams, User

from src.utils.date_utils import to_utc_isostring

pytestmark = pytest.mark.asyncio


@pytest.fixture
def user_service() -> UserService:
    return UserService(UserRepository())


@pytest.fixture
def sample_user_id() -> str:
    return str(uuid4())


@pytest.fixture
def sample_user_external_id() -> str:
    return "test-user-external-id"


@pytest.fixture
def sample_timestamps() -> tuple[datetime, datetime]:
    return (datetime.now(timezone.utc), datetime.now(timezone.utc))


class TestCreateUser:
    async def test_create_user(
        self,
        async_session: AsyncSession,
        user_service: UserService,
        sample_user_id: str,
        sample_user_external_id: str,
        sample_timestamps: tuple[datetime, datetime],
    ) -> None:
        params = CreateUserParams(
            id=sample_user_id,
            external_id=sample_user_external_id,
            created_at=sample_timestamps[0],
            updated_at=sample_timestamps[1],
            last_signed_in_at=sample_timestamps[1],
            email="test@test.com",
            name="Test User",
        )

        result = await user_service.create_user(async_session, params)

        assert isinstance(result, User)

        assert result.id == sample_user_id
        assert result.external_id == sample_user_external_id
        assert result.created_at == to_utc_isostring(sample_timestamps[0])
        assert result.updated_at == to_utc_isostring(sample_timestamps[1])


class TestGetUser:
    @pytest_asyncio.fixture(scope="function")
    async def create_user_in_db(
        self,
        async_session: AsyncSession,
        user_service: UserService,
        sample_user_id: str,
        sample_user_external_id: str,
        sample_timestamps: tuple[datetime, datetime],
    ) -> User:
        params = CreateUserParams(
            id=sample_user_id,
            external_id=sample_user_external_id,
            created_at=sample_timestamps[0],
            updated_at=sample_timestamps[1],
            last_signed_in_at=sample_timestamps[1],
            email="test@test.com",
            name="Test User",
        )
        return await user_service.create_user(async_session, params)

    async def test_get_user_by_id(
        self,
        async_session: AsyncSession,
        user_service: UserService,
        create_user_in_db: User,
        sample_user_id: str,
        sample_user_external_id: str,
        sample_timestamps: tuple[datetime, datetime],
    ) -> None:
        result = await user_service.get_user_by_id(async_session, sample_user_id)

        assert isinstance(result, User)

        assert result.id == sample_user_id
        assert result.external_id == sample_user_external_id
        assert result.created_at == to_utc_isostring(sample_timestamps[0])
        assert result.updated_at == to_utc_isostring(sample_timestamps[1])
        assert result.last_signed_in_at == to_utc_isostring(sample_timestamps[1])
        assert result.email == "test@test.com"
        assert result.name == "Test User"

    async def test_get_non_existent_user_by_id(
        self,
        async_session: AsyncSession,
        user_service: UserService,
    ) -> None:
        result = await user_service.get_user_by_id(async_session, "non-existent-user-id")

        assert result is None

    async def test_get_user_by_external_id(
        self,
        async_session: AsyncSession,
        user_service: UserService,
        create_user_in_db: User,
        sample_user_id: str,
        sample_user_external_id: str,
        sample_timestamps: tuple[datetime, datetime],
    ) -> None:
        result = await user_service.get_user_by_external_id(async_session, sample_user_external_id)

        assert isinstance(result, User)

        assert result.id == sample_user_id
        assert result.external_id == sample_user_external_id
        assert result.created_at == to_utc_isostring(sample_timestamps[0])
        assert result.updated_at == to_utc_isostring(sample_timestamps[1])
        assert result.last_signed_in_at == to_utc_isostring(sample_timestamps[1])
        assert result.email == "test@test.com"
        assert result.name == "Test User"

    async def test_get_non_existent_user_by_external_id(
        self,
        async_session: AsyncSession,
        user_service: UserService,
    ) -> None:
        result = await user_service.get_user_by_external_id(
            async_session, "non-existent-user-external-id"
        )

        assert result is None


class TestUpdateUser:
    async def test_update_user(
        self,
        async_session: AsyncSession,
        user_service: UserService,
        sample_user_id: str,
        sample_user_external_id: str,
        sample_timestamps: tuple[datetime, datetime],
    ) -> None:
        sample_user = {
            "id": sample_user_id,
            "external_id": sample_user_external_id,
            "created_at": sample_timestamps[0],
            "updated_at": sample_timestamps[1],
            "last_signed_in_at": sample_timestamps[1],
            "email": "test@test.com",
            "name": "Test User",
        }
        await user_service.create_user(async_session, CreateUserParams(**sample_user))
        result = await user_service.update_user(
            async_session,
            UpdateUserParams(
                id=sample_user_id,
                external_id=sample_user_external_id,
                updated_at=sample_timestamps[1],
                last_signed_in_at=sample_timestamps[1],
                email="test2@test.com",
                name="Test User 2",
            ),
        )

        assert isinstance(result, User)

        assert result.id == sample_user_id
        assert result.external_id == sample_user_external_id
        assert result.created_at == to_utc_isostring(sample_timestamps[0])
        assert result.updated_at == to_utc_isostring(sample_timestamps[1])
        assert result.last_signed_in_at == to_utc_isostring(sample_timestamps[1])
        assert result.email == "test2@test.com"
        assert result.name == "Test User 2"
