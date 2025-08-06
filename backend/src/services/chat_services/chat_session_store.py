from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from services.data_services.message_cache_service import MessageCacheService
from services.data_services.message_service import MessageService
from services.data_services.recipe_cache_service import RecipeCacheService
from services.data_services.recipe_service import RecipeService
from services.data_services.thread_cache_service import ThreadCacheService
from services.data_services.thread_service import ThreadService
from services.data_services.user_access_cache_service import UserAccessCacheService

from schemas.message_content_type import MessageContentType
from schemas.message_role import MessageRole
from schemas.messages import (
    CountMessagesParams,
    CreateAssistantRecipeMessageParams,
    CreateAssistantTextMessageParams,
    CreateAssistantToolMessageParams,
    CreateUserMessageParams,
    GetMessagesParams,
    Message,
    PaginatedMessages,
    UpdateMessageParams,
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

from utils.logger import Logger

logger = Logger("chat_session_store")


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

    async def get_user_thread(
        self, db: AsyncSession, user_access: UserAccess, thread_id: str
    ) -> Thread | None:
        cached_thread = await self.thread_cache_service.get_thread(user_access.user_id, thread_id)
        if cached_thread is not None:
            return cached_thread

        thread = await self.thread_service.get_thread(db, thread_id)
        if thread is not None:
            await self.thread_cache_service.set_thread(thread)

        return thread

    async def create_thread(self, params: CreateThreadParams) -> Thread:
        cached_thread = await self.thread_cache_service.create_thread(params)
        return cached_thread

    async def is_thread_empty(
        self, db: AsyncSession, user_access: UserAccess, thread_id: str
    ) -> bool:
        cached_thread = await self.thread_cache_service.get_thread(user_access.user_id, thread_id)
        if cached_thread is not None:
            return bool(cached_thread.is_empty)

        thread = await self.thread_service.get_thread(db, thread_id)
        if thread is not None:
            await self.thread_cache_service.set_thread(thread)
            return bool(thread.is_empty)

        return False

    async def update_thread(
        self, db: AsyncSession, user_access: UserAccess, params: UpdateThreadParams
    ) -> Thread:
        cached_thread = await self.thread_cache_service.update_thread(user_access.user_id, params)
        if cached_thread is not None:
            result = await self.thread_cache_service.update_thread(user_access.user_id, params)
            return result

        thread = await self.thread_service.update_thread(db, params)
        if thread is None:
            logger.error(f"Thread {params.id} not found for user {user_access.user_id}")
            raise ValueError(f"Thread {params.id} not found for user {user_access.user_id}")

        updated_thread = await self.thread_cache_service.update_thread(user_access.user_id, params)
        await self.thread_cache_service.set_thread(updated_thread)
        return updated_thread

    async def resume_thread(
        self, db: AsyncSession, user_access: UserAccess, params: ResumeThreadParams
    ) -> Thread:
        cached_thread = await self.thread_cache_service.resume_thread(user_access.user_id, params)
        if cached_thread is not None:
            result = await self.thread_cache_service.resume_thread(user_access.user_id, params)
            return result

        thread = await self.thread_service.resume_thread(db, params)
        if thread is None:
            logger.error(f"Thread {params.id} not found for user {user_access.user_id}")
            raise ValueError(f"Thread {params.id} not found for user {user_access.user_id}")

        resumed_thread = await self.thread_cache_service.resume_thread(user_access.user_id, params)
        await self.thread_cache_service.set_thread(resumed_thread)
        return resumed_thread

    async def get_paginated_threads(
        self, db: AsyncSession, params: GetUserThreadsParams
    ) -> PaginatedThreads:
        paginated_threads = await self.thread_service.get_paginated_threads(db, params)
        if len(paginated_threads.threads) > 0:
            for thread in paginated_threads.threads:
                await self.thread_cache_service.set_thread(thread)

        return paginated_threads

    async def get_message(
        self, db: AsyncSession, user_access: UserAccess, thread_id: str, message_id: str
    ) -> Message | None:
        cached_message = await self.message_cache_service.get_message(
            user_access.user_id, thread_id, message_id
        )
        if cached_message is not None:
            return cached_message

        message = await self.message_service.get_message(db, message_id)
        if message is not None:
            await self.message_cache_service.set_message(user_access.user_id, message)
        return message

    async def get_messages_by_ids(
        self, db: AsyncSession, user_access: UserAccess, thread_id: str, message_ids: list[str]
    ) -> list[Message]:
        cached_messages = await self.message_cache_service.get_messages_by_ids(
            user_access.user_id, thread_id, message_ids
        )
        if len(cached_messages) > 0:
            return list(cached_messages)

        messages = await self.message_service.get_messages_by_ids(db, message_ids)
        if len(messages) > 0:
            for message in messages:
                await self.message_cache_service.set_message(user_access.user_id, message)

        return list(messages)

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
    ) -> Message:
        cached_message = await self.message_cache_service.create_user_message(
            user_access.user_id,
            CreateUserMessageParams(
                id=message_id,
                role=MessageRole.user,
                content_type=MessageContentType.text,
                user_id=user_access.user_id,
                thread_id=thread_id,
                text_content=content,
                created_at=timestamp,
                updated_at=timestamp,
                ip_address=ip_address,
                safety_guard_result=safety_guard_result,
            ),
        )

        thread = await self.get_user_thread(db, user_access, thread_id)
        if thread is None:
            thread = await self.create_thread(
                CreateThreadParams(
                    id=thread_id,
                    user_id=user_access.user_id,
                    created_at=timestamp,
                    updated_at=timestamp,
                    is_empty=False,
                )
            )
        else:
            await self.thread_cache_service.update_thread(
                user_access.user_id,
                UpdateThreadParams(id=thread_id, updated_at=timestamp, is_empty=False),
            )

        await self.user_access_cache_service.increment_user_message_count(user_access.access_token)
        return cached_message

    async def create_assistant_text_message(
        self,
        db: AsyncSession,
        user_access: UserAccess,
        params: CreateAssistantTextMessageParams,
    ) -> Message:
        cached_message = await self.message_cache_service.create_assistant_text_message(
            user_access.user_id, params=params
        )
        return cached_message

    async def create_assistant_recipe_message(
        self,
        db: AsyncSession,
        user_access: UserAccess,
        params: CreateAssistantRecipeMessageParams,
    ) -> Message:
        cached_message = await self.message_cache_service.create_assistant_recipe_message(
            user_access.user_id, params=params
        )
        return cached_message

    async def create_assistant_tool_message(
        self,
        db: AsyncSession,
        user_access: UserAccess,
        params: CreateAssistantToolMessageParams,
    ) -> Message:
        cached_message = await self.message_cache_service.create_assistant_tool_message(
            user_access.user_id, params=params
        )
        return cached_message

    async def update_message(
        self,
        db: AsyncSession,
        user_access: UserAccess,
        thread_id: str,
        params: UpdateMessageParams,
    ) -> Message:
        cached_message = await self.message_cache_service.get_message(
            user_access.user_id, thread_id, params.id
        )
        if cached_message is not None:
            result = await self.message_cache_service.update_message(
                user_access.user_id, thread_id, params=params
            )
            return result

        message = await self.message_service.update_message(db, params)
        if message is None:
            logger.error(f"Message {params.id} not found for user {user_access.user_id}")
            raise ValueError(f"Message {params.id} not found for user {user_access.user_id}")

        updated_message = await self.message_cache_service.update_message(
            user_access.user_id, thread_id, params=params
        )
        await self.message_cache_service.set_message(user_access.user_id, updated_message)
        return updated_message

    async def get_paginated_messages(
        self, db: AsyncSession, user_access: UserAccess, params: GetMessagesParams
    ) -> PaginatedMessages:
        paginated_messages = await self.message_service.get_paginated_messages(db, params)
        if len(paginated_messages.messages) > 0:
            for message in paginated_messages.messages:
                await self.message_cache_service.set_message(user_access.user_id, message)

        return paginated_messages

    async def count_total_messages_sent_by_user(
        self, db: AsyncSession, user_access: UserAccess
    ) -> int:
        count = await self.message_cache_service.count_total_messages_sent_by_user(
            user_access.user_id
        )
        if count != 0:
            return int(count)

        count = await self.message_service.count_messages(
            db, CountMessagesParams(user_id=user_access.user_id, role=MessageRole.user)
        )
        return int(count)

    async def create_recipe(
        self,
        db: AsyncSession,
        user_access: UserAccess,
        thread_id: str,
        recipe_id: str,
        timestamp: datetime,
    ) -> UserRecipe:
        params = CreateRecipeParams(
            id=recipe_id,
            user_id=user_access.user_id,
            thread_id=thread_id,
            created_at=timestamp,
            updated_at=timestamp,
        )
        cached_recipe = await self.recipe_cache_service.create_recipe(params)
        return cached_recipe

    async def update_recipe(
        self,
        db: AsyncSession,
        user_access: UserAccess,
        thread_id: str,
        params: UpdateRecipeParams,
    ) -> UserRecipe:
        cached_recipe = await self.recipe_cache_service.get_recipe(
            user_access.user_id, thread_id, params.id
        )
        if cached_recipe is not None:
            result = await self.recipe_cache_service.update_recipe(
                user_access.user_id, thread_id, params
            )
            return result

        recipe = await self.recipe_service.update_recipe(db, params)
        if recipe is None:
            logger.error(f"Recipe {params.id} not found for user {user_access.user_id}")
            raise ValueError(f"Recipe {params.id} not found for user {user_access.user_id}")

        updated_recipe = await self.recipe_cache_service.update_recipe(
            user_access.user_id, thread_id, params
        )
        await self.recipe_cache_service.set_recipe(updated_recipe)

        return updated_recipe

    async def update_recipe_field(
        self,
        db: AsyncSession,
        user_access: UserAccess,
        thread_id: str,
        params: UpdateRecipeFieldParams,
    ) -> UserRecipe:
        cached_recipe = await self.recipe_cache_service.get_recipe(
            user_access.user_id, thread_id, params.id
        )
        if cached_recipe is not None:
            result = await self.recipe_cache_service.update_recipe_field(
                user_access.user_id, thread_id, params
            )
            return result

        recipe = await self.recipe_service.update_recipe_field(db, params)
        if recipe is None:
            logger.error(f"Recipe {params.id} not found for user {user_access.user_id}")
            raise ValueError(f"Recipe {params.id} not found for user {user_access.user_id}")

        updated_recipe = await self.recipe_cache_service.update_recipe_field(
            user_access.user_id, thread_id, params
        )
        await self.recipe_cache_service.set_recipe(updated_recipe)
        return updated_recipe
    
    async def get_user_recipes(self, db: AsyncSession, user_access: UserAccess) -> list[UserRecipe]:
        cached_recipes = await self.recipe_cache_service.get_user_recipes(user_access.user_id)
        if len(cached_recipes) > 0:
            return list(cached_recipes)
        
        recipes = await self.recipe_service.get_user_recipes(db, user_access.user_id)
        if len(recipes) > 0:
            for recipe in recipes:
                await self.recipe_cache_service.set_recipe(recipe)
        
        return list(recipes)

    async def get_recipes_by_message_ids(
        self,
        db: AsyncSession,
        user_access: UserAccess,
        thread_id: str,
        message_ids: list[str],
    ) -> list[UserRecipe]:
        messages = await self.get_messages_by_ids(db, user_access, thread_id, message_ids)
        recipe_ids = [message.recipe_id for message in messages if message.recipe_id]
        if len(recipe_ids) == 0:
            return []

        cached_recipes = await self.recipe_cache_service.get_recipes_by_ids(
            user_access.user_id, thread_id, recipe_ids
        )
        if len(cached_recipes) > 0:
            return list(cached_recipes)

        recipes = await self.recipe_service.get_recipes_by_message_ids(db, message_ids)
        if len(recipes) > 0:
            for recipe in recipes:
                await self.recipe_cache_service.set_recipe(recipe)

        return list(recipes)

    async def update_message_recipe_field(
        self,
        db: AsyncSession,
        user_access: UserAccess,
        thread_id: str,
        message_id: str,
        field: RecipeField,
        timestamp: datetime,
    ) -> UserRecipe:
        message = await self.get_message(db, user_access, thread_id, message_id)
        if message is None:
            logger.error(f"Message {message_id} not found for user {user_access.user_id}")
            raise ValueError(f"Message {message_id} not found")

        if message.recipe_id is None:
            logger.error(f"Message {message_id} has no recipe id for user {user_access.user_id}")
            raise ValueError(f"Message {message_id} has no recipe id")

        params = UpdateRecipeFieldParams(
            id=message.recipe_id,
            updated_at=timestamp,
            field=field,
        )

        cached_recipe = await self.recipe_cache_service.get_recipe(
            user_access.user_id, thread_id, message.recipe_id
        )
        if cached_recipe is not None:
            result = await self.recipe_cache_service.update_recipe_field(
                user_access.user_id, thread_id, params
            )
            return result

        recipe = await self.recipe_service.update_recipe_field(db, params)
        await self.recipe_cache_service.set_recipe(recipe)
        return recipe

    async def update_message_recipe(
        self,
        db: AsyncSession,
        user_access: UserAccess,
        thread_id: str,
        message_id: str,
        recipe: Recipe,
        timestamp: datetime,
    ) -> UserRecipe:
        message = await self.get_message(db, user_access, thread_id, message_id)
        if message is None:
            logger.error(f"Message {message_id} not found for user {user_access.user_id}")
            raise ValueError(f"Message {message_id} not found")

        if message.recipe_id is None:
            logger.error(f"Message {message_id} has no recipe id for user {user_access.user_id}")
            raise ValueError(f"Message {message_id} has no recipe id")

        params = UpdateRecipeParams(
            id=message.recipe_id,
            updated_at=timestamp,
            **recipe.model_dump(),
        )
        
        logger.warning(f"Updated message recipe_id: {message.recipe_id}")

        cached_recipe = await self.recipe_cache_service.get_recipe(
            user_access.user_id, thread_id, message.recipe_id
        )
        if cached_recipe is not None:
            result = await self.recipe_cache_service.update_recipe(
                user_access.user_id, thread_id, params
            )
            return result

        recipe = await self.recipe_service.update_recipe(db, params)
        await self.recipe_cache_service.set_recipe(recipe)
        
        logger.warning(f"Updated message recipe_id: {message.recipe_id}")
        
        return recipe
