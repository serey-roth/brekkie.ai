import asyncio
from datetime import datetime, timezone
from fastapi import WebSocket
import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, patch
from contextlib import asynccontextmanager

from fastapi.websockets import WebSocketState, WebSocketDisconnect

from services.chat_services.chat_session_engine import ChatSessionEngine, ChatSessionEngineState

from schemas.user_access import UserAccessData
from schemas.messages import UserMessagePayload, Message
from schemas.threads import Thread
from schemas.recipes import UserRecipe
from schemas.chat_session_errors import (
    SessionClosedError,
    AccessTokenNotFoundError,
    OverMessageLimitError,
    InvalidPayloadError,
    InternalServerError,
)

from utils.date_utils import to_utc_isostring

@pytest.fixture
def sample_thread_id():
    return "test_thread"


@pytest.fixture
def sample_access_token():
    return "test_token"


@pytest.fixture
def sample_user_id():
    return "test_user_id"

@pytest.fixture
def mock_db():
    db = AsyncMock()
    return db


@pytest_asyncio.fixture
async def mock_db_transaction_maker(mock_db):
    @asynccontextmanager
    async def db_transaction_maker():
        yield mock_db
        
    return db_transaction_maker


@pytest_asyncio.fixture
async def mock_dependencies(sample_access_token, sample_thread_id):
    return {
        'access_token': sample_access_token,
        'thread_id': sample_thread_id,
        'session_ttl': 300,
        'websocket': AsyncMock(),
        'db_transaction_maker': AsyncMock(),
        'ai_food_agent': AsyncMock(),
        'websocket_event_sender': AsyncMock(),
        'user_access_cache_service': AsyncMock(),
        'chat_session_store': AsyncMock(),
        'chat_session_handlers': AsyncMock(),
        'chat_session_limit_checker': AsyncMock(),
    }


@pytest_asyncio.fixture
async def chat_session_engine(mock_dependencies):
    return ChatSessionEngine(**mock_dependencies)


@pytest.fixture
def sample_user_access_data(sample_access_token, sample_user_id):
    return UserAccessData(
        access_token=sample_access_token,
        user_id=sample_user_id,
        is_authenticated=False,
        user_message_count=0
    )


@pytest.fixture
def sample_thread(sample_thread_id, sample_user_id):
    return Thread(
        id=sample_thread_id,
        user_id=sample_user_id,
        created_at=to_utc_isostring(datetime.now(timezone.utc)),
        updated_at=to_utc_isostring(datetime.now(timezone.utc)),
        resumed_at=None,
        error_message=None,
        title="Test Thread",
        summary=None,
        is_empty=False
    )


@pytest.fixture
def sample_message(sample_thread_id):
    return Message(
        id="msg_123",
        thread_id=sample_thread_id,
        role="user",
        content_type="text",
        text_content="Test message",
        recipe_id=None,
        created_at=to_utc_isostring(datetime.now(timezone.utc)),
        updated_at=to_utc_isostring(datetime.now(timezone.utc)),
        model_used=None,
        token_count=None,
        response_time_ms=None,
        tool_name=None,
        tool_input=None,
        tool_output=None,
        is_recipe_generation_started=None,
        is_recipe_generation_completed=None
    )


@pytest.fixture
def sample_recipe(sample_thread_id, sample_user_id):
    return UserRecipe(
        id="recipe_123",
        user_id=sample_user_id,
        thread_id=sample_thread_id,
        created_at=to_utc_isostring(datetime.now(timezone.utc)),
        updated_at=to_utc_isostring(datetime.now(timezone.utc)),
        name="Test Recipe",
        description="A test recipe",
        ingredients=None,
        instructions=None,
        categories=None,
        prep_time_minutes=15,
        cook_time_minutes=30,
        servings="4 servings",
        chef_notes=None,
        substitutions=None,
        equipment_alternatives=None,
        scaling_guidance=None,
        storage_notes=None,
        serving_suggestions=None,
        make_ahead_tips=None,
        coordination_timeline=None
    )


