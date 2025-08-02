from datetime import datetime
from typing import Any, Callable

from schemas.conversation_stream_events import TextMessageChunkGeneratedPayload, TextMessageStartedPayload
from schemas.message_content_type import MessageContentType
from schemas.message_role import MessageRole
from schemas.messages import (
    CreateAssistantRecipeMessageParams,
    CreateAssistantTextMessageParams,
    CreateAssistantToolMessageParams,
    CreateUserMessageParams,
    GetMessagesParams,
    Message,
    PaginatedMessages,
    UpdateMessageParams,
    UpdateMessageAIModelOrToolUsageParams,
)
from schemas.recipes import (
    CreateRecipeParams,
    Recipe,
    RecipeField,
    UpdateRecipeFieldParams,
    UpdateRecipeParams,
    UserRecipe,
)
from schemas.safety_guards import SafetyGuardResult
from schemas.threads import (
    CreateThreadParams,
    GetUserThreadsParams,
    PaginatedThreads,
    ResumeThreadParams,
    Thread,
    UpdateThreadParams,
)
from schemas.user_access import UserAccess
from services.data_services.message_cache_service import MessageCacheService
from services.data_services.message_service import MessageService
from services.data_services.recipe_cache_service import RecipeCacheService
from services.data_services.recipe_service import RecipeService
from services.data_services.thread_cache_service import ThreadCacheService
from services.data_services.thread_service import ThreadService
from services.data_services.user_access_cache_service import UserAccessCacheService
from sqlalchemy.ext.asyncio import AsyncSession
from utils.logger import Logger

logger = Logger("chat_session_store")


