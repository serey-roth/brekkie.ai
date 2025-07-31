from datetime import datetime, timezone
from uuid import uuid4

import pytest
from unittest.mock import patch, MagicMock
from jose.exceptions import JWTError

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

import ssl

@pytest.fixture
def sample_supabase_token(service_container: ServiceContainer, sample_ip_address: str):
    return 'test_token'

@pytest.fixture
def mock_supabase_jwks():
    """Mock Supabase JWKS endpoint response"""
    mock_response = MagicMock()
    mock_response.read.return_value = b'''{
        "keys": [
            {
                "kty": "oct",
                "kid": "test-kid",
                "use": "sig",
                "k": "test-key"
            }
        ]
    }'''
    
    with patch('api.routes.auth.urlopen', return_value=mock_response):
        yield mock_response

@pytest.fixture
def mock_jwt_decode():
    """Mock JWT decode to return a valid payload"""
    mock_payload = {
        "sub": "supabase|test-user-id",
        "aud": "authenticated",
        "iss": "https://test-project.supabase.co",
        "exp": 9999999999,
        "iat": 1234567890,
        "email": "test@test.com",
        "user_metadata": {
            "name": "Test User"
        }
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
    with patch('api.routes.auth.jwk_construct', return_value=mock_public_key):
        yield mock_public_key

class TestVerifyJWT:
    @pytest.mark.asyncio(loop_scope="session")
    async def test_success(self, async_client, service_container: ServiceContainer, sample_ip_address: str, sample_supabase_token: str, mock_supabase_jwks, mock_jwt_decode, mock_jwt_header, mock_jwk_construct):        
        headers = {
            "fly-client-ip": sample_ip_address,
            "Authorization": f"Bearer {sample_supabase_token}"
        }
        
        response = await async_client.post("/api/auth/verify-jwt", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["user_id"] is not None
        assert response.json()["access_token"] is not None
        assert response.json()["is_authenticated"] is True
        assert response.json()["user_message_count"] == 0
        assert response.json()["ip_address"] == sample_ip_address
    
    @pytest.mark.asyncio(loop_scope="session")
    async def test_missing_supabase_token(self, async_client, service_container: ServiceContainer, sample_ip_address: str):
        headers = {
            "fly-client-ip": sample_ip_address,
        }
        response = await async_client.post("/api/auth/verify-jwt", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"]["message"] == "Missing JWT token"
        
        headers = {
            "fly-client-ip": sample_ip_address,
            "Authorization": "Invalid authorization"
        }
        response = await async_client.post("/api/auth/verify-jwt", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"]["message"] == "Missing JWT token"
        
    @pytest.mark.asyncio(loop_scope="session")
    async def test_invalid_supabase_token(self, async_client, service_container: ServiceContainer, sample_ip_address: str, mock_jwk_construct):
        headers = {
            "fly-client-ip": sample_ip_address,
            "Authorization": "Bearer invalid_token" 
        }

        with patch('api.routes.auth.urlopen', return_value=MagicMock(read=lambda: b'{"keys": []}')),\
            patch('api.routes.auth.jwt.get_unverified_header', return_value={"kid": "invalid_kid"}):
            response = await async_client.post("/api/auth/verify-jwt", headers=headers)
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            assert response.json()["detail"]["message"] == "Invalid token: no matching key"
            
        with patch('api.routes.auth.jwt.decode', side_effect=JWTError("Invalid token")):
            response = await async_client.post("/api/auth/verify-jwt", headers=headers)
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            assert response.json()["detail"]["message"] == "Invalid token"
            
        with patch('api.routes.auth.urlopen', return_value=MagicMock(read=lambda: b'{"keys": [{"kty": "oct", "kid": "test-kid", "use": "sig", "k": "test-key"}]}')),\
            patch('api.routes.auth.jwt.get_unverified_header', return_value={"kid": "test-kid"}),\
            patch('api.routes.auth.jwt.decode', return_value={}):
            response = await async_client.post("/api/auth/verify-jwt", headers=headers)
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert response.json()["detail"]["message"] == "Invalid token: missing user ID"

    @pytest.mark.asyncio(loop_scope="session")
    async def test_exception(self, async_client, service_container: ServiceContainer, sample_ip_address: str, sample_supabase_token: str, mock_jwt_decode, mock_jwt_header, mock_jwk_construct, mock_supabase_jwks):
        headers = {
            "fly-client-ip": sample_ip_address,
            "Authorization": f"Bearer {sample_supabase_token}"
        }
        
        with patch.object(service_container.user_service, 'get_user_by_external_id', side_effect=Exception("Test exception")):
            response = await async_client.post("/api/auth/verify-jwt", headers=headers)
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert response.json()["detail"]["message"] == "Token verification failed"
            
    @pytest.mark.asyncio(loop_scope="session")
    async def test_existing_user_gets_updated(self, async_client, service_container: ServiceContainer, sample_ip_address: str, sample_supabase_token: str, mock_supabase_jwks, mock_jwt_decode, mock_jwt_header, mock_jwk_construct):
        old_last_signed_in_at = datetime.now(timezone.utc)
        old_user_id = str(uuid4())
        
        # Create existing user in database
        async with service_container.db_transaction_maker() as db: # type: ignore # TODO: linter will complain about missing func param but this setup passes the tests
            await service_container.user_service.create_user(db, CreateUserParams(
                id=old_user_id,
                external_id="supabase|test-user-id",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                last_signed_in_at=old_last_signed_in_at,
                email="old@test.com",
                name="Old User"
            ))
        
        headers = {
            "fly-client-ip": sample_ip_address,
            "Authorization": f"Bearer {sample_supabase_token}"
        }
        
        response = await async_client.post("/api/auth/verify-jwt", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        
        # Check that user was updated with new email and name
        async with service_container.db_transaction_maker() as db: # type: ignore # TODO: linter will complain about missing func param but this setup passes the tests
            updated_user = await service_container.user_service.get_user_by_id(db, old_user_id)
            assert updated_user is not None
            assert updated_user.email == "test@test.com"
            assert updated_user.name == "Test User"
            assert updated_user.last_signed_in_at != old_last_signed_in_at
        
        new_user_access = response.json()
        assert new_user_access["user_id"] is not None
        assert new_user_access["is_authenticated"] is True
        
    @pytest.mark.asyncio(loop_scope="session")
    async def test_auth_disabled(self, async_client, service_container: ServiceContainer, test_settings: Settings, sample_ip_address: str):
        from api.main import app
        from api.deps import get_settings
        new_settings = test_settings.model_copy(update={"enable_auth": False})
        app.dependency_overrides[get_settings] = lambda: new_settings
        
        user_access = await service_container.user_access_cache_service.create_anonymous_access(sample_ip_address)
        
        async_client.cookies.set("bk_access_token", user_access.access_token)
        
        try:
            response = await async_client.post("/api/auth/verify-jwt", headers={
                "fly-client-ip": sample_ip_address,
                "Authorization": f"Bearer {sample_supabase_token}"
            })   
            assert response.status_code == status.HTTP_403_FORBIDDEN
            assert_deep_equal(response.json(), {"detail": {"message": "Auth is disabled"}})
        
        finally:
            app.dependency_overrides = {}

    @pytest.mark.asyncio(loop_scope="session")
    async def test_user_update_with_existing_email(self, async_client, service_container: ServiceContainer, sample_ip_address: str, sample_supabase_token: str, mock_supabase_jwks, mock_jwt_decode, mock_jwt_header, mock_jwk_construct):
        headers = {
            "fly-client-ip": sample_ip_address,
            "Authorization": f"Bearer {sample_supabase_token}"
        }
        
        old_user_id = str(uuid4())      
        async with service_container.db_transaction_maker() as db: # type: ignore
            await service_container.user_service.create_user(db, CreateUserParams(
                id=old_user_id,
                external_id="different-external-id",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                last_signed_in_at=datetime.now(timezone.utc),
                email="test@test.com",  # Same email as JWT
                name="Old User"
            ))
        
        response = await async_client.post("/api/auth/verify-jwt", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        
        async with service_container.db_transaction_maker() as db: # type: ignore
            user = await service_container.user_service.get_user_by_id(db, old_user_id)
            assert user is not None
            assert user.external_id == "supabase|test-user-id"
            assert user.email == "test@test.com"
            assert user.name == "Test User"

    @pytest.mark.asyncio(loop_scope="session")
    async def test_existing_user_message_count(self, async_client, service_container: ServiceContainer, sample_ip_address: str, sample_supabase_token: str, mock_supabase_jwks, mock_jwt_decode, mock_jwt_header, mock_jwk_construct):
        """Test that existing user's message count is preserved"""
        old_user_id = str(uuid4())
        
        # Create existing user in database
        async with service_container.db_transaction_maker() as db: # type: ignore
            await service_container.user_service.create_user(db, CreateUserParams(
                id=old_user_id,
                external_id="supabase|test-user-id",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                last_signed_in_at=datetime.now(timezone.utc),
                email="test@test.com",
                name="Test User"
            ))
        
        # Mock message count to return a specific value
        with patch.object(service_container.message_service, 'count_total_messages_sent_by_user', return_value=5):
            headers = {
                "fly-client-ip": sample_ip_address,
                "Authorization": f"Bearer {sample_supabase_token}"
            }
            
            response = await async_client.post("/api/auth/verify-jwt", headers=headers)
            assert response.status_code == status.HTTP_200_OK
            
            response_data = response.json()
            assert response_data["user_message_count"] == 5
