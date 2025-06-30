from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
import asyncio

from fakeredis.aioredis import FakeRedis

from services.data_services.message_cache_service import MessageCacheService
from schemas.messages import (
    Message,
    GetMessagesParams,
    PaginatedMessages,
    CreateMessageParams,
    UpdateMessageParams,
    CreateUserMessageParams,
    CreateAssistantTextMessageParams,
    CreateAssistantRecipeMessageParams,
    CreateAssistantToolMessageParams,
)
from schemas.message_role import MessageRole
from schemas.message_content_type import MessageContentType


from utils.date_utils import to_utc_isostring

from tests.utils.assert_deep_equal import assert_deep_equal


@pytest_asyncio.fixture
async def message_cache_service(redis_client: FakeRedis) -> MessageCacheService:
    await redis_client.flushall()
    return MessageCacheService(redis_client, ttl=30) # 30 seconds for testing


class TestBasicMessageOperations:
    def test_get_message_key(self, message_cache_service: MessageCacheService):
        key = message_cache_service._get_message_key("user_id", "thread_id", "message_id")
        assert key == "brekkie:chat_session:user_id:threads:thread_id:messages:message_id"
        
        
    def test_get_all_messages_key(self, message_cache_service: MessageCacheService):
        key = message_cache_service._get_all_messages_key("user_id", "thread_id")
        assert key == "brekkie:chat_session:user_id:threads:thread_id:messages:*"
        
        
    def test_get_all_user_messages_key(self, message_cache_service: MessageCacheService):
        key = message_cache_service._get_all_user_messages_key("user_id")
        assert key == "brekkie:chat_session:user_id:threads:*:messages:*"
        
        
    @pytest.mark.asyncio
    async def test_get_and_set_message(self, message_cache_service: MessageCacheService):
        created_at = datetime.now(timezone.utc)
        updated_at = datetime.now(timezone.utc)
        message = Message(
            id="message_id",
            thread_id="thread_id",
            role=MessageRole.user,
            content_type=MessageContentType.text,
            text_content="text_content",
            created_at=to_utc_isostring(created_at),
            updated_at=to_utc_isostring(updated_at),
        )
        await message_cache_service.set_message("user_id", message)
        assert_deep_equal(await message_cache_service.get_message("user_id", "thread_id", "message_id"), message)
        
        
    @pytest.mark.asyncio
    async def test_get_and_set_message_with_ttl(self, message_cache_service: MessageCacheService):
        message = Message(
            id="message_id",
            thread_id="thread_id",
            role=MessageRole.user,
            content_type=MessageContentType.text,
            text_content="text_content",
            created_at=to_utc_isostring(datetime.now(timezone.utc)),
            updated_at=to_utc_isostring(datetime.now(timezone.utc)),
        )
        await message_cache_service.set_message("user_id", message, ttl=1)
        assert_deep_equal(await message_cache_service.get_message("user_id", "thread_id", "message_id"), message)
        await asyncio.sleep(1.5)
        assert await message_cache_service.get_message("user_id", "thread_id", "message_id") is None


    @pytest.mark.asyncio
    async def test_get_messages(self, message_cache_service: MessageCacheService):
        messages = [
            Message(
                id="message_id_1",
                thread_id="thread_id",
                role=MessageRole.user,
                content_type=MessageContentType.text,
                text_content="text_content",
                created_at=to_utc_isostring(datetime.now(timezone.utc)),
                updated_at=to_utc_isostring(datetime.now(timezone.utc)),
            ),
            Message(
                id="message_id_2",
                thread_id="thread_id",
                role=MessageRole.assistant,
                content_type=MessageContentType.text,
                text_content="text_content",
                created_at=to_utc_isostring(datetime.now(timezone.utc)),
                updated_at=to_utc_isostring(datetime.now(timezone.utc)),
            ),
        ]
        for message in messages:
            await message_cache_service.set_message("user_id", message)
        assert_deep_equal(await message_cache_service.get_messages("user_id", "thread_id"), messages)
        
        
    @pytest.mark.asyncio
    async def test_get_messages_by_id(self, message_cache_service: MessageCacheService):
        messages = [
            Message(
                id="message_id_1",
                thread_id="thread_id",
                role=MessageRole.user,
                content_type=MessageContentType.text,
                text_content="text_content",
                created_at=to_utc_isostring(datetime.now(timezone.utc)),
                updated_at=to_utc_isostring(datetime.now(timezone.utc)),
            ),
            Message(
                id="message_id_2",
                thread_id="thread_id",
                role=MessageRole.assistant,
                content_type=MessageContentType.text,
                text_content="text_content",
                created_at=to_utc_isostring(datetime.now(timezone.utc)),
                updated_at=to_utc_isostring(datetime.now(timezone.utc)),
            ),
        ]
        for message in messages:
            await message_cache_service.set_message("user_id", message)
        
        assert_deep_equal(await message_cache_service.get_messages_by_id("user_id", "thread_id", ["message_id_1", "message_id_2"]), messages)
        
        
    @pytest.mark.asyncio
    async def test_count_thread_user_messages(self, message_cache_service: MessageCacheService):
        await message_cache_service.set_message("user_id", Message(
            id="message_id_1",
            thread_id="thread_id",
            role=MessageRole.user,
            content_type=MessageContentType.text,
            text_content="text_content",
            created_at=to_utc_isostring(datetime.now(timezone.utc)),
            updated_at=to_utc_isostring(datetime.now(timezone.utc)),
        ))
        
        assert await message_cache_service.count_thread_user_messages("user_id", "thread_id") == 1
        
        
        await message_cache_service.set_message("user_id", Message(
            id="message_id_2",
            thread_id="thread_id",
            role=MessageRole.assistant,
            content_type=MessageContentType.text,
            text_content="text_content",
            created_at=to_utc_isostring(datetime.now(timezone.utc)),
            updated_at=to_utc_isostring(datetime.now(timezone.utc)),
        ))
        
        assert await message_cache_service.count_thread_user_messages("user_id", "thread_id") == 1
        
        
    @pytest.mark.asyncio
    async def test_update_message(self, message_cache_service: MessageCacheService):
        created_at = datetime.now(timezone.utc)
        updated_at = datetime.now(timezone.utc)
        
        message = Message(
            id="message_id",
            thread_id="thread_id",
            role=MessageRole.user,
            content_type=MessageContentType.text,
            text_content="text_content",
            created_at=to_utc_isostring(created_at),
            updated_at=to_utc_isostring(updated_at),
        )
        await message_cache_service.set_message("user_id", message)
        
        updated_at = datetime.now(timezone.utc)
        
        updated_message = await message_cache_service.update_message("user_id", "thread_id", UpdateMessageParams(
            id="message_id",
            updated_at=updated_at,
            text_content="updated_text_content",
        ))
        
        assert updated_message.id == "message_id"
        assert updated_message.thread_id == "thread_id"
        assert updated_message.role == MessageRole.user
        assert updated_message.content_type == MessageContentType.text
        assert updated_message.text_content == "updated_text_content"
        assert updated_message.created_at == message.created_at
        assert updated_message.updated_at == to_utc_isostring(updated_at)
        
        
    @pytest.mark.asyncio
    async def test_update_non_existent_message(self, message_cache_service: MessageCacheService):
        
        with pytest.raises(ValueError):
            await message_cache_service.update_message("user_id", "thread_id", UpdateMessageParams(
                id="message_id",
                updated_at=datetime.now(timezone.utc),
                text_content="updated_text_content",
            ))
            
            
    @pytest.mark.asyncio
    async def test_get_messages_by_user_id(self, message_cache_service: MessageCacheService):
        messages = [
            Message(
                id="message_id_1",
                thread_id="thread_id_1",
                role=MessageRole.user,
                content_type=MessageContentType.text,
                text_content="text_content",
                created_at=to_utc_isostring(datetime.now(timezone.utc)),
                updated_at=to_utc_isostring(datetime.now(timezone.utc)),
            ),
            Message(
                id="message_id_3",
                thread_id="thread_id_3",
                role=MessageRole.assistant,
                content_type=MessageContentType.text,
                text_content="text_content",
                created_at=to_utc_isostring(datetime.now(timezone.utc)),
                updated_at=to_utc_isostring(datetime.now(timezone.utc)),
            ),
        ]
        
        for message in messages:
            await message_cache_service.set_message("user_id", message) 
        
        assert_deep_equal(await message_cache_service.get_messages_by_user_id("user_id"), messages)
        
        
    @pytest.mark.asyncio
    async def test_delete_messages_by_user_id(self, message_cache_service: MessageCacheService):
        messages = [
            Message(
                id="message_id_1",
                thread_id="thread_id_1",
                role=MessageRole.user,
                content_type=MessageContentType.text,
                text_content="text_content",
                created_at=to_utc_isostring(datetime.now(timezone.utc)),
                updated_at=to_utc_isostring(datetime.now(timezone.utc)),
            ),
            Message(
                id="message_id_2",
                thread_id="thread_id_2",
                role=MessageRole.assistant,
                content_type=MessageContentType.text,
                text_content="text_content",
                created_at=to_utc_isostring(datetime.now(timezone.utc)),
                updated_at=to_utc_isostring(datetime.now(timezone.utc)),    
            ),
            Message(
                id="message_id_3",
                thread_id="thread_id_3",
                role=MessageRole.user,
                content_type=MessageContentType.text,
                text_content="text_content",
                created_at=to_utc_isostring(datetime.now(timezone.utc)),
                updated_at=to_utc_isostring(datetime.now(timezone.utc)),
            ),
        ]
        
        for message in messages:
            await message_cache_service.set_message("user_id", message)
            
        
        await message_cache_service.delete_messages_by_user_id("user_id")
        messages = await message_cache_service.get_messages_by_user_id("user_id")
        assert len(messages) == 0
        
        
