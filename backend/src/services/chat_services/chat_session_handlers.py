import uuid
from datetime import datetime
from typing import TypedDict, Union

from schemas.conversation_stream_events import (
    AIAgentErrorPayload,
    RecipeFieldDetectedPayload,
    RecipeGenerationCompletedPayload,
    RecipeGenerationStartedPayload,
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
    ApiMessage,
    UpdateMessageParams,
    UpdateMessageTextContentParams,
    UpdateMessageInputTokensParams,
    UpdateMessageOutputTokensParams,
    UpdateStrategy,
)
from schemas.recipes import UserRecipe
from schemas.threads import Thread, UpdateThreadParams
from services.chat_services.chat_session_store import ChatSessionStore
from sqlalchemy.ext.asyncio import AsyncSession
from utils.logger import Logger

logger = Logger("chat_session_handlers")


class ThreadResult(TypedDict):
    thread: Thread


class MessageResult(TypedDict):
    thread: Thread
    message: ApiMessage


class MessageAndRecipeResult(MessageResult):
    recipe: UserRecipe


class RecipeResult(TypedDict):
    recipe: UserRecipe


class ErrorResult(TypedDict):
    thread: Thread
    error_message: str


ChatSessionHandlersResult = Union[
    ThreadResult, MessageResult, MessageAndRecipeResult, RecipeResult, ErrorResult
]


