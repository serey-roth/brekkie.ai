from datetime import datetime, timezone
from typing import cast
from uuid import uuid4

import pytest
import pytest_asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from repositories.user_repository import UserRepository

from schemas.users import CreateUserParams, UpdateUserParams
from utils.date_utils import strip_timezone

pytestmark = pytest.mark.asyncio

@pytest.fixture
def user_repository():
    return UserRepository()


@pytest.fixture
def user_id():
    return str(uuid4())


class TestCreateUser:
    async def test_create_user(self, async_session: AsyncSession, user_repository: UserRepository, user_id: str):
        params = CreateUserParams(
            id=user_id,
            external_id="test-user-id",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            last_signed_in_at=datetime.now(timezone.utc),
            email="test@test.com",
            name="Test User"
        )
        
        await user_repository.create_user(async_session, params)
        await async_session.commit()
        
        user = await user_repository.get_user_by_id(async_session, user_id)
        assert user is not None
        assert str(user.id) == user_id
        assert str(user.external_id) == params.external_id
        assert cast(datetime, user.created_at) == strip_timezone(params.created_at)
        assert cast(datetime, user.updated_at) == strip_timezone(params.updated_at)
        
    
    async def test_create_user_with_existing_external_id(self, async_session: AsyncSession, user_repository: UserRepository, user_id: str):
        params = CreateUserParams(
            id=user_id,
            external_id="test-user-id",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            last_signed_in_at=datetime.now(timezone.utc),
            email="test@test.com",
            name="Test User"
        )
        
        await user_repository.create_user(async_session, params)
        await async_session.commit()
        
        with pytest.raises(ValueError) as e:
            await user_repository.create_user(async_session, params)
            
        assert str(e.value) == f"External ID {params.external_id} already in use"
        
        
@pytest.fixture
def sample_user(user_id: str):
    return {
        "id": user_id,
        "external_id": "test-user-id",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "last_signed_in_at": datetime.now(timezone.utc),
        "email": "test@test.com",
        "name": "Test User"
    }

class TestGetUserById:
    @pytest_asyncio.fixture(scope="function")
    async def create_user_in_db(self, async_session: AsyncSession, user_repository: UserRepository, sample_user: dict):
        params = CreateUserParams(**sample_user)
        
        await user_repository.create_user(async_session, params)
        await async_session.commit()
        
        
    async def test_get_user_by_id(self, async_session: AsyncSession, user_repository: UserRepository, create_user_in_db, sample_user: dict, user_id: str):
        user = await user_repository.get_user_by_id(async_session, user_id)
        assert user is not None
        assert str(user.id) == user_id
        assert user.external_id == sample_user["external_id"]
        assert cast(datetime, user.created_at) == strip_timezone(sample_user["created_at"])
        assert cast(datetime, user.updated_at) == strip_timezone(sample_user["updated_at"])
        assert cast(datetime, user.last_signed_in_at) == strip_timezone(sample_user["last_signed_in_at"])
        assert user.email == sample_user["email"]
        assert user.name == sample_user["name"]
        
    async def test_get_non_existent_user_by_id(self, async_session: AsyncSession, user_repository: UserRepository):
        user = await user_repository.get_user_by_id(async_session, "non-existing-user-id")
        assert user is None
        
        
class TestGetUserByExternalId:
    @pytest_asyncio.fixture(scope="function")
    async def create_user_in_db(self, async_session: AsyncSession, user_repository: UserRepository, sample_user: dict):
        params = CreateUserParams(**sample_user)
        
        await user_repository.create_user(async_session, params)
        await async_session.commit()
        
        
    async def test_get_user_by_external_id(self, async_session: AsyncSession, user_repository: UserRepository, create_user_in_db, sample_user: dict, user_id: str):
        user = await user_repository.get_user_by_external_id(async_session, sample_user["external_id"])
        assert user is not None
        assert str(user.id) == user_id   
        assert user.external_id == sample_user["external_id"]
        assert cast(datetime, user.created_at) == strip_timezone(sample_user["created_at"])
        assert cast(datetime, user.updated_at) == strip_timezone(sample_user["updated_at"])
        assert cast(datetime, user.last_signed_in_at) == strip_timezone(sample_user["last_signed_in_at"])
        assert user.email == sample_user["email"]
        assert user.name == sample_user["name"]
        
    async def test_get_non_existent_user_by_external_id(self, async_session: AsyncSession, user_repository: UserRepository):
        user = await user_repository.get_user_by_external_id(async_session, "non-existing-user-external-id")
        assert user is None
        

class TestUpdateUser:
    @pytest_asyncio.fixture(scope="function")
    async def create_user_in_db(self, async_session: AsyncSession, user_repository: UserRepository, sample_user: dict):
        params = CreateUserParams(**sample_user)
        
        await user_repository.create_user(async_session, params)
        await async_session.commit()
        
    async def test_update_user(self, async_session: AsyncSession, user_repository: UserRepository, create_user_in_db, sample_user: dict, user_id: str):
        params = UpdateUserParams(
            id=user_id,
            external_id=sample_user["external_id"],
            updated_at=datetime.now(timezone.utc),
            last_signed_in_at=datetime.now(timezone.utc),
            email="test@test.com",
            name="Updated Test User"
        )
        
        await user_repository.update_user(async_session, user_id, params)
        await async_session.commit()
        
        user = await user_repository.get_user_by_id(async_session, user_id)
        assert user is not None
        assert str(user.id) == user_id
        assert cast(datetime, user.updated_at) == strip_timezone(params.updated_at)
        assert params.last_signed_in_at is not None
        assert cast(datetime, user.last_signed_in_at) == strip_timezone(params.last_signed_in_at)
        assert user.email == sample_user["email"]
        assert user.external_id == sample_user["external_id"]
        assert str(user.name) == params.name
        