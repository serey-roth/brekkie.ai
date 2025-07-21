import os
from datetime import datetime, timezone

import pytest

from unittest.mock import AsyncMock

os.environ["TAVILY_API_KEY"] = "mock-tavily-api-key"

from services.ai_food_agent.google_ai_food_agent import GoogleAIFoodAgent
from services.chat_services.chat_session_handlers import ChatSessionHandlers
from services.chat_services.chat_session_message_processor import ChatSessionMessageProcessor

from schemas.user_access import UserAccess
from schemas.recipes import Recipe, RecipeField, RecipeIngredient, RecipeInstruction, RecipeCategory
from schemas.conversation_stream_events import (
    ConversationStreamEvent, 
    TextMessageStartedPayload,
    TextMessageChunkGeneratedPayload,
    TextMessageCompletedPayload,
    ConversationStreamMetadata,
    RecipeGenerationStartedPayload,
    RecipeFieldDetectedPayload,
    RecipeGenerationCompletedPayload,
    SearchStartedPayload,
    SearchCompletedPayload,
    AIAgentErrorPayload,
    SummaryUpdatedPayload,
    ThreadTitleUpdatedPayload,
    UserMessageRejectedPayload,
)

from utils.date_utils import to_utc_isostring 


@pytest.fixture
def mock_ai_food_agent():
    return AsyncMock(spec=GoogleAIFoodAgent)

@pytest.fixture
def mock_chat_session_handlers():
    return AsyncMock(spec=ChatSessionHandlers)

@pytest.fixture
def mock_on_message_processed():
    return AsyncMock()

@pytest.fixture
def chat_session_message_processor(mock_ai_food_agent, mock_chat_session_handlers, mock_on_message_processed):
    return ChatSessionMessageProcessor(
        ai_food_agent=mock_ai_food_agent,
        chat_session_handlers=mock_chat_session_handlers,
        on_message_processed=mock_on_message_processed,
    )
    
@pytest.fixture
def sample_user_access():
    return UserAccess(
        user_id="123",
        access_token="123",
        is_authenticated=False,
        user_message_count=1
    )
    
@pytest.fixture
def sample_thread_id():
    return "thread-123"

@pytest.fixture
def sample_recipe_field():
    return RecipeField(
        name="name",
        value="Test Recipe"
    )

@pytest.fixture
def sample_recipe():
    timestamp = datetime.now(timezone.utc)
    return Recipe(
        name="Test Recipe",
        description="A test recipe",
        ingredients=[
            RecipeIngredient(name="Flour", quantity="2", unit="cups"),
            RecipeIngredient(name="Sugar", quantity="1", unit="cup")
        ],
        instructions=[
            RecipeInstruction(title="Mix", description="Mix flour and sugar"),
            RecipeInstruction(title="Bake", description="Bake at 350F")
        ],
        categories=[RecipeCategory(name="Dessert")],
        prep_time_minutes=15,
        cook_time_minutes=30,
        servings="8 servings",
    )
    
@pytest.fixture
def sample_user_message_id():
    return "123"
    
class TestTextMessageStarted:
    @pytest.mark.asyncio
    async def test_text_message_started(self, chat_session_message_processor, mock_ai_food_agent, mock_chat_session_handlers, mock_on_message_processed, sample_user_access, sample_thread_id, sample_user_message_id):
        assert chat_session_message_processor.assistant_message_id is None
        
        await chat_session_message_processor._handle_event(
            user_access=sample_user_access,
            thread_id=sample_thread_id,
            user_message_id=sample_user_message_id,
            event=ConversationStreamEvent(
                event="text_message_started",
                payload=TextMessageStartedPayload()
            )
        )
        
        assert chat_session_message_processor.assistant_message_id is not None
        assert isinstance(chat_session_message_processor.assistant_message_id, str)
        
        mock_chat_session_handlers.handle_text_message_started.assert_called_once()
        call_args = mock_chat_session_handlers.handle_text_message_started.call_args
        
        assert call_args.kwargs["user_access"] == sample_user_access
        assert call_args.kwargs["thread_id"] == sample_thread_id
        assert call_args.kwargs["user_message_id"] == sample_user_message_id
        assert call_args.kwargs["payload"] == TextMessageStartedPayload()
        assert call_args.kwargs["assistant_message_id"] == chat_session_message_processor.assistant_message_id
        assert "timestamp" in call_args.kwargs
        
        mock_on_message_processed.assert_called_once()
        processing_result = mock_on_message_processed.call_args[0][0]
        assert "event" in processing_result
        assert processing_result["event"] == "text_message_started"
        assert "result" in processing_result
        assert "timestamp" in processing_result
        

