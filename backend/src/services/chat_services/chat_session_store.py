from datetime import datetime
from typing import Callable, Any, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from schemas.messages import (
    CreateAssistantToolMessageParams,
    Message,
    CreateUserMessageParams,
    CreateAssistantTextMessageParams,
    CreateAssistantRecipeMessageParams,
    UpdateMessageParams,
    GetMessagesParams,
    PaginatedMessages,
)
from schemas.recipes import (
    UserRecipe,
    CreateRecipeParams,
    UpdateRecipeParams,
    UpdateRecipeFieldParams,
)
from schemas.threads import (
    CreateThreadParams, 
    Thread, 
    UpdateThreadParams,
    PaginatedThreads,
    GetUserThreadsParams,
)
from schemas.user_access import UserAccessData

from services.data_services.message_service import MessageService
from services.data_services.message_cache_service import MessageCacheService
from services.data_services.recipe_service import RecipeService
from services.data_services.recipe_cache_service import RecipeCacheService
from services.data_services.thread_service import ThreadService
from services.data_services.thread_cache_service import ThreadCacheService
from services.data_services.user_access_cache_service import UserAccessCacheService

from utils.logger import Logger 

logger = Logger("chat_session_store")

T = TypeVar('T')


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
        user_access_data: UserAccessData,
        authenticated_func: Callable[..., Any],
        unauthenticated_func: Callable[..., Any],
        *args,
        **kwargs
    ) -> T:
        """Dispatch to either authenticated or unauthenticated function based on user access data."""
        if user_access_data.is_authenticated:
            return await authenticated_func(*args, **kwargs)
        else:
            return await unauthenticated_func(*args, **kwargs)
        

    async def get_thread(self, db: AsyncSession, user_access_data: UserAccessData, thread_id: str) -> Thread | None:
        return await self._dispatch(
            user_access_data,
            lambda: self.thread_service.get_thread(db, thread_id),
            lambda: self.thread_cache_service.get_thread(user_access_data.user_id, thread_id),
        )
    
    
    async def create_thread(self, db: AsyncSession, user_access_data: UserAccessData, params: CreateThreadParams) -> Thread:
        return await self._dispatch(
            user_access_data,
            lambda: self.thread_service.create_thread(db, params),
            lambda: self.thread_cache_service.create_thread(params)
        )
    
    
    async def is_thread_empty(self, db: AsyncSession, user_access_data: UserAccessData, thread_id: str) -> bool:
        return await self._dispatch(
            user_access_data,
            lambda: self.thread_service.is_thread_empty(db, thread_id),
            lambda: self.thread_cache_service.is_thread_empty(user_access_data.user_id, thread_id)
        )
    
    
    async def update_thread(self, db: AsyncSession, user_access_data: UserAccessData, params: UpdateThreadParams) -> Thread:
        return await self._dispatch(
            user_access_data,
            lambda: self.thread_service.update_thread(db, params),
            lambda: self.thread_cache_service.update_thread(user_access_data.user_id, params)
        )
        
    
    # TODO: Weird that we're passing user_access_data and including user_id in params
    async def get_paginated_threads(self, db: AsyncSession, user_access_data: UserAccessData, params: GetUserThreadsParams) -> PaginatedThreads:
        return await self._dispatch(
            user_access_data,
            lambda: self.thread_service.get_paginated_threads(db, params),
            lambda: self.thread_cache_service.get_paginated_threads(params)
        )

    
    async def get_message(self, db: AsyncSession, user_access_data: UserAccessData, thread_id: str, message_id: str) -> Message | None:
        return await self._dispatch(
            user_access_data,
            lambda: self.message_service.get_message(db, message_id),
            lambda: self.message_cache_service.get_message(user_access_data.user_id, thread_id, message_id)
        )
    
    
    async def create_user_message(self, db: AsyncSession, user_access_data: UserAccessData, thread_id: str, message_id: str, content: str, timestamp: datetime) -> Message:
        async def authenticated_create():
            thread = await self.thread_service.get_thread(db, thread_id)
            if thread is None:
                await self.create_thread(db, user_access_data, CreateThreadParams(
                    id=thread_id,
                    user_id=user_access_data.user_id,
                    created_at=timestamp,
                    updated_at=timestamp,
                    is_empty=False,
                ))
                
            return await self.message_service.create_user_message(db, CreateUserMessageParams(
                id=message_id,
                user_id=user_access_data.user_id,
                thread_id=thread_id,
                text_content=content,
                created_at=timestamp,
                updated_at=timestamp,
            ))
        
        async def unauthenticated_create():
            message = await self.message_cache_service.create_user_message(user_access_data.user_id, CreateUserMessageParams(
                id=message_id,
                user_id=user_access_data.user_id,
                thread_id=thread_id,
                text_content=content,
                created_at=timestamp,
                updated_at=timestamp,
            ))
            await self.thread_cache_service.update_thread(user_access_data.user_id, UpdateThreadParams(id=thread_id, updated_at=timestamp, is_empty=False))
            await self.user_access_cache_service.increment_user_message_count(user_access_data.access_token)
            return message
        
        return await self._dispatch(user_access_data, authenticated_create, unauthenticated_create)

    
    async def create_assistant_text_message(self, db: AsyncSession, user_access_data: UserAccessData, params: CreateAssistantTextMessageParams) -> Message:
        return await self._dispatch(
            user_access_data,
            lambda: self.message_service.create_assistant_text_message(db, params),
            lambda: self.message_cache_service.create_assistant_text_message(user_access_data.user_id, params=params)
        )
    
    
    async def create_assistant_recipe_message(self, db: AsyncSession, user_access_data: UserAccessData, params: CreateAssistantRecipeMessageParams) -> Message:    
        return await self._dispatch(
            user_access_data,
            lambda: self.message_service.create_assistant_recipe_message(db, params),
            lambda: self.message_cache_service.create_assistant_recipe_message(user_access_data.user_id, params=params)
        )
        
    async def create_assistant_tool_message(self, db: AsyncSession, user_access_data: UserAccessData, params: CreateAssistantToolMessageParams) -> Message:
        return await self._dispatch(
            user_access_data,
            lambda: self.message_service.create_assistant_tool_message(db, params),
            lambda: self.message_cache_service.create_assistant_tool_message(user_access_data.user_id, params=params)
        )
    

    async def update_message(self, db: AsyncSession, user_access_data: UserAccessData, thread_id: str, params: UpdateMessageParams) -> Message:
        return await self._dispatch(
            user_access_data,
            lambda: self.message_service.update_message(db, params),
            lambda: self.message_cache_service.update_message(user_access_data.user_id, thread_id, params=params)
        )
    
    
    async def get_paginated_messages(self, db: AsyncSession, user_access_data: UserAccessData, params: GetMessagesParams) -> PaginatedMessages:
        return await self._dispatch(
            user_access_data,
            lambda: self.message_service.get_paginated_messages(db, params),
            lambda: self.message_cache_service.get_paginated_messages(params)
        )


    async def count_total_messages_sent_by_user(self, db: AsyncSession, user_access_data: UserAccessData) -> int:
        return await self._dispatch(
            user_access_data,
            lambda: self.message_service.count_total_messages_sent_by_user(db, user_access_data.user_id),
            lambda: self.message_cache_service.count_total_messages_sent_by_user(user_access_data.user_id)
        )

        
    async def create_recipe(self, db: AsyncSession, user_access_data: UserAccessData, thread_id: str, recipe_id: str, timestamp: datetime) -> UserRecipe:
        params = CreateRecipeParams(
            id=recipe_id,
            user_id=user_access_data.user_id,
            thread_id=thread_id,
            created_at=timestamp,
            updated_at=timestamp,
        )
        
        return await self._dispatch(
            user_access_data,
            lambda: self.recipe_service.create_recipe(db, params),
            lambda: self.recipe_cache_service.create_recipe(params)
        )

        
    async def update_recipe(self, db: AsyncSession, user_access_data: UserAccessData, thread_id: str, params: UpdateRecipeParams) -> UserRecipe | None:
        return await self._dispatch(
            user_access_data,
            lambda: self.recipe_service.update_recipe(db, params),
            lambda: self.recipe_cache_service.update_recipe(user_access_data.user_id, thread_id, params)
        )

    
    async def update_recipe_field(self, db: AsyncSession, user_access_data: UserAccessData, thread_id: str, params: UpdateRecipeFieldParams) -> UserRecipe:
        return await self._dispatch(
            user_access_data,
            lambda: self.recipe_service.update_recipe_field(db, params),
            lambda: self.recipe_cache_service.update_recipe_field(user_access_data.user_id, thread_id, params)
        )

        
    async def get_recipes_by_message_id(self, db: AsyncSession, user_access_data: UserAccessData, thread_id: str, message_ids: list[str]) -> list[UserRecipe]:
        async def authenticated_get():
            return await self.recipe_service.get_recipes_by_message_id(db, message_ids)
        
        async def unauthenticated_get():
            messages = await self.message_cache_service.get_messages_by_id(user_access_data.user_id, thread_id, message_ids)
            recipe_ids = [message.recipe_id for message in messages if message.recipe_id]
            if len(recipe_ids) == 0:
                return []
            return await self.recipe_cache_service.get_recipes_by_ids(user_access_data.user_id, thread_id, recipe_ids)
        
        return await self._dispatch(user_access_data, authenticated_get, unauthenticated_get)