import os

os.environ["TAVILY_API_KEY"] = "mock_tavily_api_key"

from datetime import datetime, timezone
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import WebSocket
from fastapi.websockets import WebSocketState

from sqlalchemy.ext.asyncio import AsyncSession
from src.database.index import DBTransactionMaker

from src.services.ai_food_agent.google_ai_food_agent import GoogleAIFoodAgent
from src.services.chat_services.chat_session_orchestrator import ChatSessionOrchestrator
from src.services.data_services.user_access_cache_service import UserAccessCacheService
from src.services.chat_services.chat_session_store import ChatSessionStore
from src.services.chat_services.chat_session_handlers import ChatSessionHandlers
from src.services.chat_services.chat_session_limit_checker import ChatSessionLimitChecker
from src.services.chat_services.chat_session_message_guard import ChatSessionMessageGuard
from src.services.websocket_event_sender import WebSocketEventSender

from src.schemas.user_access import UserAccess
from src.schemas.threads import Thread
from src.schemas.messages import PaginatedMessages, Message, PaginatedApiMessages
from src.schemas.message_role import MessageRole
from src.schemas.message_content_type import MessageContentType
from src.schemas.recipes import UserRecipe
from src.schemas.chat_session_errors import (
    AccessTokenNotFoundError,
    InternalServerError,
    OverMessageLimitError,
    ThreadNotFoundError,
)

from src.utils.date_utils import to_utc_isostring


@pytest.fixture
def mock_db_transaction_maker() -> DBTransactionMaker:
    mock_session = MagicMock(spec=AsyncSession)

    @asynccontextmanager
    async def mock_transaction_maker() -> AsyncGenerator[AsyncSession, None]:
        yield mock_session

    return mock_transaction_maker


@pytest.fixture
def mock_user_access_cache_service() -> UserAccessCacheService:
    return MagicMock(spec=UserAccessCacheService)


@pytest.fixture
def mock_chat_session_store() -> ChatSessionStore:
    return MagicMock(spec=ChatSessionStore)


@pytest.fixture
def mock_chat_session_handlers() -> ChatSessionHandlers:
    return MagicMock(spec=ChatSessionHandlers)


@pytest.fixture
def mock_chat_session_limit_checker() -> ChatSessionLimitChecker:
    return MagicMock(spec=ChatSessionLimitChecker)


@pytest.fixture
def mock_food_agent() -> GoogleAIFoodAgent:
    return MagicMock(spec=GoogleAIFoodAgent)


@pytest.fixture
def mock_websocket_event_sender() -> WebSocketEventSender:
    return MagicMock(spec=WebSocketEventSender)


@pytest.fixture
def mock_chat_session_message_guard() -> ChatSessionMessageGuard:
    return MagicMock(spec=ChatSessionMessageGuard)


@pytest.fixture
def mock_websocket() -> AsyncMock:
    websocket = AsyncMock(spec=WebSocket)
    websocket.client_state = WebSocketState.CONNECTED
    websocket.close = AsyncMock()
    return websocket


@pytest.fixture
def orchestrator(
    mock_db_transaction_maker: DBTransactionMaker,
    mock_user_access_cache_service: UserAccessCacheService,
    mock_chat_session_store: ChatSessionStore,
    mock_chat_session_handlers: ChatSessionHandlers,
    mock_chat_session_limit_checker: ChatSessionLimitChecker,
    mock_food_agent: GoogleAIFoodAgent,
    mock_websocket_event_sender: WebSocketEventSender,
    mock_chat_session_message_guard: ChatSessionMessageGuard,
) -> ChatSessionOrchestrator:
    return ChatSessionOrchestrator(
        session_ttl=1000,
        db_transaction_maker=mock_db_transaction_maker,
        user_access_cache_service=mock_user_access_cache_service,
        ai_food_agent=mock_food_agent,
        chat_session_message_guard=mock_chat_session_message_guard,
        chat_session_store=mock_chat_session_store,
        chat_session_handlers=mock_chat_session_handlers,
        chat_session_limit_checker=mock_chat_session_limit_checker,
        websocket_event_sender=mock_websocket_event_sender,
    )


@pytest.fixture
def sample_access_token() -> str:
    return "test_access_token"


@pytest.fixture
def sample_user_id() -> str:
    return "test_user_id"


@pytest.fixture
def sample_thread_id() -> str:
    return "test_thread_id"