class TestTextMessageChunkGenerated:
    @pytest.mark.asyncio
    async def test_text_message_chunk_generated(self, chat_session_message_processor, mock_ai_food_agent, mock_chat_session_handlers, mock_on_message_processed, sample_user_access, sample_thread_id, sample_user_message_id):
        chat_session_message_processor.assistant_message_id = "123"
        
        await chat_session_message_processor._handle_event(
            user_access=sample_user_access,
            thread_id=sample_thread_id, 
            user_message_id=sample_user_message_id,
            event=ConversationStreamEvent(
                event="text_message_chunk_generated",
                payload=TextMessageChunkGeneratedPayload(
                    message_chunk="Hello",
                    metadata=ConversationStreamMetadata(model_name="gemini-2.5-flash-preview-05-20", input_tokens=0, output_tokens=100),
                )
            )
        )
        
        mock_chat_session_handlers.handle_text_message_chunk_generated.assert_called_once()
        call_args = mock_chat_session_handlers.handle_text_message_chunk_generated.call_args
        
        assert call_args.kwargs["user_access"] == sample_user_access
        assert call_args.kwargs["thread_id"] == sample_thread_id
        assert call_args.kwargs["assistant_message_id"] == chat_session_message_processor.assistant_message_id
        assert call_args.kwargs["payload"] == TextMessageChunkGeneratedPayload(
            message_chunk="Hello",
            metadata=ConversationStreamMetadata(model_name="gemini-2.5-flash-preview-05-20", input_tokens=0, output_tokens=100),
        )
        assert "timestamp" in call_args.kwargs
        assert "user_message_id" not in call_args.kwargs

    @pytest.mark.asyncio
    async def test_text_message_chunk_generated_with_missing_assistant_message_id(self, chat_session_message_processor, mock_ai_food_agent, mock_chat_session_handlers, mock_on_message_processed, sample_user_access, sample_thread_id, sample_user_message_id):
        chat_session_message_processor.assistant_message_id = None
        
        with pytest.raises(ValueError):
            await chat_session_message_processor._handle_event(
                user_access=sample_user_access,
                thread_id=sample_thread_id,
                user_message_id=sample_user_message_id,
                event=ConversationStreamEvent(
                    event="text_message_chunk_generated",
                    payload=TextMessageChunkGeneratedPayload(
                        message_chunk="Hello",
                        metadata=ConversationStreamMetadata(model_name="gemini-2.5-flash-preview-05-20", input_tokens=0, output_tokens=100),
                    )
                )
            )
            
        mock_chat_session_handlers.handle_text_message_chunk_generated.assert_not_called()
        mock_on_message_processed.assert_not_called()
        

class TestTextMessageCompleted:
    @pytest.mark.asyncio
    async def test_success(self, chat_session_message_processor, mock_ai_food_agent, mock_chat_session_handlers, mock_on_message_processed, sample_user_access, sample_thread_id, sample_user_message_id):
        chat_session_message_processor.assistant_message_id = "123"
        original_assistant_message_id = chat_session_message_processor.assistant_message_id
        
        await chat_session_message_processor._handle_event(
            user_access=sample_user_access,
            thread_id=sample_thread_id,
            user_message_id=sample_user_message_id,
            event=ConversationStreamEvent(
                event="text_message_completed",
                payload=TextMessageCompletedPayload(
                    full_message="Hello there!",
                )
            )
        )
        
        mock_chat_session_handlers.handle_text_message_completed.assert_called_once()
        call_args = mock_chat_session_handlers.handle_text_message_completed.call_args
        
        assert call_args.kwargs["user_access"] == sample_user_access
        assert call_args.kwargs["thread_id"] == sample_thread_id
        assert call_args.kwargs["assistant_message_id"] == original_assistant_message_id
        assert call_args.kwargs["payload"] == TextMessageCompletedPayload(
            full_message="Hello there!",
        )
        assert "timestamp" in call_args.kwargs
        assert "user_message_id" not in call_args.kwargs
        
        mock_on_message_processed.assert_called_once()
        processing_result = mock_on_message_processed.call_args[0][0]
        assert "event" in processing_result
        assert processing_result["event"] == "text_message_completed"
        assert "result" in processing_result
        assert "timestamp" in processing_result
        
        assert chat_session_message_processor.assistant_message_id is None
        
    @pytest.mark.asyncio
    async def test_missing_assistant_message_id_raises_value_error(self, chat_session_message_processor, mock_ai_food_agent, mock_chat_session_handlers, mock_on_message_processed, sample_user_access, sample_thread_id, sample_user_message_id):
        chat_session_message_processor.assistant_message_id = None
        
        with pytest.raises(ValueError):
            await chat_session_message_processor._handle_event(
                user_access=sample_user_access,
                thread_id=sample_thread_id,
                user_message_id=sample_user_message_id,
                event=ConversationStreamEvent(
                    event="text_message_completed",
                    payload=TextMessageCompletedPayload(
                        full_message="Hello",
                    )   
                )
            )
            
        mock_chat_session_handlers.handle_text_message_completed.assert_not_called()
        mock_on_message_processed.assert_not_called()
        
        
