import pytest
import pytest_asyncio

from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from repositories.message_repository import MessageRepository
from services.data_services.message_service import MessageService

from schemas.messages import (
    CreateMessageParams,
    CreateUserMessageParams,
    CreateAssistantTextMessageParams,
    CreateAssistantRecipeMessageParams,
    Message,
    PaginatedMessages,
    UpdateMessageParams,
    GetMessagesParams,
)

from schemas.messages import MessageRole, MessageContentType

from utils.date_utils import to_utc_isostring


pytestmark = pytest.mark.asyncio

@pytest.fixture
def message_service():
    return MessageService(MessageRepository())


class TestSimpleMessageOperations:
    async def test_create_message(self, async_session: AsyncSession, message_service: MessageService):
        params = CreateMessageParams(
            id="test-message-id",
            thread_id="test-thread-id",
            role=MessageRole.user,
            content_type=MessageContentType.text,
            text_content="test-text-content",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        
        message = await message_service.create_message(async_session, params)
        
        assert isinstance(message, Message)
        
        assert message.id == params.id
        assert message.thread_id == params.thread_id
        assert message.role == params.role
        assert message.content_type == params.content_type
        assert message.text_content == params.text_content
        assert message.created_at == to_utc_isostring(params.created_at)
        assert message.updated_at == to_utc_isostring(params.updated_at)
    
    
    async def test_create_user_message(self, async_session: AsyncSession, message_service: MessageService):
        params = CreateUserMessageParams(
            id="test-message-id",
            thread_id="test-thread-id",
            text_content="test-text-content",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        
        message = await message_service.create_user_message(async_session, params)
        
        assert isinstance(message, Message)
        
        assert message.id == params.id
        assert message.thread_id == params.thread_id
        assert message.role == MessageRole.user
        assert message.content_type == MessageContentType.text
        assert message.text_content == params.text_content
        assert message.created_at == to_utc_isostring(params.created_at)
        assert message.updated_at == to_utc_isostring(params.updated_at)
        
            
    async def test_create_assistant_text_message(self, async_session: AsyncSession, message_service: MessageService):
        params = CreateAssistantTextMessageParams(
            id="test-message-id",
            thread_id="test-thread-id",
            text_content="test-text-content",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        
        message = await message_service.create_assistant_text_message(async_session, params)
        
        assert isinstance(message, Message)
        
        assert message.id == params.id
        assert message.thread_id == params.thread_id
        assert message.role == MessageRole.assistant
        assert message.content_type == MessageContentType.text
        assert message.text_content == params.text_content
        assert message.created_at == to_utc_isostring(params.created_at)
        assert message.updated_at == to_utc_isostring(params.updated_at)
        
    
    async def test_create_assistant_recipe_message(self, async_session: AsyncSession, message_service: MessageService):
        params = CreateAssistantRecipeMessageParams(
            id="test-message-id",
            thread_id="test-thread-id",
            recipe_id="test-recipe-id",
            is_recipe_generation_started=True,
            is_recipe_generation_completed=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        
        message = await message_service.create_assistant_recipe_message(async_session, params)
        
        assert isinstance(message, Message)
        
        assert message.id == params.id
        assert message.thread_id == params.thread_id
        assert message.role == MessageRole.assistant
        assert message.content_type == MessageContentType.recipe
        assert message.recipe_id == params.recipe_id
        assert message.is_recipe_generation_started == params.is_recipe_generation_started
        assert message.is_recipe_generation_completed == params.is_recipe_generation_completed
        assert message.created_at == to_utc_isostring(params.created_at)
        assert message.updated_at == to_utc_isostring(params.updated_at)
        
    
    async def test_update_message(self, async_session: AsyncSession, message_service: MessageService):
        message = await message_service.create_assistant_text_message(async_session, CreateAssistantTextMessageParams(
            id="test-message-id",
            thread_id="test-thread-id",
            text_content="test-text-content",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        ))
        
        params = UpdateMessageParams(
            id="test-message-id",
            updated_at=datetime.now(timezone.utc),
            text_content="test-text-content-2",
        )
        
        message = await message_service.update_message(async_session, params)
        
        assert isinstance(message, Message)
        
        assert message.id == params.id
        assert message.text_content == params.text_content
        assert message.updated_at == to_utc_isostring(params.updated_at)
    
    
    async def test_get_message(self, async_session: AsyncSession, message_service: MessageService):
        params = CreateAssistantTextMessageParams(
            id="test-message-id",
            thread_id="test-thread-id",
            text_content="test-text-content",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        message = await message_service.create_assistant_text_message(async_session, params)
        
        message = await message_service.get_message(async_session, "test-message-id")
        
        assert isinstance(message, Message)
        
        assert message.id == params.id
        assert message.thread_id == params.thread_id
        assert message.role == params.role
        assert message.content_type == params.content_type
        assert message.text_content == params.text_content
        assert message.created_at == to_utc_isostring(params.created_at)
        assert message.updated_at == to_utc_isostring(params.updated_at)

    async def test_count_thread_messages(self, async_session: AsyncSession, message_service: MessageService):
        for i in range(10):
            await message_service.create_assistant_text_message(async_session, CreateAssistantTextMessageParams(
                id=f"test-message-id-{i}",
                thread_id="test-thread-id",
                text_content=f"test-text-content-{i}",
                created_at=datetime.now(timezone.utc) + timedelta(seconds=i * 10),
                updated_at=datetime.now(timezone.utc) + timedelta(seconds=i * 10),
            ))
        
        count = await message_service.count_thread_messages(async_session, "test-thread-id")
        assert count == 10
        
        
    async def test_create_messages(self, async_session: AsyncSession, message_service: MessageService):
        params = [
            CreateAssistantTextMessageParams(
                id=f"test-message-id-{i}",
                thread_id="test-thread-id",
                text_content=f"test-text-content-{i}",
                created_at=datetime.now(timezone.utc) + timedelta(seconds=i * 10),
                updated_at=datetime.now(timezone.utc) + timedelta(seconds=i * 10),
            ) for i in range(50)
        ]
        
        messages = await message_service.create_messages(async_session, params)
        
        assert len(messages) == 50
        
        for i, message in enumerate(messages):
            assert message.id == params[i].id
            assert message.text_content == params[i].text_content
            assert message.created_at == to_utc_isostring(params[i].created_at)
            
    
        
class TestPaginatedMessages:
    @pytest.fixture()
    def assistant_text_message_params(self):
        return [
            CreateAssistantTextMessageParams(
                id=f"test-message-id-{i}",
                thread_id="test-thread-id",
                text_content=f"test-text-content-{i}",
                created_at=datetime.now(timezone.utc) + timedelta(seconds=i * 10),
                updated_at=datetime.now(timezone.utc) + timedelta(seconds=i * 100),
            ) for i in range(50)
        ]


    @pytest_asyncio.fixture(scope="function")
    async def create_assistant_text_messages_in_db(self, async_session: AsyncSession, message_service: MessageService, assistant_text_message_params: list[CreateAssistantTextMessageParams]):
        for param in assistant_text_message_params:
            await message_service.create_assistant_text_message(async_session, param)
        
        
    async def test_correct_return_type(self, async_session: AsyncSession, message_service: MessageService, create_assistant_text_messages_in_db, assistant_text_message_params: list[CreateAssistantTextMessageParams]):
        get_params = GetMessagesParams(thread_id="test-thread-id")
        
        paginated_messages = await message_service.get_paginated_messages(async_session, get_params)
        
        assert isinstance(paginated_messages, PaginatedMessages)
    

    async def test_get_paginated_messages(self, async_session: AsyncSession, message_service: MessageService, create_assistant_text_messages_in_db, assistant_text_message_params: list[CreateAssistantTextMessageParams]):
        reversed_params = list(reversed(assistant_text_message_params))
        
        get_params = GetMessagesParams(
            thread_id="test-thread-id",
            limit=10,
            sort_by="created_at",
            sort_order="desc",
        )
        
        paginated_messages = await message_service.get_paginated_messages(async_session, get_params)
        
        assert len(paginated_messages.messages) == 10
        assert paginated_messages.total_count == 50
        assert paginated_messages.has_more == True
        assert paginated_messages.next_timestamp == to_utc_isostring(reversed_params[9].created_at)
        
    
    async def test_get_paginated_messages_with_default_limit(self, async_session: AsyncSession, message_service: MessageService, create_assistant_text_messages_in_db, assistant_text_message_params: list[CreateAssistantTextMessageParams]):
        reversed_params = list(reversed(assistant_text_message_params))
        
        get_params = GetMessagesParams(
            thread_id="test-thread-id",
            sort_by="created_at",
            sort_order="desc",
        )
        
        paginated_messages = await message_service.get_paginated_messages(async_session, get_params)
        
        assert len(paginated_messages.messages) == 10
        assert paginated_messages.total_count == 50
        assert paginated_messages.has_more == True
        assert paginated_messages.next_timestamp == to_utc_isostring(reversed_params[9].created_at)


    async def test_get_paginated_messages_with_sorted_by_created_at_asc(self, async_session: AsyncSession, message_service: MessageService, create_assistant_text_messages_in_db, assistant_text_message_params: list[CreateAssistantTextMessageParams]):
        get_params = GetMessagesParams(
            thread_id="test-thread-id",
            limit=10,
            sort_by="created_at",
            sort_order="asc",
        )
        
        paginated_messages = await message_service.get_paginated_messages(async_session, get_params)
        
        assert len(paginated_messages.messages) == 10
        assert paginated_messages.total_count == 50
        assert paginated_messages.has_more == True
        assert paginated_messages.next_timestamp == to_utc_isostring(assistant_text_message_params[9].created_at)
        
        
    async def test_get_paginated_messages_with_sorted_by_created_at_desc(self, async_session: AsyncSession, message_service: MessageService, create_assistant_text_messages_in_db, assistant_text_message_params: list[CreateAssistantTextMessageParams]):
        reversed_params = list(reversed(assistant_text_message_params))
        
        get_params = GetMessagesParams(
            thread_id="test-thread-id",
            limit=10,
        )

        paginated_messages = await message_service.get_paginated_messages(async_session, get_params)
        
        assert len(paginated_messages.messages) == 10
        assert paginated_messages.total_count == 50
        assert paginated_messages.has_more == True
        assert paginated_messages.next_timestamp == to_utc_isostring(reversed_params[9].created_at)
        
        
    async def test_get_paginated_messages_with_sorted_by_updated_at_desc(self, async_session: AsyncSession, message_service: MessageService, create_assistant_text_messages_in_db, assistant_text_message_params: list[CreateAssistantTextMessageParams]):
        reversed_params = list(reversed(assistant_text_message_params))
        
        get_params = GetMessagesParams(
            thread_id="test-thread-id",
            limit=10,
            sort_by="updated_at",
            sort_order="desc",
        )
        
        paginated_messages = await message_service.get_paginated_messages(async_session, get_params)
        
        assert len(paginated_messages.messages) == 10
        assert paginated_messages.total_count == 50
        assert paginated_messages.has_more == True
        assert paginated_messages.next_timestamp == to_utc_isostring(reversed_params[9].updated_at)
        
        
    async def test_get_paginated_messages_with_sorted_by_updated_at_asc(self, async_session: AsyncSession, message_service: MessageService, create_assistant_text_messages_in_db, assistant_text_message_params: list[CreateAssistantTextMessageParams]):
        get_params = GetMessagesParams(
            thread_id="test-thread-id",
            limit=10,
            sort_by="updated_at",
            sort_order="asc",
        )
        
        paginated_messages = await message_service.get_paginated_messages(async_session, get_params)
        
        assert len(paginated_messages.messages) == 10
        assert paginated_messages.total_count == 50
        assert paginated_messages.has_more == True
        assert paginated_messages.next_timestamp == to_utc_isostring(assistant_text_message_params[9].updated_at)
        
        
    async def test_get_paginated_messages_with_from_timestamp(self, async_session: AsyncSession, message_service: MessageService, create_assistant_text_messages_in_db, assistant_text_message_params: list[CreateAssistantTextMessageParams]):
        reversed_params = list(reversed(assistant_text_message_params))
        
        get_params = GetMessagesParams(
            thread_id="test-thread-id",
            limit=10,
            sort_by="created_at",
            sort_order="desc",
            from_timestamp=reversed_params[9].created_at,
        )
        
        paginated_messages = await message_service.get_paginated_messages(async_session, get_params)
        
        assert len(paginated_messages.messages) == 10
        assert paginated_messages.total_count == 50
        assert paginated_messages.has_more == True
        assert paginated_messages.next_timestamp == to_utc_isostring(reversed_params[19].created_at)
        
        
    async def test_get_paginated_messages_with_from_timestamp_and_custom_limit(self, async_session: AsyncSession, message_service: MessageService, create_assistant_text_messages_in_db, assistant_text_message_params: list[CreateAssistantTextMessageParams]):
        reversed_params = list(reversed(assistant_text_message_params))
        
        get_params = GetMessagesParams(
            thread_id="test-thread-id",
            limit=20,
            sort_by="created_at",
            sort_order="desc",
            from_timestamp=reversed_params[9].created_at,
        )
        
        paginated_messages = await message_service.get_paginated_messages(async_session, get_params)
        
        assert len(paginated_messages.messages) == 20
        assert paginated_messages.total_count == 50
        assert paginated_messages.has_more == True
        assert paginated_messages.next_timestamp == to_utc_isostring(reversed_params[29].created_at)
        
    
    async def test_get_paginated_messages_with_from_timestamp_and_custom_limit_and_no_more_messages(self, async_session: AsyncSession, message_service: MessageService, create_assistant_text_messages_in_db, assistant_text_message_params: list[CreateAssistantTextMessageParams]):        
        reversed_params = list(reversed(assistant_text_message_params))
        
        get_params = GetMessagesParams(
            thread_id="test-thread-id",
            limit=60,
            sort_by="created_at",
            sort_order="desc",
            from_timestamp=reversed_params[9].created_at,
        )
        
        paginated_messages = await message_service.get_paginated_messages(async_session, get_params)
        
        assert len(paginated_messages.messages) == 40
        assert paginated_messages.total_count == 50
        assert paginated_messages.has_more == False
        assert paginated_messages.next_timestamp is None
        
        
    async def test_get_paginated_messages_with_from_timestamp_and_invalid_limit(self, async_session: AsyncSession, message_service: MessageService, create_assistant_text_messages_in_db, assistant_text_message_params: list[CreateAssistantTextMessageParams]):
        reversed_params = list(reversed(assistant_text_message_params))
        
        with pytest.raises(ValueError) as e:
            get_params = GetMessagesParams(
                thread_id="test-thread-id",
                limit=1000,
                sort_by="created_at",
                sort_order="desc",
                from_timestamp=reversed_params[9].created_at,
            )
            
            
        with pytest.raises(ValueError) as e:
            get_params = GetMessagesParams(
                thread_id="test-thread-id",
                limit=0,
                sort_by="created_at",
                sort_order="desc",
                from_timestamp=reversed_params[9].created_at,
            )
            
