from uuid import uuid4
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from unittest.mock import MagicMock, patch

from sqlalchemy.ext.asyncio import AsyncSession

from database.schema import DBUser

from services.data_services.user_service import UserService

from repositories.user_repository import UserRepository

from schemas.users import (
    CreateUserParams,
    UpdateUserParams,
    User,
)

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
def sample_user_email():
    return "test@example.com"


@pytest.fixture
def sample_user_name():
    return "Test User"


@pytest.fixture
def sample_user_password():
    return "test-password"


@pytest.fixture
def sample_timestamps():
    return (datetime.now(timezone.utc), datetime.now(timezone.utc))


@pytest.fixture
def mock_async_session():
    return MagicMock(spec=AsyncSession)


@pytest.fixture
def mock_db_user(sample_user_id: str, sample_user_email: str, sample_user_name: str, sample_user_password: str, sample_timestamps: tuple[datetime, datetime]):
    return DBUser(
        id=sample_user_id,
        email=sample_user_email,
        name=sample_user_name,
        password_hash="hashed-password",
        created_at=sample_timestamps[0].replace(tzinfo=None),
        updated_at=sample_timestamps[1].replace(tzinfo=None),
    )


class TestUserService:
    async def test_create_user(self, user_service: UserService, mock_user_repository: UserRepository, mock_async_session: AsyncSession, mock_db_user: DBUser, sample_user_id: str, sample_user_email: str, sample_user_name: str, sample_user_password: str, sample_timestamps: tuple[datetime, datetime]):
        with patch("src.services.data_services.user_service.password_utils.hash_password") as mock_hash_password:
            params = CreateUserParams(
                id=sample_user_id,
                email=sample_user_email,
                name=sample_user_name,
                password=sample_user_password,
                created_at=sample_timestamps[0],
                updated_at=sample_timestamps[1],
            )
            
            mock_hash_password.return_value = "hashed-password"
            
            mock_user_repository.create_user.return_value = mock_db_user
            
            result = await user_service.create_user(mock_async_session, params)
            
            assert isinstance(result, User)
            
            assert result.id == sample_user_id
            assert result.email == sample_user_email
            assert result.name == sample_user_name
            assert result.created_at == to_utc_isostring(sample_timestamps[0])
            assert result.updated_at == to_utc_isostring(sample_timestamps[1])
            
            mock_hash_password.assert_called_once_with(sample_user_password)
            
            
    async def test_get_user_by_id(self, user_service: UserService, mock_user_repository: UserRepository, mock_async_session: AsyncSession, mock_db_user: DBUser, sample_user_id: str, sample_user_email: str, sample_user_name: str, sample_user_password: str, sample_timestamps: tuple[datetime, datetime]):
        mock_user_repository.get_user_by_id.return_value = mock_db_user
        
        result = await user_service.get_user_by_id(mock_async_session, sample_user_id)
        
        assert isinstance(result, User)
        
        assert result.id == sample_user_id
        assert result.email == sample_user_email
        assert result.name == sample_user_name
        assert result.created_at == to_utc_isostring(sample_timestamps[0])
        assert result.updated_at == to_utc_isostring(sample_timestamps[1])
        
        
    async def test_get_non_existent_user_by_id(self, user_service: UserService, mock_user_repository: UserRepository, mock_async_session: AsyncSession):
        mock_user_repository.get_user_by_id.return_value = None
        
        result = await user_service.get_user_by_id(mock_async_session, "non-existent-user-id")
        
        assert result is None
        
        
        
    async def test_get_user_by_email(self, user_service: UserService, mock_user_repository: UserRepository, mock_async_session: AsyncSession, mock_db_user: DBUser, sample_user_id: str, sample_user_email: str, sample_user_name: str, sample_user_password: str, sample_timestamps: tuple[datetime, datetime]):
        mock_user_repository.get_user_by_email.return_value = mock_db_user
        
        result = await user_service.get_user_by_email(mock_async_session, sample_user_email)
        
        assert isinstance(result, User)
        
        assert result.id == sample_user_id
        assert result.email == sample_user_email
        assert result.name == sample_user_name
        assert result.created_at == to_utc_isostring(sample_timestamps[0])
        assert result.updated_at == to_utc_isostring(sample_timestamps[1])
        
        
    async def test_get_non_existent_user_by_email(self, user_service: UserService, mock_user_repository: UserRepository, mock_async_session: AsyncSession):
        mock_user_repository.get_user_by_email.return_value = None
        
        result = await user_service.get_user_by_email(mock_async_session, "non-existent-user-email")
        
        assert result is None
        
        
    async def test_update_user(self, user_service: UserService, mock_user_repository: UserRepository, mock_async_session: AsyncSession, mock_db_user: DBUser, sample_user_id: str, sample_user_email: str, sample_user_name: str, sample_user_password: str, sample_timestamps: tuple[datetime, datetime]):
        with patch("src.services.data_services.user_service.password_utils.hash_password") as mock_hash_password:
            params = UpdateUserParams(
                id=sample_user_id,
                updated_at=sample_timestamps[1],
                email=sample_user_email,
                name=sample_user_name,
                password="sample-password",
            )
            
            mock_hash_password.return_value = "hashed-password"
            
            mock_user_repository.update_user.return_value = mock_db_user
            
            result = await user_service.update_user(mock_async_session, params)
            
            assert isinstance(result, User)
            
            assert result.id == sample_user_id
            assert result.email == sample_user_email
            assert result.name == sample_user_name
            assert result.created_at == to_utc_isostring(sample_timestamps[0])
            assert result.updated_at == to_utc_isostring(sample_timestamps[1])
            
            mock_hash_password.assert_called_once_with("sample-password")
            
            
    async def test_verify_password(self, user_service: UserService, mock_user_repository: UserRepository, mock_async_session: AsyncSession, mock_db_user: DBUser, sample_user_id: str, sample_user_email: str, sample_user_name: str, sample_user_password: str, sample_timestamps: tuple[datetime, datetime]):
        with patch("src.services.data_services.user_service.password_utils.verify_password") as mock_verify_password:
            mock_user_repository.get_user_by_id.return_value = mock_db_user
            
            result = await user_service.verify_password(mock_async_session, sample_user_id, sample_user_password)
            
            mock_verify_password.assert_called_once_with(sample_user_password, "hashed-password")
        
        
    async def test_verify_password_with_none_password(self, user_service: UserService, mock_user_repository: UserRepository, mock_async_session: AsyncSession, mock_db_user: DBUser, sample_user_id: str, sample_user_email: str, sample_user_name: str, sample_user_password: str, sample_timestamps: tuple[datetime, datetime]):
        mock_user_repository.get_user_by_id.return_value = mock_db_user
        
        result = await user_service.verify_password(mock_async_session, sample_user_id, None)
        
        assert result is False
        
        
    async def test_verify_password_for_non_existent_user(self, user_service: UserService, mock_user_repository: UserRepository, mock_async_session: AsyncSession, mock_db_user: DBUser, sample_user_id: str, sample_user_email: str, sample_user_name: str, sample_user_password: str, sample_timestamps: tuple[datetime, datetime]):
        mock_user_repository.get_user_by_id.return_value = None
        
        result = await user_service.verify_password(mock_async_session, sample_user_id, sample_user_password)
        
        assert result is False
        
        