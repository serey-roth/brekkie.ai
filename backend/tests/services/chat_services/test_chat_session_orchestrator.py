import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from fastapi import WebSocket
from fastapi.websockets import WebSocketState
from contextlib import asynccontextmanager

import os
os.environ["TAVILY_API_KEY"] = "mock_tavily_api_key"

from services.ai_food_agent.google_ai_food_agent import GoogleAIFoodAgent
from services.chat_services.chat_session_orchestrator import ChatSessionOrchestrator

from schemas.user_access import UserAccessData
from schemas.threads import Thread
from schemas.messages import PaginatedMessages, Message
from schemas.message_role import MessageRole
from schemas.message_content_type import MessageContentType
from schemas.recipes import UserRecipe
from schemas.chat_session_errors import (
    AccessTokenNotFoundError,
    InternalServerError,
    OverMessageLimitError,
    ThreadNotFoundError
)

from services.data_services.user_access_cache_service import UserAccessCacheService
from services.chat_services.chat_session_store import ChatSessionStore
from services.chat_services.chat_session_handlers import ChatSessionHandlers
from services.chat_services.chat_session_limit_checker import ChatSessionLimitChecker

from services.websocket_event_sender import WebSocketEventSender
from utils.date_utils import to_utc_isostring

@pytest.fixture
def mock_db_transaction_maker():
    mock_session = MagicMock()
    
    @asynccontextmanager
    async def mock_transaction_maker():
        yield mock_session
    
    return mock_transaction_maker


@pytest.fixture
def mock_user_access_cache_service():
    return MagicMock(spec=UserAccessCacheService)


@pytest.fixture
def mock_chat_session_store():
    return MagicMock(spec=ChatSessionStore)


@pytest.fixture
def mock_chat_session_handlers():
    return MagicMock(spec=ChatSessionHandlers)


@pytest.fixture
def mock_chat_session_limit_checker():
    return MagicMock(spec=ChatSessionLimitChecker)


@pytest.fixture
def mock_food_agent():
    return MagicMock(spec=GoogleAIFoodAgent)


@pytest.fixture
def mock_websocket_event_sender():
    return MagicMock(spec=WebSocketEventSender)


@pytest.fixture
def mock_websocket():
    websocket = MagicMock(spec=WebSocket)
    websocket.client_state = WebSocketState.CONNECTED
    return websocket


@pytest.fixture
def orchestrator(
    mock_db_transaction_maker,
    mock_user_access_cache_service,
    mock_chat_session_store,
    mock_chat_session_handlers,
    mock_chat_session_limit_checker,
    mock_food_agent,
    mock_websocket_event_sender
):
    return ChatSessionOrchestrator(
        session_ttl=1000,
        db_transaction_maker=mock_db_transaction_maker,
        user_access_cache_service=mock_user_access_cache_service,
        ai_food_agent=mock_food_agent,
        chat_session_store=mock_chat_session_store,
        chat_session_handlers=mock_chat_session_handlers,
        chat_session_limit_checker=mock_chat_session_limit_checker,
        websocket_event_sender=mock_websocket_event_sender
    )

@pytest.fixture
def sample_access_token():
    return "test_access_token"


@pytest.fixture
def sample_user_id():
    return "test_user_id"


@pytest.fixture
def sample_thread_id():
    return "test_thread_id"


@pytest.fixture
def sample_anonymous_user_access_data(sample_access_token, sample_user_id):
    return UserAccessData(
        access_token=sample_access_token,
        user_id=sample_user_id,
        name="test_name",
        email="test_email",
        is_authenticated=False,
        user_message_count=0
    )


@pytest.fixture
def sample_empty_thread(sample_thread_id, sample_user_id):
    return Thread(
        id=sample_thread_id,
        user_id=sample_user_id,
        is_empty=True,
        created_at=to_utc_isostring(datetime.now(timezone.utc)),
        updated_at=to_utc_isostring(datetime.now(timezone.utc))
    )
    

@pytest.fixture
def sample_thread(sample_thread_id, sample_user_id):
    return Thread(
        id=sample_thread_id,
        user_id=sample_user_id,
        is_empty=False,
        created_at=to_utc_isostring(datetime.now(timezone.utc)),
        updated_at=to_utc_isostring(datetime.now(timezone.utc)),
        error_message=None,
    )
    

