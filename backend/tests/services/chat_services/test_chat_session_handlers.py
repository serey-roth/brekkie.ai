from contextlib import asynccontextmanager
from datetime import datetime, timezone
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch

from schemas.conversation_stream_events import (
    TextMessageCompletedPayload,
    TextMessageStartedPayload, 
    ConversationStreamMetadata,
    TextMessageChunkGeneratedPayload,
    AIAgentErrorPayload,
    RecipeGenerationCompletedPayload,
    RecipeFieldDetectedPayload,
    RecipeGenerationStartedPayload,
    SearchCompletedPayload,
    SearchStartedPayload,
    SummaryUpdatedPayload,
    ThreadTitleUpdatedPayload,
)

from services.chat_services.chat_session_store import ChatSessionStore
from sqlalchemy.ext.asyncio import AsyncSession

from services.chat_services.chat_session_handlers import ChatSessionHandlers

from schemas.messages import (
    Message,
    CreateAssistantTextMessageParams,
    CreateAssistantRecipeMessageParams,
    CreateAssistantToolMessageParams,
    UpdateMessageParams,
)
from schemas.threads import (
    Thread,
    UpdateThreadParams,
)
from schemas.recipes import (
    Recipe,
    UserRecipe,
    RecipeField,
    RecipeIngredient,
    UpdateRecipeParams,
    UpdateRecipeFieldParams,
)
from schemas.user_access import UserAccessData
from schemas.message_role import MessageRole
from schemas.message_content_type import MessageContentType

from utils.date_utils import to_utc_isostring


from tests.utils.assert_deep_equal import assert_deep_equal

@pytest.fixture
def mock_async_session():
    async_session = AsyncMock(spec=AsyncSession)
    return async_session


@pytest_asyncio.fixture
async def mock_db_transaction_maker(mock_async_session):
    db_transaction = mock_async_session
    
    @asynccontextmanager
    async def transaction():
        yield db_transaction
        
    return transaction


@pytest_asyncio.fixture
def mock_chat_session_store():
    chat_session_store = AsyncMock(spec=ChatSessionStore)
    return chat_session_store


@pytest_asyncio.fixture
def chat_session_handlers(mock_db_transaction_maker, mock_chat_session_store):
    return ChatSessionHandlers(
        db_transaction_maker=mock_db_transaction_maker,
        chat_session_store=mock_chat_session_store,
    )
    
    
@pytest.fixture
def sample_user_access_data():
    return UserAccessData(
        user_id="123",
        access_token="123",
        is_authenticated=False,
        user_message_count=1
    )
    
    
class TestAssistantStartedResponding:
    @pytest.mark.asyncio
    async def test_success(self, chat_session_handlers, mock_chat_session_store, mock_async_session, sample_user_access_data):
        thread_id = "123"
        assistant_message_id = "123"
        timestamp = datetime.now(timezone.utc)
        
        expected_thread = Thread(
            id=thread_id,
            user_id=sample_user_access_data.user_id,
            error_message=None,
            is_empty=False,
            created_at=to_utc_isostring(timestamp),
            updated_at=to_utc_isostring(timestamp),
        )
        expected_message = Message(
            id=assistant_message_id,
            user_id=sample_user_access_data.user_id,
            thread_id=thread_id,
            text_content="",
            created_at=to_utc_isostring(timestamp),
            updated_at=to_utc_isostring(timestamp),
            role=MessageRole.assistant,
            content_type=MessageContentType.text
        )
        
        mock_chat_session_store.update_thread.return_value = expected_thread
        mock_chat_session_store.create_assistant_text_message.return_value = expected_message
        
        result = await chat_session_handlers.handle_text_message_started(
            user_access_data=sample_user_access_data,
            thread_id=thread_id,
            assistant_message_id=assistant_message_id,
            payload=TextMessageStartedPayload(),
            timestamp=timestamp,
        )
        
        mock_chat_session_store.update_thread.assert_called_once_with(
            mock_async_session,
            sample_user_access_data,
            UpdateThreadParams(
                id=thread_id,
                updated_at=timestamp,
                error_message=None,
                is_empty=False,
            ),
        )
        mock_chat_session_store.create_assistant_text_message.assert_called_once_with(
            mock_async_session,
            sample_user_access_data,
            CreateAssistantTextMessageParams(
                id=assistant_message_id,
                user_id=sample_user_access_data.user_id,
                thread_id=thread_id,
                text_content="",
                created_at=timestamp,
                updated_at=timestamp,
            ),
        )
        
        assert_deep_equal(result, {
            "thread": expected_thread,
            "message": expected_message,
        })
        
    @pytest.mark.asyncio
    async def test_no_db_transaction(self, chat_session_handlers, sample_user_access_data):
        @asynccontextmanager
        async def bad_transaction():
            yield None
            
        chat_session_handlers.db_transaction_maker = bad_transaction
        
        with pytest.raises(ValueError):
            await chat_session_handlers.handle_text_message_started(
                user_access_data=sample_user_access_data,
                thread_id="123",
                assistant_message_id="123",
                timestamp=datetime.now(timezone.utc),
            )
    
    
    @pytest.mark.asyncio
    async def test_error(self, chat_session_handlers, mock_chat_session_store, mock_async_session, sample_user_access_data):
        thread_id = "123"
        assistant_message_id = "123"
        timestamp = datetime.now(timezone.utc)
        
        mock_chat_session_store.update_thread.side_effect = Exception("test error")
        
        with pytest.raises(Exception):
            await chat_session_handlers.handle_text_message_started(
                user_access_data=sample_user_access_data,
                thread_id=thread_id,
                assistant_message_id=assistant_message_id,
                timestamp=timestamp,
            )