class TestAsyncContextManager:
    @pytest.mark.asyncio
    async def test_aenter_returns_self(self, chat_session_engine):
        result = await chat_session_engine.__aenter__()
        assert result is chat_session_engine

    @pytest.mark.asyncio
    async def test_aexit_calls_cleanup_timeout_task(self, chat_session_engine):
        with patch.object(chat_session_engine.state, 'cleanup_timeout_task') as mock_cleanup:
            await chat_session_engine.__aexit__(None, None, None)
            mock_cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_aexit_with_exception_still_cleans_up(self, chat_session_engine):
        with patch.object(chat_session_engine.state, 'cleanup_timeout_task') as mock_cleanup:
            test_exception = Exception("test error")
            await chat_session_engine.__aexit__(Exception, test_exception, None)
            mock_cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_context_manager_usage(self, mock_dependencies):
        with patch.object(ChatSessionEngineState, 'cleanup_timeout_task') as mock_cleanup:
            async with ChatSessionEngine(**mock_dependencies) as engine:
                assert isinstance(engine, ChatSessionEngine)
                assert not mock_cleanup.called
            
            mock_cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_context_manager_with_exception(self, mock_dependencies):
        with patch.object(ChatSessionEngineState, 'cleanup_timeout_task') as mock_cleanup:
            try:
                async with ChatSessionEngine(**mock_dependencies) as engine:
                    raise ValueError("test exception")
            except ValueError:
                pass
            
            mock_cleanup.assert_called_once()

    def test_del_with_running_timeout_task(self, mock_dependencies):
        with patch('asyncio.get_event_loop') as mock_get_loop:
            mock_loop = Mock()
            mock_loop.is_closed.return_value = False
            mock_get_loop.return_value = mock_loop
            
            engine = ChatSessionEngine(**mock_dependencies)
            engine.state.timeout_task = Mock()
            engine.state.timeout_task.done.return_value = False
            
            with patch.object(engine.state, 'cleanup_timeout_task') as mock_cleanup:
                engine.__del__()
                mock_cleanup.assert_called_once()

    def test_del_with_closed_event_loop(self, mock_dependencies):
        with patch('asyncio.get_event_loop') as mock_get_loop:
            mock_loop = Mock()
            mock_loop.is_closed.return_value = True
            mock_get_loop.return_value = mock_loop
            
            engine = ChatSessionEngine(**mock_dependencies)
            engine.state.timeout_task = Mock()
            engine.state.timeout_task.done.return_value = False
            
            with patch.object(engine.state, 'cleanup_timeout_task') as mock_cleanup:
                engine.__del__()
                mock_cleanup.assert_not_called()

    def test_del_with_runtime_error(self, mock_dependencies):
        with patch('asyncio.get_event_loop', side_effect=RuntimeError("no event loop")):
            engine = ChatSessionEngine(**mock_dependencies)
            engine.state.timeout_task = Mock()
            engine.state.timeout_task.done.return_value = False
            
            with patch.object(engine.state, 'cleanup_timeout_task') as mock_cleanup:
                engine.__del__()
                mock_cleanup.assert_not_called()

    def test_del_with_no_state_attribute(self, mock_dependencies):
        engine = ChatSessionEngine(**mock_dependencies)
        del engine.state
        
        with patch('asyncio.get_event_loop') as mock_get_loop:
            with patch.object(ChatSessionEngineState, 'cleanup_timeout_task') as mock_cleanup:
                engine.__del__()
                mock_get_loop.assert_not_called()
                mock_cleanup.assert_not_called()

    def test_del_with_no_timeout_task(self, mock_dependencies):
        with patch('asyncio.get_event_loop') as mock_get_loop:
            engine = ChatSessionEngine(**mock_dependencies)
            engine.state.timeout_task = None
            
            with patch.object(engine.state, 'cleanup_timeout_task') as mock_cleanup:
                engine.__del__()
                mock_get_loop.assert_not_called()
                mock_cleanup.assert_not_called()

    def test_del_with_done_timeout_task(self, mock_dependencies):
        with patch('asyncio.get_event_loop') as mock_get_loop:
            engine = ChatSessionEngine(**mock_dependencies)
            engine.state.timeout_task = Mock()
            engine.state.timeout_task.done.return_value = True
            
            with patch.object(engine.state, 'cleanup_timeout_task') as mock_cleanup:
                engine.__del__()
                mock_get_loop.assert_not_called()
                mock_cleanup.assert_not_called()

    @pytest.mark.asyncio
    async def test_multiple_context_manager_entries(self, mock_dependencies):
        with patch.object(ChatSessionEngineState, 'cleanup_timeout_task') as mock_cleanup:
            engine = ChatSessionEngine(**mock_dependencies)
            
            async with engine:
                async with engine:
                    assert isinstance(engine, ChatSessionEngine)
            
            assert mock_cleanup.call_count == 2

    @pytest.mark.asyncio
    async def test_context_manager_preserves_state(self, mock_dependencies):
        engine = ChatSessionEngine(**mock_dependencies)
        original_state = engine.state
        
        async with engine:
            assert engine.state is original_state
            assert not engine.state.is_closed


