import uuid
from contextlib import _AsyncGeneratorContextManager
from datetime import datetime
from functools import wraps
from typing import Any, Callable, TypedDict, Union

from schemas.conversation_stream_events import (
    AIAgentErrorPayload,
    RecipeFieldDetectedPayload,
    RecipeGenerationCompletedPayload,
    RecipeGenerationStartedPayload,
    SearchCompletedPayload,
    SearchStartedPayload,
    SummaryUpdatedPayload,
    TextMessageChunkGeneratedPayload,
    TextMessageCompletedPayload,
    TextMessageStartedPayload,
    ThreadTitleUpdatedPayload,
    UserMessageRejectedPayload,
)
from schemas.message_content_type import MessageContentType
from schemas.message_role import MessageRole
from schemas.messages import (
    CreateAssistantRecipeMessageParams,
    CreateAssistantTextMessageParams,
    CreateAssistantToolMessageParams,
    MessageResponse,
    UpdateMessageAIModelOrToolUsageParams,
    UpdateMessageParams,
)
from schemas.recipes import (
    UserRecipe,
)
from schemas.threads import (
    Thread,
    UpdateThreadParams,
)
from schemas.user_access import UserAccess
from services.chat_services.chat_session_store import ChatSessionStore
from sqlalchemy.ext.asyncio import AsyncSession
from utils.logger import Logger

logger = Logger("chat_session_handlers")

class ThreadResult(TypedDict):
    thread: Thread


class MessageResult(TypedDict):
    thread: Thread
    message: MessageResponse


class MessageAndRecipeResult(MessageResult):
    recipe: UserRecipe


class RecipeResult(TypedDict):
    recipe: UserRecipe


class ErrorResult(TypedDict):
    thread: Thread
    error_message: str


ChatSessionHandlersResult = Union[ThreadResult, MessageResult, MessageAndRecipeResult, RecipeResult, ErrorResult]


