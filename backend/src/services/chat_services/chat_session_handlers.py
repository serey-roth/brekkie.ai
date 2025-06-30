from contextlib import _AsyncGeneratorContextManager
from functools import wraps
from datetime import datetime
from typing import TypedDict, Union, TypeVar, Callable, Any
import uuid

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from schemas.conversation_stream_events import (
    TextMessageStartedPayload,
    TextMessageCompletedPayload,
    TextMessageChunkGeneratedPayload,
    RecipeGenerationStartedPayload,
    SearchCompletedPayload,
    SearchStartedPayload,
    RecipeFieldDetectedPayload,
    RecipeGenerationCompletedPayload,
    AIAgentErrorPayload,
    SummaryUpdatedPayload,
    ThreadTitleUpdatedPayload,
)
from schemas.messages import (
    CreateAssistantToolMessageParams,
    Message,
    CreateAssistantTextMessageParams,
    CreateAssistantRecipeMessageParams,
    UpdateMessageParams,
)
from schemas.threads import (
    Thread,
    UpdateThreadParams,
)
from schemas.recipes import (
    UserRecipe, 
    UpdateRecipeParams,
    UpdateRecipeFieldParams,
)
from schemas.user_access import UserAccessData

from services.chat_services.chat_session_store import ChatSessionStore

from utils.logger import Logger

logger = Logger("chat_session_handlers")


DecoratorFunc = TypeVar("DecoratorFunc", bound=Callable[..., Any])

def with_db_transaction(func: DecoratorFunc) -> DecoratorFunc:
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        async with self.db_transaction_maker() as db:
            if db is None or not isinstance(db, AsyncSession):
                raise ValueError("Database session is not found")
            return await func(self, *args, db=db, **kwargs)
    return wrapper



class BaseResult(TypedDict):
    thread: Thread


class MessageResult(BaseResult):
    message: Message


class MessageAndRecipeResult(MessageResult):
    recipe: UserRecipe


class ErrorResult(BaseResult):
    thread: Thread
    error_message: str


ChatSessionHandlersResult = Union[MessageResult, MessageAndRecipeResult, ErrorResult]


