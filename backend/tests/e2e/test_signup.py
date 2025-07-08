from datetime import datetime, timezone
from uuid import uuid4

import pytest
from unittest.mock import patch

import asyncio
from fastapi import status

from config.settings import Settings

from services.service_container import ServiceContainer

from schemas.users import CreateUserParams
from schemas.threads import Thread, GetUserThreadsParams
from schemas.messages import Message, GetMessagesParams
from schemas.recipes import Recipe, RecipeIngredient, RecipeInstruction, RecipeCategory

from tests.test_helpers.assert_deep_equal import assert_deep_equal
from utils.date_utils import to_utc_isostring


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
        
        ip_address = "192.168.1.100"
        headers = {
            "fly-client-ip": ip_address
        }
        
        async_client.cookies.set("bk_access_token", user_access_data.access_token)

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
        
        assert response.cookies.get("bk_access_token") is not None
        
        assert await service_container.anonymous_access_service.ip_rate_limiter.get_current_count(ip_address) == 0
        
        old_user_access_data = await service_container.user_access_cache_service.get_user_access(user_access_data.access_token)
        assert old_user_access_data is None
        
    @pytest.mark.asyncio(loop_scope="session")
    async def test_signup_with_rate_limit_exceeded(self, async_client, service_container: ServiceContainer):
        user_access_data = await service_container.user_access_cache_service.create_anonymous_access()
        
        payload = {
            "email": "new@example.com",
            "name": "New User",
            "password": "password123",  
            "confirm_password": "password123"
        }
        
        ip_address = "192.168.1.100"
        headers = {
            "fly-client-ip": ip_address
        }
        
        await service_container.anonymous_access_service.ip_rate_limiter.increment(ip_address)
        
        async_client.cookies.set("bk_access_token", user_access_data.access_token)
        
        response = await async_client.post("/api/auth/signup", json=payload, headers=headers)
        assert response.status_code == status.HTTP_200_OK
        
        assert await service_container.anonymous_access_service.ip_rate_limiter.get_current_count(ip_address) == 0
        
    @pytest.mark.asyncio(loop_scope="session")
    async def test_signup_with_auth_disabled(self, async_client, service_container: ServiceContainer, settings: Settings):
        settings.enable_auth = False
        response = await async_client.post("/api/auth/signup", json={})
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert_deep_equal(response.json(), {"detail": {"message": "Feature temporarily unavailable. Please check back later."}})

    @pytest.mark.asyncio(loop_scope="session")
    async def test_passwords_dont_match(self, async_client, service_container: ServiceContainer):
        user_access_data = await service_container.user_access_cache_service.create_anonymous_access()
        
        payload = {
            "email": "new@example.com",
            "name": "New User",
            "password": "password123",
            "confirm_password": "different_password"
        }
        headers = {
            "fly-client-ip": "192.168.1.100"
        }
        
        async_client.cookies.set("bk_access_token", user_access_data.access_token)

        response = await async_client.post("/api/auth/signup", json=payload, headers=headers)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert response.cookies.get("bk_access_token") is None

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
        headers = {
            "fly-client-ip": "192.168.1.100"
        }
        
        async_client.cookies.set("bk_access_token", user_access_data.access_token)

        response = await async_client.post("/api/auth/signup", json=payload, headers=headers)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.cookies.get("bk_access_token") is None
        assert_deep_equal(response.json(), {"detail": {"message": "User already exists"}})

    @pytest.mark.asyncio(loop_scope="session")
    async def test_missing_token(self, async_client, service_container: ServiceContainer):
        payload = {
            "email": "new@example.com",
            "name": "New User",
            "password": "password123",
            "confirm_password": "password123"
        }

        headers = {
            "fly-client-ip": "192.168.1.100"
        }
        
        response = await async_client.post("/api/auth/signup", json=payload, headers=headers)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.cookies.get("bk_access_token") is None

    @pytest.mark.asyncio(loop_scope="session")
    async def test_invalid_token(self, async_client, service_container: ServiceContainer):
        payload = {
            "email": "new@example.com",
            "name": "New User",
            "password": "password123",
            "confirm_password": "password123"
        }
        
        headers = {
            "fly-client-ip": "192.168.1.100"
        }
        
        async_client.cookies.set("bk_access_token", "invalid_token")

        response = await async_client.post("/api/auth/signup", json=payload, headers=headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.cookies.get("bk_access_token") is None
        assert_deep_equal(response.json(), {"detail": {"message": "Access token not found"}})

    @pytest.mark.asyncio(loop_scope="session")
    async def test_already_authenticated(self, async_client, service_container: ServiceContainer):
        user_access_data = await service_container.user_access_cache_service.create_anonymous_access()
        await service_container.user_access_cache_service.promote_to_authenticated(
            access_token=user_access_data.access_token,
            user_id=user_access_data.user_id,
            email="test@example.com",
            name="Test User",
            updated_at=to_utc_isostring(datetime.now(timezone.utc)),
            user_message_count=0,
        )

        payload = {
            "email": "test@example.com",
            "name": "Test User",
            "password": "password123",
            "confirm_password": "password123"
        }
        headers = {
            "fly-client-ip": "192.168.1.100"
        }
        
        async_client.cookies.set("bk_access_token", user_access_data.access_token)

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
        
        assert response.cookies.get("bk_access_token") is None

    @pytest.mark.asyncio(loop_scope="session")
    async def test_invalid_email_format(self, async_client, service_container: ServiceContainer):
        user_access_data = await service_container.user_access_cache_service.create_anonymous_access()
        
        payload = {
            "email": "invalid-email",
            "name": "New User",
            "password": "password123",
            "confirm_password": "password123"
        }
        headers = {
            "fly-client-ip": "192.168.1.100"
        }
        
        async_client.cookies.set("bk_access_token", user_access_data.access_token)

        response = await async_client.post("/api/auth/signup", json=payload, headers=headers)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert response.cookies.get("bk_access_token") is None

    @pytest.mark.asyncio(loop_scope="session")
    async def test_missing_required_fields(self, async_client, service_container: ServiceContainer):
        user_access_data = await service_container.user_access_cache_service.create_anonymous_access()
        
        payload = {
            "email": "test@example.com"
        }
        headers = {
            "fly-client-ip": "192.168.1.100"
        }
        
        async_client.cookies.set("bk_access_token", user_access_data.access_token)

        response = await async_client.post("/api/auth/signup", json=payload, headers=headers)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert response.cookies.get("bk_access_token") is None

    @pytest.mark.asyncio(loop_scope="session")
    async def test_weak_password(self, async_client, service_container: ServiceContainer):
        user_access_data = await service_container.user_access_cache_service.create_anonymous_access()
        
        payload = {
            "email": "test@example.com",
            "name": "Test User",
            "password": "123",
            "confirm_password": "123"
        }
        headers = {
            "fly-client-ip": "192.168.1.100"
        }
        
        async_client.cookies.set("bk_access_token", user_access_data.access_token)

        response = await async_client.post("/api/auth/signup", json=payload, headers=headers)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert response.cookies.get("bk_access_token") is None

    @pytest.mark.asyncio(loop_scope="session")
    async def test_empty_name(self, async_client, service_container: ServiceContainer):
        user_access_data = await service_container.user_access_cache_service.create_anonymous_access()
        
        payload = {
            "email": "test@example.com",
            "name": "",
            "password": "password123",
            "confirm_password": "password123"
        }
        headers = {
            "fly-client-ip": "192.168.1.100"
        }
        
        async_client.cookies.set("bk_access_token", user_access_data.access_token)

        response = await async_client.post("/api/auth/signup", json=payload, headers=headers)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert response.cookies.get("bk_access_token") is None
        
    @pytest.mark.asyncio(loop_scope="session")
    async def test_signup_with_whitespace_in_fields(self, async_client, service_container: ServiceContainer):
        user_access_data = await service_container.user_access_cache_service.create_anonymous_access()

        payload = {
            "email": "  test@example.com  ",
            "name": "  Test User  ",
            "password": "password123",
            "confirm_password": "password123"
        }
        
        headers = {
            "fly-client-ip": "192.168.1.100"
        }
        
        async_client.cookies.set("bk_access_token", user_access_data.access_token)  
        response = await async_client.post("/api/auth/signup", json=payload, headers=headers)

        assert response.status_code == status.HTTP_200_OK
        assert response.cookies.get("bk_access_token") is not None
        
    @pytest.mark.asyncio(loop_scope="session")
    async def test_data_migration_successful(self, async_client, service_container: ServiceContainer):
        user_access_data = await service_container.user_access_cache_service.create_anonymous_access()
        old_user_id = user_access_data.user_id
        
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
        
        sample_recipe = Recipe(
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
            role="user",
            content_type="text",
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
                
        payload = {
            "email": "test_with_data@example.com",
            "name": "Test User with Data",
            "password": "password123",
            "confirm_password": "password123"
        }
        headers = {
            "fly-client-ip": "192.168.1.100"
        }
        
        async_client.cookies.set("bk_access_token", user_access_data.access_token)

        response = await async_client.post("/api/auth/signup", json=payload, headers=headers)

        assert response.status_code == status.HTTP_200_OK
        
        new_user_access_data = response.json()
        
        assert isinstance(new_user_access_data["user_id"], str)
        assert new_user_access_data["access_token"] is not None
        assert new_user_access_data["access_token"] != user_access_data.access_token
        assert new_user_access_data["user_id"] == old_user_id
        assert new_user_access_data["email"] == payload["email"]
        assert new_user_access_data["name"] == payload["name"]
        assert new_user_access_data["is_authenticated"] is True
        assert new_user_access_data["user_message_count"] == 1
        
        new_user_id = new_user_access_data["user_id"]
        
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
        async with service_container.db_transaction_maker() as db:
            db_thread = await service_container.thread_service.get_thread(db, sample_thread.id)
            assert db_thread is not None
            assert db_thread.user_id == new_user_id
            
            db_paginated_threads = await service_container.thread_service.get_paginated_threads(db, GetUserThreadsParams(user_id=new_user_id))
            db_paginated_messages = await service_container.message_service.get_paginated_messages(db, GetMessagesParams(user_id=new_user_id, thread_id=sample_thread.id))
            db_recipes = await service_container.recipe_service.get_user_recipes(db, user_id=new_user_id)
        
            assert len(db_paginated_threads.threads) == 1  
            assert len(db_paginated_messages.messages) == 1
            assert len(db_recipes) == 1
            
        old_user_access_data = await service_container.user_access_cache_service.get_user_access(user_access_data.access_token)
        assert old_user_access_data is None
        
    @pytest.mark.asyncio(loop_scope="session")
    async def test_signup_database_transaction_rollback(self, async_client, service_container):
        user_access_data = await service_container.user_access_cache_service.create_anonymous_access()
        
        payload = {
            "email": "test_rollback@example.com",
            "name": "Test User Rollback",
            "password": "password123",
            "confirm_password": "password123"
        }
        headers = {
            "fly-client-ip": "192.168.1.100"
        }
        
        async_client.cookies.set("bk_access_token", user_access_data.access_token)

        with patch.object(service_container.user_service, 'create_user', side_effect=Exception("Database error")):
            response = await async_client.post("/api/auth/signup", json=payload, headers=headers)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    @pytest.mark.asyncio(loop_scope="session")
    async def test_signup_redis_connection_failure(self, async_client, service_container):
        user_access_data = await service_container.user_access_cache_service.create_anonymous_access()  
        
        payload = {
            "email": "test_redis@example.com",
            "name": "Test User Redis",
            "password": "password123",
            "confirm_password": "password123"
        }
        headers = {
            "fly-client-ip": "192.168.1.100"
        }
        
        async_client.cookies.set("bk_access_token", user_access_data.access_token)

        with patch.object(service_container.user_access_cache_service, 'get_user_access', side_effect=Exception("Redis connection failed")):
            response = await async_client.post("/api/auth/signup", json=payload, headers=headers)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    @pytest.mark.asyncio(loop_scope="session")
    async def test_signup_password_hashing_integration(self, async_client, service_container):
        user_access_data = await service_container.user_access_cache_service.create_anonymous_access()
        
        payload = {
            "email": "test_hashing@example.com",
            "name": "Test User Hashing",
            "password": "password123",
            "confirm_password": "password123"
        }
        headers = {
            "fly-client-ip": "192.168.1.100"
        }
        
        async_client.cookies.set("bk_access_token", user_access_data.access_token)

        response = await async_client.post("/api/auth/signup", json=payload, headers=headers)

        assert response.status_code == status.HTTP_200_OK
        
        async with service_container.db_transaction_maker() as db:
            user = await service_container.user_service.get_user_by_email(db, "test_hashing@example.com")
            assert user is not None
            assert user.email == "test_hashing@example.com"
            assert user.name == "Test User Hashing"

    @pytest.mark.asyncio(loop_scope="session")
    async def test_revoke_old_access_token(self, async_client, service_container):
        user_access_data = await service_container.user_access_cache_service.create_anonymous_access()
        
        payload = {
            "email": "test_token@example.com",
            "name": "Test Token User",
            "password": "password123",
            "confirm_password": "password123"
        }
        headers = {
            "fly-client-ip": "192.168.1.100"
        }

        async_client.cookies.set("bk_access_token", user_access_data.access_token)

        response = await async_client.post("/api/auth/signup", json=payload, headers=headers)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        
        old_user_access_data = await service_container.user_access_cache_service.get_user_access(user_access_data.access_token)
        assert old_user_access_data is None

    @pytest.mark.asyncio(loop_scope="session")
    async def test_signup_cleanup_on_failure(self, async_client, service_container):
        user_access_data = await service_container.user_access_cache_service.create_anonymous_access()
        
        payload = {
            "email": "test_cleanup@example.com",
            "name": "Test Cleanup User",
            "password": "password123",
            "confirm_password": "password123"
        }
        headers = {
            "fly-client-ip": "192.168.1.100"
        }

        async_client.cookies.set("bk_access_token", user_access_data.access_token)

        with patch.object(service_container.user_access_cache_service, 'create_user_access', side_effect=Exception("User access creation failed")):
            response = await async_client.post("/api/auth/signup", json=payload, headers=headers)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        
        async with service_container.db_transaction_maker() as db:
            user = await service_container.user_service.get_user_by_email(db, "test_cleanup@example.com")
            assert user is None 

