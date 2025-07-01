import pytest

from datetime import datetime, timezone

from unittest.mock import AsyncMock, MagicMock

from services.data_services.thread_service import ThreadService
from services.data_services.thread_cache_service import ThreadCacheService
from services.data_services.message_service import MessageService
from services.data_services.message_cache_service import MessageCacheService
from services.data_services.recipe_service import RecipeService
from services.data_services.recipe_cache_service import RecipeCacheService
from services.data_services.user_access_cache_service import UserAccessCacheService
from services.chat_services.chat_session_store import ChatSessionStore

from schemas.message_content_type import MessageContentType
from schemas.message_role import MessageRole
from schemas.user_access import UserAccessData
from schemas.threads import CreateThreadParams, UpdateThreadParams
from schemas.messages import CreateUserMessageParams, Message
from schemas.recipes import UserRecipe, CreateRecipeParams

from utils.date_utils import to_utc_isostring



@pytest.fixture
def mock_thread_service():
    return MagicMock(spec=ThreadService)


@pytest.fixture
def mock_thread_cache_service():
    return MagicMock(spec=ThreadCacheService)


@pytest.fixture
def mock_message_service():
    return MagicMock(spec=MessageService)


@pytest.fixture
def mock_message_cache_service():
    return MagicMock(spec=MessageCacheService)


@pytest.fixture
def mock_recipe_service():
    return MagicMock(spec=RecipeService)


@pytest.fixture
def mock_recipe_cache_service():
    return MagicMock(spec=RecipeCacheService)


@pytest.fixture
def mock_user_access_cache_service():
    return MagicMock(spec=UserAccessCacheService)


@pytest.fixture
def chat_session_store(mock_thread_service, mock_thread_cache_service, mock_message_service, mock_message_cache_service, mock_recipe_service, mock_recipe_cache_service, mock_user_access_cache_service):
    return ChatSessionStore(
        thread_service=mock_thread_service,
        thread_cache_service=mock_thread_cache_service,
        message_service=mock_message_service,
        message_cache_service=mock_message_cache_service,
        recipe_service=mock_recipe_service,
        recipe_cache_service=mock_recipe_cache_service,
        user_access_cache_service=mock_user_access_cache_service,
    )


class TestDispatch:
    @pytest.mark.asyncio
    async def test_dispatch_authenticated_user(self, chat_session_store: ChatSessionStore):
        user_access_data = MagicMock(spec=UserAccessData)
        user_access_data.is_authenticated = True
        
        authenticated_func = AsyncMock(return_value="authenticated_result")
        unauthenticated_func = AsyncMock(return_value="unauthenticated_result")
        
        result = await chat_session_store._dispatch(
            user_access_data, 
            authenticated_func, 
            unauthenticated_func,
            "arg1", 
            kwarg1="value1"
        )
        
        assert result == "authenticated_result"
        authenticated_func.assert_called_once_with("arg1", kwarg1="value1")
        unauthenticated_func.assert_not_called()
        

    @pytest.mark.asyncio
    async def test_dispatch_unauthenticated_user(self, chat_session_store: ChatSessionStore):
        user_access_data = MagicMock(spec=UserAccessData)
        user_access_data.is_authenticated = False
        
        authenticated_func = AsyncMock(return_value="authenticated_result")
        unauthenticated_func = AsyncMock(return_value="unauthenticated_result")
        
        result = await chat_session_store._dispatch(
            user_access_data, 
            authenticated_func, 
            unauthenticated_func,
            "arg1", 
            kwarg1="value1"
        )
        
        assert result == "unauthenticated_result"
        unauthenticated_func.assert_called_once_with("arg1", kwarg1="value1")
        authenticated_func.assert_not_called()