class TestRecipeGenerationStarted:
    @pytest.mark.asyncio
    async def test_recipe_generation_started(self, chat_session_message_processor, mock_ai_food_agent, mock_chat_session_handlers, mock_on_message_processed, sample_user_access, sample_thread_id, sample_user_message_id):
        chat_session_message_processor.assistant_message_id = "123"
        
        await chat_session_message_processor._handle_event(
            user_access=sample_user_access,
            thread_id=sample_thread_id,
            user_message_id=sample_user_message_id,
            event=ConversationStreamEvent(
                event="recipe_generation_started",
                payload=RecipeGenerationStartedPayload(
                    tool_name="create_recipe",
                    tool_input={"idea": "Pasta Carbonara", "context": "A delicious pasta dish with eggs and bacon"},
                )   
            )
        )
        
        mock_chat_session_handlers.handle_recipe_generation_started.assert_called_once()
        call_args = mock_chat_session_handlers.handle_recipe_generation_started.call_args
        
        assert call_args.kwargs["user_access"] == sample_user_access
        assert call_args.kwargs["thread_id"] == sample_thread_id
        assert call_args.kwargs["user_message_id"] == sample_user_message_id
        assert call_args.kwargs["assistant_message_id"] == chat_session_message_processor.assistant_message_id
        assert call_args.kwargs["payload"] == RecipeGenerationStartedPayload(
            tool_name="create_recipe",
            tool_input={"idea": "Pasta Carbonara", "context": "A delicious pasta dish with eggs and bacon"},
        )
        assert "timestamp" in call_args.kwargs
        
        mock_on_message_processed.assert_called_once()
        processing_result = mock_on_message_processed.call_args[0][0]
        assert "event" in processing_result
        assert processing_result["event"] == "recipe_generation_started"
        assert "result" in processing_result
        assert "timestamp" in processing_result
        

