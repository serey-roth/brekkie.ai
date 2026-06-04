from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from services.data_services.message_service import MessageService
from services.data_services.recipe_service import RecipeService
from services.data_services.thread_service import ThreadService

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
    UserRecipe,
)
from schemas.chat_session_errors import OverMessageLimitError
from schemas.safety_guards import SafetyGuardResult
from schemas.threads import (
    CreateThreadParams,
    GetUserThreadsParams,
    PaginatedThreads,
    ResumeThreadParams,
    Thread,
    UpdateThreadParams,
)

from utils.logger import Logger

logger = Logger("chat_session_store")


class ChatSessionStore:
    def __init__(
        self,
        message_service: MessageService,
        recipe_service: RecipeService,
        thread_service: ThreadService,
    ):
        self.message_service = message_service
        self.recipe_service = recipe_service
        self.thread_service = thread_service

    async def get_user_thread(self, db: AsyncSession, thread_id: str) -> Thread | None:
        return await self.thread_service.get_thread(db, thread_id)

    async def create_thread(self, db: AsyncSession, params: CreateThreadParams) -> Thread:
        return await self.thread_service.create_thread(db, params)

    async def is_thread_empty(self, db: AsyncSession, thread_id: str) -> bool:
        return await self.thread_service.is_thread_empty(db, thread_id)

    async def update_thread(self, db: AsyncSession, params: UpdateThreadParams) -> Thread:
        return await self.thread_service.update_thread(db, params)

    async def resume_thread(self, db: AsyncSession, params: ResumeThreadParams) -> Thread | None:
        try:
            return await self.thread_service.resume_thread(db, params)
        except Exception:
            return None

    async def get_paginated_threads(
        self, db: AsyncSession, params: GetUserThreadsParams
    ) -> PaginatedThreads:
        return await self.thread_service.get_paginated_threads(db, params)

    async def get_message(self, db: AsyncSession, message_id: str) -> Message | None:
        return await self.message_service.get_message(db, message_id)

    async def get_messages_by_ids(
        self, db: AsyncSession, message_ids: list[str]
    ) -> list[Message]:
        return await self.message_service.get_messages_by_ids(db, message_ids)

    async def create_user_message(
        self,
        db: AsyncSession,
        user_id: str,
        thread_id: str,
        message_id: str,
        content: str,
        timestamp: datetime,
        safety_guard_result: SafetyGuardResult | None = None,
    ) -> Message:
        return await self.message_service.create_user_message(
            db,
            CreateUserMessageParams(
                id=message_id,
                role=MessageRole.user,
                content_type=MessageContentType.text,
                user_id=user_id,
                thread_id=thread_id,
                text_content=content,
                created_at=timestamp,
                updated_at=timestamp,
                safety_guard_result=safety_guard_result,
            ),
        )

    async def create_assistant_text_message(
        self, db: AsyncSession, params: CreateAssistantTextMessageParams
    ) -> Message:
        return await self.message_service.create_assistant_text_message(db, params)

    async def create_assistant_recipe_message(
        self, db: AsyncSession, params: CreateAssistantRecipeMessageParams
    ) -> Message:
        return await self.message_service.create_assistant_recipe_message(db, params)

    async def create_assistant_tool_message(
        self, db: AsyncSession, params: CreateAssistantToolMessageParams
    ) -> Message:
        return await self.message_service.create_assistant_tool_message(db, params)

    async def update_message(self, db: AsyncSession, params: UpdateMessageParams) -> Message:
        return await self.message_service.update_message(db, params)

    async def get_paginated_messages(
        self, db: AsyncSession, params: GetMessagesParams
    ) -> PaginatedMessages:
        return await self.message_service.get_paginated_messages(db, params)

    async def count_total_messages_sent_by_user(self, db: AsyncSession, user_id: str) -> int:
        return await self.message_service.count_messages(
            db, CountMessagesParams(user_id=user_id, role=MessageRole.user)
        )

    async def check_message_limit(
        self, db: AsyncSession, user_id: str, message_limit: int | None
    ) -> None:
        if message_limit is None:
            return
        count = await self.count_total_messages_sent_by_user(db, user_id)
        if count >= message_limit:
            raise OverMessageLimitError(message_limit)

    async def create_recipe(
        self,
        db: AsyncSession,
        user_id: str,
        thread_id: str,
        recipe_id: str,
        timestamp: datetime,
    ) -> UserRecipe:
        return await self.recipe_service.create_recipe(
            db,
            CreateRecipeParams(
                id=recipe_id,
                user_id=user_id,
                thread_id=thread_id,
                created_at=timestamp,
                updated_at=timestamp,
            ),
        )

    async def get_user_recipes(self, db: AsyncSession, user_id: str) -> list[UserRecipe]:
        return await self.recipe_service.get_user_recipes(db, user_id)

    async def get_recipes_by_message_ids(
        self, db: AsyncSession, message_ids: list[str]
    ) -> list[UserRecipe]:
        return await self.recipe_service.get_recipes_by_message_ids(db, message_ids)

    async def update_message_recipe_field(
        self, db: AsyncSession, message_id: str, field: RecipeField, timestamp: datetime
    ) -> UserRecipe:
        return await self.recipe_service.update_message_recipe_field(
            db, message_id, field, timestamp
        )

    async def update_message_recipe(
        self, db: AsyncSession, message_id: str, recipe: Recipe, timestamp: datetime
    ) -> UserRecipe:
        return await self.recipe_service.update_message_recipe(db, message_id, recipe, timestamp)