class ChatSessionHandlers:
    def __init__(
        self, 
        db_transaction_maker: _AsyncGeneratorContextManager[AsyncSession, None],
        chat_session_store: ChatSessionStore,
    ):
        self.db_transaction_maker = db_transaction_maker
        self.chat_session_store = chat_session_store
    
    @with_db_transaction
    async def handle_text_message_started(
        self, 
        user_access_data: UserAccessData,
        thread_id: str,
        assistant_message_id: str, 
        payload: TextMessageStartedPayload,
        timestamp: datetime, 
        *, 
        db: AsyncSession, 
    ) -> ChatSessionHandlersResult:
        try:
            logger.debug(f"Text message started for user_id {user_access_data.user_id} with message_id {assistant_message_id} and timestamp {timestamp}")

            thread = await self.chat_session_store.update_thread(db, user_access_data, UpdateThreadParams(
                id=thread_id,
                updated_at=timestamp,
                error_message=None,
                is_empty=False,
            ))
            message = await self.chat_session_store.create_assistant_text_message(db, user_access_data, CreateAssistantTextMessageParams(
                id=assistant_message_id,
                thread_id=thread_id,
                text_content="",
                created_at=timestamp,
                updated_at=timestamp,
            ))
            
            return { "thread": thread, "message": message }
        
        except Exception as e:
            logger.error(f"Error when handling text message started for user_id {user_access_data.user_id}: {e}")
            raise e


    @with_db_transaction
    async def handle_text_message_chunk_generated(
        self, 
        user_access_data: UserAccessData,   
        thread_id: str,
        assistant_message_id: str, 
        payload: TextMessageChunkGeneratedPayload, 
        timestamp: datetime, 
        *, 
        db: AsyncSession
    ) -> ChatSessionHandlersResult:
        try:
            logger.debug(f"Text message chunk generated for user_id {user_access_data.user_id} with message_id {assistant_message_id} and message chunk {payload.message_chunk[:50]}... and timestamp {timestamp}")

            current_message = await self.chat_session_store.get_message(db, user_access_data, thread_id, assistant_message_id)
            if current_message is None:
                raise ValueError(f"Message {assistant_message_id} not found")
            
            message_chunk = payload.message_chunk
            updated_text_content = (current_message.text_content or "") + message_chunk
            
            metadata = payload.metadata
            updated_input_tokens = (current_message.input_tokens or 0) + metadata.input_tokens
            updated_output_tokens = (current_message.output_tokens or 0) + metadata.output_tokens
            
            thread = await self.chat_session_store.update_thread(db, user_access_data, UpdateThreadParams(
                id=thread_id,
                updated_at=timestamp,
                error_message=None,
                is_empty=False,
            ))
            message = await self.chat_session_store.update_message(db, user_access_data, thread_id, UpdateMessageParams(
                id=assistant_message_id,
                updated_at=timestamp,
                model_name=metadata.model_name,
                text_content=updated_text_content,
                input_tokens=updated_input_tokens,
                output_tokens=updated_output_tokens,
            ))
            
            return { "thread": thread, "message": message }
            
        except Exception as e:
            logger.error(f"Error when handling text message chunk generated for user_id {user_access_data.user_id}: {e}")
            raise e


    @with_db_transaction
    async def handle_text_message_completed(
        self, 
        user_access_data: UserAccessData,
        thread_id: str,
        assistant_message_id: str, 
        payload: TextMessageCompletedPayload,
        timestamp: datetime, 
        *, 
        db: AsyncSession,
    ) -> ChatSessionHandlersResult:
        try:
            logger.debug(f"Text message completed for user_id {user_access_data.user_id} with message_id {assistant_message_id} and full_message {payload.full_message[:50]}...")
        
            thread = await self.chat_session_store.update_thread(db, user_access_data, UpdateThreadParams(
                id=thread_id,
                updated_at=timestamp,
                error_message=None,
                is_empty=False,
            ))
            message = await self.chat_session_store.update_message(db, user_access_data, thread_id, UpdateMessageParams(
                id=assistant_message_id,
                updated_at=timestamp,
                text_content=payload.full_message,
            ))
            
            return { "thread": thread, "message": message }
    
        except Exception as e:
            logger.error(f"Error when handling text message completed for user_id {user_access_data.user_id}: {e}")
            raise e
        

    @with_db_transaction
    async def handle_recipe_generation_started(
        self, 
        user_access_data: UserAccessData,
        thread_id: str,
        assistant_message_id: str, 
        payload: RecipeGenerationStartedPayload,
        timestamp: datetime, 
        *, 
        db: AsyncSession,
    ) -> ChatSessionHandlersResult:
        try:
            logger.debug(f"Recipe generation started for user_id {user_access_data.user_id} with message_id {assistant_message_id} and timestamp {timestamp}")
        
            recipe_tool_name = payload.tool_name
            recipe_tool_input = payload.tool_input
            
            recipe_id = str(uuid.uuid4())
            recipe = await self.chat_session_store.create_recipe(db, user_access_data, thread_id, recipe_id, timestamp)
            thread = await self.chat_session_store.update_thread(db, user_access_data, UpdateThreadParams(
                id=thread_id,
                updated_at=timestamp,
                error_message=None,
                is_empty=False,
            ))
            message = await self.chat_session_store.create_assistant_recipe_message(db, user_access_data, CreateAssistantRecipeMessageParams(
                id=assistant_message_id,
                thread_id=thread_id,
                recipe_id=recipe_id,
                is_recipe_generation_started=True,
                tool_name=recipe_tool_name,
                tool_input=recipe_tool_input,
                created_at=timestamp,
                updated_at=timestamp,
            ))
            
            return { "thread": thread, "message": message, "recipe": recipe }
            
        except Exception as e:
            logger.error(f"Error when handling recipe generation started for user_id {user_access_data.user_id}: {e}")
            raise e


    @with_db_transaction
    async def handle_recipe_field_detected(
        self, 
        user_access_data: UserAccessData,
        thread_id: str,
        assistant_message_id: str, 
        payload: RecipeFieldDetectedPayload,
        timestamp: datetime, 
        *, 
        db: AsyncSession,
    ) -> ChatSessionHandlersResult:
        try:
            logger.debug(f"Recipe field detected for user_id {user_access_data.user_id} with message_id {assistant_message_id} and field {payload.field.name} and value {payload.field.value} and timestamp {timestamp}")
            
            field = payload.field
            
            message = await self.chat_session_store.get_message(db, user_access_data, thread_id, assistant_message_id)
            if message.recipe_id is None:
                logger.error(f"Message {assistant_message_id} has no recipe id")
                raise ValueError(f"Message {assistant_message_id} has no recipe id")
            
            recipe = await self.chat_session_store.update_recipe_field(db, user_access_data, thread_id, UpdateRecipeFieldParams(
                id=message.recipe_id,
                updated_at=timestamp,
                field=field,
            ))
            thread = await self.chat_session_store.update_thread(db, user_access_data, UpdateThreadParams(
                id=thread_id,
                updated_at=timestamp,
                error_message=None,
                is_empty=False,
            ))
            message = await self.chat_session_store.update_message(db, user_access_data, thread_id, UpdateMessageParams(
                id=assistant_message_id,
                updated_at=timestamp,
                recipe_id=recipe.id,
            ))

            return { "thread": thread, "message": message, "recipe": recipe }

        except Exception as e:
            logger.error(f"Error when handling recipe field detected for user_id {user_access_data.user_id}: {e}")
            raise e


    @with_db_transaction
    async def handle_recipe_generation_completed(
        self, 
        user_access_data: UserAccessData,
        thread_id: str,
        assistant_message_id: str, 
        payload: RecipeGenerationCompletedPayload,
        timestamp: datetime, 
        *, 
        db: AsyncSession,
    ) -> ChatSessionHandlersResult:
        try:
            logger.debug(f"Recipe generation completed for user_id {user_access_data.user_id} with message_id {assistant_message_id} and timestamp {timestamp}")
        
            message = await self.chat_session_store.get_message(db, user_access_data, thread_id, assistant_message_id)
            if message.recipe_id is None:
                logger.error(f"Message {assistant_message_id} has no recipe id")
                raise ValueError(f"Message {assistant_message_id} has no recipe id")
            
            recipe_tool_output = payload.tool_output
            recipe_tool_metadata = payload.tool_metadata
            recipe = payload.recipe
            
            model_name = recipe_tool_metadata.model_name
            updated_input_tokens = (message.input_tokens or 0) + recipe_tool_metadata.input_tokens
            updated_output_tokens = (message.output_tokens or 0) + recipe_tool_metadata.output_tokens
            
            recipe = await self.chat_session_store.update_recipe(db, user_access_data, thread_id, UpdateRecipeParams(
                id=message.recipe_id,
                updated_at=timestamp,
                **recipe.model_dump(),
            ))
            thread = await self.chat_session_store.update_thread(db, user_access_data, UpdateThreadParams(
                id=thread_id,
                updated_at=timestamp,
                error_message=None,
                is_empty=False,
            ))
            message = await self.chat_session_store.update_message(db, user_access_data, thread_id, UpdateMessageParams(
                id=assistant_message_id,
                updated_at=timestamp,
                recipe_id=recipe.id,
                is_recipe_generation_started=False,
                is_recipe_generation_completed=True,
                tool_output=recipe_tool_output,
                model_name=model_name,
                input_tokens=updated_input_tokens,
                output_tokens=updated_output_tokens,
            ))
            
            return { "thread": thread, "message": message, "recipe": recipe }
            
        except Exception as e:
            logger.error(f"Error when handling recipe generation completed for user_id {user_access_data.user_id}: {e}")
            raise e


    @with_db_transaction
    async def handle_search_started(
        self, 
        user_access_data: UserAccessData,
        thread_id: str,
        assistant_message_id: str, 
        payload: SearchStartedPayload,
        timestamp: datetime, 
        *, 
        db: AsyncSession,
    ) -> ChatSessionHandlersResult:
        try:
            logger.debug(f"Search started for user_id {user_access_data.user_id} with message_id {assistant_message_id} and timestamp {timestamp}")
            
            search_tool_name = payload.tool_name
            search_tool_input = payload.tool_input
            
            thread = await self.chat_session_store.update_thread(db, user_access_data, UpdateThreadParams(
                id=thread_id,
                updated_at=timestamp,
                error_message=None,
                is_empty=False,
            ))
            message = await self.chat_session_store.create_assistant_tool_message(db, user_access_data, CreateAssistantToolMessageParams(
                id=assistant_message_id,
                thread_id=thread_id,
                tool_name=search_tool_name,
                tool_input=search_tool_input,
                created_at=timestamp,
                updated_at=timestamp,
            ))
            
            return { "thread": thread, "message": message }

        except Exception as e:
            logger.error(f"Error when handling search started for user_id {user_access_data.user_id}: {e}")
            raise e


    @with_db_transaction
    async def handle_search_completed(
        self, 
        user_access_data: UserAccessData,
        thread_id: str,
        assistant_message_id: str, 
        payload: SearchCompletedPayload,
        timestamp: datetime, 
        *, 
        db: AsyncSession,
    ) -> ChatSessionHandlersResult:
        try:
            logger.debug(f"Search completed for user_id {user_access_data.user_id} with message_id {assistant_message_id} and timestamp {timestamp}")

            message = await self.chat_session_store.get_message(db, user_access_data, thread_id, assistant_message_id)
            if message is None:
                logger.error(f"Message {assistant_message_id} not found")
                raise ValueError(f"Message {assistant_message_id} not found")
            
            search_tool_output = payload.tool_output
            search_tool_metadata = payload.tool_metadata
            model_name = search_tool_metadata.model_name
            updated_input_tokens = (message.input_tokens or 0) + search_tool_metadata.input_tokens
            updated_output_tokens = (message.output_tokens or 0) + search_tool_metadata.output_tokens
            
            thread = await self.chat_session_store.update_thread(db, user_access_data, UpdateThreadParams(
                id=thread_id,
                updated_at=timestamp,
                error_message=None,
                is_empty=False,
            ))
            message = await self.chat_session_store.update_message(db, user_access_data, thread_id, UpdateMessageParams(
                id=assistant_message_id,
                updated_at=timestamp,
                tool_output=search_tool_output,
                model_name=model_name,
                input_tokens=updated_input_tokens,
                output_tokens=updated_output_tokens,
            ))
            
            return { "thread": thread, "message": message }
        
        except Exception as e:
            logger.error(f"Error when handling search completed for user_id {user_access_data.user_id}: {e}")
            raise e


    @with_db_transaction
    async def handle_ai_agent_error(
        self, 
        user_access_data: UserAccessData,
        thread_id: str,
        payload: AIAgentErrorPayload,
        timestamp: datetime, 
        *, 
        db: AsyncSession,
    ) -> ChatSessionHandlersResult:
        try:
            logger.error(f"Error for user_id {user_access_data.user_id} with timestamp {timestamp}: {payload.error_message}")
            
            thread = await self.chat_session_store.update_thread(db, user_access_data, UpdateThreadParams(
                id=thread_id,
                updated_at=timestamp,
                error_message=payload.error_message,
                is_empty=False,
            ))
            
            return { "thread": thread, "error_message": payload.error_message }
        
        except Exception as e:
            logger.error(f"Error when handling ai agent error for user_id {user_access_data.user_id}: {e}")
            raise e
        

    @with_db_transaction
    async def handle_summary_updated(
        self, 
        user_access_data: UserAccessData,
        thread_id: str,
        payload: SummaryUpdatedPayload,
        timestamp: datetime, 
        *, 
        db: AsyncSession,
    ) -> ChatSessionHandlersResult:
        try:
            logger.debug(f"Summary updated for user_id {user_access_data.user_id} with timestamp {timestamp} and summary {payload.summary}")
            
            thread = await self.chat_session_store.update_thread(db, user_access_data, UpdateThreadParams(
                id=thread_id,
                updated_at=timestamp,
                error_message=None,
                is_empty=False,
                summary=payload.summary,
            ))
            
            return { "thread": thread }
        
        except Exception as e:
            logger.error(f"Error when handling summary updated for user_id {user_access_data.user_id}: {e}")
            raise e
        
        
    
    @with_db_transaction
    async def handle_thread_title_updated(
        self, 
        user_access_data: UserAccessData,
        thread_id: str,
        payload: ThreadTitleUpdatedPayload,
        timestamp: datetime, 
        *, 
        db: AsyncSession,
    ) -> ChatSessionHandlersResult: 
        try:
            logger.debug(f"Thread title updated for user_id {user_access_data.user_id} with timestamp {timestamp} and thread_title {payload.thread_title}")
            
            thread = await self.chat_session_store.update_thread(db, user_access_data, UpdateThreadParams(
                id=thread_id,
                updated_at=timestamp,
                error_message=None,
                is_empty=False,
                title=payload.thread_title,
            ))  
            
            return { "thread": thread }
        
        except Exception as e:
            logger.error(f"Error when handling thread title updated for user_id {user_access_data.user_id}: {e}")
            raise e