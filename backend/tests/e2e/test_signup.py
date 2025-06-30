from datetime import datetime, timezone
from uuid import uuid4
import pytest
from fastapi import status

from schemas.users import CreateUserParams
from src.services.service_container import ServiceContainer

from tests.utils.assert_deep_equal import assert_deep_equal


class TestSignup:
    @pytest.mark.asyncio(loop_scope="session")
    async def test_successful_signup(self, async_client, service_container: ServiceContainer):
        user_access_data = await service_container.user_access_cache_service.create_anonymous_access()

        payload = {
            "email": "new@example.com",
            "name": "New User",
            "password": "password123",
            "confirm_password": "password123"
        }
        headers = {"Authorization": f"Bearer {user_access_data.access_token}"}

        response = await async_client.post("/api/auth/signup", json=payload, headers=headers)

        assert response.status_code == status.HTTP_200_OK
        assert "user_id" in response.json()
        assert "access_token" in response.json()
        assert "email" in response.json()
        assert "name" in response.json()
        assert "is_authenticated" in response.json()
        assert "user_message_count" in response.json()
        
        assert response.json()["user_id"] is not None
        assert response.json()["access_token"] is not None
        assert response.json()["email"] == "new@example.com"
        assert response.json()["name"] == "New User"
        assert response.json()["is_authenticated"] is True
        assert response.json()["user_message_count"] == 0

    @pytest.mark.asyncio(loop_scope="session")
    async def test_passwords_dont_match(self, async_client, service_container: ServiceContainer):
        user_access_data = await service_container.user_access_cache_service.create_anonymous_access()
        
        payload = {
            "email": "new@example.com",
            "name": "New User",
            "password": "password123",
            "confirm_password": "different_password"
        }
        headers = {"Authorization": f"Bearer {user_access_data.access_token}"}

        response = await async_client.post("/api/auth/signup", json=payload, headers=headers)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio(loop_scope="session")
    async def test_user_already_exists(self, async_client, service_container: ServiceContainer):
        user_access_data = await service_container.user_access_cache_service.create_anonymous_access()
        
        async with service_container.db_transaction_maker() as db:
            await service_container.user_service.create_user(db, CreateUserParams(
                id=str(uuid4()),
                email="new@example.com",
                name="New User",
                password="password123",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            ))
        
        payload = {
            "email": "new@example.com",
            "name": "New User",
            "password": "password123",
            "confirm_password": "password123"
        }
        headers = {"Authorization": f"Bearer {user_access_data.access_token}"}

        response = await async_client.post("/api/auth/signup", json=payload, headers=headers)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert_deep_equal(response.json(), {"detail": {"message": "User already exists"}})


    @pytest.mark.asyncio(loop_scope="session")
    async def test_missing_token(self, async_client, service_container: ServiceContainer):
        payload = {
            "email": "new@example.com",
            "name": "New User",
            "password": "password123",
            "confirm_password": "password123"
        }
        
        response = await async_client.post("/api/auth/signup", json=payload)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert_deep_equal(response.json(), {"detail": {"message": "Missing access token"}})
        
        headers = {}
        response = await async_client.post("/api/auth/signup", json=payload, headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert_deep_equal(response.json(), {"detail": {"message": "Missing access token"}})

        headers = {"Authorization": "Access "}
        response = await async_client.post("/api/auth/signup", json=payload, headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert_deep_equal(response.json(), {"detail": {"message": "Missing access token"}})
        
        headers = {"Authorization": "Bearer "}
        response = await async_client.post("/api/auth/signup", json=payload, headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert_deep_equal(response.json(), {"detail": {"message": "Missing access token"}})

    @pytest.mark.asyncio(loop_scope="session")
    async def test_invalid_token(self, async_client, service_container: ServiceContainer):
        payload = {
            "email": "new@example.com",
            "name": "New User",
            "password": "password123",
            "confirm_password": "password123"
        }
        
        headers = {"Authorization": f"Bearer invalid_token"}

        response = await async_client.post("/api/auth/signup", json=payload, headers=headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert_deep_equal(response.json(), {"detail": {"message": "Access token is invalid or expired"}})

    @pytest.mark.asyncio(loop_scope="session")
    async def test_already_authenticated(self, async_client, service_container: ServiceContainer):
        user_access_data = await service_container.user_access_cache_service.create_anonymous_access()
        await service_container.user_access_cache_service.promote_to_authenticated(
            access_token=user_access_data.access_token,
            user_id=user_access_data.user_id,
            email="test@example.com",
            name="Test User",
        )

        payload = {
            "email": "test@example.com",
            "name": "Test User",
            "password": "password123",
            "confirm_password": "password123"
        }
        headers = {"Authorization": f"Bearer {user_access_data.access_token}"}

        response = await async_client.post("/api/auth/signup", json=payload, headers=headers)

        assert response.status_code == status.HTTP_200_OK
        assert "user_id" in response.json()
        assert "access_token" in response.json()
        assert "email" in response.json()
        assert "name" in response.json()
        assert "is_authenticated" in response.json()
        assert "user_message_count" in response.json()
        
        assert response.json()["user_id"] is not None
        assert response.json()["access_token"] is not None
        assert response.json()["email"] == "test@example.com"
        assert response.json()["name"] == "Test User"
        assert response.json()["is_authenticated"] is True
        assert response.json()["user_message_count"] == 0

    @pytest.mark.asyncio(loop_scope="session")
    async def test_invalid_email_format(self, async_client, service_container: ServiceContainer):
        user_access_data = await service_container.user_access_cache_service.create_anonymous_access()
        
        payload = {
            "email": "invalid-email",
            "name": "New User",
            "password": "password123",
            "confirm_password": "password123"
        }
        headers = {"Authorization": f"Bearer {user_access_data.access_token}"}

        response = await async_client.post("/api/auth/signup", json=payload, headers=headers)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio(loop_scope="session")
    async def test_missing_required_fields(self, async_client, service_container: ServiceContainer):
        user_access_data = await service_container.user_access_cache_service.create_anonymous_access()
        
        payload = {
            "email": "test@example.com"
        }
        headers = {"Authorization": f"Bearer {user_access_data.access_token}"}

        response = await async_client.post("/api/auth/signup", json=payload, headers=headers)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio(loop_scope="session")
    async def test_weak_password(self, async_client, service_container: ServiceContainer):
        user_access_data = await service_container.user_access_cache_service.create_anonymous_access()
        
        payload = {
            "email": "test@example.com",
            "name": "Test User",
            "password": "123",
            "confirm_password": "123"
        }
        headers = {"Authorization": f"Bearer {user_access_data.access_token}"}

        response = await async_client.post("/api/auth/signup", json=payload, headers=headers)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


    @pytest.mark.asyncio(loop_scope="session")
    async def test_empty_name(self, async_client, service_container: ServiceContainer):
        user_access_data = await service_container.user_access_cache_service.create_anonymous_access()
        
        payload = {
            "email": "test@example.com",
            "name": "",
            "password": "password123",
            "confirm_password": "password123"
        }
        headers = {"Authorization": f"Bearer {user_access_data.access_token}"}

        response = await async_client.post("/api/auth/signup", json=payload, headers=headers)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio(loop_scope="session")
    async def test_signup_with_whitespace_in_fields(self, async_client, service_container: ServiceContainer):
        user_access_data = await service_container.user_access_cache_service.create_anonymous_access()

        payload = {
            "email": "  test@example.com  ",
            "name": "  Test User  ",
            "password": "password123",
            "confirm_password": "password123"
        }
        headers = {"Authorization": f"Bearer {user_access_data.access_token}"}

        response = await async_client.post("/api/auth/signup", json=payload, headers=headers)

        assert response.status_code == status.HTTP_200_OK