class ChatSessionHandlers:
    def __init__(
        self,
        db_transaction_maker: _AsyncGeneratorContextManager[AsyncSession],
        chat_session_store: ChatSessionStore,
    ):
        self.db_transaction_maker = db_transaction_maker
        self.chat_session_store = chat_session_store

    async def handle_text_message_started(
        self,
        db: AsyncSession,
        user_access: UserAccess,
        thread_id: str,
        assistant_message_id: str,
        payload: TextMessageStartedPayload,
        timestamp: datetime,
        *,
        user_message_id: str,
    ) -> ChatSessionHandlersResult:
        try:
            logger.debug(
                f"Text message started for user_id {user_access.user_id} with message_id {assistant_message_id} and timestamp {timestamp}"
            )
            
            thread = await self.chat_session_store.update_thread(
                db,
                user_access,
                UpdateThreadParams(
                    id=thread_id,
                    updated_at=timestamp,
                    error_message=None,
                    is_empty=False,
                ),
                flush_db=False,
            )
            message = await self.chat_session_store.create_assistant_text_message(
                db,
                user_access,
                CreateAssistantTextMessageParams(
                    id=assistant_message_id,
                    user_id=user_access.user_id,
                    thread_id=thread_id,
                    text_content="",
                    created_at=timestamp,
                    updated_at=timestamp,
                    parent_id=user_message_id,
                    role=MessageRole.assistant,
                    content_type=MessageContentType.text,
                ),
                flush_db=False,
            )

            return {"thread": thread, "message": MessageResponse.from_message(message)}

        except Exception as e:
            logger.error(
                f"Error when handling text message started for user_id {user_access.user_id}: {e}"
            )
            raise e

    async def handle_text_message_chunk_generated(
        self,
        db: AsyncSession,
        user_access: UserAccess,
        thread_id: str,
        assistant_message_id: str,
        payload: TextMessageChunkGeneratedPayload,
        timestamp: datetime,
    ) -> ChatSessionHandlersResult:
        try:
            logger.debug(
                f"Text message chunk generated for user_id {user_access.user_id} with message_id {assistant_message_id} and message chunk {payload.message_chunk[:50]}... and timestamp {timestamp}"
            )
            
            updated_message = await self.chat_session_store.update_message_ai_model_or_tool_usage(
                db,
                user_access,
                thread_id,  
                UpdateMessageAIModelOrToolUsageParams(
                    id=assistant_message_id,
                    updated_at=timestamp,
                    text_chunk=payload.message_chunk,
                    model_name=payload.metadata.model_name,
                    input_tokens=payload.metadata.input_tokens,
                    output_tokens=payload.metadata.output_tokens,
                ),
                flush_db=False,
            )
            if updated_message is None:
                raise ValueError(f"Message {assistant_message_id} not found")
                
            thread = await self.chat_session_store.update_thread(
                db,
                user_access,
                UpdateThreadParams(
                    id=thread_id,
                    updated_at=timestamp,
                    error_message=None,
                    is_empty=False,
                ),
                flush_db=False,
            )

            return {"thread": thread, "message": MessageResponse.from_message(updated_message)}

        except Exception as e:
            logger.error(
                f"Error when handling text message chunk generated for user_id {user_access.user_id}: {e}"
            )
            raise e

    async def handle_text_message_completed(
        self,
        db: AsyncSession,
        user_access: UserAccess,
        thread_id: str,
        assistant_message_id: str,
        payload: TextMessageCompletedPayload,
        timestamp: datetime,
    ) -> ChatSessionHandlersResult:
        try:
            logger.debug(
                f"Text message completed for user_id {user_access.user_id} with message_id {assistant_message_id} and full_message {payload.full_message[:50]}..."
            )

            updated_message = await self.chat_session_store.update_message(
                db,
                user_access,
                thread_id,
                UpdateMessageParams(
                    id=assistant_message_id,
                    updated_at=timestamp,
                    text_content=payload.full_message,
                ),
                flush_db=False,
            )
            if updated_message is None:
                raise ValueError(f"Message {assistant_message_id} not found")
            
            updated_thread = await self.chat_session_store.update_thread(
                db,
                user_access,
                UpdateThreadParams(
                    id=thread_id,
                    updated_at=timestamp,
                    error_message=None,
                    is_empty=False,
                ),
                flush_db=False,
            )
            
            return {"thread": updated_thread, "message": MessageResponse.from_message(updated_message)}

        except Exception as e:
            logger.error(
                f"Error when handling text message completed for user_id {user_access.user_id}: {e}"
            )
            raise e

    async def handle_recipe_generation_started(
        self,
        db: AsyncSession,
        user_access: UserAccess,
        thread_id: str,
        assistant_message_id: str,
        payload: RecipeGenerationStartedPayload,
        timestamp: datetime,
        user_message_id: str,
    ) -> ChatSessionHandlersResult:
        try:
            logger.debug(
                f"Recipe generation started for user_id {user_access.user_id} with message_id {assistant_message_id} and timestamp {timestamp}"
            )

            recipe_tool_name = payload.tool_name
            recipe_tool_input = payload.tool_input
            recipe_id = str(uuid.uuid4())

            recipe = await self.chat_session_store.create_recipe(
                db, user_access, thread_id, recipe_id, timestamp, flush_db=False
            )
            message = await self.chat_session_store.create_assistant_recipe_message(
                db,
                user_access,
                CreateAssistantRecipeMessageParams(
                    id=assistant_message_id,
                    user_id=user_access.user_id,
                    thread_id=thread_id,
                    recipe_id=recipe_id,
                    is_recipe_generation_started=True,
                    tool_name=recipe_tool_name,
                    tool_input=recipe_tool_input,
                    created_at=timestamp,
                    updated_at=timestamp,
                    parent_id=user_message_id,
                    role=MessageRole.assistant,
                    content_type=MessageContentType.recipe,
                ),
                flush_db=False,
            )
            thread = await self.chat_session_store.update_thread(
                db,
                user_access,
                UpdateThreadParams(
                    id=thread_id,
                    updated_at=timestamp,
                    error_message=None,
                    is_empty=False,
                ),
                flush_db=False,
            )
            return {
                "thread": thread,
                "message": MessageResponse.from_message(message),
                "recipe": recipe,
            }

        except Exception as e:
            logger.error(
                f"Error when handling recipe generation started for user_id {user_access.user_id}: {e}"
            )
            raise e

    async def handle_recipe_field_detected(
        self,
        db: AsyncSession,
        user_access: UserAccess,
        thread_id: str,
        assistant_message_id: str,
        payload: RecipeFieldDetectedPayload,
        timestamp: datetime,
    ) -> ChatSessionHandlersResult:
        try:
            logger.debug(
                f"Recipe field detected for user_id {user_access.user_id} with message_id {assistant_message_id} and field {payload.field.name} and value {payload.field.value} and timestamp {timestamp}"
            )

            field = payload.field
            updated_recipe = await self.chat_session_store.update_recipe_field_by_message_id(
                db,
                user_access,
                thread_id,
                assistant_message_id,
                field,
                timestamp,
                flush_db=False,
            )

            return { "recipe": updated_recipe }

        except Exception as e:
            logger.error(
                f"Error when handling recipe field detected for user_id {user_access.user_id}: {e}"
            )
            raise e

    async def handle_recipe_generation_completed(
        self,
        db: AsyncSession,
        user_access: UserAccess,
        thread_id: str,
        assistant_message_id: str,
        payload: RecipeGenerationCompletedPayload,
        timestamp: datetime,
    ) -> ChatSessionHandlersResult:
        try:
            logger.debug(
                f"Recipe generation completed for user_id {user_access.user_id} with message_id {assistant_message_id} and timestamp {timestamp}"
            )

            updated_message = await self.chat_session_store.update_message_ai_model_or_tool_usage(
                db,
                user_access,
                thread_id,
                UpdateMessageAIModelOrToolUsageParams(
                    id=assistant_message_id,
                    updated_at=timestamp,
                    model_name=payload.tool_metadata.model_name,
                    input_tokens=payload.tool_metadata.input_tokens,
                    output_tokens=payload.tool_metadata.output_tokens,
                    tool_output=payload.tool_output,
                    is_recipe_generation_completed=True,
                    is_recipe_generation_started=False,
                ),
                flush_db=False,
            )
            if updated_message is None:
                raise ValueError(f"Message {assistant_message_id} not found")

            recipe = await self.chat_session_store.update_recipe_by_message_id(
                db,
                user_access,
                thread_id,
                assistant_message_id,
                payload.recipe,
                timestamp,
                flush_db=False,
            )
            
            thread = await self.chat_session_store.update_thread(
                db,
                user_access,
                UpdateThreadParams(
                    id=thread_id,
                    updated_at=timestamp,
                    error_message=None,
                    is_empty=False,
                ),
                flush_db=False,
            )

            return {
                "thread": thread,
                "message": MessageResponse.from_message(updated_message),
                "recipe": recipe,
            }

        except Exception as e:
            logger.error(
                f"Error when handling recipe generation completed for user_id {user_access.user_id}: {e}"
            )
            raise e

    async def handle_search_started(
        self,
        db: AsyncSession,
        user_access: UserAccess,
        thread_id: str,
        assistant_message_id: str,
        payload: SearchStartedPayload,
        timestamp: datetime,
        user_message_id: str,
    ) -> ChatSessionHandlersResult:
        try:
            logger.debug(
                f"Search started for user_id {user_access.user_id} with message_id {assistant_message_id} and timestamp {timestamp}"
            )
            
            updated_thread = await self.chat_session_store.update_thread(
                db,
                user_access,
                UpdateThreadParams(
                    id=thread_id,
                    updated_at=timestamp,
                    error_message=None,
                    is_empty=False,
                ),
                flush_db=False,
            )
            message = await self.chat_session_store.create_assistant_tool_message(
                db,
                user_access,
                CreateAssistantToolMessageParams(
                    id=assistant_message_id,
                    user_id=user_access.user_id,
                    thread_id=thread_id,
                    tool_name=payload.tool_name,
                    tool_input=payload.tool_input,
                    created_at=timestamp,
                    updated_at=timestamp,
                    parent_id=user_message_id,
                    role=MessageRole.assistant,
                    content_type=MessageContentType.tool,
                ),
                flush_db=False,
            )

            return {"thread": updated_thread, "message": MessageResponse.from_message(message)}

        except Exception as e:
            logger.error(
                f"Error when handling search started for user_id {user_access.user_id}: {e}"
            )
            raise e

    async def handle_search_completed(
        self,
        db: AsyncSession,
        user_access: UserAccess,
        thread_id: str,
        assistant_message_id: str,
        payload: SearchCompletedPayload,
        timestamp: datetime,
    ) -> ChatSessionHandlersResult:
        try:
            logger.debug(
                f"Search completed for user_id {user_access.user_id} with message_id {assistant_message_id} and timestamp {timestamp}"
            )
            
            updated_message = await self.chat_session_store.update_message_ai_model_or_tool_usage(
                db,
                user_access,
                thread_id,
                UpdateMessageAIModelOrToolUsageParams(
                    id=assistant_message_id,
                    updated_at=timestamp,
                    tool_output=payload.tool_output,
                    model_name=payload.tool_metadata.model_name,
                    input_tokens=payload.tool_metadata.input_tokens,
                    output_tokens=payload.tool_metadata.output_tokens,
                ),
                flush_db=False,
            )
            if updated_message is None:
                raise ValueError(f"Message {assistant_message_id} not found")
            
            updated_thread = await self.chat_session_store.update_thread(
                db,
                user_access,
                UpdateThreadParams(
                    id=thread_id,
                    updated_at=timestamp,
                    error_message=None,
                    is_empty=False,
                ),
                flush_db=False,
            )
            
            return {"thread": updated_thread, "message": MessageResponse.from_message(updated_message)}

        except Exception as e:
            logger.error(
                f"Error when handling search completed for user_id {user_access.user_id}: {e}"
            )
            raise e

    async def handle_ai_agent_error(
        self,
        db: AsyncSession,
        user_access: UserAccess,
        thread_id: str,
        payload: AIAgentErrorPayload,
        timestamp: datetime,
    ) -> ChatSessionHandlersResult:
        try:
            logger.error(
                f"Error for user_id {user_access.user_id} with timestamp {timestamp}: {payload.error_message}"
            )

            thread = await self.chat_session_store.update_thread(
                db,
                user_access,
                UpdateThreadParams(
                    id=thread_id,
                    updated_at=timestamp,
                    error_message=payload.error_message,
                    is_empty=False,
                ),
                flush_db=False,
            )

            return {"thread": thread, "error_message": payload.error_message}

        except Exception as e:
            logger.error(
                f"Error when handling ai agent error for user_id {user_access.user_id}: {e}"
            )
            raise e

    async def handle_summary_updated(
        self,
        db: AsyncSession,
        user_access: UserAccess,
        thread_id: str,
        payload: SummaryUpdatedPayload,
        timestamp: datetime,
    ) -> ChatSessionHandlersResult:
        try:
            logger.debug(
                f"Summary updated for user_id {user_access.user_id} with timestamp {timestamp} and summary {payload.summary}"
            )

            thread = await self.chat_session_store.update_thread(
                db,
                user_access,
                UpdateThreadParams(
                    id=thread_id,
                    updated_at=timestamp,
                    error_message=None,
                    is_empty=False,
                    summary=payload.summary,
                ),
                flush_db=False,
            )

            return {"thread": thread}

        except Exception as e:
            logger.error(
                f"Error when handling summary updated for user_id {user_access.user_id}: {e}"
            )
            raise e

    async def handle_thread_title_updated(
        self,
        db: AsyncSession,
        user_access: UserAccess,
        thread_id: str,
        payload: ThreadTitleUpdatedPayload,
        timestamp: datetime,
    ) -> ChatSessionHandlersResult:
        try:
            logger.debug(
                f"Thread title updated for user_id {user_access.user_id} with timestamp {timestamp} and thread_title {payload.thread_title}"
            )

            thread = await self.chat_session_store.update_thread(
                db,
                user_access,
                UpdateThreadParams(
                    id=thread_id,
                    updated_at=timestamp,
                    error_message=None,
                    is_empty=False,
                    title=payload.thread_title,
                ),
                flush_db=False,
            )

            return {"thread": thread}

        except Exception as e:
            logger.error(
                f"Error when handling thread title updated for user_id {user_access.user_id}: {e}"
            )
            raise e

    async def handle_user_message_rejected(
        self,
        db: AsyncSession,
        user_access: UserAccess,
        thread_id: str,
        assistant_message_id: str,
        payload: UserMessageRejectedPayload,
        timestamp: datetime,
        user_message_id: str,
    ) -> ChatSessionHandlersResult:
        try:
            logger.debug(
                f"User message rejected for user_id {user_access.user_id} with timestamp {timestamp}"
            )

            updated_thread = await self.chat_session_store.update_thread(
                db,
                user_access,
                UpdateThreadParams(
                    id=thread_id,
                    updated_at=timestamp,
                    is_empty=False,
                ),
                flush_db=False,
            )

            message = await self.chat_session_store.create_assistant_text_message(
                db,
                user_access,
                CreateAssistantTextMessageParams(
                    id=assistant_message_id,
                    user_id=user_access.user_id,
                    thread_id=thread_id,
                    text_content=payload.rejection_message,
                    created_at=timestamp,
                    updated_at=timestamp,
                    parent_id=user_message_id,
                    role=MessageRole.assistant,
                    content_type=MessageContentType.text,
                ),
                flush_db=False,
            )

            return {"thread": updated_thread, "message": MessageResponse.from_message(message)}

        except Exception as e:
            logger.error(
                f"Error when handling user message rejected for user_id {user_access.user_id}: {e}"
            )
            raise e
