import json
from datetime import datetime, timezone
from typing import Any, List
from pydantic import ValidationError

from fastapi import WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState

from sqlalchemy.ext.asyncio import AsyncSession
from database.index import DBTransactionMaker

from services.ai_food_agent.ai_food_agent import AIFoodAgent
from services.chat_services.chat_session_handlers import ChatSessionHandlers
from services.chat_services.chat_session_message_guard import ChatSessionMessageGuard
from services.chat_services.chat_session_message_processor import (
    ChatSessionMessageProcessor,
    MessageProcessingResult,
)
from services.chat_services.chat_session_store import ChatSessionStore
from services.websocket_event_sender import WebSocketEventSender

from schemas.chat_session_errors import (
    ChatSessionError,
    InternalServerError,
    InvalidPayloadError,
    OverMessageLimitError,
)
from schemas.messages import UserMessagePayload
from schemas.safety_guards import SafetyIssue

from utils.logger import Logger

logger = Logger("chat_session_engine")


class ChatSessionEngine:
    def __init__(
        self,
        user_id: str,
        thread_id: str,
        message_limit: int | None,
        websocket: WebSocket,
        db_transaction_maker: DBTransactionMaker,
        ai_food_agent: AIFoodAgent,
        websocket_event_sender: WebSocketEventSender,
        chat_session_store: ChatSessionStore,
        chat_session_handlers: ChatSessionHandlers,
        chat_session_message_guard: ChatSessionMessageGuard,
    ):
        self.user_id = user_id
        self.message_limit = message_limit
        self.thread_id = thread_id
        self.websocket = websocket

        self.db_transaction_maker = db_transaction_maker
        self.ai_food_agent = ai_food_agent
        self.websocket_event_sender = websocket_event_sender
        self.session_store = chat_session_store
        self.session_handlers = chat_session_handlers
        self.message_guard = chat_session_message_guard
        self.is_closed = False

        self.message_processor = ChatSessionMessageProcessor(
            ai_food_agent=ai_food_agent,
            chat_session_handlers=chat_session_handlers,
            on_message_processed=self._handle_message_processed,
        )

    async def __aenter__(self) -> "ChatSessionEngine":
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.is_closed = True

    async def _handle_message_processed(self, processing_result: MessageProcessingResult) -> None:
        if self.is_closed:
            return

        event_name = processing_result["event"]
        handler_result = processing_result["result"]

        payload: dict[str, Any] = {"user_id": self.user_id}

        thread = handler_result.get("thread", None)
        message = handler_result.get("message", None)
        recipe = handler_result.get("recipe", None)
        error_message = handler_result.get("error_message", None)

        if thread is not None:
            payload["thread"] = thread.model_dump()
        if message is not None:
            payload["message"] = message.model_dump()
        if recipe is not None:
            payload["recipe"] = recipe.model_dump()
        if error_message is not None:
            payload["error_message"] = str(error_message)

        await self.websocket_event_sender.send_event(self.websocket, event_name, payload)

    async def _handle_chat_session_error(self, error: ChatSessionError) -> None:
        logger.error(f"Error inside message loop for user {self.user_id}: {error.type}")
        if self.is_closed or self.websocket.client_state == WebSocketState.DISCONNECTED:
            return

        self.is_closed = True
        sent = await self.websocket_event_sender.send_event(
            self.websocket, "chat_session_error", error.dict()
        )
        if sent:
            await self.websocket.close(code=error.code, reason=error.type.value)

    async def _receive_user_message(self) -> UserMessagePayload:
        try:
            raw_data = await self.websocket.receive_json()
            try:
                return UserMessagePayload.model_validate(raw_data)
            except ValidationError:
                raise InvalidPayloadError(
                    payload=raw_data if isinstance(raw_data, str) else json.dumps(raw_data)
                )
        except WebSocketDisconnect:
            logger.debug(f"WebSocket disconnected for user {self.user_id}")
            raise WebSocketDisconnect
        except InvalidPayloadError as e:
            raise e
        except Exception:
            raise InternalServerError()

    async def _reject_user_message(
        self,
        db: AsyncSession,
        user_message_id: str,
        user_input: str,
        safety_issues: List[SafetyIssue],
    ) -> None:
        try:
            rejection_message = await self.message_guard.get_rejection_message(
                user_input, safety_issues
            )
        except Exception as e:
            logger.error(f"Error generating rejection message for user {self.user_id}: {e}")
            rejection_message = "I can't respond to that message. Let's keep our conversation respectful and focused on food and cooking!"

        await self.message_processor.reject_user_message(
            db, self.user_id, self.thread_id, user_message_id, rejection_message
        )

    async def run(self) -> None:
        while not self.is_closed:
            try:
                user_message_payload = await self._receive_user_message()
                user_message_id = user_message_payload.id
                user_message_content = user_message_payload.content

                timestamp = datetime.now(timezone.utc)
                safety_guard_result = self.message_guard.check_message_safety(user_message_content)

                async with self.db_transaction_maker() as db:  # type: ignore
                    await self.session_store.check_message_limit(db, self.user_id, self.message_limit)
                    await self.session_store.create_user_message(
                        db,
                        self.user_id,
                        self.thread_id,
                        user_message_id,
                        user_message_content,
                        timestamp,
                        safety_guard_result=safety_guard_result,
                    )

                    if (
                        safety_guard_result is not None
                        and safety_guard_result.is_blocked
                        and len(safety_guard_result.issues) > 0
                    ):
                        await self._reject_user_message(
                            db, user_message_id, user_message_content, safety_guard_result.issues
                        )
                        continue

                    await self.message_processor.process_user_message(
                        db, self.user_id, self.thread_id, user_message_id, user_message_content
                    )

            except WebSocketDisconnect:
                break

            except OverMessageLimitError as e:
                await self._handle_chat_session_error(e)
                break

            except InvalidPayloadError as e:
                await self._handle_chat_session_error(e)
                continue

            except InternalServerError as e:
                await self._handle_chat_session_error(e)
                break

            except Exception as e:
                logger.error(f"Error inside message loop for user {self.user_id}: {e}")
                await self._handle_chat_session_error(InternalServerError())
                continue