class TestHandleSessionTimeout:
    @pytest.mark.asyncio
    async def test_session_closes(self, chat_session_engine):
        chat_session_engine.state.session_ttl = 1
        with patch('asyncio.sleep') as mock_sleep, \
             patch.object(chat_session_engine.state, 'is_active', return_value=False), \
             patch.object(chat_session_engine.state, 'close') as mock_close, \
             patch.object(chat_session_engine, '_handle_chat_session_error') as mock_handle_error, \
             patch.object(chat_session_engine.state, 'cleanup_timeout_task') as mock_cleanup:
            
            await chat_session_engine.handle_session_timeout()
            
            mock_sleep.assert_called_once_with(1)
            mock_close.assert_called_once()
            mock_handle_error.assert_called_once()
            mock_cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_session_remains_active(self, chat_session_engine):
        chat_session_engine.state.session_ttl = 1
        with patch('asyncio.sleep') as mock_sleep, \
             patch.object(chat_session_engine.state, 'is_active', return_value=True), \
             patch.object(chat_session_engine.state, 'close') as mock_close, \
             patch.object(chat_session_engine, '_handle_chat_session_error') as mock_handle_error, \
             patch.object(chat_session_engine.state, 'cleanup_timeout_task') as mock_cleanup:
            
            def side_effect_sleep(duration):
                chat_session_engine.state.is_closed = True
                return None
            
            mock_sleep.side_effect = side_effect_sleep
            
            await chat_session_engine.handle_session_timeout()
            
            mock_sleep.assert_called_once_with(1)
            mock_close.assert_not_called()
            mock_handle_error.assert_not_called()
            mock_cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_cancelled_error(self, chat_session_engine):
        with patch('asyncio.sleep', side_effect=asyncio.CancelledError()), \
             patch.object(chat_session_engine.state, 'cleanup_timeout_task') as mock_cleanup:
            
            await chat_session_engine.handle_session_timeout()
            
            mock_cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_general_exception(self, chat_session_engine):
        with patch('asyncio.sleep', side_effect=Exception("test error")), \
             patch.object(chat_session_engine.state, 'cleanup_timeout_task') as mock_cleanup:
            
            await chat_session_engine.handle_session_timeout()
            
            mock_cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_multiple_sleep_cycles(self, chat_session_engine):
        chat_session_engine.state.session_ttl = 1
        with patch('asyncio.sleep') as mock_sleep, \
             patch.object(chat_session_engine.state, 'is_active', return_value=True), \
             patch.object(chat_session_engine.state, 'close') as mock_close, \
             patch.object(chat_session_engine, '_handle_chat_session_error') as mock_handle_error, \
             patch.object(chat_session_engine.state, 'cleanup_timeout_task') as mock_cleanup:
            
            call_count = 0
            def side_effect_sleep(duration):
                nonlocal call_count
                call_count += 1
                if call_count >= 2:
                    chat_session_engine.state.is_closed = True
                return None
            
            mock_sleep.side_effect = side_effect_sleep
            
            await chat_session_engine.handle_session_timeout()
            
            assert mock_sleep.call_count == 2
            mock_close.assert_not_called()
            mock_handle_error.assert_not_called()
            mock_cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_session_closed_immediately(self, chat_session_engine):
        chat_session_engine.state.is_closed = True
        
        with patch('asyncio.sleep') as mock_sleep, \
             patch.object(chat_session_engine.state, 'cleanup_timeout_task') as mock_cleanup:
            
            await chat_session_engine.handle_session_timeout()
            
            mock_sleep.assert_not_called()
            mock_cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_session_closed_error(self, chat_session_engine):
        chat_session_engine.state.session_ttl = 1
        with patch('asyncio.sleep') as mock_sleep, \
             patch.object(chat_session_engine.state, 'is_active', return_value=False), \
             patch.object(chat_session_engine.state, 'close') as mock_close, \
             patch.object(chat_session_engine, '_handle_chat_session_error') as mock_handle_error, \
             patch.object(chat_session_engine.state, 'cleanup_timeout_task') as mock_cleanup:
            
            await chat_session_engine.handle_session_timeout()
            
            mock_handle_error.assert_called_once()
            call_args = mock_handle_error.call_args[0][0]
            assert isinstance(call_args, SessionClosedError)
            assert call_args.access_token == 'test_token'
            assert call_args.close_reason == 'timeout'