class TestCreateUserMessage:
    @pytest.mark.asyncio
    async def test_create_first_user_message_authenticated(self, chat_session_store: ChatSessionStore, mock_thread_service: ThreadService, mock_message_service: MessageService, mock_message_cache_service: MessageCacheService):
        user_access_data = MagicMock(spec=UserAccessData)
        user_access_data.is_authenticated = True
        user_access_data.user_id = "user_id"
        user_access_data.access_token = "access_token"
        
        mock_db = MagicMock()
        mock_thread_service.get_thread.return_value = None
        
        thread_id = "thread_id"
        message_id = "message_id"
        timestamp = datetime.now(timezone.utc)
        
        expected_message = Message(
            id=message_id,
            user_id=user_access_data.user_id,
            thread_id=thread_id,
            text_content="content_authenticated",
            role=MessageRole.user,
            content_type=MessageContentType.text,
            created_at=to_utc_isostring(timestamp),
            updated_at=to_utc_isostring(timestamp),
        )
        
        mock_message_service.create_user_message = AsyncMock(return_value=expected_message)
        
        result = await chat_session_store.create_user_message(mock_db, user_access_data, thread_id, message_id, "content_authenticated", timestamp)
        
        assert result == expected_message
        
        mock_thread_service.get_thread.assert_called_once_with(mock_db, thread_id)
        mock_thread_service.create_thread.assert_called_once_with(mock_db, CreateThreadParams(
            id=thread_id,
            user_id=user_access_data.user_id,
            created_at=timestamp,
            updated_at=timestamp,
            is_empty=False,
        ))
        mock_message_service.create_user_message.assert_called_once_with(mock_db, CreateUserMessageParams(
            id=message_id,
            user_id=user_access_data.user_id,
            thread_id=thread_id,
            text_content="content_authenticated",
            created_at=timestamp,
            updated_at=timestamp,
        ))
        
        mock_message_cache_service.create_user_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_user_message_unauthenticated(self, chat_session_store: ChatSessionStore, mock_thread_cache_service: ThreadCacheService, mock_message_cache_service: MessageCacheService, mock_user_access_cache_service: UserAccessCacheService, mock_thread_service: ThreadService, mock_message_service: MessageService):
        user_access_data = MagicMock(spec=UserAccessData)
        user_access_data.is_authenticated = False
        user_access_data.user_id = "user_id"
        user_access_data.access_token = "access_token"
        
        mock_db = MagicMock()
        
        thread_id = "thread_id"
        message_id = "message_id"
        timestamp = datetime.now(timezone.utc)
        
        expected_message = Message(
            id=message_id,
            user_id=user_access_data.user_id,
            thread_id=thread_id,
            text_content="content_unauthenticated",
            role=MessageRole.user,
            content_type=MessageContentType.text,
            created_at=to_utc_isostring(timestamp),
            updated_at=to_utc_isostring(timestamp),
        )
        
        mock_message_cache_service.create_user_message = AsyncMock(return_value=expected_message)
        
        result = await chat_session_store.create_user_message(mock_db, user_access_data, thread_id, message_id, "content_unauthenticated", timestamp)
        
        assert result == expected_message
        
        mock_thread_cache_service.update_thread.assert_called_once_with(user_access_data.user_id, UpdateThreadParams(id=thread_id, updated_at=timestamp, is_empty=False))
        mock_message_cache_service.create_user_message.assert_called_once_with(user_access_data.user_id, CreateUserMessageParams(
            id=message_id,
            user_id=user_access_data.user_id,
            thread_id=thread_id,
            text_content="content_unauthenticated",
            created_at=timestamp,
            updated_at=timestamp,
        ))
        mock_user_access_cache_service.increment_user_message_count.assert_called_once_with(user_access_data.access_token)
        mock_thread_service.get_thread.assert_not_called()
        mock_thread_service.create_thread.assert_not_called()
        mock_message_service.create_user_message.assert_not_called()