class TestAssistantResponding:
    @pytest.mark.asyncio
    async def test_success(self, chat_session_handlers, mock_chat_session_store, mock_async_session, sample_user_access_data):
        thread_id = "123"
        assistant_message_id = "123"
        message_chunk = "test_chunk"
        metadata = ConversationStreamMetadata(
            model_name="test_model",
            input_tokens=10,
            output_tokens=20,
        )
        timestamp = datetime.now(timezone.utc)
        
        expected_thread = Thread(
            id=thread_id,
            user_id=sample_user_access_data.user_id,
            error_message=None,
            is_empty=False,
            created_at=to_utc_isostring(timestamp),
            updated_at=to_utc_isostring(timestamp),
        )
        
        initial_message = Message(
            id=assistant_message_id,
            user_id=sample_user_access_data.user_id,
            thread_id=thread_id,
            text_content="",
            created_at=to_utc_isostring(timestamp),
            updated_at=to_utc_isostring(timestamp),
            role=MessageRole.assistant,
            content_type=MessageContentType.text,
            input_tokens=0,
            output_tokens=0,
        )
        expected_message = Message(
            id=assistant_message_id,
            user_id=sample_user_access_data.user_id,
            thread_id=thread_id,
            text_content="test content",
            created_at=to_utc_isostring(timestamp),
            updated_at=to_utc_isostring(timestamp),
            role=MessageRole.assistant,
            content_type=MessageContentType.text,
            model_name=metadata.model_name,
            input_tokens=metadata.input_tokens,
            output_tokens=metadata.output_tokens,
        )
        
        mock_chat_session_store.get_message.return_value = initial_message
        mock_chat_session_store.update_thread.return_value = expected_thread
        mock_chat_session_store.update_message.return_value = expected_message
        
        result = await chat_session_handlers.handle_text_message_chunk_generated(
            user_access_data=sample_user_access_data,
            thread_id=thread_id,
            assistant_message_id=assistant_message_id,
            payload=TextMessageChunkGeneratedPayload(
                message_chunk=message_chunk,
                metadata=metadata,
            ),
            timestamp=timestamp,
        )
        
        mock_chat_session_store.update_thread.assert_called_once_with(
            mock_async_session,
            sample_user_access_data,
            UpdateThreadParams(
                id=thread_id,
                updated_at=timestamp,
                error_message=None,
                is_empty=False,
            ),
        )
        mock_chat_session_store.update_message.assert_called_once_with(
            mock_async_session,
            sample_user_access_data,
            thread_id,
            UpdateMessageParams(
                id=assistant_message_id,
                updated_at=timestamp,
                text_content=initial_message.text_content + message_chunk,
                model_name=metadata.model_name,
                input_tokens=initial_message.input_tokens + metadata.input_tokens,
                output_tokens=initial_message.output_tokens + metadata.output_tokens,
            ),
        )
        
        assert_deep_equal(result, {
            "thread": expected_thread,
            "message": expected_message,
        })
        
    @pytest.mark.asyncio
    async def test_error(self, chat_session_handlers, mock_chat_session_store, mock_async_session, sample_user_access_data):
        thread_id = "123"
        assistant_message_id = "123"
        message_chunk = "test_chunk"
        metadata = ConversationStreamMetadata(
            model_name="test_model",
            input_tokens=10,
            output_tokens=20,
        )
        timestamp = datetime.now(timezone.utc)
        
        mock_chat_session_store.update_thread.side_effect = Exception("test error")
        
        with pytest.raises(Exception):
            await chat_session_handlers.handle_text_message_chunk_generated(
                user_access_data=sample_user_access_data,
                thread_id=thread_id,
                assistant_message_id=assistant_message_id,
                payload=TextMessageChunkGeneratedPayload(
                    message_chunk=message_chunk,
                    metadata=metadata,
                ),
                timestamp=timestamp,
            )