class TestRecipeFieldDetected:
    @pytest.mark.asyncio
    async def test_success(self, chat_session_message_processor, mock_ai_food_agent, mock_chat_session_handlers, mock_on_message_processed, sample_user_access, sample_thread_id, sample_user_message_id, sample_recipe):
        chat_session_message_processor.assistant_message_id = "123"
        
        await chat_session_message_processor._handle_event(
            user_access=sample_user_access,
            thread_id=sample_thread_id,
            user_message_id=sample_user_message_id,
            event=ConversationStreamEvent(
                event="recipe_field_detected",
                payload=RecipeFieldDetectedPayload(
                    field=RecipeField(
                        name="name",
                        value="Pasta Carbonara",
                    )
                )
            )
        )
        
        mock_chat_session_handlers.handle_recipe_field_detected.assert_called_once()
        call_args = mock_chat_session_handlers.handle_recipe_field_detected.call_args
        
        assert call_args.kwargs["user_access"] == sample_user_access
        assert call_args.kwargs["thread_id"] == sample_thread_id
        assert call_args.kwargs["assistant_message_id"] == chat_session_message_processor.assistant_message_id
        assert call_args.kwargs["payload"] == RecipeFieldDetectedPayload(
            field=RecipeField(
                name="name",
                value="Pasta Carbonara",
            )
        )
        assert "timestamp" in call_args.kwargs
        assert "user_message_id" not in call_args.kwargs
        
        mock_on_message_processed.assert_called_once()
        processing_result = mock_on_message_processed.call_args[0][0]
        assert "event" in processing_result
        assert processing_result["event"] == "recipe_field_detected"
        assert "result" in processing_result
        assert "timestamp" in processing_result
        
    @pytest.mark.asyncio
    async def test_missing_assistant_message_id_raises_value_error(self, chat_session_message_processor, mock_ai_food_agent, mock_chat_session_handlers, mock_on_message_processed, sample_user_access, sample_thread_id, sample_user_message_id):
        chat_session_message_processor.assistant_message_id = None
        
        with pytest.raises(ValueError):
            await chat_session_message_processor._handle_event(
                user_access=sample_user_access,
                thread_id=sample_thread_id,
                user_message_id=sample_user_message_id,
                event=ConversationStreamEvent(
                    event="recipe_field_detected",
                    payload=RecipeFieldDetectedPayload(
                        field=RecipeField(
                            name="name",
                            value="Pasta Carbonara",
                        )
                    )   
                )
            )
            
        mock_chat_session_handlers.handle_recipe_field_detected.assert_not_called()
        mock_on_message_processed.assert_not_called()
        
        
class TestRecipeGenerationCompleted:
    @pytest.mark.asyncio
    async def test_success(self, chat_session_message_processor, mock_ai_food_agent, mock_chat_session_handlers, mock_on_message_processed, sample_user_access, sample_thread_id, sample_user_message_id, sample_recipe):
        chat_session_message_processor.assistant_message_id = "123"
        original_assistant_message_id = chat_session_message_processor.assistant_message_id
        
        await chat_session_message_processor._handle_event(
            user_access=sample_user_access,
            thread_id=sample_thread_id,
            user_message_id=sample_user_message_id,
            event=ConversationStreamEvent(
                event="recipe_generation_completed",
                payload=RecipeGenerationCompletedPayload(
                    recipe=sample_recipe,
                    tool_output={"recipe_xml": "<recipe>Pasta Carbonara</recipe>"},
                    tool_metadata=ConversationStreamMetadata(model_name="gemini-2.5-flash-preview-05-20", input_tokens=0, output_tokens=100),
                )
            )
        )
        
        mock_chat_session_handlers.handle_recipe_generation_completed.assert_called_once()
        call_args = mock_chat_session_handlers.handle_recipe_generation_completed.call_args
        
        assert call_args.kwargs["user_access"] == sample_user_access
        assert call_args.kwargs["thread_id"] == sample_thread_id
        assert call_args.kwargs["assistant_message_id"] == original_assistant_message_id
        assert call_args.kwargs["payload"] == RecipeGenerationCompletedPayload(
            recipe=sample_recipe,
            tool_output={"recipe_xml": "<recipe>Pasta Carbonara</recipe>"},
            tool_metadata=ConversationStreamMetadata(model_name="gemini-2.5-flash-preview-05-20", input_tokens=0, output_tokens=100),
        )
        assert "timestamp" in call_args.kwargs
        assert "user_message_id" not in call_args.kwargs
        
        mock_on_message_processed.assert_called_once()
        processing_result = mock_on_message_processed.call_args[0][0]
        assert "event" in processing_result
        assert processing_result["event"] == "recipe_generation_completed"
        assert "result" in processing_result
        assert "timestamp" in processing_result
        
        assert chat_session_message_processor.assistant_message_id is None
        
    @pytest.mark.asyncio
    async def test_missing_assistant_message_id_raises_value_error(self, chat_session_message_processor, mock_ai_food_agent, mock_chat_session_handlers, mock_on_message_processed, sample_user_access, sample_thread_id, sample_user_message_id, sample_recipe):
        chat_session_message_processor.assistant_message_id = None
        
        with pytest.raises(ValueError):
            await chat_session_message_processor._handle_event(
                user_access=sample_user_access,
                thread_id=sample_thread_id,
                user_message_id=sample_user_message_id,
                event=ConversationStreamEvent(
                    event="recipe_generation_completed",
                    payload=RecipeGenerationCompletedPayload(
                        recipe=sample_recipe,
                        tool_output={"recipe_xml": "<recipe>Pasta Carbonara</recipe>"},
                        tool_metadata=ConversationStreamMetadata(model_name="gemini-2.5-flash-preview-05-20", input_tokens=0, output_tokens=100),
                    )
                )
            )
            
            
