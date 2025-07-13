from unittest.mock import patch
import pytest

from datetime import datetime, timezone
from fastapi import status
from uuid import uuid4

from schemas.message_role import MessageRole
from schemas.message_content_type import MessageContentType
from schemas.messages import CreateMessageParams
from services.service_container import ServiceContainer

from schemas.users import CreateUserParams
from schemas.threads import CreateThreadParams

from tests.test_helpers.assert_deep_equal import assert_deep_equal

from config.settings import Settings

pytestmark = pytest.mark.asyncio

class TestLogin:
    @pytest.mark.asyncio(loop_scope="session")
    async def test_successful_login(self, async_client, service_container: ServiceContainer, sample_ip_address: str):
        user_access_data = await service_container.user_access_cache_service.create_anonymous_access(sample_ip_address)
        
        user_id = user_access_data.user_id
        
        async with service_container.db_transaction_maker() as db: # type: ignore # TODO: linter will complain about missing func param but this setup passes the tests
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
                role=MessageRole.user,
                content_type=MessageContentType.text,
                text_content="Hello, world!",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            ))
        
        headers = {
            "fly-client-ip": sample_ip_address
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
        assert response.json()["ip_address"] == sample_ip_address
        
        assert response.cookies.get("bk_access_token") is not None
        
        assert await service_container.anonymous_access_service.ip_rate_limiter.get_current_anonymous_access_count(sample_ip_address) == 0
                
        old_user_access_data = await service_container.user_access_cache_service.get_user_access(user_access_data.access_token)
        assert old_user_access_data is None
        
    @pytest.mark.asyncio(loop_scope="session")
    async def test_login_without_existing_access_token(self, async_client, service_container: ServiceContainer, sample_ip_address: str):
        user_access_data = await service_container.user_access_cache_service.create_anonymous_access(sample_ip_address)
        
        user_id = user_access_data.user_id
        
        async with service_container.db_transaction_maker() as db: # type: ignore # TODO: linter will complain about missing func param but this setup passes the tests
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
                role=MessageRole.user,
                content_type=MessageContentType.text,
                text_content="Hello, world!",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            ))
            
        headers = {
            "fly-client-ip": sample_ip_address
        }
        
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
            
        assert await service_container.anonymous_access_service.ip_rate_limiter.get_current_anonymous_access_count(ip_address) == 0
        
    @pytest.mark.asyncio(loop_scope="session")
    async def test_login_with_rate_limit_exceeded(self, async_client, service_container: ServiceContainer, sample_ip_address: str):
        user_access_data = await service_container.user_access_cache_service.create_anonymous_access(sample_ip_address)
        
        user_id = user_access_data.user_id
        
        async with service_container.db_transaction_maker() as db: # type: ignore # TODO: linter will complain about missing func param but this setup passes the tests
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
                role=MessageRole.user,
                content_type=MessageContentType.text,
                text_content="Hello, world!",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            ))
            
            
        payload = {
            "email": "test@example.com",
            "password": "password123",  
        }
        
        headers = {
            "fly-client-ip": sample_ip_address
        }
        
        await service_container.anonymous_access_service.ip_rate_limiter.increment_anonymous_access_count(sample_ip_address)
        
        async_client.cookies.set("bk_access_token", user_access_data.access_token)
        
        response = await async_client.post("/api/auth/login", json=payload, headers=headers)
        assert response.status_code == status.HTTP_200_OK
        
        assert await service_container.anonymous_access_service.ip_rate_limiter.get_current_anonymous_access_count(sample_ip_address) == 0
        
    @pytest.mark.asyncio(loop_scope="session")
    async def test_login_with_auth_disabled(self, async_client, service_container: ServiceContainer, test_settings: Settings, sample_ip_address: str):
        # TODO: This is a hack to override the settings for the test
        from api.main import app
        from api.deps import get_settings
        new_settings = test_settings.model_copy(update={"enable_auth": False})
        app.dependency_overrides[get_settings] = lambda: new_settings

        try:
            response = await async_client.post("/api/auth/login", json={
                "email": "test@example.com",
                "password": "password123",
            }, headers={})
            
            assert response.status_code == status.HTTP_403_FORBIDDEN
            assert response.cookies.get("bk_access_token") is None
            assert_deep_equal(response.json(), {"detail": {"message": "Feature temporarily unavailable. Please check back later."}})
        finally:
            app.dependency_overrides = {}
        
    @pytest.mark.asyncio(loop_scope="session")
    async def test_user_does_not_exist(self, async_client, service_container: ServiceContainer, sample_ip_address: str):
        user_access_data = await service_container.user_access_cache_service.create_anonymous_access(sample_ip_address)
        
        headers = {
            "fly-client-ip": sample_ip_address
        }
        
        payload = {
            "email": "test_user@example.com",
            "password": "password123",
        }
        
        async_client.cookies.set("bk_access_token", user_access_data.access_token)
        
        response = await async_client.post("/api/auth/login", json=payload, headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.cookies.get("bk_access_token") is None
        assert_deep_equal(response.json(), {"detail": {"message": "User does not exist"}})
        
    @pytest.mark.asyncio(loop_scope="session")
    async def test_invalid_password(self, async_client, service_container: ServiceContainer, sample_ip_address: str):
        user_access_data = await service_container.user_access_cache_service.create_anonymous_access(sample_ip_address)
        
        async with service_container.db_transaction_maker() as db: # type: ignore # TODO: linter will complain about missing func param but this setup passes the tests
            await service_container.user_service.create_user(db, CreateUserParams(
                id=str(uuid4()),
                email="test_user@example.com",
                name="Test User",
                password="password123",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            ))
            
        headers = {
            "fly-client-ip": sample_ip_address
        }
        
        payload = {
            "email": "test_user@example.com",
            "password": "invalid_password",
        }
        
        async_client.cookies.set("bk_access_token", user_access_data.access_token)
        
        response = await async_client.post("/api/auth/login", json=payload, headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.cookies.get("bk_access_token") is None
        assert_deep_equal(response.json(), {"detail": {"message": "Invalid credentials"}})
        
    @pytest.mark.asyncio(loop_scope="session")
    async def test_missing_email(self, async_client, service_container: ServiceContainer, sample_ip_address: str):  
        user_access_data = await service_container.user_access_cache_service.create_anonymous_access(sample_ip_address)
        
        headers = {
            "fly-client-ip": sample_ip_address
        }
        
        payload = {
            "password": "password123",
        }
        
        async_client.cookies.set("bk_access_token", user_access_data.access_token)
        
        response = await async_client.post("/api/auth/login", json=payload, headers=headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert response.cookies.get("bk_access_token") is None
        
    @pytest.mark.asyncio(loop_scope="session")
    async def test_missing_password(self, async_client, service_container: ServiceContainer, sample_ip_address: str):
        user_access_data = await service_container.user_access_cache_service.create_anonymous_access(sample_ip_address)
        
        headers = {
            "fly-client-ip": sample_ip_address
        }
        
        payload = {
            "email": "test@example.com",
        }
        
        async_client.cookies.set("bk_access_token", user_access_data.access_token)
        
        response = await async_client.post("/api/auth/login", json=payload, headers=headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert response.cookies.get("bk_access_token") is None
        
    @pytest.mark.asyncio(loop_scope="session")
    async def test_invalid_email(self, async_client, service_container: ServiceContainer, sample_ip_address: str):
        user_access_data = await service_container.user_access_cache_service.create_anonymous_access(sample_ip_address)
        
        headers = {
            "fly-client-ip": sample_ip_address
        }
        
        payload = {
            "email": "invalid_email",
            "password": "password123",
        }
        
        async_client.cookies.set("bk_access_token", user_access_data.access_token)
        
        response = await async_client.post("/api/auth/login", json=payload, headers=headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert response.cookies.get("bk_access_token") is None