class TestAssistantFinishedResponding:
    @pytest.mark.asyncio
    async def test_success(self, chat_session_handlers, mock_chat_session_store, mock_async_session, sample_user_access_data):
        thread_id = "123"
        assistant_message_id = "123"
        full_message = "This is the complete response"
        timestamp = datetime.now(timezone.utc)
        
        expected_thread = Thread(
            id=thread_id,
            user_id=sample_user_access_data.user_id,
            error_message=None,
            is_empty=False,
            created_at=to_utc_isostring(timestamp),
            updated_at=to_utc_isostring(timestamp),
        )
        expected_message = Message(
            id=assistant_message_id,
            user_id=sample_user_access_data.user_id,
            thread_id=thread_id,
            text_content=full_message,
            created_at=to_utc_isostring(timestamp),
            updated_at=to_utc_isostring(timestamp),
            role=MessageRole.assistant,
            content_type=MessageContentType.text
        )
        
        mock_chat_session_store.update_thread.return_value = expected_thread
        mock_chat_session_store.update_message.return_value = expected_message
        
        result = await chat_session_handlers.handle_text_message_completed(
            user_access_data=sample_user_access_data,
            thread_id=thread_id,
            assistant_message_id=assistant_message_id,
            payload=TextMessageCompletedPayload(
                full_message=full_message,
            ),
            timestamp=timestamp,
        )
        
        mock_chat_session_store.update_thread.assert_called_once_with(
            mock_async_session,
            sample_user_access_data,
            UpdateThreadParams(
                id=thread_id,
                updated_at=timestamp,
                error_message=None,
                is_empty=False,
            ),
        )
        mock_chat_session_store.update_message.assert_called_once_with(
            mock_async_session,
            sample_user_access_data,
            thread_id,
            UpdateMessageParams(
                id=assistant_message_id,
                updated_at=timestamp,
                text_content=full_message,
            ),
        )
        
        assert_deep_equal(result, {
            "thread": expected_thread,
            "message": expected_message,
        })
        
    @pytest.mark.asyncio
    async def test_error(self, chat_session_handlers, mock_chat_session_store, mock_async_session, sample_user_access_data):
        thread_id = "123"
        assistant_message_id = "123"
        full_message = "This is the complete response"
        timestamp = datetime.now(timezone.utc)
        
        mock_chat_session_store.update_thread.side_effect = Exception("test error")
        
        with pytest.raises(Exception):
            await chat_session_handlers.handle_text_message_completed(
                user_access_data=sample_user_access_data,
                thread_id=thread_id,
                assistant_message_id=assistant_message_id,
                payload=TextMessageCompletedPayload(
                    full_message=full_message,
                ),
                timestamp=timestamp,
            )


class TestRecipeGenerationStarted:
    @pytest.mark.asyncio
    async def test_success(self, chat_session_handlers, mock_chat_session_store, mock_async_session, sample_user_access_data):
        thread_id = "123"
        assistant_message_id = "123"
        timestamp = datetime.now(timezone.utc)
        
        recipe_tool_name = "recipe_tool"
        recipe_tool_input = {
            "idea": "recipe idea",
            "context": "recipe context",
        }
        
        expected_thread = Thread(
            id=thread_id,
            user_id=sample_user_access_data.user_id,
            error_message=None,
            is_empty=False,
            created_at=to_utc_isostring(timestamp),
            updated_at=to_utc_isostring(timestamp),
        )
        expected_recipe = UserRecipe(
            id="recipe_123",
            user_id=sample_user_access_data.user_id,
            thread_id=thread_id,
            name=None,
            description=None,
            ingredients=None,
            instructions=None,
            categories=None,
            prep_time_minutes=None,
            cook_time_minutes=None,
            servings=None,
            chef_notes=None,
            substitutions=None,
            equipment_alternatives=None,
            scaling_guidance=None,
            storage_notes=None,
            serving_suggestions=None,
            make_ahead_tips=None,
            coordination_timeline=None,
            created_at=to_utc_isostring(timestamp),
            updated_at=to_utc_isostring(timestamp),
        )
        expected_message = Message(
            id=assistant_message_id,
            user_id=sample_user_access_data.user_id,
            thread_id=thread_id,
            recipe_id=expected_recipe.id,
            created_at=to_utc_isostring(timestamp),
            updated_at=to_utc_isostring(timestamp),
            role=MessageRole.assistant,
            content_type=MessageContentType.recipe,
            tool_name=recipe_tool_name,
            tool_input=recipe_tool_input,
        )
        
        mock_chat_session_store.create_recipe.return_value = expected_recipe
        mock_chat_session_store.update_thread.return_value = expected_thread
        mock_chat_session_store.create_assistant_recipe_message.return_value = expected_message
        
        with patch("src.services.chat_services.chat_session_handlers.uuid.uuid4") as mock_uuid:
            mock_uuid.return_value = "recipe_123"
            
            result = await chat_session_handlers.handle_recipe_generation_started(
                user_access_data=sample_user_access_data,
                thread_id=thread_id,
                assistant_message_id=assistant_message_id,
                payload=RecipeGenerationStartedPayload(
                    tool_name=recipe_tool_name,
                    tool_input=recipe_tool_input,
                ),
                timestamp=timestamp,
            )
            
            mock_chat_session_store.create_recipe.assert_called_once()
            mock_chat_session_store.update_thread.assert_called_once_with(
                mock_async_session,
                sample_user_access_data,
                UpdateThreadParams(
                    id=thread_id,
                    updated_at=timestamp,
                    error_message=None,
                    is_empty=False,
                ),
            )
            mock_chat_session_store.create_assistant_recipe_message.assert_called_once_with(
                mock_async_session,
                sample_user_access_data,
                CreateAssistantRecipeMessageParams(
                    id=assistant_message_id,
                    user_id=sample_user_access_data.user_id,
                    thread_id=thread_id,
                    recipe_id=expected_recipe.id,
                    is_recipe_generation_started=True,
                    tool_name=recipe_tool_name,
                    tool_input=recipe_tool_input,
                    created_at=timestamp,
                    updated_at=timestamp,
                ),
            )
            
            assert_deep_equal(result, {
                "thread": expected_thread,
                "message": expected_message,
                "recipe": expected_recipe,
            })
        
    @pytest.mark.asyncio
    async def test_error(self, chat_session_handlers, mock_chat_session_store, mock_async_session, sample_user_access_data):
        thread_id = "123"
        assistant_message_id = "123"
        timestamp = datetime.now(timezone.utc)
        
        recipe_tool_name = "recipe_tool"
        recipe_tool_input = {
            "idea": "recipe idea",
            "context": "recipe context",
        }
        
        mock_chat_session_store.create_recipe.side_effect = Exception("test error")
        
        with pytest.raises(Exception):
            await chat_session_handlers.handle_recipe_generation_started(
                user_access_data=sample_user_access_data,
                thread_id=thread_id,
                assistant_message_id=assistant_message_id,
                payload=RecipeGenerationStartedPayload(
                    tool_name=recipe_tool_name,
                    tool_input=recipe_tool_input,
                ),
                timestamp=timestamp,
            )


