from datetime import datetime, timezone
from uuid import uuid4

import pytest
from unittest.mock import patch, MagicMock
from jose.exceptions import JWTError

import asyncio
from fastapi import status

from config.settings import Settings

from services.service_container import ServiceContainer

from schemas.users import CreateUserParams
from schemas.threads import Thread, GetUserThreadsParams
from schemas.messages import Message, GetMessagesParams
from schemas.recipes import UserRecipe, RecipeIngredient, RecipeInstruction, RecipeCategory
from schemas.message_role import MessageRole
from schemas.message_content_type import MessageContentType

from tests.test_helpers.assert_deep_equal import assert_deep_equal
from utils.date_utils import to_utc_isostring

@pytest.fixture
def sample_auth0_token(service_container: ServiceContainer, sample_ip_address: str):
    return 'test_token'

@pytest.fixture
def mock_auth0_jwks():
    """Mock Auth0 JWKS endpoint response"""
    mock_response = MagicMock()
    mock_response.read.return_value = b'''{
        "keys": [
            {
                "kty": "RSA",
                "kid": "test-kid",
                "use": "sig",
                "n": "test-n",
                "e": "AQAB"
            }
        ]
    }'''
    
    with patch('api.routes.auth.urlopen', return_value=mock_response):
        yield mock_response

@pytest.fixture
def mock_jwt_decode():
    """Mock JWT decode to return a valid payload"""
    mock_payload = {
        "sub": "auth0|test-user-id",
        "aud": "https://brekkie-ai.fly.dev/api",
        "iss": "https://dev-1oqfxpe3kn4ryzgd.us.auth0.com/",
        "exp": 9999999999,
        "iat": 1234567890
    }
    
    with patch('api.routes.auth.jwt.decode', return_value=mock_payload):
        yield mock_payload

@pytest.fixture
def mock_jwt_header():
    """Mock JWT header to return a valid header"""
    mock_header = {"kid": "test-kid"}
    with patch('api.routes.auth.jwt.get_unverified_header', return_value=mock_header):
        yield mock_header

@pytest.fixture
def mock_jwk_construct():
    """Mock JWK construct to return a valid public key"""
    mock_public_key = MagicMock()
    with patch('api.routes.auth.jwk.construct', return_value=mock_public_key):
        yield mock_public_key