@pytest.fixture
def sample_anonymous_user_access(sample_access_token: str, sample_user_id: str) -> UserAccess:
    return UserAccess(
        access_token=sample_access_token,
        user_id=sample_user_id,
        is_authenticated=False,
        user_message_count=0,
    )


@pytest.fixture
def sample_empty_thread(sample_thread_id: str, sample_user_id: str) -> Thread:
    return Thread(
        id=sample_thread_id,
        user_id=sample_user_id,
        is_empty=True,
        created_at=to_utc_isostring(datetime.now(timezone.utc)),
        updated_at=to_utc_isostring(datetime.now(timezone.utc)),
    )


@pytest.fixture
def sample_thread(sample_thread_id: str, sample_user_id: str) -> Thread:
    return Thread(
        id=sample_thread_id,
        user_id=sample_user_id,
        is_empty=False,
        created_at=to_utc_isostring(datetime.now(timezone.utc)),
        updated_at=to_utc_isostring(datetime.now(timezone.utc)),
        error_message=None,
    )


@pytest.fixture
def sample_messages(sample_thread_id: str, sample_user_id: str) -> list[Message]:
    return [
        Message(
            id="msg1",
            user_id=sample_user_id,
            thread_id=sample_thread_id,
            role=MessageRole.user,
            content_type=MessageContentType.text,
            text_content="test_content",
            created_at=to_utc_isostring(datetime.now(timezone.utc)),
            updated_at=to_utc_isostring(datetime.now(timezone.utc)),
        )
    ]


@pytest.fixture
def sample_paginated_messages(
    sample_thread_id: str, sample_messages: list[Message]
) -> PaginatedMessages:
    return PaginatedMessages(
        messages=sample_messages, total_count=1, has_more=False, next_timestamp=None
    )


@pytest.fixture
def sample_recipes(sample_thread_id: str, sample_user_id: str) -> list[UserRecipe]:
    return [
        UserRecipe(
            id="recipe1",
            thread_id=sample_thread_id,
            user_id=sample_user_id,
            created_at=to_utc_isostring(datetime.now(timezone.utc)),
            updated_at=to_utc_isostring(datetime.now(timezone.utc)),
        )
    ]