class TestRecipeFieldDetected:
    @pytest.mark.asyncio
    async def test_success(self, chat_session_handlers, mock_chat_session_store, mock_async_session, sample_user_access_data):
        thread_id = "123"
        assistant_message_id = "123"
        timestamp = datetime.now(timezone.utc)
        field = RecipeField(name="name", value="Test Recipe")
        
        existing_message = Message(
            id=assistant_message_id,
            user_id=sample_user_access_data.user_id,
            thread_id=thread_id,
            recipe_id="recipe_123",
            created_at=to_utc_isostring(timestamp),
            updated_at=to_utc_isostring(timestamp),
            role=MessageRole.assistant,
            content_type=MessageContentType.recipe
        )
        
        expected_thread = Thread(
            id=thread_id,
            user_id=sample_user_access_data.user_id,
            error_message=None,
            is_empty=False,
            created_at=to_utc_isostring(timestamp),
            updated_at=to_utc_isostring(timestamp),
        )
        expected_recipe = UserRecipe(
            id="recipe_123",
            user_id=sample_user_access_data.user_id,
            thread_id=thread_id,
            name="Test Recipe",
            description=None,
            ingredients=None,
            instructions=None,
            categories=None,
            prep_time_minutes=None,
            cook_time_minutes=None,
            servings=None,
            chef_notes=None,
            substitutions=None,
            equipment_alternatives=None,
            scaling_guidance=None,
            storage_notes=None,
            serving_suggestions=None,
            make_ahead_tips=None,
            coordination_timeline=None,
            created_at=to_utc_isostring(timestamp),
            updated_at=to_utc_isostring(timestamp),
        )
        expected_message = Message(
            id=assistant_message_id,
            user_id=sample_user_access_data.user_id,
            thread_id=thread_id,
            recipe_id=expected_recipe.id,
            created_at=to_utc_isostring(timestamp),
            updated_at=to_utc_isostring(timestamp),
            role=MessageRole.assistant,
            content_type=MessageContentType.recipe
        )
        
        mock_chat_session_store.get_message.return_value = existing_message
        mock_chat_session_store.update_recipe_field.return_value = expected_recipe
        mock_chat_session_store.update_thread.return_value = expected_thread
        mock_chat_session_store.update_message.return_value = expected_message
        
        result = await chat_session_handlers.handle_recipe_field_detected(
            user_access_data=sample_user_access_data,
            thread_id=thread_id,
            assistant_message_id=assistant_message_id,
            payload=RecipeFieldDetectedPayload(
                field=field,
            ),
            timestamp=timestamp,
        )
        
        mock_chat_session_store.get_message.assert_called_once_with(
            mock_async_session,
            sample_user_access_data,
            thread_id,
            assistant_message_id,
        )
        mock_chat_session_store.update_recipe_field.assert_called_once_with(
            mock_async_session,
            sample_user_access_data,
            thread_id,
            UpdateRecipeFieldParams(
                id=existing_message.recipe_id,
                updated_at=timestamp,
                field=field,
            ),
        )
        mock_chat_session_store.update_thread.assert_called_once_with(
            mock_async_session,
            sample_user_access_data,
            UpdateThreadParams(
                id=thread_id,
                updated_at=timestamp,
                error_message=None,
                is_empty=False,
            ),
        )
        mock_chat_session_store.update_message.assert_called_once_with(
            mock_async_session,
            sample_user_access_data,
            thread_id,
            UpdateMessageParams(
                id=assistant_message_id,
                updated_at=timestamp,
                recipe_id=expected_recipe.id,
            ),
        )
        
        assert_deep_equal(result, {
            "thread": expected_thread,
            "message": expected_message,
            "recipe": expected_recipe,
        })
        
    @pytest.mark.asyncio
    async def test_message_without_recipe_id(self, chat_session_handlers, mock_chat_session_store, mock_async_session, sample_user_access_data):
        thread_id = "123"
        assistant_message_id = "123"
        timestamp = datetime.now(timezone.utc)
        field = RecipeField(name="name", value="Test Recipe")
        
        existing_message = Message(
            id=assistant_message_id,
            user_id=sample_user_access_data.user_id,
            thread_id=thread_id,
            recipe_id=None,
            created_at=to_utc_isostring(timestamp),
            updated_at=to_utc_isostring(timestamp),
            role=MessageRole.assistant,
            content_type=MessageContentType.recipe
        )
        
        mock_chat_session_store.get_message.return_value = existing_message
        
        with pytest.raises(ValueError):
            await chat_session_handlers.handle_recipe_field_detected(
                user_access_data=sample_user_access_data,
                thread_id=thread_id,
                assistant_message_id=assistant_message_id,
                payload=RecipeFieldDetectedPayload(
                    field=field,
                ),
                timestamp=timestamp,
            )
        
    @pytest.mark.asyncio
    async def test_error(self, chat_session_handlers, mock_chat_session_store, mock_async_session, sample_user_access_data):
        thread_id = "123"
        assistant_message_id = "123"
        timestamp = datetime.now(timezone.utc)
        field = RecipeField(name="name", value="Test Recipe")
        
        mock_chat_session_store.get_message.side_effect = Exception("test error")
        
        with pytest.raises(Exception):
            await chat_session_handlers.handle_recipe_field_detected(
                user_access_data=sample_user_access_data,
                thread_id=thread_id,
                assistant_message_id=assistant_message_id,
                field=field,
                timestamp=timestamp,
            )