class TestVerifyToken:
    @pytest.mark.asyncio(loop_scope="session")
    async def test_successful_verify(self, async_client, service_container: ServiceContainer, sample_ip_address: str, sample_auth0_token: str, mock_auth0_jwks, mock_jwt_decode, mock_jwt_header, mock_jwk_construct):
        user_access = await service_container.user_access_cache_service.create_anonymous_access(sample_ip_address)
        
        
        headers = {
            "fly-client-ip": sample_ip_address,
            "Authorization": f"Bearer {sample_auth0_token}"
        }
        
        async_client.cookies.set("bk_access_token", user_access.access_token)

        response = await async_client.post("/api/auth/verify-token", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["user_id"] == user_access.user_id
        assert response.json()["access_token"] is not None
        assert response.json()["is_authenticated"] is True
        assert response.json()["ip_address"] == sample_ip_address
        assert response.json()["user_message_count"] == 0
        
        assert response.cookies.get("bk_access_token") is not None
        
        assert await service_container.anonymous_access_service.ip_rate_limiter.get_current_anonymous_access_count(sample_ip_address) == 0
        
        old_user_access = await service_container.user_access_cache_service.get_user_access(user_access.access_token)
        assert old_user_access is None
        
    @pytest.mark.asyncio(loop_scope="session")
    async def test_data_migration_successful(self, async_client, service_container: ServiceContainer, sample_ip_address: str, sample_auth0_token: str, mock_auth0_jwks, mock_jwt_decode, mock_jwt_header, mock_jwk_construct):
        user_access = await service_container.user_access_cache_service.create_anonymous_access(sample_ip_address)
        old_user_id = user_access.user_id
        
        sample_thread = Thread(
            id="anon123",
            user_id=old_user_id,
            created_at=to_utc_isostring(datetime.now()),
            updated_at=to_utc_isostring(datetime.now()),
            resumed_at=to_utc_isostring(datetime.now()),
            is_empty=False,
            title="Test Thread",
            summary="Test summary",
            error_message=None
        )
        
        sample_recipe = UserRecipe(
            id="anon123",
            user_id=old_user_id,
            thread_id=sample_thread.id,
            created_at=to_utc_isostring(datetime.now()),
            updated_at=to_utc_isostring(datetime.now()),
            name="Test Recipe",
            description="A test recipe",
            ingredients=[RecipeIngredient(name="ingredient 1", quantity="1", unit="unit")],
            instructions=[RecipeInstruction(title="step 1", description="step 1")],
            categories=[RecipeCategory(name="main dish")],
            prep_time_minutes=15,
            cook_time_minutes=30,
            servings="4 servings",
            chef_notes="Test notes",
            substitutions=None,
            equipment_alternatives=None,
            scaling_guidance="Test guidance",
            storage_notes="Test storage",
            serving_suggestions="Test serving",
            make_ahead_tips="Test tips",
            coordination_timeline="Test timeline"
        )
        
        sample_message = Message(
            id="anon123",
            user_id=old_user_id,
            thread_id=sample_thread.id,
            role=MessageRole.user,
            content_type=MessageContentType.text,
            text_content="Hello, world!",
            created_at=to_utc_isostring(datetime.now()),
            updated_at=to_utc_isostring(datetime.now()),
            model_name="gpt-4",
            input_tokens=10,
            output_tokens=20,
            tool_name=None,
            tool_input=None,
            tool_output=None,
            recipe_id=sample_recipe.id,
            is_recipe_generation_started=False,
            is_recipe_generation_completed=True
        )
        
        await service_container.thread_cache_service.set_thread(sample_thread)
        await service_container.message_cache_service.set_message(user_id=old_user_id, message=sample_message)
        await service_container.recipe_cache_service.set_recipe(sample_recipe)
        
        cached_threads = await service_container.thread_cache_service.get_threads(old_user_id)
        cached_messages = await service_container.message_cache_service.get_messages_by_user_id(old_user_id)
        cached_recipes = await service_container.recipe_cache_service.get_recipes_by_user_id(old_user_id)
        
        assert len(cached_threads) == 1
        assert len(cached_messages) == 1
        assert len(cached_recipes) == 1
                
        headers = {
            "fly-client-ip": sample_ip_address,
            "Authorization": f"Bearer {sample_auth0_token}"
        }
        
        async_client.cookies.set("bk_access_token", user_access.access_token)

        response = await async_client.post("/api/auth/verify-token", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        
        new_user_access = response.json()
        
        assert isinstance(new_user_access["user_id"], str)
        assert new_user_access["access_token"] is not None
        assert new_user_access["access_token"] != user_access.access_token
        assert new_user_access["user_id"] == old_user_id
        assert new_user_access["is_authenticated"] is True
        assert new_user_access["user_message_count"] == 1
        assert new_user_access["ip_address"] == sample_ip_address
        
        new_user_id = new_user_access["user_id"]
        
        # Execute migration directly (like a background task would)
        await asyncio.sleep(0.1)
    
        # Check both cache and database for migrated data
        cached_threads = await service_container.thread_cache_service.get_threads(old_user_id)
        cached_messages = await service_container.message_cache_service.get_messages_by_user_id(old_user_id)
        cached_recipes = await service_container.recipe_cache_service.get_recipes_by_user_id(old_user_id)
        
        # Old user data should be deleted from cache
        assert len(cached_threads) == 0
        assert len(cached_messages) == 0
        assert len(cached_recipes) == 0
                
        # User data should be migrated to db - use separate sessions like in production
        async with service_container.db_transaction_maker() as db: # type: ignore # TODO: linter will complain about missing func param but this setup passes the tests
            db_thread = await service_container.thread_service.get_thread(db, sample_thread.id)
            assert db_thread is not None
            assert db_thread.user_id == new_user_id
            
            db_paginated_threads = await service_container.thread_service.get_paginated_threads(db, GetUserThreadsParams(user_id=new_user_id))
            db_paginated_messages = await service_container.message_service.get_paginated_messages(db, GetMessagesParams(user_id=new_user_id, thread_id=sample_thread.id))
            db_recipes = await service_container.recipe_service.get_user_recipes(db, user_id=new_user_id)
        
            assert len(db_paginated_threads.threads) == 1  
            assert len(db_paginated_messages.messages) == 1
            assert len(db_recipes) == 1
            
        old_user_access = await service_container.user_access_cache_service.get_user_access(user_access.access_token)
        assert old_user_access is None
    
    @pytest.mark.asyncio(loop_scope="session")
    async def test_missing_auth0_token(self, async_client, service_container: ServiceContainer, sample_ip_address: str):
        user_access = await service_container.user_access_cache_service.create_anonymous_access(sample_ip_address)
        
        headers = {
            "fly-client-ip": sample_ip_address,
        }
        response = await async_client.post("/api/auth/verify-token", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"]["message"] == "Missing auth0 token"
        
        headers = {
            "fly-client-ip": sample_ip_address,
            "Authorization": "Invalid authorization"
        }
        response = await async_client.post("/api/auth/verify-token", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"]["message"] == "Missing auth0 token"
        
    @pytest.mark.asyncio(loop_scope="session")
    async def test_invalid_auth0_token(self, async_client, service_container: ServiceContainer, sample_ip_address: str, mock_jwk_construct):
        user_access = await service_container.user_access_cache_service.create_anonymous_access(sample_ip_address)
        
        headers = {
            "fly-client-ip": sample_ip_address,
            "Authorization": "Bearer invalid_token" 
        }
        
        async_client.cookies.set("bk_access_token", user_access.access_token)
        
        with patch('api.routes.auth.urlopen', return_value=MagicMock(read=lambda: b'{"keys": []}')),\
            patch('api.routes.auth.jwt.get_unverified_header', return_value={"kid": "invalid_kid"}):
            response = await async_client.post("/api/auth/verify-token", headers=headers)
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            assert response.json()["detail"]["message"] == "Invalid token"
            
            
        with patch('api.routes.auth.jwt.decode', side_effect=JWTError("Invalid token")):
            response = await async_client.post("/api/auth/verify-token", headers=headers)
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            assert response.json()["detail"]["message"] == "Invalid token"
            
        with patch('api.routes.auth.urlopen', return_value=MagicMock(read=lambda: b'{"keys": [{"kty": "RSA", "kid": "test-kid", "use": "sig", "n": "test-n", "e": "AQAB"}]}')),\
            patch('api.routes.auth.jwt.get_unverified_header', return_value={"kid": "test-kid"}),\
            patch('api.routes.auth.jwt.decode', return_value={}):
            response = await async_client.post("/api/auth/verify-token", headers=headers)
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert response.json()["detail"]["message"] == "Invalid token: missing user ID"
            
    @pytest.mark.asyncio(loop_scope="session")
    async def test_access_token_not_found(self, async_client, service_container: ServiceContainer, sample_ip_address: str):
        user_access = await service_container.user_access_cache_service.create_anonymous_access(sample_ip_address)
        
        headers = {
            "fly-client-ip": sample_ip_address,
            "Authorization": f"Bearer {sample_auth0_token}"
        }
                
        response = await async_client.post("/api/auth/verify-token", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"]["message"] == "Missing access token"
        
    @pytest.mark.asyncio(loop_scope="session")
    async def test_access_record_not_found(self, async_client, service_container: ServiceContainer, sample_ip_address: str):
        headers = {
            "fly-client-ip": sample_ip_address,
            "Authorization": f"Bearer {sample_auth0_token}"
        }
        
        async_client.cookies.set("bk_access_token", "invalid_token")
                
        response = await async_client.post("/api/auth/verify-token", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"]["message"] == "Access record not found"
        
    @pytest.mark.asyncio(loop_scope="session")
    async def test_exception(self, async_client, service_container: ServiceContainer, sample_ip_address: str, sample_auth0_token: str, mock_jwt_decode, mock_jwt_header, mock_jwk_construct, mock_auth0_jwks):
        user_access = await service_container.user_access_cache_service.create_anonymous_access(sample_ip_address)
        
        headers = {
            "fly-client-ip": sample_ip_address,
            "Authorization": f"Bearer {sample_auth0_token}"
        }
        
        async_client.cookies.set("bk_access_token", user_access.access_token)
        
        with patch.object(service_container.user_access_cache_service, 'get_user_access', side_effect=Exception("Test exception")):
            response = await async_client.post("/api/auth/verify-token", headers=headers)
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert response.json()["detail"]["message"] == "Token verification failed"

    @pytest.mark.asyncio(loop_scope="session")
    async def test_user_already_authenticated(self, async_client, service_container: ServiceContainer, sample_ip_address: str, sample_auth0_token: str, mock_jwt_decode, mock_jwt_header, mock_jwk_construct, mock_auth0_jwks):
        user_access = await service_container.user_access_cache_service.create_anonymous_access(sample_ip_address)
        await service_container.user_access_cache_service.promote_to_authenticated(
            access_token=user_access.access_token,
            user_id=user_access.user_id,
            updated_at=to_utc_isostring(datetime.now(timezone.utc)),
            user_message_count=0,
        )
        
        async with service_container.db_transaction_maker() as db: # type: ignore # TODO: linter will complain about missing func param but this setup passes the tests
            await service_container.user_service.create_user(db, CreateUserParams(
                id=user_access.user_id,
                external_id="auth0|test-user-id",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            ))
        
        headers = {
            "fly-client-ip": sample_ip_address,
            "Authorization": f"Bearer {sample_auth0_token}"
        }
        
        async_client.cookies.set("bk_access_token", user_access.access_token)
        
        response = await async_client.post("/api/auth/verify-token", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        
        new_user_access = response.json()
        assert new_user_access["user_id"] == user_access.user_id
        assert new_user_access["access_token"] == user_access.access_token
        assert new_user_access["is_authenticated"] is True
        assert new_user_access["user_message_count"] == 0
        assert new_user_access["ip_address"] == sample_ip_address
        
    @pytest.mark.asyncio(loop_scope="session")
    async def test_user_not_authenticated(self, async_client, service_container: ServiceContainer, sample_ip_address: str, sample_auth0_token: str, mock_jwt_decode, mock_jwt_header, mock_jwk_construct, mock_auth0_jwks):
        user_access = await service_container.user_access_cache_service.create_anonymous_access(sample_ip_address)
        
        async with service_container.db_transaction_maker() as db: # type: ignore # TODO: linter will complain about missing func param but this setup passes the tests
            await service_container.user_service.create_user(db, CreateUserParams(
                id=user_access.user_id,
                external_id="auth0|test-user-id",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            ))
        
        headers = {
            "fly-client-ip": sample_ip_address,
            "Authorization": f"Bearer {sample_auth0_token}"
        }
        
        async_client.cookies.set("bk_access_token", user_access.access_token)
        
        response = await async_client.post("/api/auth/verify-token", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        
        new_user_access = response.json()
        assert new_user_access["user_id"] == user_access.user_id
        assert new_user_access["access_token"] != user_access.access_token
        assert new_user_access["is_authenticated"] is True
        assert new_user_access["user_message_count"] == 0
        assert new_user_access["ip_address"] == sample_ip_address
        
        async with service_container.db_transaction_maker() as db: # type: ignore # TODO: linter will complain about missing func param but this setup passes the tests
            old_user_access = await service_container.user_access_cache_service.get_user_access(user_access.access_token)
            assert old_user_access is None
            
            rate_limit = await service_container.anonymous_access_service.ip_rate_limiter.get_current_anonymous_access_count(sample_ip_address)
            assert rate_limit == 0
            
        assert response.cookies.get("bk_access_token") is not None
        assert response.cookies.get("bk_access_token") != user_access.access_token
        
    @pytest.mark.asyncio(loop_scope="session")
    async def test_auth0_token_expired(self, async_client, service_container: ServiceContainer, test_settings: Settings, sample_ip_address: str, sample_auth0_token: str, mock_jwt_header, mock_jwk_construct, mock_auth0_jwks):
        user_access = await service_container.user_access_cache_service.create_anonymous_access(sample_ip_address)
        
        headers = {
            "fly-client-ip": sample_ip_address,
            "Authorization": f"Bearer {sample_auth0_token}"
        }
        
        async_client.cookies.set("bk_access_token", user_access.access_token)
        
        with patch('api.routes.auth.jwt.decode', return_value={"sub": "auth0|test-user-id", "exp": 100, "iat": 1715808000, "aud":"https://brekkie-ai.fly.dev/api", "iss": "https://dev-1oqfxpe3kn4ryzgd.us.auth0.com/"}):
            response = await async_client.post("/api/auth/verify-token", headers=headers)
            assert response.status_code == status.HTTP_200_OK
            
            # Get the new access token from the response
            new_user_access = response.json()
            new_access_token = new_user_access["access_token"]
            
            # Check that the old access token is revoked
            old_ttl = await service_container.user_access_cache_service.get_ttl(user_access.access_token)
            assert old_ttl is None or old_ttl == -2  # -2 means key doesn't exist in Redis
            
            # Check that the new access token has the correct TTL
            new_ttl = await service_container.user_access_cache_service.get_ttl(new_access_token)
            assert new_ttl is not None
            assert new_ttl == test_settings.user_access_cache_ttl
            
    @pytest.mark.asyncio(loop_scope="session")
    async def test_auth0_token_wrong_audience(self, async_client, service_container: ServiceContainer, test_settings: Settings, sample_ip_address: str, sample_auth0_token: str, mock_jwt_header, mock_jwk_construct, mock_auth0_jwks):
        user_access = await service_container.user_access_cache_service.create_anonymous_access(sample_ip_address)
        
        headers = {
            "fly-client-ip": sample_ip_address,
            "Authorization": f"Bearer {sample_auth0_token}"
        }
        
        async_client.cookies.set("bk_access_token", user_access.access_token)
        
        with patch('api.routes.auth.jwt.decode', side_effect=JWTError("Invalid audience")):
            response = await async_client.post("/api/auth/verify-token", headers=headers)
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            assert response.json()["detail"]["message"] == "Invalid token"
            
    @pytest.mark.asyncio(loop_scope="session")
    async def test_auth0_token_wrong_domain(self, async_client, service_container: ServiceContainer, test_settings: Settings, sample_ip_address: str, sample_auth0_token: str, mock_jwt_header, mock_jwk_construct, mock_auth0_jwks):
        user_access = await service_container.user_access_cache_service.create_anonymous_access(sample_ip_address)
        
        headers = {
            "fly-client-ip": sample_ip_address,
            "Authorization": f"Bearer {sample_auth0_token}"
        }
        
        async_client.cookies.set("bk_access_token", user_access.access_token)
        
        with patch('api.routes.auth.jwt.decode', side_effect=JWTError("Invalid issuer")):
            response = await async_client.post("/api/auth/verify-token", headers=headers)
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            assert response.json()["detail"]["message"] == "Invalid token"
            
    @pytest.mark.asyncio(loop_scope="session")
    async def test_auth_disabled(self, async_client, service_container: ServiceContainer, test_settings: Settings, sample_ip_address: str):
        from api.main import app
        from api.deps import get_settings
        new_settings = test_settings.model_copy(update={"enable_auth": False})
        app.dependency_overrides[get_settings] = lambda: new_settings
        
        user_access = await service_container.user_access_cache_service.create_anonymous_access(sample_ip_address)
        
        async_client.cookies.set("bk_access_token", user_access.access_token)
        
        try:
            response = await async_client.post("/api/auth/verify-token", headers={
                "fly-client-ip": sample_ip_address,
                "Authorization": f"Bearer {sample_auth0_token}"
            })   
            assert response.status_code == status.HTTP_403_FORBIDDEN
            assert_deep_equal(response.json(), {"detail": {"message": "Auth is disabled"}})
        
        finally:
            app.dependency_overrides = {}