class TestHandleMessageProcessed:
    @pytest.mark.asyncio
    async def test_session_closed(self, chat_session_engine):
        chat_session_engine.state.is_closed = True
        
        with patch.object(chat_session_engine.websocket_event_sender, 'send_event', new_callable=AsyncMock) as mock_send:
            result = {"result": {"thread": None, "message": None, "recipe": None, "error_message": "test"}}
            await chat_session_engine._handle_message_processed(result)
            
            mock_send.assert_not_called()

    @pytest.mark.asyncio
    async def test_text_message_started(self, chat_session_engine, sample_thread, sample_user_access_data):
        chat_session_engine.user_access_cache_service.get_user_access.return_value = sample_user_access_data
        chat_session_engine.chat_session_limit_checker.has_message_limit_reached.return_value = False
        
        with patch.object(chat_session_engine.websocket_event_sender, 'send_event', new_callable=AsyncMock) as mock_send:
            result = {"event": "text_message_started", "result": {"thread": sample_thread, "message": None, "recipe": None, "error_message": None}}
            await chat_session_engine._handle_message_processed(result)
            
            mock_send.assert_called_once_with(chat_session_engine.websocket, "text_message_started", {
                "user_access_data": sample_user_access_data.model_dump(),
                "thread": sample_thread.model_dump()
            })

    @pytest.mark.asyncio
    async def test_text_message_chunk_generated(self, chat_session_engine, sample_thread, sample_message, sample_user_access_data):
        chat_session_engine.user_access_cache_service.get_user_access.return_value = sample_user_access_data
        chat_session_engine.chat_session_limit_checker.has_message_limit_reached.return_value = False
        
        with patch.object(chat_session_engine.websocket_event_sender, 'send_event', new_callable=AsyncMock) as mock_send:
            result = {"event": "text_message_chunk_generated", "result": {"thread": sample_thread, "message": sample_message, "recipe": None, "error_message": None}}
            await chat_session_engine._handle_message_processed(result)
            
            mock_send.assert_called_once_with(chat_session_engine.websocket, "text_message_chunk_generated", {
                "user_access_data": sample_user_access_data.model_dump(),
                "message": sample_message.model_dump(),
                "thread": sample_thread.model_dump()
            })

    @pytest.mark.asyncio
    async def test_text_message_completed(self, chat_session_engine, sample_thread, sample_message, sample_user_access_data):
        chat_session_engine.user_access_cache_service.get_user_access.return_value = sample_user_access_data
        chat_session_engine.chat_session_limit_checker.has_message_limit_reached.return_value = False
        
        with patch.object(chat_session_engine.websocket_event_sender, 'send_event', new_callable=AsyncMock) as mock_send:
            result = {"event": "text_message_completed", "result": {"thread": sample_thread, "message": sample_message, "recipe": None, "error_message": None}}
            await chat_session_engine._handle_message_processed(result)
            
            mock_send.assert_called_once_with(chat_session_engine.websocket, "text_message_completed", {
                "user_access_data": sample_user_access_data.model_dump(),
                "message": sample_message.model_dump(),
                "thread": sample_thread.model_dump()
            })

    @pytest.mark.asyncio
    async def test_recipe_generation_started(self, chat_session_engine, sample_thread, sample_recipe, sample_user_access_data):
        chat_session_engine.user_access_cache_service.get_user_access.return_value = sample_user_access_data
        chat_session_engine.chat_session_limit_checker.has_message_limit_reached.return_value = False
        
        with patch.object(chat_session_engine.websocket_event_sender, 'send_event', new_callable=AsyncMock) as mock_send:
            result = {"event": "recipe_generation_started", "result": {"thread": sample_thread, "message": None, "recipe": sample_recipe, "error_message": None}}
            await chat_session_engine._handle_message_processed(result)
            
            mock_send.assert_called_once_with(chat_session_engine.websocket, "recipe_generation_started", {
                "user_access_data": sample_user_access_data.model_dump(),
                "recipe": sample_recipe.model_dump(),
                "thread": sample_thread.model_dump()
            })

    @pytest.mark.asyncio
    async def test_recipe_field_detected(self, chat_session_engine, sample_thread, sample_message, sample_recipe, sample_user_access_data):
        chat_session_engine.user_access_cache_service.get_user_access.return_value = sample_user_access_data
        chat_session_engine.chat_session_limit_checker.has_message_limit_reached.return_value = False
        
        with patch.object(chat_session_engine.websocket_event_sender, 'send_event', new_callable=AsyncMock) as mock_send:
            result = {"event": "recipe_field_detected", "result": {"thread": sample_thread, "message": sample_message, "recipe": sample_recipe, "error_message": None}}
            await chat_session_engine._handle_message_processed(result)
            
            mock_send.assert_called_once_with(chat_session_engine.websocket, "recipe_field_detected", {
                "user_access_data": sample_user_access_data.model_dump(),
                "recipe": sample_recipe.model_dump(),
                "message": sample_message.model_dump(),
                "thread": sample_thread.model_dump()
            })

    @pytest.mark.asyncio
    async def test_recipe_generation_completed(self, chat_session_engine, sample_thread, sample_message, sample_recipe, sample_user_access_data):
        chat_session_engine.user_access_cache_service.get_user_access.return_value = sample_user_access_data
        chat_session_engine.chat_session_limit_checker.has_message_limit_reached.return_value = False
        
        with patch.object(chat_session_engine.websocket_event_sender, 'send_event', new_callable=AsyncMock) as mock_send:
            result = {"event": "recipe_generation_completed", "result": {"thread": sample_thread, "message": sample_message, "recipe": sample_recipe, "error_message": None}}
            await chat_session_engine._handle_message_processed(result)
            
            mock_send.assert_called_once_with(chat_session_engine.websocket, "recipe_generation_completed", {
                "user_access_data": sample_user_access_data.model_dump(),
                "recipe": sample_recipe.model_dump(),
                "message": sample_message.model_dump(),
                "thread": sample_thread.model_dump()
            })

    @pytest.mark.asyncio
    async def test_search_started(self, chat_session_engine, sample_thread, sample_message, sample_user_access_data):
        chat_session_engine.user_access_cache_service.get_user_access.return_value = sample_user_access_data
        chat_session_engine.chat_session_limit_checker.has_message_limit_reached.return_value = False
        
        with patch.object(chat_session_engine.websocket_event_sender, 'send_event', new_callable=AsyncMock) as mock_send:
            result = {"event": "search_started", "result": {"thread": sample_thread, "message": sample_message, "recipe": None, "error_message": None}}
            await chat_session_engine._handle_message_processed(result)
            
            mock_send.assert_called_once_with(chat_session_engine.websocket, "search_started", {
                "user_access_data": sample_user_access_data.model_dump(),
                "message": sample_message.model_dump(),
                "thread": sample_thread.model_dump()
            })

    @pytest.mark.asyncio
    async def test_search_completed(self, chat_session_engine, sample_thread, sample_message, sample_user_access_data):
        chat_session_engine.user_access_cache_service.get_user_access.return_value = sample_user_access_data
        chat_session_engine.chat_session_limit_checker.has_message_limit_reached.return_value = False
        
        with patch.object(chat_session_engine.websocket_event_sender, 'send_event', new_callable=AsyncMock) as mock_send:
            result = {"event": "search_completed", "result": {"thread": sample_thread, "message": sample_message, "recipe": None, "error_message": None}}
            await chat_session_engine._handle_message_processed(result)
            
            mock_send.assert_called_once_with(chat_session_engine.websocket, "search_completed", {
                "user_access_data": sample_user_access_data.model_dump(),
                "message": sample_message.model_dump(),
                "thread": sample_thread.model_dump()
            })

    @pytest.mark.asyncio
    async def test_summary_updated(self, chat_session_engine, sample_thread, sample_user_access_data):
        chat_session_engine.user_access_cache_service.get_user_access.return_value = sample_user_access_data
        chat_session_engine.chat_session_limit_checker.has_message_limit_reached.return_value = False
        
        with patch.object(chat_session_engine.websocket_event_sender, 'send_event', new_callable=AsyncMock) as mock_send:
            result = {"event": "summary_updated", "result": {"thread": sample_thread, "message": None, "recipe": None, "error_message": None}}
            await chat_session_engine._handle_message_processed(result)
            
            mock_send.assert_called_once_with(chat_session_engine.websocket, "summary_updated", {
                "user_access_data": sample_user_access_data.model_dump(),
                "thread": sample_thread.model_dump()
            })

    @pytest.mark.asyncio
    async def test_thread_title_updated(self, chat_session_engine, sample_thread, sample_user_access_data):
        chat_session_engine.user_access_cache_service.get_user_access.return_value = sample_user_access_data
        chat_session_engine.chat_session_limit_checker.has_message_limit_reached.return_value = False
        
        with patch.object(chat_session_engine.websocket_event_sender, 'send_event', new_callable=AsyncMock) as mock_send:
            result = {"event": "thread_title_updated", "result": {"thread": sample_thread, "message": None, "recipe": None, "error_message": None}}
            await chat_session_engine._handle_message_processed(result)
            
            mock_send.assert_called_once_with(chat_session_engine.websocket, "thread_title_updated", {
                "user_access_data": sample_user_access_data.model_dump(),
                "thread": sample_thread.model_dump()
            })

    @pytest.mark.asyncio
    async def test_error_message(self, chat_session_engine, sample_thread, sample_user_access_data):
        chat_session_engine.user_access_cache_service.get_user_access.return_value = sample_user_access_data
        chat_session_engine.chat_session_limit_checker.has_message_limit_reached.return_value = False
        
        with patch.object(chat_session_engine.websocket_event_sender, 'send_event', new_callable=AsyncMock) as mock_send:
            result = {"event": "ai_agent_error", "result": {"thread": sample_thread, "message": None, "recipe": None, "error_message": "Something went wrong"}}
            await chat_session_engine._handle_message_processed(result)
            
            mock_send.assert_called_once_with(chat_session_engine.websocket, "ai_agent_error", {
                "user_access_data": sample_user_access_data.model_dump(),
                "error_message": "Something went wrong",
                "thread": sample_thread.model_dump()
            })