class TestSearchStarted:
    @pytest.mark.asyncio
    async def test_search_started(self, chat_session_message_processor, mock_ai_food_agent, mock_chat_session_handlers, mock_on_message_processed, sample_user_access, sample_thread_id, sample_user_message_id):
        chat_session_message_processor.assistant_message_id = "123"
        
        await chat_session_message_processor._handle_event(
            user_access=sample_user_access,
            thread_id=sample_thread_id,
            user_message_id=sample_user_message_id,
            event=ConversationStreamEvent(
                event="search_started",
                payload=SearchStartedPayload(
                    tool_name="tavily_search",
                    tool_input={"query": "Pasta Carbonara", "context": "A delicious pasta dish with eggs and bacon"},
                )
            )
        )
        
        mock_chat_session_handlers.handle_search_started.assert_called_once()
        call_args = mock_chat_session_handlers.handle_search_started.call_args
        
        assert call_args.kwargs["user_access"] == sample_user_access
        assert call_args.kwargs["thread_id"] == sample_thread_id
        assert call_args.kwargs["user_message_id"] == sample_user_message_id
        assert call_args.kwargs["assistant_message_id"] == chat_session_message_processor.assistant_message_id
        assert call_args.kwargs["payload"] == SearchStartedPayload(
            tool_name="tavily_search",
            tool_input={"query": "Pasta Carbonara", "context": "A delicious pasta dish with eggs and bacon"},
        )
        assert "timestamp" in call_args.kwargs
        
        mock_on_message_processed.assert_called_once()
        processing_result = mock_on_message_processed.call_args[0][0]
        assert "event" in processing_result
        assert processing_result["event"] == "search_started"
        assert "result" in processing_result
        assert "timestamp" in processing_result
        

class TestSearchCompleted:
    @pytest.mark.asyncio
    async def test_search_completed(self, chat_session_message_processor, mock_ai_food_agent, mock_chat_session_handlers, mock_on_message_processed, sample_user_access, sample_thread_id, sample_user_message_id):
        chat_session_message_processor.assistant_message_id = "123"
        original_assistant_message_id = chat_session_message_processor.assistant_message_id
        
        await chat_session_message_processor._handle_event(
            user_access=sample_user_access,
            thread_id=sample_thread_id,
            user_message_id=sample_user_message_id,
            event=ConversationStreamEvent(
                event="search_completed",
                payload=SearchCompletedPayload(
                    tool_output={"results": [{"title": "Pasta Carbonara", "url": "https://www.example.com", "snippet": "A delicious pasta dish with eggs and bacon"}]},
                    tool_metadata=ConversationStreamMetadata(model_name="gemini-2.5-flash-preview-05-20", input_tokens=0, output_tokens=100),
                )
            )
        )
        
        mock_chat_session_handlers.handle_search_completed.assert_called_once()
        call_args = mock_chat_session_handlers.handle_search_completed.call_args
        
        assert call_args.kwargs["user_access"] == sample_user_access
        assert call_args.kwargs["thread_id"] == sample_thread_id
        assert call_args.kwargs["assistant_message_id"] == original_assistant_message_id
        assert call_args.kwargs["payload"] == SearchCompletedPayload(
            tool_output={"results": [{"title": "Pasta Carbonara", "url": "https://www.example.com", "snippet": "A delicious pasta dish with eggs and bacon"}]},
            tool_metadata=ConversationStreamMetadata(model_name="gemini-2.5-flash-preview-05-20", input_tokens=0, output_tokens=100),
        )
        assert "timestamp" in call_args.kwargs
        assert "user_message_id" not in call_args.kwargs
        
        mock_on_message_processed.assert_called_once()
        processing_result = mock_on_message_processed.call_args[0][0]
        assert "event" in processing_result
        assert processing_result["event"] == "search_completed"
        assert "result" in processing_result
        assert "timestamp" in processing_result
        
    @pytest.mark.asyncio
    async def test_search_completed_with_missing_assistant_message_id(self, chat_session_message_processor, mock_ai_food_agent, mock_chat_session_handlers, mock_on_message_processed, sample_user_access, sample_thread_id, sample_user_message_id):
        chat_session_message_processor.assistant_message_id = None
        
        with pytest.raises(ValueError):
            await chat_session_message_processor._handle_event(
                user_access=sample_user_access,
                thread_id=sample_thread_id,
                user_message_id=sample_user_message_id,
                event=ConversationStreamEvent(
                    event="search_completed",
                    payload=SearchCompletedPayload(
                        tool_output={"results": [{"title": "Pasta Carbonara", "url": "https://www.example.com", "snippet": "A delicious pasta dish with eggs and bacon"}]},
                        tool_metadata=ConversationStreamMetadata(model_name="gemini-2.5-flash-preview-05-20", input_tokens=0, output_tokens=100),   
                    )
                )
            )
            
        mock_chat_session_handlers.handle_search_completed.assert_not_called()
        mock_on_message_processed.assert_not_called()   
        
        
