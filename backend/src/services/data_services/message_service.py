from datetime import datetime
from typing import cast

from database.schema import DBMessage
from repositories.message_repository import MessageRepository
from schemas.message_content_type import MessageContentType
from schemas.message_role import MessageRole
from schemas.messages import (
    CreateAssistantRecipeMessageParams,
    CreateAssistantTextMessageParams,
    CreateAssistantToolMessageParams,
    CreateMessageParams,
    CreateUserMessageParams,
    GetDBMessagesParams,
    GetMessagesParams,
    Message,
    MessageResponse,
    PaginatedMessages,
    UpdateMessageParams,
    UpdateMessageAIModelOrToolUsageParams,
)
from schemas.safety_guards import SafetyGuardResult
from sqlalchemy.ext.asyncio import AsyncSession
from utils.date_utils import to_utc_isostring
from utils.logger import Logger

logger = Logger("message_service")


class MessageService:
    def __init__(self, repository: MessageRepository):
        self.repository = repository

    def _to_message_dto(self, message: DBMessage) -> Message:
        # TODO: Is there a simpler way to map SqlAlchemy models to DTOs?
        return Message(
            id=str(message.id),
            user_id=str(message.user_id),
            thread_id=str(message.thread_id),
            role=MessageRole(message.role),
            content_type=MessageContentType(message.content_type),
            text_content=str(message.text_content) if message.text_content is not None else None,
            parent_id=str(message.parent_id) if message.parent_id is not None else None,
            recipe_id=str(message.recipe_id) if message.recipe_id is not None else None,
            created_at=to_utc_isostring(cast(datetime, message.created_at)),
            updated_at=to_utc_isostring(cast(datetime, message.updated_at)),
            model_name=str(message.model_name) if message.model_name is not None else None,
            input_tokens=cast(int, message.input_tokens)
            if message.input_tokens is not None
            else None,
            output_tokens=cast(int, message.output_tokens)
            if message.output_tokens is not None
            else None,
            tool_name=str(message.tool_name) if message.tool_name is not None else None,
            tool_input=cast(dict, message.tool_input) if message.tool_input is not None else None,
            tool_output=cast(dict, message.tool_output)
            if message.tool_output is not None
            else None,
            is_recipe_generation_started=cast(bool, message.is_recipe_generation_started),
            is_recipe_generation_completed=cast(bool, message.is_recipe_generation_completed),
            ip_address=str(message.ip_address) if message.ip_address is not None else None,
            safety_guard_result=SafetyGuardResult.model_validate(message.safety_guard_result)
            if message.safety_guard_result is not None
            else None,
        )

    async def create_message(self, db: AsyncSession, params: CreateMessageParams, flush_db: bool = True) -> Message:
        logger.debug(f"Creating message with {params}")
        message = await self.repository.create_message(db, params, flush_db)
        return self._to_message_dto(message)

    async def create_user_message(
        self, db: AsyncSession, params: CreateUserMessageParams, flush_db: bool = True
    ) -> Message:
        logger.debug(f"Creating user message for thread {params.thread_id} with {params}")
        return await self.create_message(db, params, flush_db)

    async def create_assistant_text_message(
        self, db: AsyncSession, params: CreateAssistantTextMessageParams, flush_db: bool = True
    ) -> Message:
        logger.debug(f"Creating assistant text message for thread {params.thread_id} with {params}")
        return await self.create_message(db, params, flush_db)

    async def create_assistant_recipe_message(
        self, db: AsyncSession, params: CreateAssistantRecipeMessageParams, flush_db: bool = True
    ) -> Message:
        logger.debug(
            f"Creating assistant recipe message for thread {params.thread_id} with {params}"
        )
        return await self.create_message(db, params, flush_db)

    async def create_assistant_tool_message(
        self, db: AsyncSession, params: CreateAssistantToolMessageParams, flush_db: bool = True
    ) -> Message:
        logger.debug(f"Creating assistant tool message for thread {params.thread_id} with {params}")
        return await self.create_message(db, params, flush_db)

    async def update_message(self, db: AsyncSession, params: UpdateMessageParams, flush_db: bool = True) -> Message:
        logger.debug(f"Updating message {params.id} with {params}")
        message = await self.repository.update_message(db, params, flush_db)
        return self._to_message_dto(message)

    async def get_message(self, db: AsyncSession, message_id: str) -> Message | None:
        logger.debug(f"Getting message {message_id}")
        message = await self.repository.get_message(db, message_id)
        return self._to_message_dto(message) if message else None

    async def get_paginated_messages(
        self, db: AsyncSession, params: GetMessagesParams
    ) -> PaginatedMessages:
        logger.debug(
            f"Getting paginated messages for thread {params.thread_id} with params {params}"
        )

        if params.limit > 100 or params.limit < 1:
            raise ValueError("Limit must be between 1 and 100")

        paginated_limit = params.limit + 1

        sort_by = params.sort_by
        new_params = GetDBMessagesParams(
            user_id=params.user_id,
            thread_id=params.thread_id,
            limit=paginated_limit,
            from_timestamp=params.from_timestamp,
            sort_by=sort_by,
            sort_order=params.sort_order,
        )

        db_messages = await self.repository.get_messages(db, new_params)

        has_more = len(db_messages) > params.limit
        messages_to_return = db_messages[: params.limit]

        next_timestamp = None
        if has_more and len(messages_to_return) > 0:
            next_timestamp = to_utc_isostring(
                cast(datetime, messages_to_return[-1].created_at)
                if sort_by == "created_at"
                else cast(datetime, messages_to_return[-1].updated_at)
            )

        message_responses = [
            MessageResponse.from_message(self._to_message_dto(message))
            for message in messages_to_return
        ]
        return PaginatedMessages(
            messages=message_responses,
            total_count=await self.repository.count_thread_messages(db, params.thread_id),
            has_more=has_more,
            next_timestamp=next_timestamp,
        )

    async def count_total_messages_sent_by_user(self, db: AsyncSession, user_id: str) -> int:
        logger.debug(f"Counting total messages sent by user {user_id}")
        return await self.repository.count_total_messages_sent_by_user(db, user_id)

    async def count_thread_messages(self, db: AsyncSession, thread_id: str) -> int:
        logger.debug(f"Counting thread messages for thread {thread_id}")
        return await self.repository.count_thread_messages(db, thread_id)

    async def create_messages(
        self, db: AsyncSession, params: list[CreateMessageParams], flush_db: bool = True
    ) -> list[Message]:
        logger.debug(f"Creating messages with {params}")
        db_messages = await self.repository.create_messages(db, params, flush_db)
        return [self._to_message_dto(message) for message in db_messages]

    async def update_message_tool_usage(self, db: AsyncSession, params: UpdateMessageAIModelOrToolUsageParams, flush_db: bool = True) -> Message:
        logger.debug(f"Updating message {params.id} tool usage with {params}")
        db_message = await self.repository.update_message_tool_usage(db, params, flush_db)
        return self._to_message_dto(db_message)