class TestHandleChatSessionError:
    @pytest.mark.asyncio
    async def test_closed(self, chat_session_engine):
        chat_session_engine.state.is_closed = True
        error = Mock()
        error.type = Mock()
        with patch.object(chat_session_engine.websocket_event_sender, 'send_event', new_callable=AsyncMock) as mock_send:
            await chat_session_engine._handle_chat_session_error(error)
            mock_send.assert_not_called()

    @pytest.mark.asyncio
    async def test_ws_disconnected(self, chat_session_engine):
        chat_session_engine.websocket.client_state = WebSocketState.DISCONNECTED
        error = Mock()
        error.type = Mock()
        with patch.object(chat_session_engine.websocket_event_sender, 'send_event', new_callable=AsyncMock) as mock_send:
            await chat_session_engine._handle_chat_session_error(error)
            mock_send.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_event_false(self, chat_session_engine):
        chat_session_engine.websocket.client_state = WebSocketState.CONNECTED
        error = Mock()
        error.type = Mock()
        error.dict.return_value = {"foo": "bar"}
        error.code = 4000
        error.type.value = "err"
        with patch.object(chat_session_engine.websocket_event_sender, 'send_event', new_callable=AsyncMock, return_value=False) as mock_send, \
             patch.object(chat_session_engine.websocket, 'close', new_callable=AsyncMock) as mock_close:
            await chat_session_engine._handle_chat_session_error(error)
            mock_send.assert_called_once()
            mock_close.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_event_true(self, chat_session_engine):
        chat_session_engine.websocket.client_state = WebSocketState.CONNECTED
        error = Mock()
        error.type = Mock()
        error.dict.return_value = {"foo": "bar"}
        error.code = 4000
        error.type.value = "err"
        with patch.object(chat_session_engine.websocket_event_sender, 'send_event', new_callable=AsyncMock, return_value=True) as mock_send, \
             patch.object(chat_session_engine.websocket, 'close', new_callable=AsyncMock) as mock_close:
            await chat_session_engine._handle_chat_session_error(error)
            mock_send.assert_called_once()
            mock_close.assert_called_once_with(code=4000, reason="err")


