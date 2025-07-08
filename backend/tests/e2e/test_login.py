from unittest.mock import patch
import pytest

from datetime import datetime, timezone
from fastapi import status
from uuid import uuid4

from schemas.messages import CreateMessageParams
from services.service_container import ServiceContainer

from schemas.users import CreateUserParams
from schemas.threads import CreateThreadParams

from tests.test_helpers.assert_deep_equal import assert_deep_equal


pytestmark = pytest.mark.asyncio

class TestLogin:
    @pytest.mark.asyncio(loop_scope="session")
    async def test_successful_login(self, async_client, service_container: ServiceContainer):
        user_access_data = await service_container.user_access_cache_service.create_anonymous_access()
        
        user_id = user_access_data.user_id
        
        async with service_container.db_transaction_maker() as db:
            await service_container.user_service.create_user(db, CreateUserParams(
                id=user_id,
                email="test@example.com",
                name="Test User",
                password="password123",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            ))
            thread_id = str(uuid4())
            await service_container.thread_service.create_thread(db, CreateThreadParams(
                id=thread_id,
                user_id=user_id,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                title="Test Thread",
                is_empty=False,
            ))
            message_id = str(uuid4())
            await service_container.message_service.create_message(db, CreateMessageParams(
                id=message_id,
                user_id=user_id,
                thread_id=thread_id,
                role="user",
                content_type="text",
                text_content="Hello, world!",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            ))
        
        ip_address = "192.168.1.100"
        headers = {
            "fly-client-ip": ip_address
        }   
        
        payload = {
            "email": "test@example.com",
            "password": "password123",
        }
        
        async_client.cookies.set("bk_access_token", user_access_data.access_token)

        response = await async_client.post("/api/auth/login", json=payload, headers=headers)
        assert response.status_code == status.HTTP_200_OK
        
        assert response.json()["user_id"] == user_id
        assert response.json()["is_authenticated"] is True
        assert response.json()["user_message_count"] == 1
        assert response.cookies.get("bk_access_token") is not None
        
        assert await service_container.anonymous_access_service.ip_rate_limiter.get_current_count(ip_address) == 0
                
        old_user_access_data = await service_container.user_access_cache_service.get_user_access(user_access_data.access_token)
        assert old_user_access_data is None
        
    @pytest.mark.asyncio(loop_scope="session")
    async def test_login_without_existing_access_token(self, async_client, service_container: ServiceContainer):
        user_access_data = await service_container.user_access_cache_service.create_anonymous_access()
        
        user_id = user_access_data.user_id
        
        async with service_container.db_transaction_maker() as db:
            await service_container.user_service.create_user(db, CreateUserParams(
                id=user_id,
                email="test@example.com",
                name="Test User",
                password="password123",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            ))
            thread_id = str(uuid4())
            await service_container.thread_service.create_thread(db, CreateThreadParams(
                id=thread_id,
                user_id=user_id,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                title="Test Thread",
                is_empty=False,
            ))
            message_id = str(uuid4())
            await service_container.message_service.create_message(db, CreateMessageParams(
                id=message_id,
                user_id=user_id,
                thread_id=thread_id,
                role="user",
                content_type="text",
                text_content="Hello, world!",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            ))
            
        payload = {
            "email": "test@example.com",
            "password": "password123",
        }
        
        ip_address = "192.168.1.100"
        headers = {
            "fly-client-ip": ip_address
        }
        
        with patch.object(service_container.user_access_cache_service, "revoke_access") as mock_revoke_access:
            response = await async_client.post("/api/auth/login", json=payload, headers=headers)
            assert response.status_code == status.HTTP_200_OK
            assert response.cookies.get("bk_access_token") is not None
            
            assert not mock_revoke_access.called
            
        assert await service_container.anonymous_access_service.ip_rate_limiter.get_current_count(ip_address) == 0
        
        
    @pytest.mark.asyncio(loop_scope="session")
    async def test_login_with_rate_limit_exceeded(self, async_client, service_container: ServiceContainer):
        user_access_data = await service_container.user_access_cache_service.create_anonymous_access()
        
        user_id = user_access_data.user_id
        
        async with service_container.db_transaction_maker() as db:
            await service_container.user_service.create_user(db, CreateUserParams(
                id=user_id,
                email="test@example.com",
                name="Test User",
                password="password123",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            ))
            thread_id = str(uuid4())
            await service_container.thread_service.create_thread(db, CreateThreadParams(
                id=thread_id,
                user_id=user_id,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                title="Test Thread",
                is_empty=False,
            ))
            message_id = str(uuid4())
            await service_container.message_service.create_message(db, CreateMessageParams(
                id=message_id,
                user_id=user_id,
                thread_id=thread_id,
                role="user",
                content_type="text",
                text_content="Hello, world!",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            ))
            
            
        payload = {
            "email": "test@example.com",
            "password": "password123",  
        }
        
        ip_address = "192.168.1.100"
        headers = {
            "fly-client-ip": ip_address
        }
        
        await service_container.anonymous_access_service.ip_rate_limiter.increment(ip_address)
        
        async_client.cookies.set("bk_access_token", user_access_data.access_token)
        
        response = await async_client.post("/api/auth/login", json=payload, headers=headers)
        assert response.status_code == status.HTTP_200_OK
        
        assert await service_container.anonymous_access_service.ip_rate_limiter.get_current_count(ip_address) == 0
        
        
    @pytest.mark.asyncio(loop_scope="session")
    async def test_user_does_not_exist(self, async_client, service_container: ServiceContainer):
        user_access_data = await service_container.user_access_cache_service.create_anonymous_access()
        
        payload = {
            "email": "test_user@example.com",
            "password": "password123",
        }
        
        async_client.cookies.set("bk_access_token", user_access_data.access_token)
        
        response = await async_client.post("/api/auth/login", json=payload)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.cookies.get("bk_access_token") is None
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
        
        async_client.cookies.set("bk_access_token", user_access_data.access_token)
        
        response = await async_client.post("/api/auth/login", json=payload)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.cookies.get("bk_access_token") is None
        assert_deep_equal(response.json(), {"detail": {"message": "Invalid credentials"}})
        
    @pytest.mark.asyncio(loop_scope="session")
    async def test_missing_email(self, async_client, service_container: ServiceContainer):  
        user_access_data = await service_container.user_access_cache_service.create_anonymous_access()
        
        payload = {
            "password": "password123",
        }
        
        async_client.cookies.set("bk_access_token", user_access_data.access_token)
        
        response = await async_client.post("/api/auth/login", json=payload)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert response.cookies.get("bk_access_token") is None
        
    @pytest.mark.asyncio(loop_scope="session")
    async def test_missing_password(self, async_client, service_container: ServiceContainer):
        user_access_data = await service_container.user_access_cache_service.create_anonymous_access()
        
        payload = {
            "email": "test@example.com",
        }
        
        async_client.cookies.set("bk_access_token", user_access_data.access_token)
        
        response = await async_client.post("/api/auth/login", json=payload)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert response.cookies.get("bk_access_token") is None
        
    @pytest.mark.asyncio(loop_scope="session")
    async def test_invalid_email(self, async_client, service_container: ServiceContainer):
        user_access_data = await service_container.user_access_cache_service.create_anonymous_access()
        
        payload = {
            "email": "invalid_email",
            "password": "password123",
        }
        
        async_client.cookies.set("bk_access_token", user_access_data.access_token)
        
        response = await async_client.post("/api/auth/login", json=payload)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert response.cookies.get("bk_access_token") is None