class TestStartSession:
    @pytest.mark.asyncio
    async def test_start_session_success(
        self,
        orchestrator: ChatSessionOrchestrator,
        mock_websocket: AsyncMock,
        mock_user_access_cache_service: UserAccessCacheService,
        mock_chat_session_store: ChatSessionStore,
        mock_chat_session_limit_checker: ChatSessionLimitChecker,
        mock_websocket_event_sender: WebSocketEventSender,
        sample_access_token: str,
        sample_anonymous_user_access: UserAccess,
        sample_empty_thread: Thread,
    ) -> None:
        mock_user_access_cache_service.get_user_access = AsyncMock(
            return_value=sample_anonymous_user_access
        )
        mock_chat_session_limit_checker.has_message_limit_reached = AsyncMock(return_value=False)

        mock_chat_session_store.create_thread = AsyncMock(return_value=sample_empty_thread)

        with patch(
            "services.chat_services.chat_session_engine.ChatSessionEngine.run",
            new_callable=AsyncMock,
        ) as mock_run:
            await orchestrator.start_session(sample_access_token, mock_websocket)

            mock_user_access_cache_service.get_user_access.assert_called_once_with(
                sample_access_token
            )
            mock_chat_session_limit_checker.has_message_limit_reached.assert_called_once_with(
                sample_access_token
            )
            mock_chat_session_store.create_thread.assert_called_once()
            mock_websocket_event_sender.send_event.assert_called_once_with(
                mock_websocket,
                "thread_started",
                {
                    "user_access": sample_anonymous_user_access.model_dump(),
                    "thread": sample_empty_thread.model_dump(),
                },
            )
            mock_run.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_session_access_token_not_found(
        self,
        orchestrator: ChatSessionOrchestrator,
        mock_websocket: AsyncMock,
        mock_user_access_cache_service: UserAccessCacheService,
        mock_websocket_event_sender: WebSocketEventSender,
        sample_access_token: str,
    ) -> None:
        mock_user_access_cache_service.get_user_access = AsyncMock(return_value=None)

        await orchestrator.start_session(sample_access_token, mock_websocket)

        chat_error = AccessTokenNotFoundError(sample_access_token)
        mock_websocket_event_sender.send_event.assert_called_once_with(
            mock_websocket, "chat_session_error", chat_error.dict()
        )
        mock_websocket.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_session_limit_reached(
        self,
        orchestrator: ChatSessionOrchestrator,
        mock_websocket: AsyncMock,
        mock_user_access_cache_service: UserAccessCacheService,
        mock_chat_session_limit_checker: ChatSessionLimitChecker,
        mock_websocket_event_sender: WebSocketEventSender,
        sample_access_token: str,
        sample_anonymous_user_access: UserAccess,
    ) -> None:
        mock_user_access_cache_service.get_user_access = AsyncMock(
            return_value=sample_anonymous_user_access
        )
        mock_chat_session_limit_checker.has_message_limit_reached = AsyncMock(return_value=True)
        mock_chat_session_limit_checker.get_message_limit = AsyncMock(return_value=100)

        await orchestrator.start_session(sample_access_token, mock_websocket)

        chat_error = OverMessageLimitError(100)
        mock_websocket_event_sender.send_event.assert_called_once_with(
            mock_websocket, "chat_session_error", chat_error.dict()
        )
        mock_websocket.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_session_disconnected(
        self,
        orchestrator: ChatSessionOrchestrator,
        mock_websocket: AsyncMock,
        mock_user_access_cache_service: UserAccessCacheService,
        mock_chat_session_limit_checker: ChatSessionLimitChecker,
        mock_chat_session_store: ChatSessionStore,
        sample_access_token: str,
        sample_anonymous_user_access: UserAccess,
        sample_empty_thread: Thread,
    ) -> None:
        mock_user_access_cache_service.get_user_access = AsyncMock(
            return_value=sample_anonymous_user_access
        )
        mock_chat_session_limit_checker.has_message_limit_reached = AsyncMock(return_value=False)
        mock_chat_session_limit_checker.get_message_limit = AsyncMock(return_value=100)
        mock_chat_session_store.create_thread = AsyncMock(return_value=sample_empty_thread)
        mock_websocket.client_state = WebSocketState.DISCONNECTED

        with patch(
            "services.chat_services.chat_session_engine.ChatSessionEngine.run",
            new_callable=AsyncMock,
        ) as mock_run:
            await orchestrator.start_session(sample_access_token, mock_websocket)

            mock_run.assert_not_called()

    @pytest.mark.asyncio
    async def test_start_session_internal_error(
        self,
        orchestrator: ChatSessionOrchestrator,
        mock_websocket: AsyncMock,
        mock_user_access_cache_service: UserAccessCacheService,
        mock_chat_session_limit_checker: ChatSessionLimitChecker,
        mock_chat_session_store: ChatSessionStore,
        mock_websocket_event_sender: WebSocketEventSender,
        sample_access_token: str,
        sample_empty_thread: Thread,
    ) -> None:
        mock_user_access_cache_service.get_user_access = AsyncMock(
            side_effect=Exception("Test error")
        )
        mock_chat_session_limit_checker.has_message_limit_reached = AsyncMock(return_value=False)
        mock_chat_session_limit_checker.get_message_limit = AsyncMock(return_value=100)
        mock_chat_session_store.create_thread = AsyncMock(return_value=sample_empty_thread)

        with patch(
            "services.chat_services.chat_session_engine.ChatSessionEngine.run",
            new_callable=AsyncMock,
        ) as mock_run:
            await orchestrator.start_session(sample_access_token, mock_websocket)

            mock_run.assert_not_called()

            chat_error = InternalServerError()
            mock_websocket_event_sender.send_event.assert_called_once_with(
                mock_websocket, "chat_session_error", chat_error.dict()
            )
            mock_websocket.close.assert_called_once()