class TestGetUserAccessData:
    @pytest.mark.asyncio
    async def test_success(self, chat_session_engine, sample_user_access_data):
        chat_session_engine.user_access_cache_service.get_user_access.return_value = sample_user_access_data
        chat_session_engine.chat_session_limit_checker.has_message_limit_reached.return_value = False
        result = await chat_session_engine._get_user_access_data()
        assert result == sample_user_access_data

    @pytest.mark.asyncio
    async def test_access_token_not_found(self, chat_session_engine):
        chat_session_engine.user_access_cache_service.get_user_access.return_value = None
        with pytest.raises(AccessTokenNotFoundError):
            await chat_session_engine._get_user_access_data()
            
    @pytest.mark.asyncio
    async def test_internal_error(self, chat_session_engine):
        chat_session_engine.user_access_cache_service.get_user_access.side_effect = Exception("fail")
        with pytest.raises(InternalServerError):
            await chat_session_engine._get_user_access_data()


class TestCheckMessageLimit:
    @pytest.mark.asyncio
    async def test_success(self, chat_session_engine):
        chat_session_engine.chat_session_limit_checker.has_message_limit_reached.return_value = False
        await chat_session_engine._check_message_limit()
        chat_session_engine.chat_session_limit_checker.has_message_limit_reached.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_over_message_limit(self, chat_session_engine):
        chat_session_engine.chat_session_limit_checker.has_message_limit_reached.return_value = True
        with pytest.raises(OverMessageLimitError):
            await chat_session_engine._check_message_limit()

    @pytest.mark.asyncio
    async def test_internal_error(self, chat_session_engine):
        chat_session_engine.chat_session_limit_checker.has_message_limit_reached.side_effect = Exception("fail")
        with pytest.raises(InternalServerError):
            await chat_session_engine._check_message_limit()


