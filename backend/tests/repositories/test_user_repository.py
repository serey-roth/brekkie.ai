from datetime import datetime, timezone
from uuid import uuid4
import pytest
import pytest_asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from repositories.user_repository import (
    UserRepository,
    CreateDbUserParams,
    UpdateDbUserParams,
)

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
        params = CreateDbUserParams(
            id=user_id,
            email="test@example.com",
            name="Test User",
            password_hash="password_hash",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        
        await user_repository.create_user(async_session, params)
        await async_session.commit()
        
        user = await user_repository.get_user_by_id(async_session, user_id)
        assert user is not None
        assert user.id == user_id
        assert user.email == params.email
        assert user.name == params.name
        assert user.password_hash == params.password_hash
        assert user.created_at == strip_timezone(params.created_at)
        assert user.updated_at == strip_timezone(params.updated_at)
        
    
    async def test_create_user_with_existing_email(self, async_session: AsyncSession, user_repository: UserRepository, user_id: str):
        params = CreateDbUserParams(
            id=user_id,
            email="test@example.com",
            name="Test User",
            password_hash="password_hash",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        
        await user_repository.create_user(async_session, params)
        await async_session.commit()
        
        with pytest.raises(ValueError) as e:
            await user_repository.create_user(async_session, params)
            
        assert str(e.value) == f"Email {params.email} already in use"
        
        
@pytest.fixture
def sample_user(user_id: str):
    return {
        "id": user_id,
        "email": "test@example.com",
        "name": "Test User",
        "password_hash": "password_hash",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }


class TestGetUserById:
    @pytest_asyncio.fixture(scope="function")
    async def create_user_in_db(self, async_session: AsyncSession, user_repository: UserRepository, sample_user: dict):
        params = CreateDbUserParams(**sample_user)
        
        await user_repository.create_user(async_session, params)
        await async_session.commit()
        
        
    async def test_get_user_by_id(self, async_session: AsyncSession, user_repository: UserRepository, create_user_in_db, sample_user: dict, user_id: str):
        user = await user_repository.get_user_by_id(async_session, user_id)
        assert user is not None
        assert user.id == user_id
        assert user.email == sample_user["email"]
        assert user.name == sample_user["name"]
        assert user.password_hash == sample_user["password_hash"]
        assert user.created_at == strip_timezone(sample_user["created_at"])
        assert user.updated_at == strip_timezone(sample_user["updated_at"])
        

    async def test_get_non_existent_user_by_id(self, async_session: AsyncSession, user_repository: UserRepository):
        user = await user_repository.get_user_by_id(async_session, "non-existing-user-id")
        assert user is None
        
        
class TestGetUserByEmail:
    @pytest_asyncio.fixture(scope="function")
    async def create_user_in_db(self, async_session: AsyncSession, user_repository: UserRepository, sample_user: dict):
        params = CreateDbUserParams(**sample_user)
        
        await user_repository.create_user(async_session, params)
        await async_session.commit()
        
        
    async def test_get_user_by_email(self, async_session: AsyncSession, user_repository: UserRepository, create_user_in_db, sample_user: dict, user_id: str):
        user = await user_repository.get_user_by_email(async_session, sample_user["email"])
        assert user is not None
        assert user.id == user_id   
        assert user.email == sample_user["email"]
        
    
    async def test_get_non_existent_user_by_email(self, async_session: AsyncSession, user_repository: UserRepository):
        user = await user_repository.get_user_by_email(async_session, "non-existing-user-email")
        assert user is None
        
        
class TestUpdateUser:
    @pytest_asyncio.fixture(scope="function")
    async def create_user_in_db(self, async_session: AsyncSession, user_repository: UserRepository, sample_user: dict):
        params = CreateDbUserParams(**sample_user)
        
        await user_repository.create_user(async_session, params)
        await async_session.commit()
        
        
    async def test_update_user(self, async_session: AsyncSession, user_repository: UserRepository, create_user_in_db, sample_user: dict, user_id: str):
        params = UpdateDbUserParams(
            id=user_id,
            email="updated@example.com",
            name="Updated User",
            password_hash="updated_password_hash",
            updated_at=datetime.now(timezone.utc),
        )
        
        await user_repository.update_user(async_session, params)
        await async_session.commit()
        
        user = await user_repository.get_user_by_id(async_session, user_id)
        assert user is not None
        assert user.id == user_id   
        
        
    async def test_update_user_with_none_values(self, async_session: AsyncSession, user_repository: UserRepository, create_user_in_db, sample_user: dict, user_id: str):
        params = UpdateDbUserParams(
            id=user_id,
            email=None,
            name=None,
            password_hash=None,
            updated_at=datetime.now(timezone.utc),
        )
        
        await user_repository.update_user(async_session, params)
        await async_session.commit()
        
        user = await user_repository.get_user_by_id(async_session, user_id)
        assert user is not None
        assert user.id == user_id
        assert user.email is not None
        assert user.name is not None
        assert user.password_hash is not None
        
        
    async def test_update_user_with_non_existent_user(self, async_session: AsyncSession, user_repository: UserRepository):
        params = UpdateDbUserParams(
            id="non-existing-user-id",
            email="updated@example.com",
            name="Updated User",
            password_hash="updated_password_hash",
            updated_at=datetime.now(timezone.utc),
        )
        
        with pytest.raises(ValueError) as e:
            await user_repository.update_user(async_session, params)
            
        assert str(e.value) == f"User {params.id} not found"
        
        
    async def test_update_user_with_existing_email(self, async_session: AsyncSession, user_repository: UserRepository, create_user_in_db, sample_user: dict, user_id: str):
        another_user = await user_repository.create_user(async_session, CreateDbUserParams(
            id=str(uuid4()),
            email="another@example.com",
            name="Another User",
            password_hash="another_password_hash",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        ))
        await async_session.commit()
        
        params = UpdateDbUserParams(
            id=user_id,
            email=another_user.email,
            updated_at=datetime.now(timezone.utc),
        )
        
        with pytest.raises(ValueError) as e:
            await user_repository.update_user(async_session, params)
            
        assert str(e.value) == f"Email {params.email} already in use"
        