class TestCreateRecipe:
    @pytest.mark.asyncio
    async def test_create_recipe_authenticated(self, chat_session_store: ChatSessionStore, mock_recipe_service: RecipeService, mock_recipe_cache_service: RecipeCacheService):
        user_access_data = MagicMock(spec=UserAccessData)
        user_access_data.user_id = "user_id"
        user_access_data.access_token = "access_token"
        user_access_data.is_authenticated = True
        
        mock_db = MagicMock()
        
        thread_id = "thread_id"
        recipe_id = "recipe_id"
        timestamp = datetime.now(timezone.utc)
        
        expected_recipe = UserRecipe(
            id=recipe_id,
            user_id=user_access_data.user_id,
            thread_id=thread_id,
            created_at=to_utc_isostring(timestamp),
            updated_at=to_utc_isostring(timestamp),
        )
        
        mock_recipe_service.create_recipe = AsyncMock(return_value=expected_recipe)
        
        result = await chat_session_store.create_recipe(mock_db, user_access_data, thread_id, recipe_id, timestamp)
        
        assert result == expected_recipe
        
        mock_recipe_service.create_recipe.assert_called_once_with(mock_db, CreateRecipeParams(
            id=recipe_id,
            user_id=user_access_data.user_id,
            thread_id=thread_id,
            created_at=timestamp,
            updated_at=timestamp,
        ))
        mock_recipe_cache_service.create_recipe.assert_not_called()


    @pytest.mark.asyncio
    async def test_create_recipe_unauthenticated(self, chat_session_store: ChatSessionStore, mock_recipe_cache_service: RecipeCacheService, mock_recipe_service: RecipeService):
        user_access_data = MagicMock(spec=UserAccessData)
        user_access_data.is_authenticated = False
        user_access_data.user_id = "user_id"
        user_access_data.access_token = "access_token"
        
        mock_db = MagicMock()
        
        thread_id = "thread_id"
        recipe_id = "recipe_id"
        timestamp = datetime.now(timezone.utc)
        
        expected_recipe = UserRecipe(
            id=recipe_id,
            user_id=user_access_data.user_id,
            thread_id=thread_id,
            created_at=to_utc_isostring(timestamp),
            updated_at=to_utc_isostring(timestamp),
        )
        
        mock_recipe_cache_service.create_recipe = AsyncMock(return_value=expected_recipe)
        
        result = await chat_session_store.create_recipe(mock_db, user_access_data, thread_id, recipe_id, timestamp)
        
        assert result == expected_recipe
        
        mock_recipe_cache_service.create_recipe.assert_called_once_with(CreateRecipeParams(
            id=recipe_id,
            user_id=user_access_data.user_id,
            thread_id=thread_id,
            created_at=timestamp,
            updated_at=timestamp,
        ))
        mock_recipe_service.create_recipe.assert_not_called()