class TestRecipeGenerationCompleted:
    @pytest.mark.asyncio
    async def test_success(self, chat_session_handlers, mock_chat_session_store, mock_async_session, sample_user_access_data):
        thread_id = "123"
        assistant_message_id = "123"
        timestamp = datetime.now(timezone.utc)
        recipe = Recipe(
            name="Test Recipe",
            description="A test recipe",
            ingredients=[RecipeIngredient(name="Test Ingredient", quantity="1", unit="cup")],
            instructions=[],
            categories=[],
            prep_time_minutes=10,
            cook_time_minutes=20,
            servings="4",
        )
        
        recipe_tool_output = { "recipe_xml": "test recipe xml" }
        recipe_tool_metadata = ConversationStreamMetadata(
            model_name="test_model",
            input_tokens=10,
            output_tokens=20,
        )
        
        existing_message = Message(
            id=assistant_message_id,
            user_id=sample_user_access_data.user_id,
            thread_id=thread_id,
            recipe_id="recipe_123",
            created_at=to_utc_isostring(timestamp),
            updated_at=to_utc_isostring(timestamp),
            role=MessageRole.assistant,
            content_type=MessageContentType.recipe
        )
        
        expected_thread = Thread(
            id=thread_id,
            user_id=sample_user_access_data.user_id,
            error_message=None,
            is_empty=False,
            created_at=to_utc_isostring(timestamp),
            updated_at=to_utc_isostring(timestamp),
        )
        expected_recipe = UserRecipe(
            id="recipe_123",
            user_id=sample_user_access_data.user_id,
            thread_id=thread_id,
            name="Test Recipe",
            description="A test recipe",
            ingredients=[RecipeIngredient(name="Test Ingredient", quantity="1", unit="cup")],
            instructions=[],
            categories=[],
            prep_time_minutes=10,
            cook_time_minutes=20,
            servings="4",
            chef_notes=None,
            substitutions=None,
            equipment_alternatives=None,
            scaling_guidance=None,
            storage_notes=None,
            serving_suggestions=None,
            make_ahead_tips=None,
            coordination_timeline=None,
            created_at=to_utc_isostring(timestamp),
            updated_at=to_utc_isostring(timestamp),
        )
        expected_message = Message(
            id=assistant_message_id,
            user_id=sample_user_access_data.user_id,
            thread_id=thread_id,
            recipe_id=expected_recipe.id,
            created_at=to_utc_isostring(timestamp),
            updated_at=to_utc_isostring(timestamp),
            role=MessageRole.assistant,
            content_type=MessageContentType.recipe,
            tool_output=recipe_tool_output,
            model_name=recipe_tool_metadata.model_name,
            input_tokens=recipe_tool_metadata.input_tokens,
            output_tokens=recipe_tool_metadata.output_tokens,
        )
        
        mock_chat_session_store.get_message.return_value = existing_message
        mock_chat_session_store.update_recipe.return_value = expected_recipe
        mock_chat_session_store.update_thread.return_value = expected_thread
        mock_chat_session_store.update_message.return_value = expected_message
        
        result = await chat_session_handlers.handle_recipe_generation_completed(
            user_access_data=sample_user_access_data,
            thread_id=thread_id,
            assistant_message_id=assistant_message_id,
            payload=RecipeGenerationCompletedPayload(
                recipe=recipe,
                tool_output=recipe_tool_output,
                tool_metadata=recipe_tool_metadata,
            ),
            timestamp=timestamp,
        )
        
        mock_chat_session_store.get_message.assert_called_once_with(
            mock_async_session,
            sample_user_access_data,
            thread_id,
            assistant_message_id,
        )
        mock_chat_session_store.update_recipe.assert_called_once_with(
            mock_async_session,
            sample_user_access_data,
            thread_id,
            UpdateRecipeParams(
                id=existing_message.recipe_id,
                updated_at=timestamp,
                **recipe.model_dump(),
            ),
        )
        mock_chat_session_store.update_thread.assert_called_once_with(
            mock_async_session,
            sample_user_access_data,
            UpdateThreadParams(
                id=thread_id,
                updated_at=timestamp,
                error_message=None,
                is_empty=False,
            ),
        )
        mock_chat_session_store.update_message.assert_called_once_with(
            mock_async_session,
            sample_user_access_data,
            thread_id,
            UpdateMessageParams(
                id=assistant_message_id,
                updated_at=timestamp,
                recipe_id=expected_recipe.id,
                is_recipe_generation_started=False,
                is_recipe_generation_completed=True,
                tool_output=recipe_tool_output,
                model_name=recipe_tool_metadata.model_name,
                input_tokens=recipe_tool_metadata.input_tokens,
                output_tokens=recipe_tool_metadata.output_tokens,
            ),
        )
        
        assert_deep_equal(result, {
            "thread": expected_thread,
            "message": expected_message,
            "recipe": expected_recipe,
        })
        
    @pytest.mark.asyncio
    async def test_message_without_recipe_id(self, chat_session_handlers, mock_chat_session_store, mock_async_session, sample_user_access_data):
        thread_id = "123"
        assistant_message_id = "123"
        timestamp = datetime.now(timezone.utc)
        recipe = Recipe(name="Test Recipe")
        
        recipe_tool_output = { "recipe_xml": "test recipe xml" }
        recipe_tool_metadata = ConversationStreamMetadata(
            model_name="test_model",
            input_tokens=10,
            output_tokens=20,
        )
        
        existing_message = Message(
            id=assistant_message_id,
            user_id=sample_user_access_data.user_id,
            thread_id=thread_id,
            recipe_id=None,
            created_at=to_utc_isostring(timestamp),
            updated_at=to_utc_isostring(timestamp),
            role=MessageRole.assistant,
            content_type=MessageContentType.recipe
        )
        
        mock_chat_session_store.get_message.return_value = existing_message
        
        with pytest.raises(ValueError):
            await chat_session_handlers.handle_recipe_generation_completed(
                user_access_data=sample_user_access_data,
                thread_id=thread_id,
                assistant_message_id=assistant_message_id,
                payload=RecipeGenerationCompletedPayload(
                    recipe=recipe,
                    tool_output=recipe_tool_output,
                    tool_metadata=recipe_tool_metadata,
                ),
                timestamp=timestamp,
            )
        
    @pytest.mark.asyncio
    async def test_error(self, chat_session_handlers, mock_chat_session_store, mock_async_session, sample_user_access_data):
        thread_id = "123"
        assistant_message_id = "123"
        timestamp = datetime.now(timezone.utc)
        recipe = Recipe(name="Test Recipe")
        
        mock_chat_session_store.get_message.side_effect = Exception("test error")
        
        with pytest.raises(Exception):
            await chat_session_handlers.handle_recipe_generation_completed(
                user_access_data=sample_user_access_data,
                thread_id=thread_id,
                assistant_message_id=assistant_message_id,
                recipe=recipe,
                timestamp=timestamp,
            )