class TestCreateMessage:
    @pytest.mark.asyncio
    async def test_create_message(self, message_cache_service: MessageCacheService):
        created_at = datetime.now(timezone.utc)
        updated_at = datetime.now(timezone.utc)
        
        expected_message = Message(
            id="message_id",
            thread_id="thread_id",
            role=MessageRole.user,
            content_type=MessageContentType.text,
            text_content="text_content",
            created_at=to_utc_isostring(created_at),
            updated_at=to_utc_isostring(updated_at),
        )

        params = CreateMessageParams(
            id="message_id",
            thread_id="thread_id",
            role=MessageRole.user,
            content_type=MessageContentType.text,
            text_content="text_content",
            created_at=created_at,
            updated_at=updated_at,
        )
        
        await message_cache_service.create_message("user_id", params)
        assert_deep_equal(await message_cache_service.get_message("user_id", "thread_id", "message_id"), expected_message)


    @pytest.mark.asyncio
    async def test_create_message_with_ttl(self, message_cache_service: MessageCacheService):
        created_at = datetime.now(timezone.utc)
        updated_at = datetime.now(timezone.utc)
        
        expected_message = Message(
            id="message_id",
            thread_id="thread_id",
            role=MessageRole.user,
            content_type=MessageContentType.text,
            text_content="text_content",
            created_at=to_utc_isostring(created_at),
            updated_at=to_utc_isostring(updated_at),
        )
        
        params = CreateMessageParams(
            id="message_id",
            thread_id="thread_id",
            role=MessageRole.user,
            content_type=MessageContentType.text,
            text_content="text_content",
            created_at=created_at,
            updated_at=updated_at,
        )
        
        await message_cache_service.create_message("user_id", params, ttl=1)
        
        assert_deep_equal(await message_cache_service.get_message("user_id", "thread_id", "message_id"), expected_message)
        
        await asyncio.sleep(1.5)
        
        assert await message_cache_service.get_message("user_id", "thread_id", "message_id") is None
        

    @pytest.mark.asyncio
    async def test_create_user_message(self, message_cache_service: MessageCacheService):
        created_at = datetime.now(timezone.utc)
        updated_at = datetime.now(timezone.utc)
        
        expected_message = Message(
            id="message_id",
            thread_id="thread_id",
            role=MessageRole.user,
            content_type=MessageContentType.text,
            text_content="text_content",
            created_at=to_utc_isostring(created_at),
            updated_at=to_utc_isostring(updated_at),
        )
        
        params = CreateUserMessageParams(
            id="message_id",
            thread_id="thread_id",
            text_content="text_content",
            created_at=created_at,
            updated_at=updated_at,
        )
        
        await message_cache_service.create_user_message("user_id", params)
        
        assert_deep_equal(await message_cache_service.get_message("user_id", "thread_id", "message_id"), expected_message)
        
        
    @pytest.mark.asyncio
    async def test_create_assistant_text_message(self, message_cache_service: MessageCacheService):
        created_at = datetime.now(timezone.utc)
        updated_at = datetime.now(timezone.utc)
        
        expected_message = Message(
            id="message_id",
            thread_id="thread_id",
            role=MessageRole.assistant,
            content_type=MessageContentType.text,
            text_content="text_content",
            created_at=to_utc_isostring(created_at),
            updated_at=to_utc_isostring(updated_at),
        )
        
        params = CreateAssistantTextMessageParams(
            id="message_id",    
            thread_id="thread_id",
            text_content="text_content",
            created_at=created_at,
            updated_at=updated_at,
        )
        
        await message_cache_service.create_assistant_text_message("user_id", params)
        
        assert_deep_equal(await message_cache_service.get_message("user_id", "thread_id", "message_id"), expected_message)
        

    @pytest.mark.asyncio
    async def test_create_assistant_recipe_message(self, message_cache_service: MessageCacheService):
        created_at = datetime.now(timezone.utc)
        updated_at = datetime.now(timezone.utc)
        
        expected_message = Message(
            id="message_id",
            thread_id="thread_id",
            role=MessageRole.assistant,
            content_type=MessageContentType.recipe,
            recipe_id="recipe_id",
            created_at=to_utc_isostring(created_at),
            updated_at=to_utc_isostring(updated_at),
            is_recipe_generation_started=True,
            is_recipe_generation_completed=False,
        )
        
        params = CreateAssistantRecipeMessageParams(
            id="message_id",
            thread_id="thread_id",
            recipe_id="recipe_id",
            created_at=created_at,
            updated_at=updated_at,
            is_recipe_generation_started=True,
            is_recipe_generation_completed=False,
        )
        
        await message_cache_service.create_assistant_recipe_message("user_id", params)
        
        assert_deep_equal(await message_cache_service.get_message("user_id", "thread_id", "message_id"), expected_message)
        
        
    @pytest.mark.asyncio
    async def test_create_assistant_message_with_ai_model_info(self, message_cache_service: MessageCacheService):
        created_at = datetime.now(timezone.utc)
        updated_at = datetime.now(timezone.utc)
        
        expected_message = Message(
            id="message_id",
            thread_id="thread_id",
            role=MessageRole.assistant,
            content_type=MessageContentType.text,
            text_content="text_content",
            created_at=to_utc_isostring(created_at),
            updated_at=to_utc_isostring(updated_at),
            model_used="gpt-4o",
            token_count=1000,
            response_time_ms=1000,
        )
        
        params = CreateAssistantTextMessageParams(
            id="message_id",
            thread_id="thread_id",
            text_content="text_content",
            created_at=created_at,
            updated_at=updated_at,
            model_used="gpt-4o",
            token_count=1000,
            response_time_ms=1000,
        )
        
        await message_cache_service.create_assistant_text_message("user_id", params)
        
        assert_deep_equal(await message_cache_service.get_message("user_id", "thread_id", "message_id"), expected_message)
        
        
    @pytest.mark.asyncio
    async def test_create_assistant_tool_message(self, message_cache_service: MessageCacheService):
        created_at = datetime.now(timezone.utc)
        updated_at = datetime.now(timezone.utc)
        
        expected_message = Message(
            id="message_id",
            thread_id="thread_id",
            role=MessageRole.assistant,
            content_type=MessageContentType.tool,
            tool_name="tool_name",
            tool_input={"key": "value"},
            tool_output={"key": "value"},
            created_at=to_utc_isostring(created_at),
            updated_at=to_utc_isostring(updated_at),
            model_used="gpt-4o",
            token_count=1000,
            response_time_ms=1000,
        )
        
        params = CreateAssistantToolMessageParams(
            id="message_id",
            thread_id="thread_id",
            tool_name="tool_name",
            tool_input={"key": "value"},
            tool_output={"key": "value"},
            created_at=created_at,
            updated_at=updated_at,
            model_used="gpt-4o",
            token_count=1000,
            response_time_ms=1000,
        )
        
        await message_cache_service.create_assistant_tool_message("user_id", params)
        
        assert_deep_equal(await message_cache_service.get_message("user_id", "thread_id", "message_id"), expected_message)
        

