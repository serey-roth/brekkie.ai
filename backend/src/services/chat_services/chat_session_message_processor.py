from typing import Callable, Awaitable, TypedDict
from datetime import datetime, timezone
import uuid

from schemas.conversation_stream_events import (
    AIAgentErrorPayload,
    ConversationStreamEvent,
    ConversationStreamEventName,
    UserMessageRejectedPayload,
)

from schemas.user_access import UserAccessData

from services.ai_food_agent.ai_food_agent import AIFoodAgent
from services.chat_services.chat_session_handlers import (
    ChatSessionHandlers,
    ChatSessionHandlersResult,
)

from utils.logger import Logger

logger = Logger("chat_session_message_processor", level="WARNING")


class MessageProcessingResult(TypedDict):
    event: ConversationStreamEventName
    result: ChatSessionHandlersResult
    timestamp: datetime


class ChatSessionMessageProcessor:
    def __init__(
        self,
        ai_food_agent: AIFoodAgent,
        chat_session_handlers: ChatSessionHandlers,
        on_message_processed: Callable[[MessageProcessingResult], Awaitable[None]] | None = None,
    ):
        self.ai_food_agent = ai_food_agent
        self.chat_session_handlers = chat_session_handlers
        self.on_message_processed = on_message_processed

        self.assistant_message_id = None

        self._event_handlers: dict[
            ConversationStreamEventName, Callable[..., Awaitable[ChatSessionHandlersResult]]
        ] = {
            "text_message_started": self.chat_session_handlers.handle_text_message_started,
            "text_message_chunk_generated": self.chat_session_handlers.handle_text_message_chunk_generated,
            "text_message_completed": self.chat_session_handlers.handle_text_message_completed,
            "recipe_generation_started": self.chat_session_handlers.handle_recipe_generation_started,
            "recipe_field_detected": self.chat_session_handlers.handle_recipe_field_detected,
            "recipe_generation_completed": self.chat_session_handlers.handle_recipe_generation_completed,
            "search_started": self.chat_session_handlers.handle_search_started,
            "search_completed": self.chat_session_handlers.handle_search_completed,
            "summary_updated": self.chat_session_handlers.handle_summary_updated,
            "thread_title_updated": self.chat_session_handlers.handle_thread_title_updated,
            "ai_agent_error": self.chat_session_handlers.handle_ai_agent_error,
            "user_message_rejected": self.chat_session_handlers.handle_user_message_rejected,
        }

    def _requires_user_message_id(self, event: ConversationStreamEvent) -> bool:
        event_name = event.event
        return event_name in [
            "text_message_started",
            "recipe_generation_started",
            "search_started",
            "user_message_rejected",
        ]

    def _requires_assistant_message_id(self, event: ConversationStreamEvent) -> bool:
        event_name = event.event
        return event_name in [
            "text_message_started",
            "text_message_chunk_generated",
            "text_message_completed",
            "recipe_generation_started",
            "recipe_field_detected",
            "recipe_generation_completed",
            "search_started",
            "search_completed",
            "user_message_rejected",
        ]

    def _requires_existing_assistant_message_id(self, event: ConversationStreamEvent) -> bool:
        event_name = event.event
        return event_name in [
            "text_message_chunk_generated",
            "text_message_completed",
            "recipe_field_detected",
            "recipe_generation_completed",
            "search_completed",
        ]

    def _should_create_assistant_message(self, event: ConversationStreamEvent) -> bool:
        event_name = event.event
        return event_name in [
            "text_message_started",
            "recipe_generation_started",
            "search_started",
            "user_message_rejected",
        ]

    def _should_reset_assistant_message(self, event: ConversationStreamEvent) -> bool:
        event_name = event.event
        return event_name in [
            "text_message_completed",
            "recipe_generation_completed",
            "search_completed",
            "user_message_rejected",
        ]

    async def _call_handler(
        self,
        user_access_data: UserAccessData,
        thread_id: str,
        user_message_id: str,
        assistant_message_id: str | None,
        event: ConversationStreamEvent,
        timestamp: datetime,
    ) -> ChatSessionHandlersResult:
        event_name = event.event
        handler = self._event_handlers.get(event_name)

        if handler is None:
            raise ValueError(f"Unknown event name: {event_name}")

        kwargs = {
            "user_access_data": user_access_data,
            "thread_id": thread_id,
            "payload": event.payload,
            "timestamp": timestamp,
        }

        if self._requires_user_message_id(event):
            kwargs["user_message_id"] = user_message_id

        if self._requires_assistant_message_id(event):
            if assistant_message_id is None:
                raise ValueError("Assistant message id is not set")

            kwargs["assistant_message_id"] = assistant_message_id

        return await handler(**kwargs)

    async def _handle_event(
        self,
        user_access_data: UserAccessData,
        thread_id: str,
        user_message_id: str,
        event: ConversationStreamEvent,
    ):
        if self._should_create_assistant_message(event):
            self.assistant_message_id = str(uuid.uuid4())

        if self._requires_existing_assistant_message_id(event):
            if self.assistant_message_id is None:
                raise ValueError("Assistant message id is not set")

        assistant_message_id = self.assistant_message_id

        timestamp = datetime.now(timezone.utc)

        result = await self._call_handler(
            user_access_data=user_access_data,
            thread_id=thread_id,
            user_message_id=user_message_id,
            assistant_message_id=assistant_message_id,
            event=event,
            timestamp=timestamp,
        )

        if self.on_message_processed:
            await self.on_message_processed(
                {"event": event.event, "result": result, "timestamp": timestamp}
            )

        if self._should_reset_assistant_message(event):
            self.assistant_message_id = None

    async def process_user_message(
        self,
        user_access_data: UserAccessData,
        thread_id: str,
        user_message_id: str,
        user_input: str,
    ):
        try:
            logger.debug(
                f"Processing chat message from user {user_access_data.user_id}: {user_input[:50]}..."
            )

            async def on_event(event: ConversationStreamEvent):
                await self._handle_event(user_access_data, thread_id, user_message_id, event)

            await self.ai_food_agent.stream_conversation(
                user_id=user_access_data.user_id,
                thread_id=thread_id,
                user_input=user_input,
                on_event=on_event,
            )

        except Exception as e:
            logger.error(f"Error processing user message: {str(e)}")
            await self._handle_event(
                user_access_data=user_access_data,
                thread_id=thread_id,
                user_message_id=user_message_id,
                event=ConversationStreamEvent(
                    event="ai_agent_error", payload=AIAgentErrorPayload(error_message=str(e))
                ),
            )

    async def reject_user_message(
        self,
        user_access_data: UserAccessData,
        thread_id: str,
        user_message_id: str,
        rejection_message: str,
    ):
        await self._handle_event(
            user_access_data=user_access_data,
            thread_id=thread_id,
            user_message_id=user_message_id,
            event=ConversationStreamEvent(
                event="user_message_rejected",
                payload=UserMessageRejectedPayload(rejection_message=rejection_message),
            ),
        )