class TestSearchStarted:
    @pytest.mark.asyncio
    async def test_success(self, chat_session_handlers, mock_chat_session_store, mock_async_session, sample_user_access_data):
        thread_id = "123"
        assistant_message_id = "123"
        timestamp = datetime.now(timezone.utc)
        
        search_tool_name = "search_tool"
        search_tool_input = {
            "query": "test query",
        }
        
        expected_thread = Thread(
            id=thread_id,
            user_id=sample_user_access_data.user_id,
            error_message=None,
            is_empty=False,
            created_at=to_utc_isostring(timestamp),
            updated_at=to_utc_isostring(timestamp),
        )
        
        expected_message = Message(
            id=assistant_message_id,
            user_id=sample_user_access_data.user_id,
            thread_id=thread_id,
            tool_name=search_tool_name,
            tool_input=search_tool_input,
            created_at=to_utc_isostring(timestamp),
            updated_at=to_utc_isostring(timestamp),
            role=MessageRole.assistant,
            content_type=MessageContentType.tool,
        )
        
        mock_chat_session_store.update_thread.return_value = expected_thread
        mock_chat_session_store.create_assistant_tool_message.return_value = expected_message
        
        result = await chat_session_handlers.handle_search_started(
            user_access_data=sample_user_access_data,
            thread_id=thread_id,
            assistant_message_id=assistant_message_id,
            payload=SearchStartedPayload(
                tool_name=search_tool_name,
                tool_input=search_tool_input,
            ),
            timestamp=timestamp,
        )
        
        mock_chat_session_store.update_thread.assert_called_once_with(  
            mock_async_session,
            sample_user_access_data,
            UpdateThreadParams(
                id=thread_id,
                updated_at=timestamp,
                error_message=None, 
                is_empty=False,
            ),
        )
        
        mock_chat_session_store.create_assistant_tool_message.assert_called_once_with(
            mock_async_session,
            sample_user_access_data,
            CreateAssistantToolMessageParams(
                id=assistant_message_id,
                user_id=sample_user_access_data.user_id,
                thread_id=thread_id,
                tool_name=search_tool_name,
                tool_input=search_tool_input,
                created_at=timestamp,
                updated_at=timestamp,
            ),
        )
        
        assert_deep_equal(result, {
            "thread": expected_thread,  
            "message": expected_message,
        })
        
    @pytest.mark.asyncio
    async def test_error(self, chat_session_handlers, mock_chat_session_store, mock_async_session, sample_user_access_data):
        thread_id = "123"
        assistant_message_id = "123"
        timestamp = datetime.now(timezone.utc)
        
        search_tool_name = "search_tool"
        search_tool_input = {
            "query": "test query",
        }
        
        mock_chat_session_store.update_thread.side_effect = Exception("test error")
        
        with pytest.raises(Exception):
            await chat_session_handlers.handle_search_started(
                user_access_data=sample_user_access_data,
                thread_id=thread_id,
                assistant_message_id=assistant_message_id,
                payload=SearchStartedPayload(
                    tool_name=search_tool_name,
                    tool_input=search_tool_input,
                ),
                timestamp=timestamp,
            )
            