class TestReceiveUserMessage:
    @pytest.mark.asyncio
    async def test_success(self, chat_session_engine):
        chat_session_engine.websocket.receive_json.return_value = {"id": "1", "content": "hi"}
        with patch("schemas.messages.UserMessagePayload.model_validate", return_value=UserMessagePayload(id="1", content="hi")) as mock_validate:
            result = await chat_session_engine._receive_user_message()
            assert result == UserMessagePayload(id="1", content="hi")
            mock_validate.assert_called_once()

    @pytest.mark.asyncio
    async def test_ws_disconnect(self, chat_session_engine):
        chat_session_engine.websocket.receive_json.side_effect = WebSocketDisconnect()
        with pytest.raises(WebSocketDisconnect):
            await chat_session_engine._receive_user_message()

    @pytest.mark.asyncio
    async def test_validation_error(self, chat_session_engine):
        chat_session_engine.websocket.receive_json.return_value = {"id": 1, "content": "hi"}
        with pytest.raises(InvalidPayloadError):
            await chat_session_engine._receive_user_message()  

    @pytest.mark.asyncio
    async def test_internal_error(self, chat_session_engine):
        chat_session_engine.websocket.receive_json.side_effect = Exception("fail")
        with pytest.raises(InternalServerError):
            await chat_session_engine._receive_user_message()


class TestHandleUserMessage:
    @pytest.mark.asyncio
    async def test_success(self, chat_session_engine, sample_user_access_data, sample_thread_id, mock_db, mock_db_transaction_maker):
        chat_session_engine.db_transaction_maker = mock_db_transaction_maker
        user_access_data = sample_user_access_data
        payload = UserMessagePayload(id="1", content="hi")
        
        with patch.object(chat_session_engine, 'message_processor', new_callable=AsyncMock) as mock_processor,\
            patch('services.chat_services.chat_session_engine.datetime') as mock_datetime:
            
            timestamp = datetime.now(timezone.utc)
            mock_datetime.now.return_value = timestamp
            
            await chat_session_engine._handle_user_message(user_access_data, payload)
            
            chat_session_engine.session_store.create_user_message.assert_awaited_once_with(
                mock_db,
                user_access_data,
                sample_thread_id,
                payload.id,
                payload.content,
                timestamp
            )
            
            mock_processor.process_user_message.assert_awaited_once_with(user_access_data, sample_thread_id, payload.content)