class TestResumeSession:
    @pytest.mark.asyncio
    async def test_resume_session_success_without_recipes(
        self,
        orchestrator: ChatSessionOrchestrator,
        mock_websocket: AsyncMock,
        mock_user_access_cache_service: UserAccessCacheService,
        mock_chat_session_store: ChatSessionStore,
        mock_websocket_event_sender: WebSocketEventSender,
        sample_access_token: str,
        sample_thread_id: str,
        sample_anonymous_user_access: UserAccess,
        sample_thread: Thread,
        sample_paginated_messages: PaginatedMessages,
        sample_recipes: list[UserRecipe],
    ) -> None:
        mock_user_access_cache_service.get_user_access = AsyncMock(
            return_value=sample_anonymous_user_access
        )

        with (
            patch.object(
                mock_chat_session_store,
                "resume_thread",
                new_callable=AsyncMock,
                return_value=sample_thread,
            ),
            patch.object(
                mock_chat_session_store,
                "get_paginated_messages",
                new_callable=AsyncMock,
                return_value=sample_paginated_messages,
            ),
            patch.object(
                mock_chat_session_store,
                "get_recipes_by_message_ids",
                new_callable=AsyncMock,
                return_value=sample_recipes,
            ),
            patch(
                "services.chat_services.chat_session_engine.ChatSessionEngine.run",
                new_callable=AsyncMock,
            ) as mock_run,
        ):
            await orchestrator.resume_session(sample_access_token, sample_thread_id, mock_websocket)

            mock_chat_session_store.resume_thread.assert_called_once()
            mock_chat_session_store.get_paginated_messages.assert_called_once()
            mock_chat_session_store.get_recipes_by_message_ids.assert_not_called()
            expected_paginated_messages = PaginatedApiMessages.from_paginated_messages(sample_paginated_messages)
            
            mock_websocket_event_sender.send_event.assert_called_once_with(
                mock_websocket,
                "thread_resumed",
                {
                    "user_access": sample_anonymous_user_access.model_dump(),
                    "thread": sample_thread.model_dump(),
                    "paginated_messages": expected_paginated_messages.model_dump(),
                    "recipes": [],
                },
            )

            mock_run.assert_called_once()

    @pytest.mark.asyncio
    async def test_resume_session_success_with_recipes(
        self,
        orchestrator: ChatSessionOrchestrator,
        mock_websocket: AsyncMock,
        mock_user_access_cache_service: UserAccessCacheService,
        mock_chat_session_store: ChatSessionStore,
        mock_websocket_event_sender: WebSocketEventSender,
        sample_access_token: str,
        sample_thread_id: str,
        sample_anonymous_user_access: UserAccess,
        sample_thread: Thread,
        sample_paginated_messages: PaginatedMessages,
        sample_recipes: list[UserRecipe],
    ) -> None:
        mock_user_access_cache_service.get_user_access = AsyncMock(
            return_value=sample_anonymous_user_access
        )

        paginated_messages_with_recipes = sample_paginated_messages.copy()
        paginated_messages_with_recipes.messages[0].recipe_id = sample_recipes[0].id

        with (
            patch.object(
                mock_chat_session_store,
                "resume_thread",
                new_callable=AsyncMock,
                return_value=sample_thread,
            ),
            patch.object(
                mock_chat_session_store,
                "get_paginated_messages",
                new_callable=AsyncMock,
                return_value=paginated_messages_with_recipes,
            ),
            patch.object(
                mock_chat_session_store,
                "get_recipes_by_message_ids",
                new_callable=AsyncMock,
                return_value=sample_recipes,
            ),
            patch(
                "services.chat_services.chat_session_engine.ChatSessionEngine.run",
                new_callable=AsyncMock,
            ) as mock_run,
        ):
            await orchestrator.resume_session(sample_access_token, sample_thread_id, mock_websocket)

            mock_chat_session_store.resume_thread.assert_called_once()
            mock_chat_session_store.get_paginated_messages.assert_called_once()
            mock_chat_session_store.get_recipes_by_message_ids.assert_called_once()
            expected_paginated_messages = PaginatedApiMessages.from_paginated_messages(paginated_messages_with_recipes)
            
            mock_websocket_event_sender.send_event.assert_called_once_with(
                mock_websocket,
                "thread_resumed",
                {
                    "user_access": sample_anonymous_user_access.model_dump(),
                    "thread": sample_thread.model_dump(),
                    "paginated_messages": expected_paginated_messages.model_dump(),
                    "recipes": [recipe.model_dump() for recipe in sample_recipes],
                },
            )

            mock_run.assert_called_once()

    @pytest.mark.asyncio
    async def test_resume_session_token_expired(
        self,
        orchestrator: ChatSessionOrchestrator,
        mock_websocket: AsyncMock,
        mock_user_access_cache_service: UserAccessCacheService,
        mock_websocket_event_sender: WebSocketEventSender,
        sample_access_token: str,
        sample_thread_id: str,
    ) -> None:
        mock_user_access_cache_service.get_user_access = AsyncMock(return_value=None)

        await orchestrator.resume_session(sample_access_token, sample_thread_id, mock_websocket)

        chat_error = AccessTokenNotFoundError(sample_access_token)
        mock_websocket_event_sender.send_event.assert_called_once_with(
            mock_websocket, "chat_session_error", chat_error.dict()
        )
        mock_websocket.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_resume_session_thread_not_found(
        self,
        orchestrator: ChatSessionOrchestrator,
        mock_websocket: AsyncMock,
        mock_user_access_cache_service: UserAccessCacheService,
        mock_chat_session_store: ChatSessionStore,
        mock_websocket_event_sender: WebSocketEventSender,
        sample_access_token: str,
        sample_thread_id: str,
        sample_anonymous_user_access: UserAccess,
    ) -> None:
        mock_user_access_cache_service.get_user_access = AsyncMock(
            return_value=sample_anonymous_user_access
        )
        mock_chat_session_store.resume_thread = AsyncMock(return_value=None)

        await orchestrator.resume_session(sample_access_token, sample_thread_id, mock_websocket)

        chat_error = ThreadNotFoundError(thread_id=sample_thread_id)
        mock_websocket_event_sender.send_event.assert_called_once_with(
            mock_websocket, "chat_session_error", chat_error.dict()
        )
        mock_websocket.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_resume_session_disconnected(
        self,
        orchestrator: ChatSessionOrchestrator,
        mock_websocket: AsyncMock,
        mock_user_access_cache_service: UserAccessCacheService,
        sample_access_token: str,
        sample_thread_id: str,
        sample_thread: Thread,
        sample_paginated_messages: PaginatedMessages,
        sample_recipes: list[UserRecipe],
        sample_anonymous_user_access: UserAccess,
    ) -> None:
        mock_user_access_cache_service.get_user_access = AsyncMock(
            return_value=sample_anonymous_user_access
        )
        mock_websocket.client_state = WebSocketState.DISCONNECTED

        with (
            patch.object(
                orchestrator,
                "_resume_thread",
                new_callable=AsyncMock,
                return_value={
                    "thread": sample_thread.model_dump(),
                    "paginated_messages": sample_paginated_messages.model_dump(),
                    "recipes": [recipe.model_dump() for recipe in sample_recipes],
                },
            ),
            patch(
                "services.chat_services.chat_session_engine.ChatSessionEngine.run",
                new_callable=AsyncMock,
            ) as mock_run,
        ):
            await orchestrator.resume_session(sample_access_token, sample_thread_id, mock_websocket)

            mock_run.assert_not_called()

    @pytest.mark.asyncio
    async def test_resume_session_internal_error(
        self,
        orchestrator: ChatSessionOrchestrator,
        mock_websocket: AsyncMock,
        mock_user_access_cache_service: UserAccessCacheService,
        mock_chat_session_limit_checker: ChatSessionLimitChecker,
        mock_chat_session_store: ChatSessionStore,
        mock_websocket_event_sender: WebSocketEventSender,
        sample_access_token: str,
        sample_thread_id: str,
        sample_thread: Thread,
        sample_paginated_messages: PaginatedMessages,
        sample_recipes: list[UserRecipe],
    ) -> None:
        mock_user_access_cache_service.get_user_access = AsyncMock(
            side_effect=Exception("Test error")
        )
        mock_chat_session_limit_checker.has_message_limit_reached = AsyncMock(return_value=False)
        mock_chat_session_limit_checker.get_message_limit = AsyncMock(return_value=100)
        mock_chat_session_store.create_thread = AsyncMock(return_value=sample_thread)

        with (
            patch.object(
                orchestrator,
                "_resume_thread",
                new_callable=AsyncMock,
                return_value={
                    "thread": sample_thread.model_dump(),
                    "paginated_messages": sample_paginated_messages.model_dump(),
                    "recipes": [recipe.model_dump() for recipe in sample_recipes],
                },
            ),
            patch(
                "services.chat_services.chat_session_engine.ChatSessionEngine.run",
                new_callable=AsyncMock,
            ) as mock_run,
        ):
            await orchestrator.resume_session(sample_access_token, sample_thread_id, mock_websocket)

            mock_run.assert_not_called()

            chat_error = InternalServerError()
            mock_websocket_event_sender.send_event.assert_called_once_with(
                mock_websocket, "chat_session_error", chat_error.dict()
            )
            mock_websocket.close.assert_called_once()
