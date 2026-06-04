import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import WebSocket
from fastapi.websockets import WebSocketState
from sqlalchemy.ext.asyncio import AsyncSession

from database.index import DBTransactionMaker

from services.ai_food_agent.ai_food_agent import AIFoodAgent
from services.chat_services.chat_session_engine import ChatSessionEngine
from services.chat_services.chat_session_handlers import ChatSessionHandlers
from services.chat_services.chat_session_message_guard import ChatSessionMessageGuard
from services.chat_services.chat_session_store import ChatSessionStore
from services.websocket_event_sender import WebSocketEventSender

from schemas.chat_session_errors import (
    ChatSessionError,
    InternalServerError,
    OverMessageLimitError,
    ThreadNotFoundError,
)
from schemas.messages import GetMessagesParams, PaginatedApiMessages
from schemas.threads import CreateThreadParams, ResumeThreadParams, Thread

from utils.logger import Logger

logger = Logger("chat_session_maker")


class ChatSessionOrchestrator:
    def __init__(
        self,
        message_limit: int | None,
        db_transaction_maker: DBTransactionMaker,
        ai_food_agent: AIFoodAgent,
        websocket_event_sender: WebSocketEventSender,
        chat_session_store: ChatSessionStore,
        chat_session_handlers: ChatSessionHandlers,
        chat_session_message_guard: ChatSessionMessageGuard,
    ):
        self.message_limit = message_limit
        self.db_transaction_maker = db_transaction_maker
        self.ai_food_agent = ai_food_agent
        self.websocket_event_sender = websocket_event_sender
        self.chat_session_store = chat_session_store
        self.chat_session_handlers = chat_session_handlers
        self.chat_session_message_guard = chat_session_message_guard

    def _create_chat_session_engine(
        self, user_id: str, thread_id: str, websocket: WebSocket
    ) -> ChatSessionEngine:
        return ChatSessionEngine(
            user_id=user_id,
            thread_id=thread_id,
            message_limit=self.message_limit,
            websocket=websocket,
            db_transaction_maker=self.db_transaction_maker,
            ai_food_agent=self.ai_food_agent,
            websocket_event_sender=self.websocket_event_sender,
            chat_session_store=self.chat_session_store,
            chat_session_handlers=self.chat_session_handlers,
            chat_session_message_guard=self.chat_session_message_guard,
        )

    async def _handle_chat_session_error(
        self, websocket: WebSocket, error: ChatSessionError
    ) -> None:
        sent = await self.websocket_event_sender.send_event(
            websocket, "chat_session_error", error.dict()
        )
        if sent and websocket.client_state == WebSocketState.CONNECTED:
            await websocket.close(code=error.code, reason=error.type.value)

    async def _create_new_thread(self, db: AsyncSession, user_id: str) -> Thread:
        timestamp = datetime.now(timezone.utc)
        return await self.chat_session_store.create_thread(
            db,
            CreateThreadParams(
                id=str(uuid.uuid4()),
                user_id=user_id,
                created_at=timestamp,
                updated_at=timestamp,
                is_empty=True,
            ),
        )

    async def start_session(self, user_id: str, websocket: WebSocket) -> None:
        logger.info(f"Starting session for user: {user_id}")

        try:
            async with self.db_transaction_maker() as db:  # type: ignore
                await self.chat_session_store.check_message_limit(db, user_id, self.message_limit)
                thread = await self._create_new_thread(db, user_id)

            sent = await self.websocket_event_sender.send_event(
                websocket,
                "thread_started",
                {"user_id": user_id, "thread": thread.model_dump()},
            )

            if sent and websocket.client_state == WebSocketState.CONNECTED:
                engine = self._create_chat_session_engine(user_id, thread.id, websocket)
                async with engine:
                    await engine.run()
            else:
                logger.info(f"WebSocket disconnected for user: {user_id}")

        except OverMessageLimitError as e:
            await self._handle_chat_session_error(websocket, e)

        except Exception as e:
            logger.error(f"Error starting session: {e}")
            await self._handle_chat_session_error(websocket, InternalServerError())

    async def _resume_thread(self, user_id: str, thread_id: str) -> dict[str, Any]:
        async with self.db_transaction_maker() as db:  # type: ignore
            timestamp = datetime.now(timezone.utc)

            thread = await self.chat_session_store.resume_thread(
                db, ResumeThreadParams(id=thread_id, resumed_at=timestamp)
            )
            if thread is None:
                raise ThreadNotFoundError(thread_id=thread_id)

            paginated_messages = await self.chat_session_store.get_paginated_messages(
                db,
                GetMessagesParams(
                    user_id=user_id,
                    thread_id=thread_id,
                    limit=10,
                    sort_by="created_at",
                    sort_order="desc",
                ),
            )

            recipe_message_ids = [
                msg.id for msg in paginated_messages.messages if msg.recipe_id
            ]
            recipes = (
                await self.chat_session_store.get_recipes_by_message_ids(db, recipe_message_ids)
                if recipe_message_ids
                else []
            )

            return {
                "thread": thread.model_dump(),
                "paginated_messages": PaginatedApiMessages.from_paginated_messages(
                    paginated_messages
                ).model_dump(),
                "recipes": [recipe.model_dump() for recipe in recipes],
            }

    async def resume_session(self, user_id: str, thread_id: str, websocket: WebSocket) -> None:
        logger.info(f"Resuming session for user: {user_id}, thread: {thread_id}")

        try:
            loaded_data = await self._resume_thread(user_id, thread_id)

            sent = await self.websocket_event_sender.send_event(
                websocket,
                "thread_resumed",
                {
                    "user_id": user_id,
                    "thread": loaded_data["thread"],
                    "paginated_messages": loaded_data["paginated_messages"],
                    "recipes": loaded_data["recipes"],
                },
            )

            if sent and websocket.client_state == WebSocketState.CONNECTED:
                engine = self._create_chat_session_engine(user_id, thread_id, websocket)
                async with engine:
                    await engine.run()
            else:
                logger.info(f"WebSocket disconnected for user: {user_id}")

        except ThreadNotFoundError as e:
            await self._handle_chat_session_error(websocket, e)

        except Exception as e:
            logger.error(f"Error resuming session: {e}")
            await self._handle_chat_session_error(websocket, InternalServerError())
