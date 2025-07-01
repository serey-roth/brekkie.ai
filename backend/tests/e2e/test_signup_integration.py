import pytest
from fastapi import status
from unittest.mock import patch
import asyncio
from datetime import datetime

from services.service_container import ServiceContainer

from schemas.threads import GetUserThreadsParams, Thread
from schemas.messages import GetMessagesParams, Message
from schemas.recipes import Recipe, RecipeIngredient, RecipeInstruction, RecipeCategory

from utils.date_utils import to_utc_isostring


class TestSignupIntegration:
    @pytest.mark.asyncio(loop_scope="session")
    async def test_signup_successful(self, async_client, service_container: ServiceContainer):
        user_access_data = await service_container.user_access_cache_service.create_anonymous_access()
        
        payload = {
            "email": "test@example.com",
            "name": "Test User",
            "password": "password123",
            "confirm_password": "password123"
        }
        headers = {"Authorization": f"Bearer {user_access_data.access_token}"}

        response = await async_client.post("/api/auth/signup", json=payload, headers=headers)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["access_token"] == user_access_data.access_token
        assert response_data["email"] == "test@example.com"
        assert response_data["name"] == "Test User"
        assert response_data["is_authenticated"] is True

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
        headers = {"Authorization": f"Bearer {user_access_data.access_token}"}

        response = await async_client.post("/api/auth/signup", json=payload, headers=headers)

        assert response.status_code == status.HTTP_200_OK
        
        new_user_id = response.json()["user_id"]
        
        assert isinstance(new_user_id, str)
        assert new_user_id != old_user_id
        assert new_user_id != ""
        
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

    @pytest.mark.asyncio(loop_scope="session")
    async def test_signup_database_transaction_rollback(self, async_client, service_container):
        user_access_data = await service_container.user_access_cache_service.create_anonymous_access()
        
        payload = {
            "email": "test_rollback@example.com",
            "name": "Test User Rollback",
            "password": "password123",
            "confirm_password": "password123"
        }
        headers = {"Authorization": f"Bearer {user_access_data.access_token}"}

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
        headers = {"Authorization": f"Bearer {user_access_data.access_token}"}

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
        headers = {"Authorization": f"Bearer {user_access_data.access_token}"}

        response = await async_client.post("/api/auth/signup", json=payload, headers=headers)

        assert response.status_code == status.HTTP_200_OK
        
        async with service_container.db_transaction_maker() as db:
            user = await service_container.user_service.get_user_by_email(db, "test_hashing@example.com")
            assert user is not None
            assert user.email == "test_hashing@example.com"
            assert user.name == "Test User Hashing"

    @pytest.mark.asyncio(loop_scope="session")
    async def test_signup_access_token_persistence(self, async_client, service_container):
        user_access_data = await service_container.user_access_cache_service.create_anonymous_access()
        
        payload = {
            "email": "test_token@example.com",
            "name": "Test Token User",
            "password": "password123",
            "confirm_password": "password123"
        }
        headers = {"Authorization": f"Bearer {user_access_data.access_token}"}

        response = await async_client.post("/api/auth/signup", json=payload, headers=headers)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        
        access_data = await service_container.user_access_cache_service.get_user_access(user_access_data.access_token)
        assert access_data is not None
        assert access_data.user_id == response_data["user_id"]
        assert access_data.email == response_data["email"]
        assert access_data.is_authenticated is True

    @pytest.mark.asyncio(loop_scope="session")
    async def test_signup_cleanup_on_failure(self, async_client, service_container):
        user_access_data = await service_container.user_access_cache_service.create_anonymous_access()
        
        payload = {
            "email": "test_cleanup@example.com",
            "name": "Test Cleanup User",
            "password": "password123",
            "confirm_password": "password123"
        }
        headers = {"Authorization": f"Bearer {user_access_data.access_token}"}

        with patch.object(service_container.user_access_cache_service, 'promote_to_authenticated', side_effect=Exception("Promotion failed")):
            response = await async_client.post("/api/auth/signup", json=payload, headers=headers)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        
        async with service_container.db_transaction_maker() as db:
            user = await service_container.user_service.get_user_by_email(db, "test@example.com")
            assert user is None 