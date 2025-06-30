import pytest
from datetime import datetime, timezone
from fastapi import status
from uuid import uuid4

from services.service_container import ServiceContainer

from schemas.user_access import UserAccessData
from schemas.users import CreateUserParams, User
from schemas.threads import GetUserThreadsParams, Thread
from schemas.messages import GetMessagesParams, Message
from schemas.recipes import Recipe, RecipeIngredient, RecipeInstruction, RecipeCategory

from tests.utils.assert_deep_equal import assert_deep_equal
from utils.date_utils import to_utc_isostring


pytestmark = pytest.mark.asyncio

class TestLogin:
    @pytest.mark.asyncio(loop_scope="session")
    async def test_successful_login(self, async_client, service_container: ServiceContainer):
        user_access_data = await service_container.user_access_cache_service.create_anonymous_access()
        
        user_id = str(uuid4())
        
        async with service_container.db_transaction_maker() as db:
            user = await service_container.user_service.create_user(db, CreateUserParams(
                id=user_id,
                email="test@example.com",
                name="Test User",
                password="password123",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            ))
        
        payload = {
            "email": "test@example.com",
            "password": "password123",
        }
        headers = {"Authorization": f"Bearer {user_access_data.access_token}"}
        
        response = await async_client.post("/api/auth/login", json=payload, headers=headers)
        assert response.status_code == status.HTTP_200_OK
        
        user_access_data = await service_container.user_access_cache_service.get_user_access(user_access_data.access_token)
        assert user_access_data is not None
        assert user_access_data.user_id == user_id
        assert user_access_data.is_authenticated is True
        assert user_access_data.user_message_count == 0
        
    @pytest.mark.asyncio(loop_scope="session")
    async def test_successful_login_with_authenticated_access(self, async_client, service_container: ServiceContainer):
        user_access_data = await service_container.user_access_cache_service.create_anonymous_access()
        await service_container.user_access_cache_service.promote_to_authenticated(
            access_token=user_access_data.access_token,
            user_id=user_access_data.user_id,
            email="test@example.com",
            name="Test User",
        )
        
        
        payload = {
            "email": "test@example.com",
            "password": "password123",
        }
        headers = {"Authorization": f"Bearer {user_access_data.access_token}"}
        
        response = await async_client.post("/api/auth/login", json=payload, headers=headers)
        assert response.status_code == status.HTTP_200_OK
        
        user_access_data = await service_container.user_access_cache_service.get_user_access(user_access_data.access_token)
        assert user_access_data is not None
        assert user_access_data.user_id is not None
        assert user_access_data.is_authenticated is True
        assert user_access_data.user_message_count == 0
    
    @pytest.mark.asyncio(loop_scope="session")
    async def test_missing_access_token(self, async_client, service_container: ServiceContainer):
        payload = {
            "email": "test@example.com",
            "password": "password123",
        }
        
        response = await async_client.post("/api/auth/login", json=payload)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert_deep_equal(response.json(), {"detail": {"message": "Missing access token"}})
        
        headers = {}
        response = await async_client.post("/api/auth/login", json=payload, headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert_deep_equal(response.json(), {"detail": {"message": "Missing access token"}})
    
        headers = {"Authorization": "Access "}
        response = await async_client.post("/api/auth/login", json=payload, headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert_deep_equal(response.json(), {"detail": {"message": "Missing access token"}})
        
        headers = {"Authorization": "Bearer "}
        response = await async_client.post("/api/auth/login", json=payload, headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert_deep_equal(response.json(), {"detail": {"message": "Missing access token"}})
        
    @pytest.mark.asyncio(loop_scope="session")
    async def test_invalid_access_token(self, async_client, service_container: ServiceContainer):
        payload = {
            "email": "test@example.com",
            "password": "password123",
        }
        
        headers = {"Authorization": "Bearer invalid_token"}
        response = await async_client.post("/api/auth/login", json=payload, headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert_deep_equal(response.json(), {"detail": {"message": "Access token is invalid or expired"}})
    
    @pytest.mark.asyncio(loop_scope="session")
    async def test_user_not_found(self, async_client, service_container: ServiceContainer):
        user_access_data = await service_container.user_access_cache_service.create_anonymous_access()
        
        payload = {
            "email": "test_user@example.com",
            "password": "password123",
        }
        
        headers = {"Authorization": f"Bearer {user_access_data.access_token}"}
        response = await async_client.post("/api/auth/login", json=payload, headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert_deep_equal(response.json(), {"detail": {"message": "User does not exist"}})
    
    @pytest.mark.asyncio(loop_scope="session")
    async def test_invalid_password(self, async_client, service_container: ServiceContainer):
        user_access_data = await service_container.user_access_cache_service.create_anonymous_access()
        
        async with service_container.db_transaction_maker() as db:
            await service_container.user_service.create_user(db, CreateUserParams(
                id=str(uuid4()),
                email="test_user@example.com",
                name="Test User",
                password="password123",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            ))
            
        payload = {
            "email": "test_user@example.com",
            "password": "invalid_password",
        }
        
        headers = {"Authorization": f"Bearer {user_access_data.access_token}"}
        response = await async_client.post("/api/auth/login", json=payload, headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert_deep_equal(response.json(), {"detail": {"message": "Invalid credentials"}})
        
    @pytest.mark.asyncio(loop_scope="session")
    async def test_missing_email(self, async_client, service_container: ServiceContainer):
        user_access_data = await service_container.user_access_cache_service.create_anonymous_access()
        
        payload = {
            "password": "password123",
        }
        
        headers = {"Authorization": f"Bearer {user_access_data.access_token}"}
        response = await async_client.post("/api/auth/login", json=payload, headers=headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
    @pytest.mark.asyncio(loop_scope="session")
    async def test_missing_password(self, async_client, service_container: ServiceContainer):
        user_access_data = await service_container.user_access_cache_service.create_anonymous_access()
        
        payload = {
            "email": "test@example.com",
        }
        
        headers = {"Authorization": f"Bearer {user_access_data.access_token}"}
        response = await async_client.post("/api/auth/login", json=payload, headers=headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
    @pytest.mark.asyncio(loop_scope="session")
    async def test_invalid_email(self, async_client, service_container: ServiceContainer):
        user_access_data = await service_container.user_access_cache_service.create_anonymous_access()
        
        payload = {
            "email": "invalid_email",
            "password": "password123",
        }
        
        headers = {"Authorization": f"Bearer {user_access_data.access_token}"}
        response = await async_client.post("/api/auth/login", json=payload, headers=headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        