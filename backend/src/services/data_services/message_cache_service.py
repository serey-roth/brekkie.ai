from datetime import datetime, timezone

from schemas.message_role import MessageRole
from schemas.messages import (
    CreateAssistantRecipeMessageParams,
    CreateAssistantTextMessageParams,
    CreateAssistantToolMessageParams,
    CreateMessageParams,
    CreateUserMessageParams,
    GetMessagesParams,
    Message,
    PaginatedMessages,
    UpdateMessageParams,
    UpdateStrategy,
)
from services.redis.redis_cache import RedisCache
from services.redis.redis_client import RedisClient
from utils.date_utils import to_utc_isostring


class MessageCacheService:
    def __init__(self, redis_client: RedisClient, ttl: int):
        self.message_cache = RedisCache[Message](redis_client)
        self.ttl = ttl

    def _get_message_key(self, user_id: str, thread_id: str, message_id: str) -> str:
        return f"brekkie:chat_session:{user_id}:threads:{thread_id}:messages:{message_id}"

    def _get_all_messages_key(self, user_id: str, thread_id: str) -> str:
        return f"brekkie:chat_session:{user_id}:threads:{thread_id}:messages:*"

    def _get_all_user_messages_key(self, user_id: str) -> str:
        return f"brekkie:chat_session:{user_id}:threads:*:messages:*"

    async def get_message(self, user_id: str, thread_id: str, message_id: str) -> Message | None:
        return await self.message_cache.get_json(
            self._get_message_key(user_id, thread_id, message_id), Message
        )

    async def get_messages(self, user_id: str, thread_id: str) -> list[Message]:
        results = await self.message_cache.get_all_json_by_pattern(
            pattern=self._get_all_messages_key(user_id, thread_id), model=Message
        )
        return list(results)

    async def get_messages_by_user_id(self, user_id: str) -> list[Message]:
        results = await self.message_cache.get_all_json_by_pattern(
            pattern=self._get_all_user_messages_key(user_id), model=Message
        )
        return list(results)

    async def get_messages_by_ids(
        self, user_id: str, thread_id: str, message_ids: list[str]
    ) -> list[Message]:
        keys = [self._get_message_key(user_id, thread_id, message_id) for message_id in message_ids]
        results = await self.message_cache.get_all_json_by_keys(keys=keys, model=Message)
        return list(results)

    async def set_message(
        self, user_id: str, message: Message, ttl: int | None = None, keep_ttl: bool = False
    ) -> None:
        if keep_ttl:
            set_ttl = None
        else:
            set_ttl = ttl if ttl is not None else self.ttl
        await self.message_cache.set_json(
            self._get_message_key(user_id, message.thread_id, message.id),
            message,
            ttl=set_ttl,
            keep_ttl=keep_ttl,
        )

    async def create_message(
        self, user_id: str, params: CreateMessageParams, ttl: int | None = None
    ) -> Message:
        message = Message(
            created_at=to_utc_isostring(params.created_at),
            updated_at=to_utc_isostring(params.updated_at),
            **params.model_dump(
                exclude={"created_at", "updated_at"}, exclude_unset=True, exclude_none=True
            ),
        )
        await self.set_message(user_id, message, ttl=ttl)
        return message

    async def create_user_message(
        self, user_id: str, params: CreateUserMessageParams, ttl: int | None = None
    ) -> Message:
        message = await self.create_message(user_id, params, ttl)
        return message

    async def create_assistant_text_message(
        self, user_id: str, params: CreateAssistantTextMessageParams, ttl: int | None = None
    ) -> Message:
        message = await self.create_message(user_id, params, ttl)
        return message

    async def create_assistant_recipe_message(
        self, user_id: str, params: CreateAssistantRecipeMessageParams, ttl: int | None = None
    ) -> Message:
        message = await self.create_message(user_id, params, ttl)
        return message

    async def create_assistant_tool_message(
        self, user_id: str, params: CreateAssistantToolMessageParams, ttl: int | None = None
    ) -> Message:
        message = await self.create_message(user_id, params, ttl)
        return message

    async def update_message(
        self, user_id: str, thread_id: str, params: UpdateMessageParams
    ) -> Message:
        message = await self.get_message(user_id, thread_id, params.id)
        if message is None:
            raise ValueError(f"Message {params.id} not found")

        new_message = message.model_copy(deep=True)

        updated_at = params.updated_at
        new_message.updated_at = to_utc_isostring(updated_at)

        text_content_update = params.text_content_update
        if text_content_update is not None:
            if text_content_update.strategy == UpdateStrategy.REPLACE:
                new_message.text_content = text_content_update.text_content
            else:
                new_message.text_content = (
                    str(new_message.text_content) or ""
                ) + text_content_update.text_content

        input_tokens_update = params.input_tokens_update
        if input_tokens_update is not None:
            if input_tokens_update.strategy == UpdateStrategy.REPLACE:
                new_message.input_tokens = input_tokens_update.input_tokens
            else:
                new_message.input_tokens = (
                    int(input_tokens_update.input_tokens)
                    if input_tokens_update.input_tokens is not None
                    else 0
                )
                new_message.input_tokens = (
                    new_message.input_tokens + input_tokens_update.input_tokens
                )

        output_tokens_update = params.output_tokens_update
        if output_tokens_update is not None:
            if output_tokens_update.strategy == UpdateStrategy.REPLACE:
                new_message.output_tokens = output_tokens_update.output_tokens
            else:
                new_message.output_tokens = (
                    int(output_tokens_update.output_tokens)
                    if output_tokens_update.output_tokens is not None
                    else 0
                )
                new_message.output_tokens = (
                    new_message.output_tokens + output_tokens_update.output_tokens
                )

        items_to_update = params.model_dump(
            exclude={
                "id",
                "updated_at",
                "text_content_update",
                "input_tokens_update",
                "output_tokens_update",
            },
            exclude_none=True,
            exclude_unset=True,
        )
        for field, value in items_to_update.items():
            if value is not None:
                setattr(new_message, field, value)

        previous_ttl = await self.message_cache.get_ttl(
            self._get_message_key(user_id, thread_id, params.id)
        )
        if previous_ttl is None or previous_ttl < 0:
            await self.set_message(user_id, new_message, ttl=self.ttl)
        else:
            await self.set_message(user_id, new_message, keep_ttl=True)

        return new_message

    async def count_total_messages_sent_by_user(self, user_id: str) -> int:
        user_messages = await self.get_messages_by_user_id(user_id)
        return sum(1 for message in user_messages if message.role == MessageRole.user)

    # TODO: Duplicate logic from thread_cache_service.py. Extract sorting and filtering to a separate class?
    async def _sort_messages(
        self, messages: list[Message], sort_by: str, sort_order: str
    ) -> list[Message]:
        copied_messages = [m.model_copy(deep=True) for m in messages]

        def sort_fn(m: Message) -> datetime:
            if sort_by == "created_at":
                return datetime.fromisoformat(m.created_at).replace(tzinfo=timezone.utc)
            else:
                return datetime.fromisoformat(m.updated_at).replace(tzinfo=timezone.utc)

        copied_messages.sort(key=sort_fn, reverse=sort_order == "desc")
        return copied_messages

    async def _filter_messages(
        self,
        messages: list[Message],
        from_timestamp: datetime | None,
        sort_by: str,
        sort_order: str,
    ) -> list[Message]:
        copied_messages = [m.model_copy(deep=True) for m in messages]

        def filter_fn(m: Message) -> bool:
            if from_timestamp is None:
                return True

            if sort_by == "created_at" and sort_order == "asc":
                return (
                    datetime.fromisoformat(m.created_at).replace(tzinfo=timezone.utc)
                    > from_timestamp
                )
            elif sort_by == "created_at" and sort_order == "desc":
                return (
                    datetime.fromisoformat(m.created_at).replace(tzinfo=timezone.utc)
                    < from_timestamp
                )
            elif sort_by == "updated_at" and sort_order == "asc":
                return (
                    datetime.fromisoformat(m.updated_at).replace(tzinfo=timezone.utc)
                    > from_timestamp
                )
            elif sort_by == "updated_at" and sort_order == "desc":
                return (
                    datetime.fromisoformat(m.updated_at).replace(tzinfo=timezone.utc)
                    < from_timestamp
                )
            else:
                raise ValueError(f"Invalid sort_by or sort_order: {sort_by} {sort_order}")

        copied_messages = [m for m in copied_messages if filter_fn(m)]
        return copied_messages

    async def get_paginated_messages(self, params: GetMessagesParams) -> PaginatedMessages:
        messages = await self.get_messages(params.user_id, params.thread_id)
        if len(messages) == 0:
            return PaginatedMessages(
                messages=[],
                total_count=0,
                has_more=False,
                next_timestamp=None,
            )

        copied_messages = await self._sort_messages(messages, params.sort_by, params.sort_order)
        if params.from_timestamp:
            copied_messages = await self._filter_messages(
                copied_messages, params.from_timestamp, params.sort_by, params.sort_order
            )

        paginated_limit = params.limit + 1
        limited_messages = copied_messages[:paginated_limit]
        has_more = len(limited_messages) > params.limit

        messages_to_return = limited_messages[: params.limit]

        last_message = messages_to_return[-1] if has_more else None
        if last_message and params.sort_by == "created_at":
            next_timestamp = last_message.created_at
        elif last_message and params.sort_by == "updated_at":
            next_timestamp = last_message.updated_at
        else:
            next_timestamp = None

        return PaginatedMessages(
            messages=messages_to_return,
            total_count=len(messages),
            has_more=has_more,
            next_timestamp=next_timestamp,
        )