class TestAiAgentError:
    @pytest.mark.asyncio
    async def test_ai_agent_error(self, chat_session_message_processor, mock_ai_food_agent, mock_chat_session_handlers, mock_on_message_processed, sample_user_access, sample_user_message_id):
        thread_id = "123"   
        error_message = "AI agent error"
        
        mock_ai_food_agent.stream_conversation.side_effect = Exception(error_message)
        
        await chat_session_message_processor._handle_event(
            user_access=sample_user_access,
            thread_id=thread_id,
            user_message_id=sample_user_message_id,
            event=ConversationStreamEvent(
                event="ai_agent_error",
                payload=AIAgentErrorPayload(error_message=error_message)
            )
        )
        
        mock_chat_session_handlers.handle_ai_agent_error.assert_called_once()   
        call_args = mock_chat_session_handlers.handle_ai_agent_error.call_args

        assert call_args.kwargs["user_access"] == sample_user_access
        assert call_args.kwargs["thread_id"] == thread_id
        assert call_args.kwargs["payload"].error_message == error_message
        assert "timestamp" in call_args.kwargs
        assert "user_message_id" not in call_args.kwargs
        
        

class TestSummaryUpdated:
    @pytest.mark.asyncio
    async def test_summary_updated(self, chat_session_message_processor, mock_ai_food_agent, mock_chat_session_handlers, mock_on_message_processed, sample_user_access, sample_thread_id, sample_user_message_id):
        chat_session_message_processor.assistant_message_id = "123"
        
        await chat_session_message_processor._handle_event(
            user_access=sample_user_access,
            thread_id=sample_thread_id,
            user_message_id=sample_user_message_id,
            event=ConversationStreamEvent(
                event="summary_updated",
                payload=SummaryUpdatedPayload(
                    summary="A delicious pasta dish with eggs and bacon",
                )   
            )
        )
        
        mock_chat_session_handlers.handle_summary_updated.assert_called_once()
        call_args = mock_chat_session_handlers.handle_summary_updated.call_args
        
        assert call_args.kwargs["user_access"] == sample_user_access
        assert call_args.kwargs["thread_id"] == sample_thread_id
        assert "assistant_message_id" not in call_args.kwargs
        assert call_args.kwargs["payload"] == SummaryUpdatedPayload(
            summary="A delicious pasta dish with eggs and bacon",
        )
        assert "timestamp" in call_args.kwargs
        assert "user_message_id" not in call_args.kwargs
        
        mock_on_message_processed.assert_called_once()
        processing_result = mock_on_message_processed.call_args[0][0]
        assert "event" in processing_result
        assert processing_result["event"] == "summary_updated"
        assert "result" in processing_result
        assert "timestamp" in processing_result
        