@pytest.fixture
def sample_messages(sample_thread_id, sample_user_id):
    return [Message(
        id="msg1", 
        user_id=sample_user_id,
        thread_id=sample_thread_id, 
        role=MessageRole.user,
        content_type=MessageContentType.text,
        text_content="test_content", 
        created_at=to_utc_isostring(datetime.now(timezone.utc)), 
        updated_at=to_utc_isostring(datetime.now(timezone.utc))
    )]
    

@pytest.fixture
def sample_paginated_messages(sample_thread_id, sample_messages):
    return PaginatedMessages(
        messages=sample_messages,
        total_count=1,
        has_more=False,
        next_timestamp=None
    )
    
    
@pytest.fixture
def sample_recipes(sample_thread_id, sample_user_id):
    return [UserRecipe(id="recipe1", thread_id=sample_thread_id, user_id=sample_user_id, created_at=to_utc_isostring(datetime.now(timezone.utc)), updated_at=to_utc_isostring(datetime.now(timezone.utc)))]


class TestStartSession:
    @pytest.mark.asyncio
    async def test_start_session_success(
        self, 
        orchestrator,
        mock_websocket, 
        mock_user_access_cache_service, 
        mock_chat_session_store, 
        mock_chat_session_limit_checker,
        mock_websocket_event_sender, 
        sample_access_token,
        sample_anonymous_user_access_data, 
        sample_empty_thread,
    ):

        mock_user_access_cache_service.get_user_access = AsyncMock(return_value=sample_anonymous_user_access_data)
        mock_chat_session_limit_checker.has_message_limit_reached = AsyncMock(return_value=False)
        
        mock_chat_session_store.create_thread = AsyncMock(return_value=sample_empty_thread)
        
        with patch('services.chat_services.chat_session_engine.ChatSessionEngine.run', new_callable=AsyncMock) as mock_run:
            await orchestrator.start_session(sample_access_token, mock_websocket)
            
            mock_user_access_cache_service.get_user_access.assert_called_once_with(sample_access_token)
            mock_chat_session_limit_checker.has_message_limit_reached.assert_called_once_with(sample_access_token)
            mock_chat_session_store.create_thread.assert_called_once()
            mock_websocket_event_sender.send_event.assert_called_once_with(
                mock_websocket,
                "thread_started",
                {
                    "user_access_data": sample_anonymous_user_access_data.model_dump(),
                    "thread": sample_empty_thread.model_dump()
                }
            )
            mock_run.assert_called_once()


    @pytest.mark.asyncio
    async def test_start_session_access_token_not_found(
        self, 
        orchestrator, 
        mock_websocket, 
        mock_user_access_cache_service, 
        mock_websocket_event_sender,
        sample_access_token,
    ):
        mock_user_access_cache_service.get_user_access = AsyncMock(return_value=None)
        
        await orchestrator.start_session(sample_access_token, mock_websocket)
        
        chat_error = AccessTokenNotFoundError(sample_access_token)
        mock_websocket_event_sender.send_event.assert_called_once_with(
            mock_websocket,
            "chat_session_error",
            chat_error.dict()
        )
        mock_websocket.close.assert_called_once()


    @pytest.mark.asyncio
    async def test_start_session_limit_reached(
        self, 
        orchestrator, 
        mock_websocket, 
        mock_user_access_cache_service, 
        mock_chat_session_limit_checker,
        mock_websocket_event_sender, 
        sample_access_token,
        sample_anonymous_user_access_data,
    ):
        mock_user_access_cache_service.get_user_access = AsyncMock(return_value=sample_anonymous_user_access_data)
        mock_chat_session_limit_checker.has_message_limit_reached = AsyncMock(return_value=True)
        mock_chat_session_limit_checker.get_message_limit = AsyncMock(return_value=100)
        
        await orchestrator.start_session(sample_access_token, mock_websocket)
        
        chat_error = OverMessageLimitError(100)
        mock_websocket_event_sender.send_event.assert_called_once_with(
            mock_websocket,
            "chat_session_error",
            chat_error.dict()
        )
        mock_websocket.close.assert_called_once()


    @pytest.mark.asyncio
    async def test_start_session_disconnected(
        self, 
        orchestrator, 
        mock_websocket, 
        mock_user_access_cache_service, 
        mock_chat_session_limit_checker,
        mock_chat_session_store,
        sample_access_token,
        sample_anonymous_user_access_data,
        sample_empty_thread,
    ):
        mock_user_access_cache_service.get_user_access = AsyncMock(return_value=sample_anonymous_user_access_data)
        mock_chat_session_limit_checker.has_message_limit_reached = AsyncMock(return_value=False)
        mock_chat_session_limit_checker.get_message_limit = AsyncMock(return_value=100)
        mock_chat_session_store.create_thread = AsyncMock(return_value=sample_empty_thread)
        mock_websocket.client_state = WebSocketState.DISCONNECTED

        with patch('services.chat_services.chat_session_engine.ChatSessionEngine.run', new_callable=AsyncMock) as mock_run:
            await orchestrator.start_session(sample_access_token, mock_websocket)

            mock_run.assert_not_called()
            

    @pytest.mark.asyncio
    async def test_start_session_internal_error(
        self, 
        orchestrator, 
        mock_websocket, 
        mock_user_access_cache_service, 
        mock_chat_session_limit_checker,
        mock_chat_session_store,
        mock_websocket_event_sender, 
        sample_access_token,
        sample_empty_thread,
    ):
        mock_user_access_cache_service.get_user_access = AsyncMock(side_effect=Exception("Test error"))
        mock_chat_session_limit_checker.has_message_limit_reached = AsyncMock(return_value=False)
        mock_chat_session_limit_checker.get_message_limit = AsyncMock(return_value=100)
        mock_chat_session_store.create_thread = AsyncMock(return_value=sample_empty_thread)
        
        with patch('services.chat_services.chat_session_engine.ChatSessionEngine.run', new_callable=AsyncMock) as mock_run:
            await orchestrator.start_session(sample_access_token, mock_websocket)
            
            mock_run.assert_not_called()
            
            chat_error = InternalServerError()
            mock_websocket_event_sender.send_event.assert_called_once_with(
                mock_websocket,
                "chat_session_error",
                chat_error.dict()
            )
            mock_websocket.close.assert_called_once() 