class TestGetPaginatedMessages:
    @pytest.fixture
    def user_id(self) -> str:
        return "user_id"
    
    @pytest.fixture
    def thread_id(self) -> str:
        return "thread_id"

    
    @pytest.fixture
    def sample_messages(self, thread_id: str) -> list[Message]:
        return [
            Message(
                id=f"message_id_{i}",
                thread_id=thread_id,
                role=MessageRole.user if i % 2 == 0 else MessageRole.assistant,
                content_type=MessageContentType.text,
                text_content=f"text_content_{i}",
                created_at=to_utc_isostring(datetime.now(timezone.utc) + timedelta(seconds=i * 10)),
                updated_at=to_utc_isostring(datetime.now(timezone.utc) + timedelta(seconds=i * 10 + 1)),  
            ) for i in range(50)
        ]

        
    @pytest_asyncio.fixture
    async def create_messages(self, message_cache_service: MessageCacheService, sample_messages: list[Message], user_id: str, thread_id: str) -> list[Message]:
        for message in sample_messages:
            await message_cache_service.set_message(user_id, message)
        return sample_messages
        

    @pytest.mark.asyncio
    async def test_no_messages(self, message_cache_service: MessageCacheService, create_messages: list[Message], user_id: str, thread_id: str):
        result = await message_cache_service.get_paginated_messages(user_id=user_id, params=GetMessagesParams(
            thread_id="non_existent_thread_id",
            limit=10,
        )) 
        
        assert isinstance(result, PaginatedMessages)
        
        assert len(result.messages) == 0
        assert result.total_count == 0
        assert result.has_more is False
        assert result.next_timestamp is None
        

        
    @pytest.mark.asyncio
    async def test_sort_by_created_at_asc(self, message_cache_service: MessageCacheService, create_messages: list[Message], user_id: str, thread_id: str, sample_messages: list[Message]):
        result = await message_cache_service.get_paginated_messages(user_id=user_id, params=GetMessagesParams(
            thread_id=thread_id,
            limit=10,
            sort_by="created_at",
            sort_order="asc",
        ))
        
        expected_next_timestamp = sample_messages[9].created_at
        
        assert isinstance(result, PaginatedMessages)
        
        assert len(result.messages) == 10
        assert result.total_count == 50
        assert result.has_more is True
        assert result.next_timestamp is not None
        assert result.next_timestamp == expected_next_timestamp
        
        
    @pytest.mark.asyncio
    async def test_sort_by_created_at_desc(self, message_cache_service: MessageCacheService, create_messages: list[Message], user_id: str, thread_id: str, sample_messages: list[Message]):
        result = await message_cache_service.get_paginated_messages(user_id=user_id, params=GetMessagesParams(
            thread_id=thread_id,
            limit=10,
            sort_by="created_at",
            sort_order="desc",
        ))
        
        expected_next_timestamp = sample_messages[40].created_at
        
        assert isinstance(result, PaginatedMessages)
        
        assert len(result.messages) == 10    
        assert result.total_count == 50
        assert result.has_more is True
        assert result.next_timestamp is not None
        assert result.next_timestamp == expected_next_timestamp
        
        
    @pytest.mark.asyncio
    async def test_sort_by_updated_at_asc(self, message_cache_service: MessageCacheService, create_messages: list[Message], user_id: str, thread_id: str, sample_messages: list[Message]):
        result = await message_cache_service.get_paginated_messages(user_id=user_id, params=GetMessagesParams(
            thread_id=thread_id,
            limit=10,
            sort_by="updated_at",
            sort_order="asc",
        ))
        
        expected_next_timestamp = sample_messages[9].updated_at
        
        assert isinstance(result, PaginatedMessages)
        
        assert len(result.messages) == 10
        assert result.total_count == 50
        assert result.has_more is True
        assert result.next_timestamp is not None
        assert result.next_timestamp == expected_next_timestamp
        
        
    @pytest.mark.asyncio
    async def test_sort_by_updated_at_desc(self, message_cache_service: MessageCacheService, create_messages: list[Message], user_id: str, thread_id: str, sample_messages: list[Message]):
        result = await message_cache_service.get_paginated_messages(user_id=user_id, params=GetMessagesParams(
            thread_id=thread_id,
            limit=10,
            sort_by="updated_at",
            sort_order="desc",
        ))
        
        expected_next_timestamp = sample_messages[40].updated_at
        
        assert isinstance(result, PaginatedMessages)
        
        assert len(result.messages) == 10
        assert result.total_count == 50
        assert result.has_more is True
        assert result.next_timestamp is not None
        assert result.next_timestamp == expected_next_timestamp
        
        
    @pytest.mark.asyncio
    async def test_large_limit(self, message_cache_service: MessageCacheService, create_messages: list[Message], user_id: str, thread_id: str, sample_messages: list[Message]):
        result = await message_cache_service.get_paginated_messages(user_id=user_id, params=GetMessagesParams(
            thread_id=thread_id,
            limit=30,
            sort_by="created_at",
            sort_order="asc",
        ))
        
        expected_next_timestamp = sample_messages[29].created_at
        
        assert isinstance(result, PaginatedMessages)
        
        assert len(result.messages) == 30
        assert result.total_count == 50
        assert result.has_more is True
        assert result.next_timestamp is not None
        assert result.next_timestamp == expected_next_timestamp
        
        
    @pytest.mark.asyncio
    async def test_no_more_messages(self, message_cache_service: MessageCacheService, create_messages: list[Message], user_id: str, thread_id: str, sample_messages: list[Message]):
        result = await message_cache_service.get_paginated_messages(user_id=user_id, params=GetMessagesParams(
            thread_id=thread_id,
            limit=100,
            sort_by="created_at",
            sort_order="asc",
        ))
        
        assert isinstance(result, PaginatedMessages)
        
        assert len(result.messages) == 50
        assert result.total_count == 50
        assert result.has_more is False
        assert result.next_timestamp is None
        
        
    @pytest.mark.asyncio
    async def test_from_timestamp_and_sort_by_created_at_asc(self, message_cache_service: MessageCacheService, create_messages: list[Message], user_id: str, thread_id: str, sample_messages: list[Message]):
        result = await message_cache_service.get_paginated_messages(user_id=user_id, params=GetMessagesParams(
            thread_id=thread_id,
            limit=10,
            from_timestamp=sample_messages[9].created_at,
            sort_by="created_at",
            sort_order="asc",
        ))
        
        expected_next_timestamp = sample_messages[19].created_at
        
        assert isinstance(result, PaginatedMessages)
        
        assert len(result.messages) == 10
        assert result.total_count == 50
        assert result.has_more is True
        assert result.next_timestamp is not None
        assert result.next_timestamp == expected_next_timestamp
        
        
    @pytest.mark.asyncio
    async def test_from_timestamp_and_sort_by_created_at_desc(self, message_cache_service: MessageCacheService, create_messages: list[Message], user_id: str, thread_id: str, sample_messages: list[Message]):
        result = await message_cache_service.get_paginated_messages(user_id=user_id, params=GetMessagesParams(
            thread_id=thread_id,
            limit=10,
            from_timestamp=sample_messages[40].created_at,
            sort_by="created_at",
            sort_order="desc",
        ))
        
        expected_next_timestamp = sample_messages[30].created_at
        
        assert isinstance(result, PaginatedMessages)
        
        assert len(result.messages) == 10
        assert result.total_count == 50
        assert result.has_more is True
        assert result.next_timestamp is not None
        assert result.next_timestamp == expected_next_timestamp
        
        
    @pytest.mark.asyncio
    async def test_from_timestamp_and_sort_by_updated_at_asc(self, message_cache_service: MessageCacheService, create_messages: list[Message], user_id: str, thread_id: str, sample_messages: list[Message]):
        result = await message_cache_service.get_paginated_messages(user_id=user_id, params=GetMessagesParams(
            thread_id=thread_id,
            limit=10,
            from_timestamp=sample_messages[9].updated_at,
            sort_by="updated_at",
            sort_order="asc",
        ))
        
        expected_next_timestamp = sample_messages[19].updated_at
        
        assert isinstance(result, PaginatedMessages)
        
        assert len(result.messages) == 10
        assert result.total_count == 50
        assert result.has_more is True
        assert result.next_timestamp is not None
        assert result.next_timestamp == expected_next_timestamp
        
        
    @pytest.mark.asyncio
    async def test_from_timestamp_and_sort_by_updated_at_desc(self, message_cache_service: MessageCacheService, create_messages: list[Message], user_id: str, thread_id: str, sample_messages: list[Message]):
        result = await message_cache_service.get_paginated_messages(user_id=user_id, params=GetMessagesParams(
            thread_id=thread_id,
            limit=10,
            from_timestamp=sample_messages[40].updated_at,
            sort_by="updated_at",
            sort_order="desc",
        ))
        
        expected_next_timestamp = sample_messages[30].updated_at
        
        assert isinstance(result, PaginatedMessages)
        
        assert len(result.messages) == 10
        assert result.total_count == 50
        assert result.has_more is True
        assert result.next_timestamp is not None
        assert result.next_timestamp == expected_next_timestamp
        
        
        