class TestRun:
    @pytest_asyncio.fixture
    async def mock_websocket(self):
        mock_websocket = AsyncMock(spec=WebSocket)
        mock_websocket.client_state = WebSocketState.CONNECTED
        return mock_websocket

    @pytest_asyncio.fixture
    async def run_chat_session_engine(self, mock_dependencies, mock_websocket, sample_user_id):
        mock_dependencies['websocket'] = mock_websocket
        engine = ChatSessionEngine(**mock_dependencies)
        engine._get_user_access_data = AsyncMock(return_value=UserAccessData(
            access_token="test_token",
            user_id=sample_user_id,
            is_authenticated=False,
            user_message_count=0
        ))
        engine._check_message_limit = AsyncMock()
        engine._receive_user_message = AsyncMock(return_value=UserMessagePayload(id="1", content="hi"))
        
        async def close_after_one(*args, **kwargs):
            engine.state.is_closed = True
            
        engine._handle_user_message = AsyncMock()  
        engine._handle_user_message.side_effect = close_after_one
        
        return engine

    @pytest.mark.asyncio
    async def test_success(self, run_chat_session_engine):
        run_chat_session_engine.state.is_closed = False
        
        await run_chat_session_engine.run()

        run_chat_session_engine._check_message_limit.assert_awaited_once()
        run_chat_session_engine._get_user_access_data.assert_awaited_once()
        run_chat_session_engine._receive_user_message.assert_awaited_once()
        run_chat_session_engine._handle_user_message.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_ws_disconnect(self, run_chat_session_engine):
        run_chat_session_engine._get_user_access_data.side_effect = WebSocketDisconnect()
            
        await run_chat_session_engine.run()
        run_chat_session_engine._get_user_access_data.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_access_token_not_found(self, run_chat_session_engine):
        error = AccessTokenNotFoundError(access_token="bad_token")
        run_chat_session_engine._get_user_access_data.side_effect = error
        run_chat_session_engine._handle_chat_session_error = AsyncMock()
        
        await run_chat_session_engine.run()
        run_chat_session_engine._handle_chat_session_error.assert_awaited_once_with(error)

    @pytest.mark.asyncio
    async def test_over_message_limit(self, run_chat_session_engine):
        error = OverMessageLimitError(message_limit=5)
        run_chat_session_engine._get_user_access_data.side_effect = error
        run_chat_session_engine._handle_chat_session_error = AsyncMock()
        
        await run_chat_session_engine.run()
        run_chat_session_engine._handle_chat_session_error.assert_awaited_once_with(error)

    @pytest.mark.asyncio
    async def test_invalid_payload(self, run_chat_session_engine):
        error = InvalidPayloadError(payload=UserMessagePayload(id="1", content="hi"))
        
        run_chat_session_engine._receive_user_message.side_effect = [
            error,
            WebSocketDisconnect()
        ]
        run_chat_session_engine._handle_chat_session_error = AsyncMock()
        
        await run_chat_session_engine.run()
        run_chat_session_engine._handle_chat_session_error.assert_awaited_once_with(error)

    @pytest.mark.asyncio
    async def test_internal_server_error(self, run_chat_session_engine):
        error = InternalServerError()
        
        run_chat_session_engine._receive_user_message.side_effect = error
        run_chat_session_engine._handle_chat_session_error = AsyncMock()
        
        await run_chat_session_engine.run()
        run_chat_session_engine._handle_chat_session_error.assert_awaited_once_with(error)

    @pytest.mark.asyncio
    async def test_general_exception(self, run_chat_session_engine):
        error = Exception("unexpected error")
        
        run_chat_session_engine._receive_user_message.side_effect = [
            error,
            WebSocketDisconnect()
        ]
        run_chat_session_engine._handle_chat_session_error = AsyncMock()
        
        await run_chat_session_engine.run()
        run_chat_session_engine._handle_chat_session_error.assert_awaited_once_with(InternalServerError())