class TestGetRecipesByMessageId:
    @pytest.mark.asyncio
    async def test_get_recipes_by_message_id_authenticated(self, chat_session_store: ChatSessionStore, mock_recipe_service: RecipeService, mock_recipe_cache_service: RecipeCacheService, mock_message_cache_service: MessageCacheService):
        user_access_data = MagicMock(spec=UserAccessData)
        user_access_data.is_authenticated = True
        user_access_data.user_id = "user_id"
        user_access_data.access_token = "access_token"
        
        mock_db = MagicMock()
        
        thread_id = "thread_id"
        message_ids = ["message_id_1", "message_id_2"]
        timestamp = datetime.now(timezone.utc)
        
        expected_recipes = [
            UserRecipe(
                id="recipe_id_1",
                user_id=user_access_data.user_id,
                thread_id=thread_id,
                created_at=to_utc_isostring(timestamp),
                updated_at=to_utc_isostring(timestamp),
            ),
            UserRecipe(
                id="recipe_id_2",
                user_id=user_access_data.user_id,
                thread_id=thread_id,
                created_at=to_utc_isostring(timestamp),
                updated_at=to_utc_isostring(timestamp),
            )
        ]
        
        mock_recipe_service.get_recipes_by_message_id = AsyncMock(return_value=expected_recipes)
        
        result = await chat_session_store.get_recipes_by_message_id(mock_db, user_access_data, thread_id, message_ids)
        
        assert result == expected_recipes
        
        mock_recipe_service.get_recipes_by_message_id.assert_called_once_with(mock_db, message_ids)
        mock_message_cache_service.get_messages_by_id.assert_not_called()
        mock_recipe_cache_service.get_recipes_by_ids.assert_not_called()


    @pytest.mark.asyncio
    async def test_get_recipes_by_message_id_unauthenticated(self, chat_session_store: ChatSessionStore, mock_recipe_cache_service: RecipeCacheService, mock_message_cache_service: MessageCacheService, mock_recipe_service: RecipeService):
        user_access_data = MagicMock(spec=UserAccessData)
        user_access_data.is_authenticated = False
        user_access_data.user_id = "user_id"
        user_access_data.access_token = "access_token"
        
        mock_db = MagicMock()
        
        thread_id = "thread_id"
        message_ids = ["message_id_1", "message_id_2"]
        timestamp = datetime.now(timezone.utc)
        
        mock_messages = [
            Message(
                id="message_id_1",
                user_id=user_access_data.user_id,
                thread_id=thread_id,
                text_content="content_1",
                role=MessageRole.assistant,
                content_type=MessageContentType.recipe,
                recipe_id="recipe_id_1",
                created_at=to_utc_isostring(timestamp),
                updated_at=to_utc_isostring(timestamp),
            ),
            Message(
                id="message_id_2",
                user_id=user_access_data.user_id,
                thread_id=thread_id,
                text_content="content_2",
                role=MessageRole.assistant,
                content_type=MessageContentType.recipe,
                recipe_id="recipe_id_2",
                created_at=to_utc_isostring(timestamp),
                updated_at=to_utc_isostring(timestamp),
            )
        ]
        
        expected_recipes = [
            UserRecipe(
                id="recipe_id_1",
                user_id=user_access_data.user_id,
                thread_id=thread_id,
                created_at=to_utc_isostring(timestamp),
                updated_at=to_utc_isostring(timestamp),
            ),
            UserRecipe(
                id="recipe_id_2",
                user_id=user_access_data.user_id,
                thread_id=thread_id,
                created_at=to_utc_isostring(timestamp),
                updated_at=to_utc_isostring(timestamp),
            )
        ]
        
        mock_message_cache_service.get_messages_by_id.return_value = mock_messages
        mock_recipe_cache_service.get_recipes_by_ids = AsyncMock(return_value=expected_recipes)
        
        result = await chat_session_store.get_recipes_by_message_id(mock_db, user_access_data, thread_id, message_ids)
        
        assert result == expected_recipes
        
        mock_message_cache_service.get_messages_by_id.assert_called_once_with(user_access_data.user_id, thread_id, message_ids)
        mock_recipe_cache_service.get_recipes_by_ids.assert_called_once_with(user_access_data.user_id, thread_id, ["recipe_id_1", "recipe_id_2"])
        mock_recipe_service.get_recipes_by_message_id.assert_not_called()


    @pytest.mark.asyncio
    async def test_get_recipes_by_message_id_unauthenticated_empty_result(self, chat_session_store: ChatSessionStore, mock_recipe_cache_service: RecipeCacheService, mock_message_cache_service: MessageCacheService, mock_recipe_service: RecipeService):
        user_access_data = MagicMock(spec=UserAccessData)
        user_access_data.is_authenticated = False
        user_access_data.user_id = "user_id"
        user_access_data.access_token = "access_token"
        
        mock_db = MagicMock()
        
        thread_id = "thread_id"
        message_ids = ["message_id_1", "message_id_2"]
        timestamp = datetime.now(timezone.utc)
        
        mock_message_cache_service.get_messages_by_id.return_value = []
        
        result = await chat_session_store.get_recipes_by_message_id(mock_db, user_access_data, thread_id, message_ids)
        
        assert result == []
        
        mock_message_cache_service.get_messages_by_id.assert_called_once_with(user_access_data.user_id, thread_id, message_ids)
        mock_recipe_cache_service.get_recipes_by_ids.assert_not_called()
        mock_recipe_service.get_recipes_by_message_id.assert_not_called()