class TestSearchCompleted:
    @pytest.mark.asyncio
    async def test_success(self, chat_session_handlers, mock_chat_session_store, mock_async_session, sample_user_access_data):
        thread_id = "123"
        assistant_message_id = "123"
        timestamp = datetime.now(timezone.utc)
        
        search_tool_output = { "search_results": "test search results" }
        search_tool_metadata = ConversationStreamMetadata(
            model_name="test_model",
            input_tokens=10,
            output_tokens=20,
        )
        
        existing_message = Message(
            id=assistant_message_id,
            user_id=sample_user_access_data.user_id,
            thread_id=thread_id,
            created_at=to_utc_isostring(timestamp),
            updated_at=to_utc_isostring(timestamp),
            role=MessageRole.assistant,
            content_type=MessageContentType.tool,
        )
        
        expected_thread = Thread(
            id=thread_id,
            user_id=sample_user_access_data.user_id,
            error_message=None,
            is_empty=False,
            created_at=to_utc_isostring(timestamp),
            updated_at=to_utc_isostring(timestamp),
        )
        
        expected_message = Message(
            id=assistant_message_id,
            user_id=sample_user_access_data.user_id,
            thread_id=thread_id,
            created_at=to_utc_isostring(timestamp),
            updated_at=to_utc_isostring(timestamp),
            role=MessageRole.assistant,
            content_type=MessageContentType.tool,
            tool_output=search_tool_output,
            model_name=search_tool_metadata.model_name,
            input_tokens=search_tool_metadata.input_tokens,
            output_tokens=search_tool_metadata.output_tokens,
        )
        
        mock_chat_session_store.get_message.return_value = existing_message
        mock_chat_session_store.update_thread.return_value = expected_thread
        mock_chat_session_store.update_message.return_value = expected_message
        
        result = await chat_session_handlers.handle_search_completed(
            user_access_data=sample_user_access_data,
            thread_id=thread_id,    
            assistant_message_id=assistant_message_id,
            payload=SearchCompletedPayload(
                tool_output=search_tool_output,
                tool_metadata=search_tool_metadata,
            ),
            timestamp=timestamp,
        )
        
        mock_chat_session_store.get_message.assert_called_once_with(
            mock_async_session,
            sample_user_access_data,
            thread_id,
            assistant_message_id,
        )
        
        mock_chat_session_store.update_thread.assert_called_once_with(
            mock_async_session,
            sample_user_access_data,
            UpdateThreadParams(
                id=thread_id,
                updated_at=timestamp,
                error_message=None,
                is_empty=False,
            ),
        )
        
        mock_chat_session_store.update_message.assert_called_once_with(
            mock_async_session,
            sample_user_access_data,
            thread_id,
            UpdateMessageParams(
                id=assistant_message_id,
                updated_at=timestamp,
                tool_output=search_tool_output,
                model_name=search_tool_metadata.model_name,
                input_tokens=search_tool_metadata.input_tokens,
                output_tokens=search_tool_metadata.output_tokens,
            ),
        )
        
        assert_deep_equal(result, {
            "thread": expected_thread,
            "message": expected_message,
        })
        
    @pytest.mark.asyncio
    async def test_message_not_found(self, chat_session_handlers, mock_chat_session_store, mock_async_session, sample_user_access_data):
        thread_id = "123"
        assistant_message_id = "123"
        timestamp = datetime.now(timezone.utc)

        search_tool_output = { "search_results": "test search results" }
        search_tool_metadata = ConversationStreamMetadata(
            model_name="test_model",
            input_tokens=10,
            output_tokens=20,
        )
        
        mock_chat_session_store.get_message.return_value = None
        
        with pytest.raises(ValueError):
            await chat_session_handlers.handle_search_completed(
                user_access_data=sample_user_access_data,
                thread_id=thread_id,
                assistant_message_id=assistant_message_id,
                payload=SearchCompletedPayload(
                    tool_output=search_tool_output,
                    tool_metadata=search_tool_metadata,
                ),
                timestamp=timestamp,
            )
            
    @pytest.mark.asyncio
    async def test_error(self, chat_session_handlers, mock_chat_session_store, mock_async_session, sample_user_access_data):
        thread_id = "123"
        assistant_message_id = "123"
        timestamp = datetime.now(timezone.utc)
        
        search_tool_output = { "search_results": "test search results" }
        search_tool_metadata = ConversationStreamMetadata(
            model_name="test_model",
            input_tokens=10,
            output_tokens=20,
        )
        
        mock_chat_session_store.get_message.side_effect = Exception("test error")
        
        with pytest.raises(Exception):
            await chat_session_handlers.handle_search_completed(
                user_access_data=sample_user_access_data,
                thread_id=thread_id,
                assistant_message_id=assistant_message_id,
                payload=SearchCompletedPayload( 
                    tool_output=search_tool_output,
                    tool_metadata=search_tool_metadata,
                ),
                timestamp=timestamp,
            )