# TODO: Use a custom TTL when creating data? Currently use each cache's default TTL.
class ChatSessionStore:
    def __init__(
        self,
        message_service: MessageService,
        message_cache_service: MessageCacheService,
        recipe_service: RecipeService,
        recipe_cache_service: RecipeCacheService,
        thread_service: ThreadService,
        thread_cache_service: ThreadCacheService,
        user_access_cache_service: UserAccessCacheService,
    ):
        self.message_service = message_service
        self.message_cache_service = message_cache_service
        self.recipe_service = recipe_service
        self.recipe_cache_service = recipe_cache_service
        self.thread_service = thread_service
        self.thread_cache_service = thread_cache_service
        self.user_access_cache_service = user_access_cache_service

    async def _dispatch(
        self,
        user_access: UserAccess,
        authenticated_func: Callable[..., Any],
        unauthenticated_func: Callable[..., Any],
        *args,
        **kwargs,
    ) -> Any:
        """Dispatch to either authenticated or unauthenticated function based on user access data."""
        if user_access.is_authenticated:
            return await authenticated_func(*args, **kwargs)
        else:
            return await unauthenticated_func(*args, **kwargs)

    async def get_thread(
        self, db: AsyncSession, user_access: UserAccess, thread_id: str
    ) -> Thread | None:
        return await self._dispatch(
            user_access,
            lambda: self.thread_service.get_thread(db, thread_id),
            lambda: self.thread_cache_service.get_thread(user_access.user_id, thread_id),
        )

    async def create_thread(
        self, db: AsyncSession, user_access: UserAccess, params: CreateThreadParams, flush_db: bool = True
    ) -> Thread:
        return await self._dispatch(
            user_access,
            lambda: self.thread_service.create_thread(db, params, flush_db),
            lambda: self.thread_cache_service.create_thread(params),
        )

    async def is_thread_empty(
        self, db: AsyncSession, user_access: UserAccess, thread_id: str
    ) -> bool:
        return await self._dispatch(
            user_access,
            lambda: self.thread_service.is_thread_empty(db, thread_id),
            lambda: self.thread_cache_service.is_thread_empty(user_access.user_id, thread_id),
        )

    async def update_thread(
        self, db: AsyncSession, user_access: UserAccess, params: UpdateThreadParams, flush_db: bool = True
    ) -> Thread:
        return await self._dispatch(
            user_access,
            lambda: self.thread_service.update_thread(db, params, flush_db),
            lambda: self.thread_cache_service.update_thread(user_access.user_id, params),
        )

    async def resume_thread(
        self, db: AsyncSession, user_access: UserAccess, params: ResumeThreadParams, flush_db: bool = True
    ) -> Thread:
        return await self._dispatch(
            user_access,
            lambda: self.thread_service.resume_thread(db, params, flush_db),
            lambda: self.thread_cache_service.resume_thread(user_access.user_id, params),
        )

    # TODO: Weird that we're passing user_access and including user_id in params
    async def get_paginated_threads(
        self, db: AsyncSession, user_access: UserAccess, params: GetUserThreadsParams
    ) -> PaginatedThreads:
        return await self._dispatch(
            user_access,
            lambda: self.thread_service.get_paginated_threads(db, params),
            lambda: self.thread_cache_service.get_paginated_threads(params),
        )

    async def get_message(
        self, db: AsyncSession, user_access: UserAccess, thread_id: str, message_id: str
    ) -> Message | None:
        return await self._dispatch(
            user_access,
            lambda: self.message_service.get_message(db, message_id),
            lambda: self.message_cache_service.get_message(
                user_access.user_id, thread_id, message_id
            ),
        )

    async def create_user_message(
        self,
        db: AsyncSession,
        user_access: UserAccess,
        thread_id: str,
        message_id: str,
        content: str,
        timestamp: datetime,
        ip_address: str | None = None,
        safety_guard_result: SafetyGuardResult | None = None,
        flush_db: bool = True,
    ) -> Message:
        async def authenticated_create():
            thread = await self.thread_service.get_thread(db, thread_id)
            if thread is None:
                await self.create_thread(
                    db,
                    user_access,
                    CreateThreadParams(
                        id=thread_id,
                        user_id=user_access.user_id,
                        created_at=timestamp,
                        updated_at=timestamp,
                        is_empty=False,
                    ),
                    flush_db,
                )

            return await self.message_service.create_user_message(
                db,
                CreateUserMessageParams(
                    id=message_id,
                    user_id=user_access.user_id,
                    thread_id=thread_id,
                    text_content=content,
                    created_at=timestamp,
                    updated_at=timestamp,
                    ip_address=ip_address,
                    safety_guard_result=safety_guard_result,
                ),  # type: ignore
            )

        async def unauthenticated_create():
            message = await self.message_cache_service.create_user_message(
                user_access.user_id,
                CreateUserMessageParams(
                    id=message_id,
                    user_id=user_access.user_id,
                    thread_id=thread_id,
                    text_content=content,
                    created_at=timestamp,
                    updated_at=timestamp,
                    ip_address=ip_address,
                    safety_guard_result=safety_guard_result,
                ),  # type: ignore
            )
            await self.thread_cache_service.update_thread(
                user_access.user_id,
                UpdateThreadParams(id=thread_id, updated_at=timestamp, is_empty=False),
            )
            await self.user_access_cache_service.increment_user_message_count(
                user_access.access_token
            )
            return message

        return await self._dispatch(user_access, authenticated_create, unauthenticated_create)

    async def create_assistant_text_message(
        self,
        db: AsyncSession,
        user_access: UserAccess,
        params: CreateAssistantTextMessageParams,
        flush_db: bool = True,
    ) -> Message:
        return await self._dispatch(
            user_access,
            lambda: self.message_service.create_assistant_text_message(db, params, flush_db),
            lambda: self.message_cache_service.create_assistant_text_message(
                user_access.user_id, params=params
            ),
        )

    async def create_assistant_recipe_message(
        self,
        db: AsyncSession,
        user_access: UserAccess,
        params: CreateAssistantRecipeMessageParams,
        flush_db: bool = True,
    ) -> Message:
        return await self._dispatch(
            user_access,
            lambda: self.message_service.create_assistant_recipe_message(db, params, flush_db),
            lambda: self.message_cache_service.create_assistant_recipe_message(
                user_access.user_id, params=params
            ),
        )

    async def create_assistant_tool_message(
        self,
        db: AsyncSession,
        user_access: UserAccess,
        params: CreateAssistantToolMessageParams,
        flush_db: bool = True,
    ) -> Message:
        return await self._dispatch(
            user_access,
            lambda: self.message_service.create_assistant_tool_message(db, params, flush_db),
            lambda: self.message_cache_service.create_assistant_tool_message(
                user_access.user_id, params=params
            ),
        )

    async def update_message(
        self,
        db: AsyncSession,
        user_access: UserAccess,
        thread_id: str,
        params: UpdateMessageParams,
        flush_db: bool = True,
    ) -> Message:
        return await self._dispatch(
            user_access,
            lambda: self.message_service.update_message(db, params, flush_db),
            lambda: self.message_cache_service.update_message(
                user_access.user_id, thread_id, params=params
            ),
        )

    async def get_paginated_messages(
        self, db: AsyncSession, user_access: UserAccess, params: GetMessagesParams
    ) -> PaginatedMessages:
        return await self._dispatch(
            user_access,
            lambda: self.message_service.get_paginated_messages(db, params),
            lambda: self.message_cache_service.get_paginated_messages(params),
        )

    async def count_total_messages_sent_by_user(
        self, db: AsyncSession, user_access: UserAccess
    ) -> int:
        return await self._dispatch(
            user_access,
            lambda: self.message_service.count_total_messages_sent_by_user(
                db, user_access.user_id
            ),
            lambda: self.message_cache_service.count_total_messages_sent_by_user(
                user_access.user_id
            ),
        )

    async def create_recipe(
        self,
        db: AsyncSession,
        user_access: UserAccess,
        thread_id: str,
        recipe_id: str,
        timestamp: datetime,
        flush_db: bool = True,
    ) -> UserRecipe:
        params = CreateRecipeParams(
            id=recipe_id,
            user_id=user_access.user_id,
            thread_id=thread_id,
            created_at=timestamp,
            updated_at=timestamp,
        )

        return await self._dispatch(
            user_access,
            lambda: self.recipe_service.create_recipe(db, params, flush_db),
            lambda: self.recipe_cache_service.create_recipe(params),
        )

    async def update_recipe(
        self,
        db: AsyncSession,
        user_access: UserAccess,
        thread_id: str,
        params: UpdateRecipeParams,
        flush_db: bool = True,
    ) -> UserRecipe:
        return await self._dispatch(
            user_access,
            lambda: self.recipe_service.update_recipe(db, params, flush_db),
            lambda: self.recipe_cache_service.update_recipe(
                user_access.user_id, thread_id, params
            ),
        )

    async def update_recipe_field(
        self,
        db: AsyncSession,
        user_access: UserAccess,
        thread_id: str,
        params: UpdateRecipeFieldParams,
        flush_db: bool = True,
    ) -> UserRecipe:
        return await self._dispatch(
            user_access,
            lambda: self.recipe_service.update_recipe_field(db, params, flush_db),
            lambda: self.recipe_cache_service.update_recipe_field(
                user_access.user_id, thread_id, params
            ),
        )

    async def get_recipes_by_message_id(
        self,
        db: AsyncSession,
        user_access: UserAccess,
        thread_id: str,
        message_ids: list[str],
    ) -> list[UserRecipe]:
        async def authenticated_get():
            return await self.recipe_service.get_recipes_by_message_id(db, message_ids)

        async def unauthenticated_get():
            messages = await self.message_cache_service.get_messages_by_id(
                user_access.user_id, thread_id, message_ids
            )
            recipe_ids = [message.recipe_id for message in messages if message.recipe_id]
            if len(recipe_ids) == 0:
                return []
            return await self.recipe_cache_service.get_recipes_by_ids(
                user_access.user_id, thread_id, recipe_ids
            )

        return await self._dispatch(user_access, authenticated_get, unauthenticated_get)

    async def update_message_ai_model_or_tool_usage(
        self,
        db: AsyncSession,
        user_access: UserAccess,
        thread_id: str,
        params: UpdateMessageAIModelOrToolUsageParams,
        flush_db: bool = True,
    ) -> Message:
        async def authenticated_update():
            return await self.message_service.update_message_tool_usage(db, params, flush_db)

        async def unauthenticated_update():
            current_message = await self.message_cache_service.get_message(
                user_access.user_id, thread_id, params.id
            )
            if current_message is None:
                raise ValueError(f"Message {params.id} not found")

            updated_message_params = UpdateMessageParams(
                id=params.id,
                updated_at=params.updated_at,
                model_name=params.model_name,
                input_tokens=(current_message.input_tokens or 0) + (params.input_tokens or 0) if params.input_tokens is not None else None,
                output_tokens=(current_message.output_tokens or 0) + (params.output_tokens or 0) if params.output_tokens is not None else None,
                tool_name=params.tool_name,
                tool_input=params.tool_input,
                tool_output=params.tool_output,
                is_recipe_generation_started=params.is_recipe_generation_started,
                is_recipe_generation_completed=params.is_recipe_generation_completed,
                text_content=(current_message.text_content or "") + params.text_chunk if params.text_chunk is not None else None,
            )
            
            return await self.message_cache_service.update_message(
                user_access.user_id, thread_id, params=updated_message_params
            )

        return await self._dispatch(user_access, authenticated_update, unauthenticated_update)
    
    async def update_recipe_field_by_message_id(
        self,
        db: AsyncSession,
        user_access: UserAccess,
        thread_id: str,
        message_id: str,
        field: RecipeField,
        timestamp: datetime,
        flush_db: bool = True,
    ) -> UserRecipe:
        
        async def authenticated_update():
            return await self.recipe_service.update_recipe_field_by_message_id(db, message_id, field, timestamp, flush_db)

        async def unauthenticated_update():
            current_message = await self.message_cache_service.get_message(
                user_access.user_id, thread_id, message_id
            )
            if current_message is None:
                raise ValueError(f"Message {message_id} not found")
            
            if current_message.recipe_id is None:
                raise ValueError(f"Message {message_id} has no recipe id")
            
            return await self.recipe_cache_service.update_recipe_field(
                user_access.user_id, thread_id, UpdateRecipeFieldParams(
                    id=current_message.recipe_id,
                    updated_at=timestamp,
                    field=field,
                )
            )

        return await self._dispatch(user_access, authenticated_update, unauthenticated_update)
    
    async def update_recipe_by_message_id(
        self,
        db: AsyncSession,
        user_access: UserAccess,
        thread_id: str,
        message_id: str,
        recipe: Recipe,
        timestamp: datetime,
        flush_db: bool = True,
    ) -> UserRecipe:
        async def authenticated_update():
            return await self.recipe_service.update_recipe_by_message_id(db, message_id, recipe, timestamp, flush_db)

        async def unauthenticated_update():
            current_message = await self.message_cache_service.get_message(
                user_access.user_id, thread_id, message_id
            )
            if current_message is None:
                raise ValueError(f"Message {message_id} not found")
            
            if current_message.recipe_id is None:
                raise ValueError(f"Message {message_id} has no recipe id")
            
            return await self.recipe_cache_service.update_recipe(
                user_access.user_id, thread_id, UpdateRecipeParams(
                    id=current_message.recipe_id,
                    updated_at=timestamp,
                    **recipe.model_dump(),
                )
            )

        return await self._dispatch(user_access, authenticated_update, unauthenticated_update)