class ChatSessionHandlers:
    def __init__(self, chat_session_store: ChatSessionStore):
        self.chat_session_store = chat_session_store

    async def handle_text_message_started(
        self,
        db: AsyncSession,
        user_id: str,
        thread_id: str,
        assistant_message_id: str,
        payload: TextMessageStartedPayload,
        timestamp: datetime,
        *,
        user_message_id: str,
    ) -> ChatSessionHandlersResult:
        try:
            thread = await self.chat_session_store.update_thread(
                db,
                UpdateThreadParams(
                    id=thread_id, updated_at=timestamp, error_message=None, is_empty=False
                ),
            )
            message = await self.chat_session_store.create_assistant_text_message(
                db,
                CreateAssistantTextMessageParams(
                    id=assistant_message_id,
                    user_id=user_id,
                    thread_id=thread_id,
                    text_content="",
                    created_at=timestamp,
                    updated_at=timestamp,
                    parent_id=user_message_id,
                    role=MessageRole.assistant,
                    content_type=MessageContentType.text,
                ),
            )
            return {"thread": thread, "message": ApiMessage.from_message(message)}
        except Exception as e:
            logger.error(f"Error when handling text message started for user_id {user_id}: {e}")
            raise e

    async def handle_text_message_chunk_generated(
        self,
        db: AsyncSession,
        user_id: str,
        thread_id: str,
        assistant_message_id: str,
        payload: TextMessageChunkGeneratedPayload,
        timestamp: datetime,
    ) -> ChatSessionHandlersResult:
        try:
            updated_message = await self.chat_session_store.update_message(
                db,
                UpdateMessageParams(
                    id=assistant_message_id,
                    updated_at=timestamp,
                    text_content_update=UpdateMessageTextContentParams(
                        text_content=payload.message_chunk,
                        strategy=UpdateStrategy.APPEND,
                    ),
                    input_tokens_update=UpdateMessageInputTokensParams(
                        input_tokens=payload.metadata.input_tokens,
                        strategy=UpdateStrategy.APPEND,
                    ),
                    output_tokens_update=UpdateMessageOutputTokensParams(
                        output_tokens=payload.metadata.output_tokens,
                        strategy=UpdateStrategy.APPEND,
                    ),
                    model_name=payload.metadata.model_name,
                ),
            )
            thread = await self.chat_session_store.update_thread(
                db,
                UpdateThreadParams(
                    id=thread_id, updated_at=timestamp, error_message=None, is_empty=False
                ),
            )
            return {"thread": thread, "message": ApiMessage.from_message(updated_message)}
        except Exception as e:
            logger.error(
                f"Error when handling text message chunk generated for user_id {user_id}: {e}"
            )
            raise e

    async def handle_text_message_completed(
        self,
        db: AsyncSession,
        user_id: str,
        thread_id: str,
        assistant_message_id: str,
        payload: TextMessageCompletedPayload,
        timestamp: datetime,
    ) -> ChatSessionHandlersResult:
        try:
            updated_message = await self.chat_session_store.update_message(
                db,
                UpdateMessageParams(
                    id=assistant_message_id,
                    updated_at=timestamp,
                    text_content_update=UpdateMessageTextContentParams(
                        text_content=payload.full_message,
                        strategy=UpdateStrategy.REPLACE,
                    ),
                ),
            )
            updated_thread = await self.chat_session_store.update_thread(
                db,
                UpdateThreadParams(
                    id=thread_id, updated_at=timestamp, error_message=None, is_empty=False
                ),
            )
            return {"thread": updated_thread, "message": ApiMessage.from_message(updated_message)}
        except Exception as e:
            logger.error(
                f"Error when handling text message completed for user_id {user_id}: {e}"
            )
            raise e

    async def handle_recipe_generation_started(
        self,
        db: AsyncSession,
        user_id: str,
        thread_id: str,
        assistant_message_id: str,
        payload: RecipeGenerationStartedPayload,
        timestamp: datetime,
        user_message_id: str,
    ) -> ChatSessionHandlersResult:
        try:
            recipe_id = str(uuid.uuid4())
            recipe = await self.chat_session_store.create_recipe(
                db, user_id, thread_id, recipe_id, timestamp
            )
            message = await self.chat_session_store.create_assistant_recipe_message(
                db,
                CreateAssistantRecipeMessageParams(
                    id=assistant_message_id,
                    user_id=user_id,
                    thread_id=thread_id,
                    recipe_id=recipe_id,
                    is_recipe_generation_started=True,
                    tool_name=payload.tool_name,
                    tool_input=payload.tool_input,
                    created_at=timestamp,
                    updated_at=timestamp,
                    parent_id=user_message_id,
                    role=MessageRole.assistant,
                    content_type=MessageContentType.recipe,
                ),
            )
            thread = await self.chat_session_store.update_thread(
                db,
                UpdateThreadParams(
                    id=thread_id, updated_at=timestamp, error_message=None, is_empty=False
                ),
            )
            return {"thread": thread, "message": ApiMessage.from_message(message), "recipe": recipe}
        except Exception as e:
            logger.error(
                f"Error when handling recipe generation started for user_id {user_id}: {e}"
            )
            raise e

    async def handle_recipe_field_detected(
        self,
        db: AsyncSession,
        user_id: str,
        thread_id: str,
        assistant_message_id: str,
        payload: RecipeFieldDetectedPayload,
        timestamp: datetime,
    ) -> ChatSessionHandlersResult:
        try:
            updated_recipe = await self.chat_session_store.update_message_recipe_field(
                db, assistant_message_id, payload.field, timestamp
            )
            return {"recipe": updated_recipe}
        except Exception as e:
            logger.error(f"Error when handling recipe field detected for user_id {user_id}: {e}")
            raise e

    async def handle_recipe_generation_completed(
        self,
        db: AsyncSession,
        user_id: str,
        thread_id: str,
        assistant_message_id: str,
        payload: RecipeGenerationCompletedPayload,
        timestamp: datetime,
    ) -> ChatSessionHandlersResult:
        try:
            updated_message = await self.chat_session_store.update_message(
                db,
                UpdateMessageParams(
                    id=assistant_message_id,
                    updated_at=timestamp,
                    input_tokens_update=UpdateMessageInputTokensParams(
                        input_tokens=payload.tool_metadata.input_tokens,
                        strategy=UpdateStrategy.APPEND,
                    ),
                    output_tokens_update=UpdateMessageOutputTokensParams(
                        output_tokens=payload.tool_metadata.output_tokens,
                        strategy=UpdateStrategy.APPEND,
                    ),
                    tool_output=payload.tool_output,
                    is_recipe_generation_completed=True,
                    is_recipe_generation_started=False,
                    model_name=payload.tool_metadata.model_name,
                ),
            )
            recipe = await self.chat_session_store.update_message_recipe(
                db, assistant_message_id, payload.recipe, timestamp
            )
            thread = await self.chat_session_store.update_thread(
                db,
                UpdateThreadParams(
                    id=thread_id, updated_at=timestamp, error_message=None, is_empty=False
                ),
            )
            return {
                "thread": thread,
                "message": ApiMessage.from_message(updated_message),
                "recipe": recipe,
            }
        except Exception as e:
            logger.error(
                f"Error when handling recipe generation completed for user_id {user_id}: {e}"
            )
            raise e

    async def handle_ai_agent_error(
        self,
        db: AsyncSession,
        user_id: str,
        thread_id: str,
        payload: AIAgentErrorPayload,
        timestamp: datetime,
    ) -> ChatSessionHandlersResult:
        try:
            logger.error(f"Error for user_id {user_id} with timestamp {timestamp}: {payload.error_message}")
            thread = await self.chat_session_store.update_thread(
                db,
                UpdateThreadParams(
                    id=thread_id,
                    updated_at=timestamp,
                    error_message=payload.error_message,
                    is_empty=False,
                ),
            )
            return {"thread": thread, "error_message": payload.error_message}
        except Exception as e:
            logger.error(f"Error when handling ai agent error for user_id {user_id}: {e}")
            raise e

    async def handle_summary_updated(
        self,
        db: AsyncSession,
        user_id: str,
        thread_id: str,
        payload: SummaryUpdatedPayload,
        timestamp: datetime,
    ) -> ChatSessionHandlersResult:
        try:
            thread = await self.chat_session_store.update_thread(
                db,
                UpdateThreadParams(
                    id=thread_id,
                    updated_at=timestamp,
                    error_message=None,
                    is_empty=False,
                    summary=payload.summary,
                ),
            )
            return {"thread": thread}
        except Exception as e:
            logger.error(f"Error when handling summary updated for user_id {user_id}: {e}")
            raise e

    async def handle_thread_title_updated(
        self,
        db: AsyncSession,
        user_id: str,
        thread_id: str,
        payload: ThreadTitleUpdatedPayload,
        timestamp: datetime,
    ) -> ChatSessionHandlersResult:
        try:
            thread = await self.chat_session_store.update_thread(
                db,
                UpdateThreadParams(
                    id=thread_id,
                    updated_at=timestamp,
                    error_message=None,
                    is_empty=False,
                    title=payload.thread_title,
                ),
            )
            return {"thread": thread}
        except Exception as e:
            logger.error(f"Error when handling thread title updated for user_id {user_id}: {e}")
            raise e

    async def handle_user_message_rejected(
        self,
        db: AsyncSession,
        user_id: str,
        thread_id: str,
        assistant_message_id: str,
        payload: UserMessageRejectedPayload,
        timestamp: datetime,
        user_message_id: str,
    ) -> ChatSessionHandlersResult:
        try:
            updated_thread = await self.chat_session_store.update_thread(
                db,
                UpdateThreadParams(id=thread_id, updated_at=timestamp, is_empty=False),
            )
            message = await self.chat_session_store.create_assistant_text_message(
                db,
                CreateAssistantTextMessageParams(
                    id=assistant_message_id,
                    user_id=user_id,
                    thread_id=thread_id,
                    text_content=payload.rejection_message,
                    created_at=timestamp,
                    updated_at=timestamp,
                    parent_id=user_message_id,
                    role=MessageRole.assistant,
                    content_type=MessageContentType.text,
                ),
            )
            return {"thread": updated_thread, "message": ApiMessage.from_message(message)}
        except Exception as e:
            logger.error(f"Error when handling user message rejected for user_id {user_id}: {e}")
            raise e