class TestAiAgentError:
    @pytest.mark.asyncio
    async def test_success(self, chat_session_handlers, mock_chat_session_store, mock_async_session, sample_user_access_data):
        thread_id = "123"
        error_message = "An error occurred"
        timestamp = datetime.now(timezone.utc)
        
        expected_thread = Thread(
            id=thread_id,
            user_id=sample_user_access_data.user_id,
            error_message=error_message,
            is_empty=False,
            created_at=to_utc_isostring(timestamp),
            updated_at=to_utc_isostring(timestamp),
        )
        
        mock_chat_session_store.update_thread.return_value = expected_thread
        
        result = await chat_session_handlers.handle_ai_agent_error(
            user_access_data=sample_user_access_data,
            thread_id=thread_id,
            payload=AIAgentErrorPayload(
                error_message=error_message,
            ),
            timestamp=timestamp,
        )
        
        mock_chat_session_store.update_thread.assert_called_once_with(
            mock_async_session,
            sample_user_access_data,
            UpdateThreadParams(
                id=thread_id,
                updated_at=timestamp,
                error_message=error_message,
                is_empty=False,
            ),
        )
        
        assert_deep_equal(result, {
            "thread": expected_thread,
            "error_message": error_message,
        })
        
    @pytest.mark.asyncio
    async def test_error(self, chat_session_handlers, mock_chat_session_store, mock_async_session, sample_user_access_data):
        thread_id = "123"
        error_message = "An error occurred"
        timestamp = datetime.now(timezone.utc)
        
        mock_chat_session_store.update_thread.side_effect = Exception("test error")
        
        with pytest.raises(Exception):
            await chat_session_handlers.handle_ai_agent_error(
                user_access_data=sample_user_access_data,
                thread_id=thread_id,
                payload=AIAgentErrorPayload(
                    error_message=error_message,
                ),
                timestamp=timestamp,
            )
            

class TestSummaryUpdated:
    @pytest.mark.asyncio
    async def test_success(self, chat_session_handlers, mock_chat_session_store, mock_async_session, sample_user_access_data):
        thread_id = "123"
        summary = "This is a test summary"
        timestamp = datetime.now(timezone.utc)
        
        expected_thread = Thread(
            id=thread_id,   
            user_id=sample_user_access_data.user_id,
            error_message=None,
            is_empty=False,
            created_at=to_utc_isostring(timestamp),
            updated_at=to_utc_isostring(timestamp),
            summary=summary,
        )
        
        mock_chat_session_store.update_thread.return_value = expected_thread
        
        result = await chat_session_handlers.handle_summary_updated(
            user_access_data=sample_user_access_data,
            thread_id=thread_id,
            payload=SummaryUpdatedPayload(
                summary=summary,
            ),
            timestamp=timestamp,
        )           
        
        mock_chat_session_store.update_thread.assert_called_once_with(
            mock_async_session,
            sample_user_access_data,
            UpdateThreadParams(
                id=thread_id,
                updated_at=timestamp,
                error_message=None,
                is_empty=False,
                summary=summary,
            ),
        )
        
        assert_deep_equal(result, {
            "thread": expected_thread,
        })
        
    @pytest.mark.asyncio
    async def test_error(self, chat_session_handlers, mock_chat_session_store, mock_async_session, sample_user_access_data):
        thread_id = "123"
        summary = "This is a test summary"
        timestamp = datetime.now(timezone.utc)
        
        mock_chat_session_store.update_thread.side_effect = Exception("test error")
        
        with pytest.raises(Exception):
            await chat_session_handlers.handle_summary_updated(
                user_access_data=sample_user_access_data,
                thread_id=thread_id,
                payload=SummaryUpdatedPayload(
                    summary=summary,
                ),
                timestamp=timestamp,
            )
            

class TestThreadTitleUpdated:
    @pytest.mark.asyncio
    async def test_success(self, chat_session_handlers, mock_chat_session_store, mock_async_session, sample_user_access_data):
        thread_id = "123"
        thread_title = "This is a test title"
        timestamp = datetime.now(timezone.utc)
        
        expected_thread = Thread(
            id=thread_id,
            user_id=sample_user_access_data.user_id,
            error_message=None,
            is_empty=False,
            created_at=to_utc_isostring(timestamp),
            updated_at=to_utc_isostring(timestamp),     
            title=thread_title,
        )
        
        mock_chat_session_store.update_thread.return_value = expected_thread
        
        result = await chat_session_handlers.handle_thread_title_updated(
            user_access_data=sample_user_access_data,
            thread_id=thread_id,
            payload=ThreadTitleUpdatedPayload(      
                thread_title=thread_title,
            ),
            timestamp=timestamp,
        )
        
        mock_chat_session_store.update_thread.assert_called_once_with(
            mock_async_session,
            sample_user_access_data,
            UpdateThreadParams(
                id=thread_id,
                updated_at=timestamp,
                error_message=None,
                is_empty=False,
                title=thread_title,
            ),
        )
        
        assert_deep_equal(result, {
            "thread": expected_thread,
        })
        