class TestResumeSession:
    @pytest.mark.asyncio
    async def test_resume_session_success(
        self,
        orchestrator,
        mock_websocket,
        mock_user_access_cache_service,
        mock_chat_session_store,
        mock_websocket_event_sender,
        sample_access_token,
        sample_thread_id,
        sample_anonymous_user_access_data,
        sample_thread,
        sample_paginated_messages,
        sample_recipes
    ):
        mock_user_access_cache_service.get_user_access = AsyncMock(return_value=sample_anonymous_user_access_data)
        
        with patch.object(mock_chat_session_store, 'get_thread', new_callable=AsyncMock, return_value=sample_thread), \
            patch.object(mock_chat_session_store, 'resume_thread', new_callable=AsyncMock, return_value=sample_thread), \
            patch.object(mock_chat_session_store, 'get_paginated_messages', new_callable=AsyncMock, return_value=sample_paginated_messages), \
            patch.object(mock_chat_session_store, 'get_recipes_by_message_id', new_callable=AsyncMock, return_value=sample_recipes), \
            patch('services.chat_services.chat_session_engine.ChatSessionEngine.run', new_callable=AsyncMock) as mock_run:
                        
            await orchestrator.resume_session(sample_access_token, sample_thread_id, mock_websocket)
            
            mock_chat_session_store.get_thread.assert_called_once()
            mock_chat_session_store.resume_thread.assert_called_once()
            mock_chat_session_store.get_paginated_messages.assert_called_once()
            mock_chat_session_store.get_recipes_by_message_id.assert_called_once()
            mock_websocket_event_sender.send_event.assert_called_once_with(
                mock_websocket,
                "thread_resumed",
                {
                    "user_access_data": sample_anonymous_user_access_data.model_dump(),
                    "thread": sample_thread.model_dump(),
                    "paginated_messages": sample_paginated_messages.model_dump(),
                    "recipes": [recipe.model_dump() for recipe in sample_recipes]
                }
            )
            
            mock_run.assert_called_once()


    @pytest.mark.asyncio
    async def test_resume_session_token_expired(
        self, 
        orchestrator, 
        mock_websocket, 
        mock_user_access_cache_service, 
        mock_websocket_event_sender,
        sample_access_token,
        sample_thread_id,
    ):
        
        mock_user_access_cache_service.get_user_access = AsyncMock(return_value=None)
        
        await orchestrator.resume_session(sample_access_token, sample_thread_id, mock_websocket)

        chat_error = AccessTokenNotFoundError(sample_access_token)
        mock_websocket_event_sender.send_event.assert_called_once_with(
            mock_websocket,
            "chat_session_error",
            chat_error.dict()
        )
        mock_websocket.close.assert_called_once()


    @pytest.mark.asyncio
    async def test_resume_session_thread_not_found(
        self,
        orchestrator,
        mock_websocket,
        mock_user_access_cache_service,
        mock_chat_session_store,
        mock_websocket_event_sender,
        sample_access_token,
        sample_thread_id,
        sample_anonymous_user_access_data,
    ):
        
        mock_user_access_cache_service.get_user_access = AsyncMock(return_value=sample_anonymous_user_access_data)
        mock_chat_session_store.get_thread = AsyncMock(return_value=None)
        
        await orchestrator.resume_session(sample_access_token, sample_thread_id, mock_websocket)
        
        chat_error = ThreadNotFoundError(sample_thread_id)
        mock_websocket_event_sender.send_event.assert_called_once_with(
            mock_websocket,
            "chat_session_error",
            chat_error.dict()
        )
        mock_websocket.close.assert_called_once()


    @pytest.mark.asyncio
    async def test_resume_session_disconnected(
        self, 
        orchestrator, 
        mock_websocket, 
        mock_user_access_cache_service, 
        sample_access_token,
        sample_thread_id,
        sample_thread,
        sample_paginated_messages,
        sample_recipes,
        sample_anonymous_user_access_data,
    ):
        
        mock_user_access_cache_service.get_user_access = AsyncMock(return_value=sample_anonymous_user_access_data)
        mock_websocket.client_state = WebSocketState.DISCONNECTED
        
        with patch.object(orchestrator, '_resume_thread', new_callable=AsyncMock, return_value={
                "thread": sample_thread.model_dump(),
                "paginated_messages": sample_paginated_messages.model_dump(),
                "recipes": [recipe.model_dump() for recipe in sample_recipes]
            }), \
            patch('services.chat_services.chat_session_engine.ChatSessionEngine.run', new_callable=AsyncMock) as mock_run:
            
            await orchestrator.resume_session(sample_access_token, sample_thread_id, mock_websocket)

            mock_run.assert_not_called()
        

    @pytest.mark.asyncio
    async def test_resume_session_internal_error(
        self,
        orchestrator,
        mock_websocket,
        mock_user_access_cache_service,
        mock_chat_session_limit_checker,
        mock_chat_session_store,
        mock_websocket_event_sender,
        sample_access_token,
        sample_thread_id,
        sample_thread,
        sample_paginated_messages,
        sample_recipes
    ):
        mock_user_access_cache_service.get_user_access = AsyncMock(side_effect=Exception("Test error"))
        mock_chat_session_limit_checker.has_message_limit_reached = AsyncMock(return_value=False)
        mock_chat_session_limit_checker.get_message_limit = AsyncMock(return_value=100)
        mock_chat_session_store.create_thread = AsyncMock(return_value=sample_thread)
        
        with patch.object(orchestrator, '_resume_thread', new_callable=AsyncMock, return_value={
                "thread": sample_thread.model_dump(),
                "paginated_messages": sample_paginated_messages.model_dump(),
                "recipes": [recipe.model_dump() for recipe in sample_recipes]
            }), \
            patch('services.chat_services.chat_session_engine.ChatSessionEngine.run', new_callable=AsyncMock) as mock_run:
            await orchestrator.resume_session(sample_access_token, sample_thread_id, mock_websocket)
            
            mock_run.assert_not_called()
        
            chat_error = InternalServerError()
            mock_websocket_event_sender.send_event.assert_called_once_with(
                mock_websocket,
                "chat_session_error",
                chat_error.dict()
            )
            mock_websocket.close.assert_called_once() 
        
        