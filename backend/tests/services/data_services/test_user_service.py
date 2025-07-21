from uuid import uuid4
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from unittest.mock import MagicMock, patch

from sqlalchemy.ext.asyncio import AsyncSession

from database.schema import DBUser

from services.data_services.user_service import UserService

from repositories.user_repository import UserRepository

from schemas.users import CreateUserParams, User

from utils.date_utils import to_utc_isostring

pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_user_repository():
    return MagicMock(spec=UserRepository)


@pytest.fixture
def user_service(mock_user_repository):
    return UserService(mock_user_repository)


@pytest.fixture
def sample_user_id():
    return str(uuid4())


@pytest.fixture
def sample_user_external_id():
    return "test-user-external-id"


@pytest.fixture
def sample_timestamps():
    return (datetime.now(timezone.utc), datetime.now(timezone.utc))


@pytest.fixture
def mock_async_session():
    return MagicMock(spec=AsyncSession)


@pytest.fixture
def mock_db_user(sample_user_id: str, sample_user_external_id: str, sample_timestamps: tuple[datetime, datetime]):
    return DBUser(
        id=sample_user_id,
        external_id=sample_user_external_id,
        created_at=sample_timestamps[0].replace(tzinfo=None),
        updated_at=sample_timestamps[1].replace(tzinfo=None),
    )


class TestUserService:
    async def test_create_user(self, user_service: UserService, mock_user_repository: UserRepository, mock_async_session: AsyncSession, mock_db_user: DBUser, sample_user_id: str, sample_user_external_id: str, sample_timestamps: tuple[datetime, datetime]):
        params = CreateUserParams(
            id=sample_user_id,
            external_id=sample_user_external_id,
            created_at=sample_timestamps[0],
            updated_at=sample_timestamps[1],
        )
                
        mock_user_repository.create_user.return_value = mock_db_user
        
        result = await user_service.create_user(mock_async_session, params)
        
        assert isinstance(result, User)
        
        assert result.id == sample_user_id
        assert result.external_id == sample_user_external_id
        assert result.created_at == to_utc_isostring(sample_timestamps[0])
        assert result.updated_at == to_utc_isostring(sample_timestamps[1])
                        
            
    async def test_get_user_by_id(self, user_service: UserService, mock_user_repository: UserRepository, mock_async_session: AsyncSession, mock_db_user: DBUser, sample_user_id: str, sample_user_external_id: str, sample_timestamps: tuple[datetime, datetime]):
        mock_user_repository.get_user_by_id.return_value = mock_db_user
        
        result = await user_service.get_user_by_id(mock_async_session, sample_user_id)
        
        assert isinstance(result, User)
        
        assert result.id == sample_user_id
        assert result.external_id == sample_user_external_id
        assert result.created_at == to_utc_isostring(sample_timestamps[0])
        assert result.updated_at == to_utc_isostring(sample_timestamps[1])
        
        
    async def test_get_non_existent_user_by_id(self, user_service: UserService, mock_user_repository: UserRepository, mock_async_session: AsyncSession):
        mock_user_repository.get_user_by_id.return_value = None
        
        result = await user_service.get_user_by_id(mock_async_session, "non-existent-user-id")
        
        assert result is None
        
        
        
    async def test_get_user_by_external_id(self, user_service: UserService, mock_user_repository: UserRepository, mock_async_session: AsyncSession, mock_db_user: DBUser, sample_user_id: str, sample_user_external_id: str, sample_timestamps: tuple[datetime, datetime]):
        mock_user_repository.get_user_by_external_id.return_value = mock_db_user
        
        result = await user_service.get_user_by_external_id(mock_async_session, sample_user_external_id)
        
        assert isinstance(result, User)
        
        assert result.id == sample_user_id
        assert result.external_id == sample_user_external_id
        assert result.created_at == to_utc_isostring(sample_timestamps[0])
        assert result.updated_at == to_utc_isostring(sample_timestamps[1])
        
        
    async def test_get_non_existent_user_by_external_id(self, user_service: UserService, mock_user_repository: UserRepository, mock_async_session: AsyncSession):
        mock_user_repository.get_user_by_external_id.return_value = None
        
        result = await user_service.get_user_by_external_id(mock_async_session, "non-existent-user-external-id")
        
        assert result is None
        