class TestThreadTitleUpdated:
    @pytest.mark.asyncio
    async def test_thread_title_updated(self, chat_session_message_processor, mock_ai_food_agent, mock_chat_session_handlers, mock_on_message_processed, sample_user_access, sample_thread_id, sample_user_message_id):
        chat_session_message_processor.assistant_message_id = "123"
        
        await chat_session_message_processor._handle_event(
            user_access=sample_user_access,
            thread_id=sample_thread_id,
            user_message_id=sample_user_message_id,
            event=ConversationStreamEvent(
                event="thread_title_updated",
                payload=ThreadTitleUpdatedPayload(
                    thread_title="A delicious pasta dish with eggs and bacon",
                )
            )
        )
        
        mock_chat_session_handlers.handle_thread_title_updated.assert_called_once()
        call_args = mock_chat_session_handlers.handle_thread_title_updated.call_args
        
        assert call_args.kwargs["user_access"] == sample_user_access
        assert call_args.kwargs["thread_id"] == sample_thread_id
        assert "assistant_message_id" not in call_args.kwargs
        assert call_args.kwargs["payload"] == ThreadTitleUpdatedPayload(
            thread_title="A delicious pasta dish with eggs and bacon",
        )
        assert "timestamp" in call_args.kwargs
        assert "user_message_id" not in call_args.kwargs
        
        mock_on_message_processed.assert_called_once()
        processing_result = mock_on_message_processed.call_args[0][0]
        assert "event" in processing_result
        assert processing_result["event"] == "thread_title_updated"
        assert "result" in processing_result
        assert "timestamp" in processing_result
        
        
class TestProcessUserMessage:
    @pytest.mark.asyncio
    async def test_success(self, chat_session_message_processor, mock_ai_food_agent, mock_chat_session_handlers, mock_on_message_processed, sample_user_access, sample_user_message_id):
        thread_id = "123"
        user_input = "Hello, can you help me with a recipe?"
        
        await chat_session_message_processor.process_user_message(
            user_access=sample_user_access,
            thread_id=thread_id,
            user_message_id=sample_user_message_id,
            user_input=user_input,
        )
        
        mock_ai_food_agent.stream_conversation.assert_called_once()
        call_args = mock_ai_food_agent.stream_conversation.call_args
        
        assert call_args.kwargs["user_id"] == sample_user_access.user_id
        assert call_args.kwargs["thread_id"] == thread_id
        assert call_args.kwargs["user_input"] == user_input
        assert call_args.kwargs["on_event"] is not None
        
        
    @pytest.mark.asyncio
    async def test_ai_agent_error(self, chat_session_message_processor, mock_ai_food_agent, mock_chat_session_handlers, mock_on_message_processed, sample_user_access, sample_user_message_id):
        thread_id = "123"
        user_input = "Hello, can you help me with a recipe?"
        error_message = "AI agent error"
        
        mock_ai_food_agent.stream_conversation.side_effect = Exception(error_message)
        
        await chat_session_message_processor.process_user_message(
            user_access=sample_user_access,
            thread_id=thread_id,
            user_message_id=sample_user_message_id,
            user_input=user_input,
        )
        
        mock_chat_session_handlers.handle_ai_agent_error.assert_called_once()
        call_args = mock_chat_session_handlers.handle_ai_agent_error.call_args
        
        assert call_args.kwargs["user_access"] == sample_user_access
        assert call_args.kwargs["thread_id"] == thread_id
        assert call_args.kwargs["payload"].error_message == error_message
        assert "timestamp" in call_args.kwargs
    
class TestRejectUserMessage:
    @pytest.mark.asyncio
    async def test_success(self, chat_session_message_processor, mock_ai_food_agent, mock_chat_session_handlers, mock_on_message_processed, sample_user_access, sample_user_message_id):
        thread_id = "123"
        rejection_message = "I'm sorry, I can't help with that."
        
        await chat_session_message_processor.reject_user_message(
            user_access=sample_user_access,
            thread_id=thread_id,
            user_message_id=sample_user_message_id,
            rejection_message=rejection_message
        )
        
        mock_chat_session_handlers.handle_user_message_rejected.assert_called_once()
        call_args = mock_chat_session_handlers.handle_user_message_rejected.call_args
        
        assert call_args.kwargs["user_access"] == sample_user_access
        assert call_args.kwargs["thread_id"] == thread_id
        assert call_args.kwargs["user_message_id"] == sample_user_message_id
        assert call_args.kwargs["payload"] == UserMessageRejectedPayload(
            rejection_message=rejection_message,
        )
        assert "timestamp" in call_args.kwargs
        assert "user_message_id" in call_args.kwargs
        
        mock_on_message_processed.assert_called_once()
        processing_result = mock_on_message_processed.call_args[0][0]
        assert "event" in processing_result
        assert processing_result["event"] == "user_message_rejected"
        assert "result" in processing_result
        assert "timestamp" in processing_result
        