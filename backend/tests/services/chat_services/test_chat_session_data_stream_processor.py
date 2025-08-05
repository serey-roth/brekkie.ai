from contextlib import asynccontextmanager
import pytest
import pytest_asyncio
from datetime import datetime, timezone
from typing import AsyncGenerator

from fakeredis.aioredis import FakeRedis
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
)

from database.index import DBTransactionMaker
from database.schema import Base

from repositories.message_repository import MessageRepository
from repositories.recipe_repository import RecipeRepository
from repositories.thread_repository import ThreadRepository

from services.chat_services.chat_session_data_stream_processor import (
    ChatSessionDataStreamProcessor,
    RetryException,
)
from services.data_services.message_cache_service import MessageCacheService
from services.data_services.message_service import MessageService
from services.data_services.recipe_cache_service import RecipeCacheService
from services.data_services.recipe_service import RecipeService
from services.data_services.thread_cache_service import ThreadCacheService
from services.data_services.thread_service import ThreadService

from schemas.messages import (
    CreateMessageParams,
    GetMessagesParams,
    MessageRole,
    MessageContentType,
    Message,
)
from schemas.recipes import (
    CreateRecipeParams,
    Recipe,
    UserRecipe,
    RecipeIngredient,
    RecipeInstruction,
    RecipeCategory,
)
from schemas.threads import CreateThreadParams, GetUserThreadsParams, Thread
from schemas.chat_session_data_stream import (
    ChatSessionDataStreamEntry,
    ChatSessionStreamEntryType,
    SyncCachedThreadWithDbEntry,
    SyncCachedMessageWithDbEntry,
    SyncCachedRecipeWithDbEntry,
)


DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="function")
async def async_engine() -> AsyncGenerator[AsyncEngine, None]:
    engine = create_async_engine(DATABASE_URL, echo=False, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def async_session(async_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    async_session = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def redis_client() -> AsyncGenerator[FakeRedis, None]:
    redis = await FakeRedis()
    yield redis
    await redis.flushall()


@pytest_asyncio.fixture(scope="function")
async def db_transaction_maker(async_session: AsyncSession) -> DBTransactionMaker:
    @asynccontextmanager
    async def transaction_maker() -> AsyncGenerator[AsyncSession, None]:
        try:
            yield async_session
            await async_session.commit()
        except Exception as e:
            print(f"Error in database transaction: {e}")
            await async_session.rollback()
            raise

    return transaction_maker


@pytest_asyncio.fixture(scope="function")
async def thread_service() -> ThreadService:
    return ThreadService(ThreadRepository())


@pytest_asyncio.fixture(scope="function")
async def message_service() -> MessageService:
    return MessageService(MessageRepository())


@pytest_asyncio.fixture(scope="function")
async def recipe_service() -> RecipeService:
    return RecipeService(RecipeRepository())


@pytest_asyncio.fixture(scope="function")
async def thread_cache_service(redis_client: FakeRedis) -> ThreadCacheService:
    return ThreadCacheService(redis_client, ttl=30)


@pytest_asyncio.fixture(scope="function")
async def message_cache_service(redis_client: FakeRedis) -> MessageCacheService:
    return MessageCacheService(redis_client, ttl=30)


@pytest_asyncio.fixture(scope="function")
async def recipe_cache_service(redis_client: FakeRedis) -> RecipeCacheService:
    return RecipeCacheService(redis_client, ttl=30)


@pytest_asyncio.fixture(scope="function")
async def stream_processor(
    redis_client: FakeRedis,
    db_transaction_maker: DBTransactionMaker,
    thread_cache_service: ThreadCacheService,
    message_cache_service: MessageCacheService,
    recipe_cache_service: RecipeCacheService,
    thread_service: ThreadService,
    message_service: MessageService,
    recipe_service: RecipeService,
) -> ChatSessionDataStreamProcessor:
    return ChatSessionDataStreamProcessor(
        stream="brekkie_ai_chat_session_test_stream",
        group="brekkie_ai_chat_session_test_group",
        consumer_name="brekkie_ai_chat_session_test_worker",
        redis_client=redis_client,
        db_transaction_maker=db_transaction_maker,
        thread_cache_service=thread_cache_service,
        message_cache_service=message_cache_service,
        recipe_cache_service=recipe_cache_service,
        thread_service=thread_service,
        message_service=message_service,
        recipe_service=recipe_service,
    )


class TestChatSessionDataStreamProcessor:
    """Integration tests for ChatSessionDataStreamProcessor using actual services"""

    @pytest.mark.asyncio
    async def test_ensure_group_exists_creates_new_group(
        self, stream_processor: ChatSessionDataStreamProcessor, redis_client: FakeRedis
    ) -> None:
        """Test that group creation works correctly"""
        await stream_processor._ensure_group_exists()

        # Verify group exists
        groups = await redis_client.xinfo_groups(stream_processor.stream)
        assert len(groups) == 1
        assert groups[0]["name"].decode() == stream_processor.group

    @pytest.mark.asyncio
    async def test_ensure_group_exists_handles_existing_group(
        self, stream_processor: ChatSessionDataStreamProcessor, redis_client: FakeRedis
    ) -> None:
        """Test that group creation handles existing groups gracefully"""
        # Create group first
        await stream_processor._ensure_group_exists()

        # Try to create again - should not raise exception
        await stream_processor._ensure_group_exists()

        # Verify only one group exists
        groups = await redis_client.xinfo_groups(stream_processor.stream)
        assert len(groups) == 1

    @pytest.mark.asyncio
    async def test_sync_cached_thread_with_db_creates_new_thread(
        self,
        stream_processor: ChatSessionDataStreamProcessor,
        thread_cache_service: ThreadCacheService,
        thread_service: ThreadService,
        async_session: AsyncSession,
    ) -> None:
        """Test syncing a new thread from cache to database"""
        user_id = "test-user-id"
        thread_id = "test-thread-id"

        # Create thread in cache
        thread = Thread(
            id=thread_id,
            user_id=user_id,
            created_at="2024-01-01T00:00:00+00:00",
            updated_at="2024-01-01T01:00:00+00:00",
            resumed_at="2024-01-01T02:00:00+00:00",
            is_empty=False,
            title="Test Thread",
            summary="Test Summary",
            error_message=None,
        )
        await thread_cache_service.set_thread(thread)

        # Sync thread
        await stream_processor._call_process_handler(
            ChatSessionDataStreamEntry(
                type=ChatSessionStreamEntryType.SYNC_CACHED_THREAD_WITH_DB,
                payload=SyncCachedThreadWithDbEntry(user_id=user_id, thread_id=thread_id),
            ),
            "test-entry-id",
        )

        # Verify thread exists in database
        db_thread = await thread_service.get_thread(async_session, thread_id)
        assert db_thread is not None
        assert db_thread.id == thread_id
        assert db_thread.user_id == user_id
        assert db_thread.title == "Test Thread"
        assert db_thread.summary == "Test Summary"
        assert db_thread.is_empty is False

    @pytest.mark.asyncio
    async def test_sync_thread_updates_existing_thread(
        self,
        stream_processor: ChatSessionDataStreamProcessor,
        thread_cache_service: ThreadCacheService,
        thread_service: ThreadService,
        async_session: AsyncSession,
    ) -> None:
        """Test syncing an existing thread with updated data"""
        user_id = "test-user-id"
        thread_id = "test-thread-id"

        # Create thread in database first
        db_thread_params = CreateThreadParams(
            user_id=user_id,
            id=thread_id,
            created_at=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 1, 1, 0, 0, tzinfo=timezone.utc),
            is_empty=True,
            title="Old Title",
            summary="Old Summary",
        )
        await thread_service.create_thread(async_session, db_thread_params)

        # Create updated thread in cache
        updated_thread = Thread(
            id=thread_id,
            user_id=user_id,
            created_at="2024-01-01T00:00:00+00:00",
            updated_at="2024-01-01T03:00:00+00:00",  # More recent
            resumed_at="2024-01-01T02:00:00+00:00",
            is_empty=False,
            title="Updated Title",
            summary="Updated Summary",
            error_message="Test Error",
        )
        await thread_cache_service.set_thread(updated_thread)

        # Sync thread
        await stream_processor._call_process_handler(
            ChatSessionDataStreamEntry(
                type=ChatSessionStreamEntryType.SYNC_CACHED_THREAD_WITH_DB,
                payload=SyncCachedThreadWithDbEntry(user_id=user_id, thread_id=thread_id),
            ),
            "test-entry-id",
        )

        # Verify thread was updated
        db_thread = await thread_service.get_thread(async_session, thread_id)
        assert db_thread is not None
        assert db_thread.title == "Updated Title"
        assert db_thread.summary == "Updated Summary"
        assert db_thread.is_empty is False
        assert db_thread.error_message == "Test Error"

    @pytest.mark.asyncio
    async def test_sync_thread_skips_older_cache_data(
        self,
        stream_processor: ChatSessionDataStreamProcessor,
        thread_cache_service: ThreadCacheService,
        thread_service: ThreadService,
        async_session: AsyncSession,
    ) -> None:
        """Test that sync skips when database is newer than cache"""
        user_id = "test-user-id"
        thread_id = "test-thread-id"

        # Create thread in database with newer timestamp
        db_thread_params = CreateThreadParams(
            user_id=user_id,
            id=thread_id,
            created_at=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 1, 3, 0, 0, tzinfo=timezone.utc),  # Newer
            is_empty=False,
            title="Database Title",
            summary="Database Summary",
        )
        await thread_service.create_thread(async_session, db_thread_params)

        # Create older thread in cache
        older_thread = Thread(
            id=thread_id,
            user_id=user_id,
            created_at="2024-01-01T00:00:00+00:00",
            updated_at="2024-01-01T01:00:00+00:00",  # Older
            resumed_at=None,
            is_empty=True,
            title="Cache Title",
            summary="Cache Summary",
            error_message=None,
        )
        await thread_cache_service.set_thread(older_thread)

        # Sync thread
        await stream_processor._call_process_handler(
            ChatSessionDataStreamEntry(
                type=ChatSessionStreamEntryType.SYNC_CACHED_THREAD_WITH_DB,
                payload=SyncCachedThreadWithDbEntry(user_id=user_id, thread_id=thread_id),
            ),
            "test-entry-id",
        )

        # Verify database thread was not updated
        db_thread = await thread_service.get_thread(async_session, thread_id)
        assert db_thread is not None
        assert db_thread.title == "Database Title"  # Should remain unchanged
        assert db_thread.summary == "Database Summary"

    @pytest.mark.asyncio
    async def test_sync_thread_skips_empty_thread(
        self,
        stream_processor: ChatSessionDataStreamProcessor,
        thread_cache_service: ThreadCacheService,
        thread_service: ThreadService,
        async_session: AsyncSession,
    ) -> None:
        """Test that sync skips when thread is empty"""
        user_id = "test-user-id"
        thread_id = "test-thread-id"

        # Create empty thread in cache
        empty_thread = Thread(
            id=thread_id,
            user_id=user_id,
            created_at="2024-01-01T00:00:00+00:00",
            updated_at="2024-01-01T01:00:00+00:00",
            resumed_at=None,
            is_empty=True,
            title="Empty Thread",
            summary="Empty Summary",
            error_message=None,
        )
        await thread_cache_service.set_thread(empty_thread)

        # Sync thread
        await stream_processor._call_process_handler(
            ChatSessionDataStreamEntry(
                type=ChatSessionStreamEntryType.SYNC_CACHED_THREAD_WITH_DB,
                payload=SyncCachedThreadWithDbEntry(user_id=user_id, thread_id=thread_id),
            ),
            "test-entry-id",
        )

        # Verify thread was not created
        db_thread = await thread_service.get_thread(async_session, thread_id)
        assert db_thread is None

    @pytest.mark.asyncio
    async def test_sync_message_creates_new_message(
        self,
        stream_processor: ChatSessionDataStreamProcessor,
        message_cache_service: MessageCacheService,
        message_service: MessageService,
        thread_service: ThreadService,
        async_session: AsyncSession,
    ) -> None:
        """Test syncing a new message from cache to database"""
        user_id = "test-user-id"
        thread_id = "test-thread-id"
        message_id = "test-message-id"

        # Create thread in database first (required for message)
        thread_params = CreateThreadParams(
            user_id=user_id,
            id=thread_id,
            created_at=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 1, 1, 0, 0, tzinfo=timezone.utc),
            is_empty=False,
            title="Test Thread",
            summary="Test Summary",
        )
        await thread_service.create_thread(async_session, thread_params)

        # Create message in cache
        message = Message(
            id=message_id,
            user_id=user_id,
            thread_id=thread_id,
            role=MessageRole.user,
            content_type=MessageContentType.text,
            parent_id=None,
            created_at="2024-01-01T02:00:00+00:00",
            updated_at="2024-01-01T02:00:00+00:00",
            model_name=None,
            tool_name=None,
            tool_input=None,
            tool_output=None,
            is_recipe_generation_started=False,
            is_recipe_generation_completed=False,
            ip_address="127.0.0.1",
            safety_guard_result=None,
            text_content="Hello, world!",
            input_tokens=10,
            output_tokens=None,
        )
        await message_cache_service.set_message(user_id, message)

        # Sync message
        await stream_processor._call_process_handler(
            ChatSessionDataStreamEntry(
                type=ChatSessionStreamEntryType.SYNC_CACHED_MESSAGE_WITH_DB,
                payload=SyncCachedMessageWithDbEntry(
                    user_id=user_id, thread_id=thread_id, message_id=message_id
                ),
            ),
            "test-entry-id",
        )

        # Verify message exists in database
        db_message = await message_service.get_message(async_session, message_id)
        assert db_message is not None
        assert db_message.id == message_id
        assert db_message.user_id == user_id
        assert db_message.thread_id == thread_id
        assert db_message.role == MessageRole.user
        assert db_message.content_type == MessageContentType.text
        assert db_message.text_content == "Hello, world!"
        assert db_message.input_tokens == 10

    @pytest.mark.asyncio
    async def test_sync_message_updates_existing_message(
        self,
        stream_processor: ChatSessionDataStreamProcessor,
        message_cache_service: MessageCacheService,
        message_service: MessageService,
        thread_service: ThreadService,
        async_session: AsyncSession,
    ) -> None:
        """Test syncing an existing message with updated data"""
        user_id = "test-user-id"
        thread_id = "test-thread-id"
        message_id = "test-message-id"

        # Create thread in database
        thread_params = CreateThreadParams(
            user_id=user_id,
            id=thread_id,
            created_at=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 1, 1, 0, 0, tzinfo=timezone.utc),
            is_empty=False,
            title="Test Thread",
            summary="Test Summary",
        )
        await thread_service.create_thread(async_session, thread_params)

        # Create message in database first
        db_message_params = CreateMessageParams(
            id=message_id,
            user_id=user_id,
            thread_id=thread_id,
            role=MessageRole.user,
            content_type=MessageContentType.text,
            created_at=datetime(2024, 1, 1, 2, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 1, 2, 0, 0, tzinfo=timezone.utc),
            text_content="Old content",
            input_tokens=5,
        )
        await message_service.create_message(async_session, db_message_params)

        # Create updated message in cache
        updated_message = Message(
            id=message_id,
            user_id=user_id,
            thread_id=thread_id,
            role=MessageRole.user,  # Keep same role since it can't be updated
            content_type=MessageContentType.text,  # Keep same content_type since it can't be updated
            parent_id=None,
            created_at="2024-01-01T02:00:00+00:00",
            updated_at="2024-01-01T04:00:00+00:00",  # Even more recent
            model_name="gpt-4",
            tool_name=None,
            tool_input=None,
            tool_output=None,
            is_recipe_generation_started=False,
            is_recipe_generation_completed=False,
            ip_address="127.0.0.1",
            safety_guard_result=None,
            text_content="Updated content",
            input_tokens=15,
            output_tokens=20,
        )
        await message_cache_service.set_message(user_id, updated_message)

        # Sync message
        await stream_processor._call_process_handler(
            ChatSessionDataStreamEntry(
                type=ChatSessionStreamEntryType.SYNC_CACHED_MESSAGE_WITH_DB,
                payload=SyncCachedMessageWithDbEntry(
                    user_id=user_id, thread_id=thread_id, message_id=message_id
                ),
            ),
            "test-entry-id",
        )

        # Verify message was updated
        db_message = await message_service.get_message(async_session, message_id)
        assert db_message is not None
        assert db_message.role == MessageRole.user  # Role should remain the same
        assert db_message.text_content == "Updated content"
        assert db_message.model_name == "gpt-4"
        assert db_message.input_tokens == 15
        assert db_message.output_tokens == 20
        assert db_message.model_name == "gpt-4"

    @pytest.mark.asyncio
    async def test_sync_message_with_parent_message(
        self,
        stream_processor: ChatSessionDataStreamProcessor,
        message_cache_service: MessageCacheService,
        message_service: MessageService,
        thread_service: ThreadService,
        async_session: AsyncSession,
    ) -> None:
        """Test syncing a message with a parent message"""
        user_id = "test-user-id"
        thread_id = "test-thread-id"
        parent_message_id = "parent-message-id"
        child_message_id = "child-message-id"

        # Create thread in database
        thread_params = CreateThreadParams(
            user_id=user_id,
            id=thread_id,
            created_at=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 1, 1, 0, 0, tzinfo=timezone.utc),
            is_empty=False,
            title="Test Thread",
            summary="Test Summary",
        )
        await thread_service.create_thread(async_session, thread_params)

        # Create parent message in database
        parent_message_params = CreateMessageParams(
            id=parent_message_id,
            user_id=user_id,
            thread_id=thread_id,
            role=MessageRole.user,
            content_type=MessageContentType.text,
            created_at=datetime(2024, 1, 1, 2, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 1, 2, 0, 0, tzinfo=timezone.utc),
            text_content="Parent message",
        )
        await message_service.create_message(async_session, parent_message_params)

        # Create child message in cache
        child_message = Message(
            id=child_message_id,
            user_id=user_id,
            thread_id=thread_id,
            role=MessageRole.assistant,
            content_type=MessageContentType.text,
            parent_id=parent_message_id,
            created_at="2024-01-01T03:00:00+00:00",
            updated_at="2024-01-01T03:00:00+00:00",
            model_name="gpt-4",
            tool_name=None,
            tool_input=None,
            tool_output=None,
            is_recipe_generation_started=False,
            is_recipe_generation_completed=False,
            ip_address="127.0.0.1",
            safety_guard_result=None,
            text_content="Child message",
            input_tokens=10,
            output_tokens=15,
        )
        await message_cache_service.set_message(user_id, child_message)

        # Sync child message
        await stream_processor._call_process_handler(
            ChatSessionDataStreamEntry(
                type=ChatSessionStreamEntryType.SYNC_CACHED_MESSAGE_WITH_DB,
                payload=SyncCachedMessageWithDbEntry(
                    user_id=user_id, thread_id=thread_id, message_id=child_message_id
                ),
            ),
            "test-entry-id",
        )

        # Verify child message was created with correct parent
        db_message = await message_service.get_message(async_session, child_message_id)
        assert db_message is not None
        assert db_message.parent_id == parent_message_id
        assert db_message.text_content == "Child message"

    @pytest.mark.asyncio
    async def test_sync_message_retries_when_parent_missing(
        self,
        stream_processor: ChatSessionDataStreamProcessor,
        message_cache_service: MessageCacheService,
        thread_service: ThreadService,
        async_session: AsyncSession,
    ) -> None:
        """Test that sync retries when parent message doesn't exist"""
        user_id = "test-user-id"
        thread_id = "test-thread-id"
        message_id = "test-message-id"

        # Create thread in database
        thread_params = CreateThreadParams(
            user_id=user_id,
            id=thread_id,
            created_at=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 1, 1, 0, 0, tzinfo=timezone.utc),
            is_empty=False,
            title="Test Thread",
            summary="Test Summary",
        )
        await thread_service.create_thread(async_session, thread_params)

        # Create message in cache with non-existent parent
        message = Message(
            id=message_id,
            user_id=user_id,
            thread_id=thread_id,
            role=MessageRole.assistant,
            content_type=MessageContentType.text,
            parent_id="non-existent-parent",
            created_at="2024-01-01T02:00:00+00:00",
            updated_at="2024-01-01T02:00:00+00:00",
            model_name="gpt-4",
            tool_name=None,
            tool_input=None,
            tool_output=None,
            is_recipe_generation_started=False,
            is_recipe_generation_completed=False,
            ip_address="127.0.0.1",
            safety_guard_result=None,
            text_content="Test message",
            input_tokens=10,
            output_tokens=15,
        )
        await message_cache_service.set_message(user_id, message)

        # Sync should raise RetryException
        with pytest.raises(
            RetryException, match="Parent message non-existent-parent does not exist in database"
        ):
            await stream_processor._call_process_handler(
                ChatSessionDataStreamEntry(
                    type=ChatSessionStreamEntryType.SYNC_CACHED_MESSAGE_WITH_DB,
                    payload=SyncCachedMessageWithDbEntry(
                        user_id=user_id, thread_id=thread_id, message_id=message_id
                    ),
                ),
                "test-entry-id",
            )

    @pytest.mark.asyncio
    async def test_sync_recipe_creates_new_recipe(
        self,
        stream_processor: ChatSessionDataStreamProcessor,
        recipe_cache_service: RecipeCacheService,
        recipe_service: RecipeService,
        thread_service: ThreadService,
        async_session: AsyncSession,
    ) -> None:
        """Test syncing a new recipe from cache to database"""
        user_id = "test-user-id"
        thread_id = "test-thread-id"
        recipe_id = "test-recipe-id"

        # Create thread in database first (required for recipe)
        thread_params = CreateThreadParams(
            user_id=user_id,
            id=thread_id,
            created_at=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 1, 1, 0, 0, tzinfo=timezone.utc),
            is_empty=False,
            title="Test Thread",
            summary="Test Summary",
        )
        await thread_service.create_thread(async_session, thread_params)

        # Create recipe in cache
        recipe = UserRecipe(
            id=recipe_id,
            user_id=user_id,
            thread_id=thread_id,
            created_at="2024-01-01T02:00:00+00:00",
            updated_at="2024-01-01T02:00:00+00:00",
            name="Test Recipe",
            description="A test recipe",
            ingredients=[
                RecipeIngredient(name="ingredient1", quantity="1", unit="cup"),
                RecipeIngredient(name="ingredient2", quantity="2", unit="tbsp"),
            ],
            instructions=[
                RecipeInstruction(title="step1", description="First step description"),
                RecipeInstruction(title="step2", description="Second step description"),
            ],
            categories=[
                RecipeCategory(name="breakfast"),
                RecipeCategory(name="quick"),
            ],
            prep_time_minutes=10,
            cook_time_minutes=20,
            servings="2",
        )
        await recipe_cache_service.set_recipe(recipe)

        # Sync recipe
        await stream_processor.sync_cached_recipe_with_db(
            SyncCachedRecipeWithDbEntry(user_id=user_id, thread_id=thread_id, recipe_id=recipe_id)
        )

        # Verify recipe exists in database
        db_recipe = await recipe_service.get_recipe(async_session, recipe_id)
        assert db_recipe is not None
        assert db_recipe.id == recipe_id
        assert db_recipe.user_id == user_id
        assert db_recipe.thread_id == thread_id
        assert db_recipe.name == "Test Recipe"
        assert db_recipe.description == "A test recipe"
        assert db_recipe.ingredients is not None
        assert len(db_recipe.ingredients) == 2
        assert db_recipe.ingredients[0].name == "ingredient1"
        assert db_recipe.ingredients[1].name == "ingredient2"
        assert db_recipe.instructions is not None
        assert len(db_recipe.instructions) == 2
        assert db_recipe.instructions[0].title == "step1"
        assert db_recipe.instructions[1].title == "step2"
        assert db_recipe.categories is not None
        assert len(db_recipe.categories) == 2
        assert db_recipe.categories[0].name == "breakfast"
        assert db_recipe.categories[1].name == "quick"

    @pytest.mark.asyncio
    async def test_sync_recipe_updates_existing_recipe(
        self,
        stream_processor: ChatSessionDataStreamProcessor,
        recipe_cache_service: RecipeCacheService,
        recipe_service: RecipeService,
        thread_service: ThreadService,
        async_session: AsyncSession,
    ) -> None:
        """Test syncing an existing recipe with updated data"""
        user_id = "test-user-id"
        thread_id = "test-thread-id"
        recipe_id = "test-recipe-id"

        # Create thread in database
        thread_params = CreateThreadParams(
            user_id=user_id,
            id=thread_id,
            created_at=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 1, 1, 0, 0, tzinfo=timezone.utc),
            is_empty=False,
            title="Test Thread",
            summary="Test Summary",
        )
        await thread_service.create_thread(async_session, thread_params)

        # Create recipe in database first
        db_recipe_params = CreateRecipeParams(
            id=recipe_id,
            user_id=user_id,
            thread_id=thread_id,
            created_at=datetime(2024, 1, 1, 2, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 1, 2, 0, 0, tzinfo=timezone.utc),
            name="Old Recipe",
            description="Old description",
            ingredients=[
                RecipeIngredient(name="old_ingredient", quantity="1", unit="piece"),
            ],
            instructions=[
                RecipeInstruction(title="old_step", description="Old step description"),
            ],
            categories=[
                RecipeCategory(name="old_category"),
            ],
        )
        await recipe_service.create_recipe(async_session, db_recipe_params)

        # Create updated recipe in cache
        updated_recipe = UserRecipe(
            id=recipe_id,
            user_id=user_id,
            thread_id=thread_id,
            created_at="2024-01-01T02:00:00+00:00",
            updated_at="2024-01-01T03:00:00+00:00",  # More recent
            name="Updated Recipe",
            description="Updated description",
            ingredients=[
                RecipeIngredient(name="new_ingredient1", quantity="3", unit="cups"),
                RecipeIngredient(name="new_ingredient2", quantity="4", unit="tbsp"),
            ],
            instructions=[
                RecipeInstruction(title="new_step1", description="New first step description"),
                RecipeInstruction(title="new_step2", description="New second step description"),
            ],
            categories=[
                RecipeCategory(name="new_category1"),
                RecipeCategory(name="new_category2"),
            ],
            prep_time_minutes=15,
            cook_time_minutes=25,
            servings="4",
        )
        await recipe_cache_service.set_recipe(updated_recipe)

        # Sync recipe
        await stream_processor.sync_cached_recipe_with_db(
            SyncCachedRecipeWithDbEntry(user_id=user_id, thread_id=thread_id, recipe_id=recipe_id)
        )

        # Verify recipe was updated
        db_recipe = await recipe_service.get_recipe(async_session, recipe_id)
        assert db_recipe is not None
        assert db_recipe.name == "Updated Recipe"
        assert db_recipe.description == "Updated description"
        assert db_recipe.ingredients is not None
        assert len(db_recipe.ingredients) == 2
        assert db_recipe.ingredients[0].name == "new_ingredient1"
        assert db_recipe.ingredients[1].name == "new_ingredient2"
        assert db_recipe.instructions is not None
        assert len(db_recipe.instructions) == 2
        assert db_recipe.instructions[0].title == "new_step1"
        assert db_recipe.instructions[1].title == "new_step2"
        assert db_recipe.categories is not None
        assert len(db_recipe.categories) == 2
        assert db_recipe.categories[0].name == "new_category1"
        assert db_recipe.categories[1].name == "new_category2"

    @pytest.mark.asyncio
    async def test_process_sync_cached_thread_with_db_entry(
        self,
        stream_processor: ChatSessionDataStreamProcessor,
        thread_cache_service: ThreadCacheService,
        thread_service: ThreadService,
        async_session: AsyncSession,
    ) -> None:
        """Test handling thread type stream entries"""
        user_id = "test-user-id"
        thread_id = "test-thread-id"

        # Create thread in cache
        thread = Thread(
            id=thread_id,
            user_id=user_id,
            created_at="2024-01-01T00:00:00+00:00",
            updated_at="2024-01-01T01:00:00+00:00",
            resumed_at=None,
            is_empty=False,
            title="Test Thread",
            summary="Test Summary",
            error_message=None,
        )
        await thread_cache_service.set_thread(thread)

        # Create stream entry
        raw_data = [
            ("type", "sync_cached_thread_with_db"),
            ("payload", f'{{"user_id": "{user_id}", "thread_id": "{thread_id}"}}'),
        ]

        # Handle entry
        await stream_processor._process_entry("test-entry-id", raw_data)

        # Verify thread was synced to database
        db_thread = await thread_service.get_thread(async_session, thread_id)
        assert db_thread is not None
        assert db_thread.id == thread_id
        assert db_thread.user_id == user_id

    @pytest.mark.asyncio
    async def test_process_sync_cached_message_with_db_entry(
        self,
        stream_processor: ChatSessionDataStreamProcessor,
        message_cache_service: MessageCacheService,
        message_service: MessageService,
        thread_service: ThreadService,
        async_session: AsyncSession,
    ) -> None:
        """Test handling message type stream entries"""
        user_id = "test-user-id"
        thread_id = "test-thread-id"
        message_id = "test-message-id"

        # Create thread in database
        thread_params = CreateThreadParams(
            user_id=user_id,
            id=thread_id,
            created_at=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 1, 1, 0, 0, tzinfo=timezone.utc),
            is_empty=False,
            title="Test Thread",
            summary="Test Summary",
        )
        await thread_service.create_thread(async_session, thread_params)

        # Create message in cache
        message = Message(
            id=message_id,
            user_id=user_id,
            thread_id=thread_id,
            role=MessageRole.user,
            content_type=MessageContentType.text,
            parent_id=None,
            created_at="2024-01-01T02:00:00+00:00",
            updated_at="2024-01-01T02:00:00+00:00",
            model_name=None,
            tool_name=None,
            tool_input=None,
            tool_output=None,
            is_recipe_generation_started=False,
            is_recipe_generation_completed=False,
            ip_address="127.0.0.1",
            safety_guard_result=None,
            text_content="Test message",
            input_tokens=10,
            output_tokens=None,
        )
        await message_cache_service.set_message(user_id, message)

        # Create stream entry
        raw_data = [
            ("type", "sync_cached_message_with_db"),
            (
                "payload",
                f'{{"user_id": "{user_id}", "thread_id": "{thread_id}", "message_id": "{message_id}"}}',
            ),
        ]

        # Handle entry
        await stream_processor._process_entry("test-entry-id", raw_data)

        # Verify message was synced to database
        db_message = await message_service.get_message(async_session, message_id)
        assert db_message is not None
        assert db_message.id == message_id
        assert db_message.user_id == user_id
        assert db_message.thread_id == thread_id

    @pytest.mark.asyncio
    async def test_process_sync_cached_recipe_with_db_entry(
        self,
        stream_processor: ChatSessionDataStreamProcessor,
        recipe_cache_service: RecipeCacheService,
        recipe_service: RecipeService,
        thread_service: ThreadService,
        async_session: AsyncSession,
    ) -> None:
        """Test handling recipe type stream entries"""
        user_id = "test-user-id"
        thread_id = "test-thread-id"
        recipe_id = "test-recipe-id"

        # Create thread in database
        thread_params = CreateThreadParams(
            user_id=user_id,
            id=thread_id,
            created_at=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 1, 1, 0, 0, tzinfo=timezone.utc),
            is_empty=False,
            title="Test Thread",
            summary="Test Summary",
        )
        await thread_service.create_thread(async_session, thread_params)

        # Create recipe in cache
        recipe = UserRecipe(
            id=recipe_id,
            user_id=user_id,
            thread_id=thread_id,
            created_at="2024-01-01T02:00:00+00:00",
            updated_at="2024-01-01T02:00:00+00:00",
            name="Test Recipe",
            description="A test recipe",
            ingredients=[
                RecipeIngredient(name="ingredient1", quantity="1", unit="cup"),
                RecipeIngredient(name="ingredient2", quantity="2", unit="tbsp"),
            ],
            instructions=[
                RecipeInstruction(title="step1", description="First step description"),
                RecipeInstruction(title="step2", description="Second step description"),
            ],
            categories=[
                RecipeCategory(name="breakfast"),
                RecipeCategory(name="quick"),
            ],
            prep_time_minutes=10,
            cook_time_minutes=20,
            servings="2",
        )
        await recipe_cache_service.set_recipe(recipe)

        # Create stream entry
        raw_data = [
            ("type", "sync_cached_recipe_with_db"),
            (
                "payload",
                f'{{"user_id": "{user_id}", "thread_id": "{thread_id}", "recipe_id": "{recipe_id}"}}',
            ),
        ]

        # Handle entry
        await stream_processor._process_entry("test-entry-id", raw_data)

        # Verify recipe was synced to database
        db_recipe = await recipe_service.get_recipe(async_session, recipe_id)
        assert db_recipe is not None
        assert db_recipe.id == recipe_id
        assert db_recipe.user_id == user_id
        assert db_recipe.thread_id == thread_id

    @pytest.mark.asyncio
    async def test_process_invalid_entry_type(
        self, stream_processor: ChatSessionDataStreamProcessor
    ) -> None:
        """Test handling invalid stream entry types"""
        raw_data = [
            ("type", "invalid_type"),
            ("payload", '{"user_id": "test", "thread_id": "test"}'),
        ]

        # Should not raise exception, just log warning
        await stream_processor._process_entry("test-entry-id", raw_data)

    @pytest.mark.asyncio
    async def test_process_missing_entry_payload(
        self, stream_processor: ChatSessionDataStreamProcessor
    ) -> None:
        """Test handling stream entries with missing payload"""
        raw_data = [
            ("type", "sync_cached_thread_with_db"),
            # Missing payload
        ]

        # Should not raise exception, just log warning
        await stream_processor._process_entry("test-entry-id", raw_data)

    @pytest.mark.asyncio
    async def test_process_missing_entry_type(
        self, stream_processor: ChatSessionDataStreamProcessor
    ) -> None:
        """Test handling stream entries with missing type"""
        raw_data = [
            ("payload", '{"user_id": "test", "thread_id": "test"}'),
            # Missing type
        ]

        # Should not raise exception, just log warning
        await stream_processor._process_entry("test-entry-id", raw_data)

    @pytest.mark.asyncio
    async def test_stop_sync_signal_handling(
        self, stream_processor: ChatSessionDataStreamProcessor
    ) -> None:
        """Test that stop sync signal handling works"""
        # Initially should run
        assert stream_processor.should_run is True

        # Simulate SIGTERM
        stream_processor.stop(15, None)
        assert stream_processor.should_run is False

        # Reset and test SIGINT
        stream_processor.should_run = True
        stream_processor.stop(2, None)
        assert stream_processor.should_run is False

    @pytest.mark.asyncio
    async def test_sync_thread_missing_from_cache(
        self, stream_processor: ChatSessionDataStreamProcessor
    ) -> None:
        """Test syncing thread that doesn't exist in cache"""
        user_id = "test-user-id"
        thread_id = "non-existent-thread-id"

        # Should not raise exception, just log info
        await stream_processor._call_process_handler(
            ChatSessionDataStreamEntry(
                type=ChatSessionStreamEntryType.SYNC_CACHED_THREAD_WITH_DB,
                payload=SyncCachedThreadWithDbEntry(user_id=user_id, thread_id=thread_id),
            ),
            "test-entry-id",
        )

    @pytest.mark.asyncio
    async def test_sync_message_missing_from_cache(
        self, stream_processor: ChatSessionDataStreamProcessor
    ) -> None:
        """Test syncing message that doesn't exist in cache"""
        user_id = "test-user-id"
        thread_id = "test-thread-id"
        message_id = "non-existent-message-id"

        # Should not raise exception, just log info
        await stream_processor._call_process_handler(
            ChatSessionDataStreamEntry(
                type=ChatSessionStreamEntryType.SYNC_CACHED_MESSAGE_WITH_DB,
                payload=SyncCachedMessageWithDbEntry(
                    user_id=user_id, thread_id=thread_id, message_id=message_id
                ),
            ),
            "test-entry-id",
        )

    @pytest.mark.asyncio
    async def test_sync_recipe_missing_from_cache(
        self, stream_processor: ChatSessionDataStreamProcessor
    ) -> None:
        """Test syncing recipe that doesn't exist in cache"""
        user_id = "test-user-id"
        thread_id = "test-thread-id"
        recipe_id = "non-existent-recipe-id"

        # Should not raise exception, just log info
        await stream_processor._call_process_handler(
            ChatSessionDataStreamEntry(
                type=ChatSessionStreamEntryType.SYNC_CACHED_RECIPE_WITH_DB,
                payload=SyncCachedRecipeWithDbEntry(
                    user_id=user_id, thread_id=thread_id, recipe_id=recipe_id
                ),
            ),
            "test-entry-id",
        )

    @pytest.mark.asyncio
    async def test_sync_message_thread_not_in_database(
        self,
        stream_processor: ChatSessionDataStreamProcessor,
        message_cache_service: MessageCacheService,
    ) -> None:
        """Test syncing message when thread doesn't exist in database"""
        user_id = "test-user-id"
        thread_id = "non-existent-thread-id"
        message_id = "test-message-id"

        # Create message in cache
        message = Message(
            id=message_id,
            user_id=user_id,
            thread_id=thread_id,
            role=MessageRole.user,
            content_type=MessageContentType.text,
            parent_id=None,
            created_at="2024-01-01T02:00:00+00:00",
            updated_at="2024-01-01T02:00:00+00:00",
            model_name=None,
            tool_name=None,
            tool_input=None,
            tool_output=None,
            is_recipe_generation_started=False,
            is_recipe_generation_completed=False,
            ip_address="127.0.0.1",
            safety_guard_result=None,
            text_content="Test message",
            input_tokens=10,
            output_tokens=None,
        )
        await message_cache_service.set_message(user_id, message)

        # Should raise RetryException
        with pytest.raises(
            RetryException, match="Thread non-existent-thread-id does not exist in database"
        ):
            await stream_processor._call_process_handler(
                ChatSessionDataStreamEntry(
                    type=ChatSessionStreamEntryType.SYNC_CACHED_MESSAGE_WITH_DB,
                    payload=SyncCachedMessageWithDbEntry(
                        user_id=user_id, thread_id=thread_id, message_id=message_id
                    ),
                ),
                "test-entry-id",
            )

    @pytest.mark.asyncio
    async def test_sync_recipe_thread_not_in_database(
        self,
        stream_processor: ChatSessionDataStreamProcessor,
        recipe_cache_service: RecipeCacheService,
    ) -> None:
        """Test syncing a recipe when the thread doesn't exist in database"""
        user_id = "non-existent-user-id"
        thread_id = "non-existent-thread-id"
        recipe_id = "test-recipe-id"

        # Create recipe in cache
        recipe = UserRecipe(
            id=recipe_id,
            user_id=user_id,
            thread_id=thread_id,
            created_at="2024-01-01T02:00:00+00:00",
            updated_at="2024-01-01T02:00:00+00:00",
            name="Test Recipe",
            description="A test recipe",
            ingredients=[
                RecipeIngredient(name="ingredient1", quantity="1", unit="cup"),
            ],
            instructions=[
                RecipeInstruction(title="step1", description="First step description"),
            ],
            categories=[
                RecipeCategory(name="breakfast"),
            ],
        )
        await recipe_cache_service.set_recipe(recipe)

        # Sync recipe should raise RetryException
        with pytest.raises(RetryException, match=f"Thread {thread_id} does not exist in database"):
            await stream_processor._call_process_handler(
                ChatSessionDataStreamEntry(
                    type=ChatSessionStreamEntryType.SYNC_CACHED_RECIPE_WITH_DB,
                    payload=SyncCachedRecipeWithDbEntry(
                        user_id=user_id, thread_id=thread_id, recipe_id=recipe_id
                    ),
                ),
                "test-entry-id",
            )

    @pytest.mark.asyncio
    async def test_process_multiple_thread_entries(
        self,
        stream_processor: ChatSessionDataStreamProcessor,
        thread_cache_service: ThreadCacheService,
        thread_service: ThreadService,
        async_session: AsyncSession,
    ) -> None:
        """Test handling multiple thread entries in sequence"""
        user_id = "test-user-id"
        thread_ids = ["thread-1", "thread-2", "thread-3"]

        # Create threads in cache
        for i, thread_id in enumerate(thread_ids):
            thread = Thread(
                id=thread_id,
                user_id=user_id,
                created_at="2024-01-01T00:00:00+00:00",
                updated_at=f"2024-01-01T0{i+1}:00:00+00:00",
                resumed_at=None,
                is_empty=False,
                title=f"Test Thread {i+1}",
                summary=f"Test Summary {i+1}",
                error_message=None,
            )
            await thread_cache_service.set_thread(thread)

        # Process multiple entries
        for i, thread_id in enumerate(thread_ids):
            raw_data = [
                ("type", "sync_cached_thread_with_db"),
                ("payload", f'{{"user_id": "{user_id}", "thread_id": "{thread_id}"}}'),
            ]
            await stream_processor._process_entry(f"entry-{i}", raw_data)

        # Verify all threads were synced to database
        for thread_id in thread_ids:
            db_thread = await thread_service.get_thread(async_session, thread_id)
            assert db_thread is not None
            assert db_thread.id == thread_id
            assert db_thread.user_id == user_id

    @pytest.mark.asyncio
    async def test_process_multiple_message_entries(
        self,
        stream_processor: ChatSessionDataStreamProcessor,
        message_cache_service: MessageCacheService,
        message_service: MessageService,
        thread_service: ThreadService,
        async_session: AsyncSession,
    ) -> None:
        """Test handling multiple message entries in sequence"""
        user_id = "test-user-id"
        thread_id = "test-thread-id"
        message_ids = ["message-1", "message-2", "message-3"]

        # Create thread in database
        thread_params = CreateThreadParams(
            user_id=user_id,
            id=thread_id,
            created_at=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 1, 1, 0, 0, tzinfo=timezone.utc),
            is_empty=False,
            title="Test Thread",
            summary="Test Summary",
        )
        await thread_service.create_thread(async_session, thread_params)

        # Create messages in cache
        for i, message_id in enumerate(message_ids):
            message = Message(
                id=message_id,
                user_id=user_id,
                thread_id=thread_id,
                role=MessageRole.user,
                content_type=MessageContentType.text,
                parent_id=None,
                created_at="2024-01-01T02:00:00+00:00",
                updated_at=f"2024-01-01T0{i+2}:00:00+00:00",
                model_name=None,
                tool_name=None,
                tool_input=None,
                tool_output=None,
                is_recipe_generation_started=False,
                is_recipe_generation_completed=False,
                ip_address="127.0.0.1",
                safety_guard_result=None,
                text_content=f"Test message {i+1}",
                input_tokens=10 + i,
                output_tokens=None,
            )
            await message_cache_service.set_message(user_id, message)

        # Process multiple entries
        for i, message_id in enumerate(message_ids):
            raw_data = [
                ("type", "sync_cached_message_with_db"),
                (
                    "payload",
                    f'{{"user_id": "{user_id}", "thread_id": "{thread_id}", "message_id": "{message_id}"}}',
                ),
            ]
            await stream_processor._process_entry(f"entry-{i}", raw_data)

        # Verify all messages were synced to database
        for i, message_id in enumerate(message_ids):
            db_message = await message_service.get_message(async_session, message_id)
            assert db_message is not None
            assert db_message.id == message_id
            assert db_message.user_id == user_id
            assert db_message.text_content == f"Test message {i+1}"

    @pytest.mark.asyncio
    async def test_process_multiple_recipe_entries(
        self,
        stream_processor: ChatSessionDataStreamProcessor,
        recipe_cache_service: RecipeCacheService,
        recipe_service: RecipeService,
        thread_service: ThreadService,
        async_session: AsyncSession,
    ) -> None:
        """Test handling multiple recipe entries in sequence"""
        user_id = "test-user-id"
        thread_id = "test-thread-id"
        recipe_ids = ["recipe-1", "recipe-2", "recipe-3"]

        # Create thread in database
        thread_params = CreateThreadParams(
            user_id=user_id,
            id=thread_id,
            created_at=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 1, 1, 0, 0, tzinfo=timezone.utc),
            is_empty=False,
            title="Test Thread",
            summary="Test Summary",
        )
        await thread_service.create_thread(async_session, thread_params)

        # Create recipes in cache
        for i, recipe_id in enumerate(recipe_ids):
            recipe = UserRecipe(
                id=recipe_id,
                user_id=user_id,
                thread_id=thread_id,
                created_at="2024-01-01T02:00:00+00:00",
                updated_at=f"2024-01-01T0{i+2}:00:00+00:00",
                name=f"Test Recipe {i+1}",
                description=f"A test recipe {i+1}",
                ingredients=[
                    RecipeIngredient(name=f"ingredient{i+1}", quantity="1", unit="cup"),
                ],
                instructions=[
                    RecipeInstruction(title=f"step{i+1}", description=f"Step {i+1} description"),
                ],
                categories=[
                    RecipeCategory(name=f"category{i+1}"),
                ],
                prep_time_minutes=10 + i,
                cook_time_minutes=20 + i,
                servings=str(i + 1),
            )
            await recipe_cache_service.set_recipe(recipe)

        # Process multiple entries
        for i, recipe_id in enumerate(recipe_ids):
            raw_data = [
                ("type", "sync_cached_recipe_with_db"),
                (
                    "payload",
                    f'{{"user_id": "{user_id}", "thread_id": "{thread_id}", "recipe_id": "{recipe_id}"}}',
                ),
            ]
            await stream_processor._process_entry(f"entry-{i}", raw_data)

        # Verify all recipes were synced to database
        for i, recipe_id in enumerate(recipe_ids):
            db_recipe = await recipe_service.get_recipe(async_session, recipe_id)
            assert db_recipe is not None
            assert db_recipe.id == recipe_id
            assert db_recipe.user_id == user_id
            assert db_recipe.name == f"Test Recipe {i+1}"

    @pytest.mark.asyncio
    async def test_retry_on_transient_error(
        self,
        stream_processor: ChatSessionDataStreamProcessor,
        thread_cache_service: ThreadCacheService,
        thread_service: ThreadService,
        async_session: AsyncSession,
    ) -> None:
        """Test that RetryException is raised when sync fails"""
        user_id = "test-user-id"
        thread_id = "test-thread-id"

        # Create thread in cache
        thread = Thread(
            id=thread_id,
            user_id=user_id,
            created_at="2024-01-01T00:00:00+00:00",
            updated_at="2024-01-01T01:00:00+00:00",
            resumed_at=None,
            is_empty=False,
            title="Test Thread",
            summary="Test Summary",
            error_message=None,
        )
        await thread_cache_service.set_thread(thread)

        # Mock the sync_thread method to raise RetryException
        original_sync_thread = stream_processor._call_process_handler
        call_count = 0

        async def mock_sync_thread(entry: ChatSessionDataStreamEntry, msg_id: str) -> None:
            nonlocal call_count
            call_count += 1
            if call_count < 3:  # Fail first 2 times, succeed on 3rd
                raise RetryException("Transient error")
            else:
                # On third call, actually sync the thread
                await original_sync_thread(
                    ChatSessionDataStreamEntry(
                        type=ChatSessionStreamEntryType.SYNC_CACHED_THREAD_WITH_DB,
                        payload=SyncCachedThreadWithDbEntry(user_id=user_id, thread_id=thread_id),
                    ),
                    "test-entry-id",
                )

        stream_processor._call_process_handler = mock_sync_thread

        try:
            # First call should raise RetryException
            with pytest.raises(RetryException, match="Transient error"):
                await stream_processor._call_process_handler(
                    ChatSessionDataStreamEntry(
                        type=ChatSessionStreamEntryType.SYNC_CACHED_THREAD_WITH_DB,
                        payload=SyncCachedThreadWithDbEntry(user_id=user_id, thread_id=thread_id),
                    ),
                    "test-entry-id",
                )

            # Second call should raise RetryException
            with pytest.raises(RetryException, match="Transient error"):
                await stream_processor._call_process_handler(
                    ChatSessionDataStreamEntry(
                        type=ChatSessionStreamEntryType.SYNC_CACHED_THREAD_WITH_DB,
                        payload=SyncCachedThreadWithDbEntry(user_id=user_id, thread_id=thread_id),
                    ),
                    "test-entry-id",
                )

            # Third call should succeed
            await stream_processor._call_process_handler(
                ChatSessionDataStreamEntry(
                    type=ChatSessionStreamEntryType.SYNC_CACHED_THREAD_WITH_DB,
                    payload=SyncCachedThreadWithDbEntry(user_id=user_id, thread_id=thread_id),
                ),
                "test-entry-id",
            )

            assert call_count == 3

            # Verify thread was synced to database
            db_thread = await thread_service.get_thread(async_session, thread_id)
            assert db_thread is not None
            assert db_thread.id == thread_id
        finally:
            # Restore original method
            stream_processor._call_process_handler = original_sync_thread

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(
        self,
        stream_processor: ChatSessionDataStreamProcessor,
        thread_cache_service: ThreadCacheService,
    ) -> None:
        """Test that RetryException is raised consistently when sync always fails"""
        user_id = "test-user-id"
        thread_id = "test-thread-id"

        # Create thread in cache
        thread = Thread(
            id=thread_id,
            user_id=user_id,
            created_at="2024-01-01T00:00:00+00:00",
            updated_at="2024-01-01T01:00:00+00:00",
            resumed_at=None,
            is_empty=False,
            title="Test Thread",
            summary="Test Summary",
            error_message=None,
        )
        await thread_cache_service.set_thread(thread)

        # Mock the sync_thread method to always raise RetryException
        original_sync_thread = stream_processor._call_process_handler

        async def mock_sync_thread(entry: ChatSessionDataStreamEntry, msg_id: str) -> None:
            raise RetryException("Persistent error")

        stream_processor._call_process_handler = mock_sync_thread

        try:
            # Call multiple times - each should raise RetryException
            for i in range(6):
                with pytest.raises(RetryException, match="Persistent error"):
                    await stream_processor._call_process_handler(
                        ChatSessionDataStreamEntry(
                            type=ChatSessionStreamEntryType.SYNC_CACHED_THREAD_WITH_DB,
                            payload=SyncCachedThreadWithDbEntry(
                                user_id=user_id, thread_id=thread_id
                            ),
                        ),
                        "test-entry-id",
                    )
        finally:
            # Restore original method
            stream_processor._call_process_handler = original_sync_thread

    @pytest.mark.asyncio
    async def test_acknowledge_successful_processing(
        self,
        stream_processor: ChatSessionDataStreamProcessor,
        thread_cache_service: ThreadCacheService,
        thread_service: ThreadService,
        async_session: AsyncSession,
    ) -> None:
        """Test that successful processing syncs data to database"""
        user_id = "test-user-id"
        thread_id = "test-thread-id"

        # Create thread in cache
        thread = Thread(
            id=thread_id,
            user_id=user_id,
            created_at="2024-01-01T00:00:00+00:00",
            updated_at="2024-01-01T01:00:00+00:00",
            resumed_at=None,
            is_empty=False,
            title="Test Thread",
            summary="Test Summary",
            error_message=None,
        )
        await thread_cache_service.set_thread(thread)

        # Create stream entry
        raw_data = [
            ("type", "sync_cached_thread_with_db"),
            ("payload", f'{{"user_id": "{user_id}", "thread_id": "{thread_id}"}}'),
        ]

        # Process the entry
        await stream_processor._process_entry("ack-test-entry", raw_data)

        # Verify thread was synced to database
        db_thread = await thread_service.get_thread(async_session, thread_id)
        assert db_thread is not None
        assert db_thread.id == thread_id
        assert db_thread.user_id == user_id

    @pytest.mark.asyncio
    async def test_acknowledge_invalid_entry(
        self,
        stream_processor: ChatSessionDataStreamProcessor,
    ) -> None:
        """Test that invalid entries are handled gracefully"""
        # Create invalid stream entry (missing type)
        raw_data = [
            ("payload", '{"user_id": "test", "thread_id": "test"}'),
        ]

        # Process the invalid entry - should not raise an exception
        await stream_processor._process_entry("invalid-entry", raw_data)

        # Test with missing payload
        raw_data_missing_payload = [
            ("type", "sync_cached_thread_with_db"),
        ]

        await stream_processor._process_entry("missing-payload-entry", raw_data_missing_payload)

        # Test with unknown type
        raw_data_unknown_type = [
            ("type", "unknown"),
            ("payload", '{"user_id": "test", "thread_id": "test"}'),
        ]

        await stream_processor._process_entry("unknown-type-entry", raw_data_unknown_type)

    @pytest.mark.asyncio
    async def test_mixed_entry_types_in_stream(
        self,
        stream_processor: ChatSessionDataStreamProcessor,
        thread_cache_service: ThreadCacheService,
        message_cache_service: MessageCacheService,
        recipe_cache_service: RecipeCacheService,
        thread_service: ThreadService,
        message_service: MessageService,
        recipe_service: RecipeService,
        async_session: AsyncSession,
    ) -> None:
        """Test handling mixed entry types in the same stream"""
        user_id = "test-user-id"
        thread_id = "test-thread-id"
        message_id = "test-message-id"
        recipe_id = "test-recipe-id"

        # Create thread in cache
        thread = Thread(
            id=thread_id,
            user_id=user_id,
            created_at="2024-01-01T00:00:00+00:00",
            updated_at="2024-01-01T01:00:00+00:00",
            resumed_at=None,
            is_empty=False,
            title="Test Thread",
            summary="Test Summary",
            error_message=None,
        )
        await thread_cache_service.set_thread(thread)

        # Create message in cache
        message = Message(
            id=message_id,
            user_id=user_id,
            thread_id=thread_id,
            role=MessageRole.user,
            content_type=MessageContentType.text,
            parent_id=None,
            created_at="2024-01-01T02:00:00+00:00",
            updated_at="2024-01-01T02:00:00+00:00",
            model_name=None,
            tool_name=None,
            tool_input=None,
            tool_output=None,
            is_recipe_generation_started=False,
            is_recipe_generation_completed=False,
            ip_address="127.0.0.1",
            safety_guard_result=None,
            text_content="Test message",
            input_tokens=10,
            output_tokens=None,
        )
        await message_cache_service.set_message(user_id, message)

        # Create recipe in cache
        recipe = UserRecipe(
            id=recipe_id,
            user_id=user_id,
            thread_id=thread_id,
            created_at="2024-01-01T02:00:00+00:00",
            updated_at="2024-01-01T02:00:00+00:00",
            name="Test Recipe",
            description="A test recipe",
            ingredients=[
                RecipeIngredient(name="ingredient1", quantity="1", unit="cup"),
            ],
            instructions=[
                RecipeInstruction(title="step1", description="First step description"),
            ],
            categories=[
                RecipeCategory(name="breakfast"),
            ],
        )
        await recipe_cache_service.set_recipe(recipe)

        # Create thread in database first
        thread_params = CreateThreadParams(
            user_id=user_id,
            id=thread_id,
            created_at=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 1, 1, 0, 0, tzinfo=timezone.utc),
            is_empty=False,
            title="Test Thread",
            summary="Test Summary",
        )
        await thread_service.create_thread(async_session, thread_params)

        # Process mixed entry types
        entries = [
            ChatSessionDataStreamEntry(
                type=ChatSessionStreamEntryType.SYNC_CACHED_THREAD_WITH_DB,
                payload=SyncCachedThreadWithDbEntry(user_id=user_id, thread_id=thread_id),
            ),
            ChatSessionDataStreamEntry(
                type=ChatSessionStreamEntryType.SYNC_CACHED_MESSAGE_WITH_DB,
                payload=SyncCachedMessageWithDbEntry(user_id=user_id, thread_id=thread_id, message_id=message_id),
            ),
            ChatSessionDataStreamEntry(
                type=ChatSessionStreamEntryType.SYNC_CACHED_RECIPE_WITH_DB,
                payload=SyncCachedRecipeWithDbEntry(user_id=user_id, thread_id=thread_id, recipe_id=recipe_id),
            ),
        ]

        for i, entry in enumerate(entries): 
            await stream_processor._process_entry(f"mixed-entry-{i}", [("type", entry.type.value), ("payload", entry.payload.model_dump_json())])

        # Verify all data was synced
        db_thread = await thread_service.get_thread(async_session, thread_id)
        assert db_thread is not None
        assert db_thread.id == thread_id

        db_message = await message_service.get_message(async_session, message_id)
        assert db_message is not None
        assert db_message.id == message_id

        db_recipe = await recipe_service.get_recipe(async_session, recipe_id)
        assert db_recipe is not None
        assert db_recipe.id == recipe_id

    @pytest.mark.asyncio
    async def test_mixed_entry_types_different_order_with_missing_parent(
        self,
        stream_processor: ChatSessionDataStreamProcessor,
        thread_cache_service: ThreadCacheService,
        message_cache_service: MessageCacheService,
        recipe_cache_service: RecipeCacheService,
        thread_service: ThreadService,
        message_service: MessageService,
        recipe_service: RecipeService,
        async_session: AsyncSession,
    ) -> None:
        """Test handling mixed entry types in different order with missing parent message"""
        user_id = "test-user-id"
        thread_id = "test-thread-id"
        message_id = "test-message-id"
        child_message_id = "test-child-message-id"
        recipe_id = "test-recipe-id"

        # Create thread in cache
        thread = Thread(
            id=thread_id,
            user_id=user_id,
            created_at="2024-01-01T00:00:00+00:00",
            updated_at="2024-01-01T01:00:00+00:00",
            resumed_at=None,
            is_empty=False,
            title="Test Thread",
            summary="Test Summary",
            error_message=None,
        )
        await thread_cache_service.set_thread(thread)

        # Create parent message in cache
        parent_message = Message(
            id=message_id,
            user_id=user_id,
            thread_id=thread_id,
            role=MessageRole.user,
            content_type=MessageContentType.text,
            parent_id=None,
            created_at="2024-01-01T02:00:00+00:00",
            updated_at="2024-01-01T02:00:00+00:00",
            model_name=None,
            tool_name=None,
            tool_input=None,
            tool_output=None,
            is_recipe_generation_started=False,
            is_recipe_generation_completed=False,
            ip_address="127.0.0.1",
            safety_guard_result=None,
            text_content="Parent message",
            input_tokens=10,
            output_tokens=None,
        )
        await message_cache_service.set_message(user_id, parent_message)

        # Create child message in cache (with parent reference)
        child_message = Message(
            id=child_message_id,
            user_id=user_id,
            thread_id=thread_id,
            role=MessageRole.assistant,
            content_type=MessageContentType.text,
            parent_id=message_id,  # References parent message
            created_at="2024-01-01T03:00:00+00:00",
            updated_at="2024-01-01T03:00:00+00:00",
            model_name="gpt-4",
            tool_name=None,
            tool_input=None,
            tool_output=None,
            is_recipe_generation_started=False,
            is_recipe_generation_completed=False,
            ip_address="127.0.0.1",
            safety_guard_result=None,
            text_content="Child message",
            input_tokens=15,
            output_tokens=20,
        )
        await message_cache_service.set_message(user_id, child_message)

        # Create recipe in cache
        recipe = UserRecipe(
            id=recipe_id,
            user_id=user_id,
            thread_id=thread_id,
            created_at="2024-01-01T04:00:00+00:00",
            updated_at="2024-01-01T04:00:00+00:00",
            name="Test Recipe",
            description="A test recipe",
            ingredients=[
                RecipeIngredient(name="ingredient1", quantity="1", unit="cup"),
            ],
            instructions=[
                RecipeInstruction(title="step1", description="First step description"),
            ],
            categories=[
                RecipeCategory(name="breakfast"),
            ],
        )
        await recipe_cache_service.set_recipe(recipe)

        # Create thread in database first
        thread_params = CreateThreadParams(
            user_id=user_id,
            id=thread_id,
            created_at=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 1, 1, 0, 0, tzinfo=timezone.utc),
            is_empty=False,
            title="Test Thread",
            summary="Test Summary",
        )
        await thread_service.create_thread(async_session, thread_params)

        # Process mixed entry types in different order:
        # 1. Recipe (should succeed)
        # 2. Child message (should fail - parent not in DB yet)
        # 3. Parent message (should succeed)
        # 4. Child message again (should succeed now)

        # First entry (recipe) should succeed
        await stream_processor._call_process_handler(
            ChatSessionDataStreamEntry(
                type=ChatSessionStreamEntryType.SYNC_CACHED_RECIPE_WITH_DB,
                payload=SyncCachedRecipeWithDbEntry(
                    user_id=user_id, thread_id=thread_id, recipe_id=recipe_id
                ),
            ),
            "test-entry-id",
        )

        # Second entry (child message) should fail due to missing parent
        with pytest.raises(
            RetryException, match=f"Parent message {message_id} does not exist in database"
        ):
            await stream_processor._call_process_handler(
                ChatSessionDataStreamEntry(
                    type=ChatSessionStreamEntryType.SYNC_CACHED_MESSAGE_WITH_DB,
                    payload=SyncCachedMessageWithDbEntry(
                        user_id=user_id, thread_id=thread_id, message_id=child_message_id
                    ),
                ),
                "test-entry-id",
            )

        # Third entry (parent message) should succeed
        await stream_processor._call_process_handler(
            ChatSessionDataStreamEntry(
                type=ChatSessionStreamEntryType.SYNC_CACHED_MESSAGE_WITH_DB,
                payload=SyncCachedMessageWithDbEntry(
                    user_id=user_id, thread_id=thread_id, message_id=message_id
                ),
            ),
            "test-entry-id",
        )

        # Fourth entry (child message again) should succeed now that parent exists
        await stream_processor._call_process_handler(
            ChatSessionDataStreamEntry(
                type=ChatSessionStreamEntryType.SYNC_CACHED_MESSAGE_WITH_DB,
                payload=SyncCachedMessageWithDbEntry(
                    user_id=user_id, thread_id=thread_id, message_id=child_message_id
                ),
            ),
            "test-entry-id",
        )

        # Verify all data was synced correctly
        db_thread = await thread_service.get_thread(async_session, thread_id)
        assert db_thread is not None
        assert db_thread.id == thread_id

        db_recipe = await recipe_service.get_recipe(async_session, recipe_id)
        assert db_recipe is not None
        assert db_recipe.id == recipe_id

        db_parent_message = await message_service.get_message(async_session, message_id)
        assert db_parent_message is not None
        assert db_parent_message.id == message_id
        assert db_parent_message.text_content == "Parent message"

        db_child_message = await message_service.get_message(async_session, child_message_id)
        assert db_child_message is not None
        assert db_child_message.id == child_message_id
        assert db_child_message.text_content == "Child message"
        assert db_child_message.parent_id == message_id

