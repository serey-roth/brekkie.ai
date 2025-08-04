from datetime import datetime, timedelta, timezone
from typing import cast, Any
from uuid import uuid4

import pytest
import pytest_asyncio
from database.schema import DBMessage
from repositories.message_repository import MessageRepository
from schemas.message_content_type import MessageContentType
from schemas.message_role import MessageRole
from schemas.messages import (
    CountMessagesParams,
    CreateMessageParams,
    GetDBMessagesParams,
    UpdateMessageInputTokensParams,
    UpdateMessageOutputTokensParams,
    UpdateMessageParams,
    UpdateMessageTextContentParams,
    UpdateStrategy,
)
from sqlalchemy.ext.asyncio import AsyncSession
from utils.date_utils import strip_timezone

from tests.test_helpers.assert_deep_equal import assert_deep_equal

pytestmark = pytest.mark.asyncio


@pytest.fixture
def message_repository() -> MessageRepository:
    return MessageRepository()


class TestCreateMessages:
    @pytest_asyncio.fixture(scope="function")
    async def create_messages_in_db(
        self,
        async_session: AsyncSession,
        message_repository: MessageRepository,
        sample_messages: list[dict[str, Any]],
    ) -> None:
        params = [CreateMessageParams(**message) for message in sample_messages]
        await message_repository.create_messages(async_session, params)
        await async_session.commit()

        assert len(params) == len(sample_messages)


class TestCreateMessage:
    async def test_create_message(
        self, async_session: AsyncSession, message_repository: MessageRepository
    ) -> None:
        """Test creating a basic message with all fields"""
        params = CreateMessageParams(
            id=str(uuid4()),
            user_id=str(uuid4()),
            thread_id=str(uuid4()),
            role=MessageRole.user,
            content_type=MessageContentType.text,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            text_content="Hello, this is a test message",
            model_name="gpt-4",
            input_tokens=150,
            output_tokens=2500,
            tool_name="recipe_generator",
            tool_input={"ingredients": ["chicken", "rice"]},
            tool_output={"recipe": "Chicken and rice recipe"},
            recipe_id=str(uuid4()),
            is_recipe_generation_started=True,
            is_recipe_generation_completed=False,
            parent_id=str(uuid4()),
        )

        await message_repository.create_message(
            db=async_session,
            params=params,
        )

        await async_session.commit()
        result = await async_session.get(DBMessage, params.id)

        assert result is not None
        assert str(result.text_content) == params.text_content
        assert str(result.recipe_id) == params.recipe_id
        assert str(result.parent_id) == params.parent_id
        assert str(result.model_name) == params.model_name
        assert cast(int, result.input_tokens) == params.input_tokens
        assert cast(int, result.output_tokens) == params.output_tokens
        assert str(result.tool_name) == params.tool_name
        assert_deep_equal(cast(dict[str, Any], result.tool_input), params.tool_input)
        assert_deep_equal(cast(dict[str, Any], result.tool_output), params.tool_output)
        assert (
            cast(bool, result.is_recipe_generation_started) == params.is_recipe_generation_started
        )
        assert (
            cast(bool, result.is_recipe_generation_completed)
            == params.is_recipe_generation_completed
        )

    async def test_create_assistant_text_message(
        self, async_session: AsyncSession, message_repository: MessageRepository
    ) -> None:
        """Test creating an assistant text message."""
        params = CreateMessageParams(
            id=str(uuid4()),
            user_id=str(uuid4()),
            thread_id=str(uuid4()),
            role=MessageRole.assistant,
            content_type=MessageContentType.text,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            text_content="Hello, this is a test message",
        )

        await message_repository.create_message(
            db=async_session,
            params=params,
        )

        await async_session.commit()
        result = await async_session.get(DBMessage, params.id)

        assert result is not None
        assert MessageRole(result.role) == MessageRole.assistant
        assert MessageContentType(result.content_type) == MessageContentType.text
        assert str(result.text_content) == params.text_content

    async def test_create_assistant_recipe_message(
        self, async_session: AsyncSession, message_repository: MessageRepository
    ) -> None:
        """Test creating an assistant recipe message."""
        params = CreateMessageParams(
            id=str(uuid4()),
            user_id=str(uuid4()),
            thread_id=str(uuid4()),
            role=MessageRole.assistant,
            content_type=MessageContentType.recipe,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            recipe_id=str(uuid4()),
        )

        await message_repository.create_message(
            db=async_session,
            params=params,
        )

        await async_session.commit()
        result = await async_session.get(DBMessage, params.id)

        assert result is not None
        assert MessageRole(result.role) == MessageRole.assistant
        assert MessageContentType(result.content_type) == MessageContentType.recipe
        assert str(result.recipe_id) == params.recipe_id

    async def test_create_user_text_message(
        self, async_session: AsyncSession, message_repository: MessageRepository
    ) -> None:
        """Test creating a user text message."""
        params = CreateMessageParams(
            id=str(uuid4()),
            user_id=str(uuid4()),
            thread_id=str(uuid4()),
            role=MessageRole.user,
            content_type=MessageContentType.text,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            text_content="Hello, this is a test message",
        )

        await message_repository.create_message(
            db=async_session,
            params=params,
        )

        await async_session.commit()
        result = await async_session.get(DBMessage, params.id)

        assert result is not None
        assert MessageRole(result.role) == MessageRole.user
        assert MessageContentType(result.content_type) == MessageContentType.text
        assert str(result.text_content) == params.text_content

    async def test_create_tool_message(
        self, async_session: AsyncSession, message_repository: MessageRepository
    ) -> None:
        """Test creating a tool message."""
        params = CreateMessageParams(
            id=str(uuid4()),
            user_id=str(uuid4()),
            thread_id=str(uuid4()),
            role=MessageRole.assistant,
            content_type=MessageContentType.tool,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            tool_name="recipe_analyzer",
            tool_input={"query": "analyze recipe"},
            tool_output={"analysis": "Recipe is healthy"},
        )

        await message_repository.create_message(
            db=async_session,
            params=params,
        )

        await async_session.commit()
        result = await async_session.get(DBMessage, params.id)

        assert result is not None
        assert MessageRole(result.role) == MessageRole.assistant
        assert MessageContentType(result.content_type) == MessageContentType.tool
        assert str(result.tool_name) == params.tool_name
        assert_deep_equal(cast(dict[str, Any], result.tool_input), params.tool_input)
        assert_deep_equal(cast(dict[str, Any], result.tool_output), params.tool_output)

    async def test_created_message_has_naive_datetime(
        self, async_session: AsyncSession, message_repository: MessageRepository
    ) -> None:
        """Test that timezone information is properly stripped from datetime fields"""
        params = CreateMessageParams(
            id=str(uuid4()),
            user_id=str(uuid4()),
            thread_id=str(uuid4()),
            role=MessageRole.user,
            content_type=MessageContentType.text,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            text_content="Hello, this is a test message",
        )

        await message_repository.create_message(
            db=async_session,
            params=params,
        )

        await async_session.commit()
        result = await async_session.get(DBMessage, params.id)

        assert result is not None
        assert result.created_at.tzinfo is None
        assert result.updated_at.tzinfo is None
        assert cast(datetime, result.created_at) == strip_timezone(params.created_at)
        assert cast(datetime, result.updated_at) == strip_timezone(params.updated_at)


class TestGetMessage:
    @pytest.fixture(scope="function")
    def message_id(self) -> str:
        return str(uuid4())

    @pytest.fixture(scope="function")
    def sample_message(self, message_id: str) -> dict[str, Any]:
        return {
            "id": message_id,
            "user_id": str(uuid4()),
            "thread_id": str(uuid4()),
            "role": MessageRole.user,
            "content_type": MessageContentType.text,
            "text_content": "I'm looking for a quick dinner recipe with chicken and vegetables",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }

    @pytest_asyncio.fixture(scope="function")
    async def create_message_in_db(
        self,
        async_session: AsyncSession,
        message_repository: MessageRepository,
        sample_message: dict[str, Any],
    ) -> None:
        params = CreateMessageParams(**sample_message)
        await message_repository.create_message(async_session, params)
        await async_session.commit()

    async def test_get_message(
        self,
        async_session: AsyncSession,
        message_repository: MessageRepository,
        create_message_in_db: None,
        message_id: str,
        sample_message: dict[str, Any],
    ) -> None:
        """Test retrieving a message by ID and verifying all fields match."""
        message = await message_repository.get_message(async_session, message_id)
        assert message is not None

        assert str(message.id) == message_id
        assert str(message.thread_id) == sample_message["thread_id"]
        assert MessageRole(message.role) == sample_message["role"]
        assert MessageContentType(message.content_type) == sample_message["content_type"]
        assert str(message.text_content) == sample_message["text_content"]
        assert cast(datetime, message.created_at) == strip_timezone(sample_message["created_at"])
        assert cast(datetime, message.updated_at) == strip_timezone(sample_message["updated_at"])

    async def test_get_non_existent_message(
        self, async_session: AsyncSession, message_repository: MessageRepository
    ) -> None:
        """Test retrieving a non-existing message."""
        message = await message_repository.get_message(async_session, "non-existing-message-id")
        assert message is None


class TestGetMessages:
    @pytest.fixture(scope="function")
    def user_id(self) -> str:
        return str(uuid4())

    @pytest.fixture(scope="function")
    def thread_id(self) -> str:
        return str(uuid4())

    @pytest.fixture(scope="function")
    def recipe_id(self) -> str:
        return str(uuid4())

    @pytest.fixture(scope="function")
    def sample_messages(self, user_id: str, thread_id: str, recipe_id: str) -> list[dict[str, Any]]:
        """Create a list of messages for testing."""
        return [
            {
                "id": str(uuid4()),
                "user_id": user_id,
                "thread_id": thread_id,
                "role": MessageRole.user,
                "content_type": MessageContentType.text,
                "text_content": "I'm looking for a quick dinner recipe with chicken and vegetables",
                "created_at": datetime.now(timezone.utc) + timedelta(seconds=1),
                "updated_at": datetime.now(timezone.utc) + timedelta(seconds=1),
            },
            {
                "id": str(uuid4()),
                "user_id": user_id,
                "thread_id": thread_id,
                "role": MessageRole.assistant,
                "content_type": MessageContentType.text,
                "text_content": "I'd be happy to help you create a delicious chicken and vegetable dinner! Let me gather some ingredients and create a recipe for you.",
                "created_at": datetime.now(timezone.utc) + timedelta(seconds=5),
                "updated_at": datetime.now(timezone.utc) + timedelta(seconds=5),
            },
            {
                "id": str(uuid4()),
                "user_id": user_id,
                "thread_id": thread_id,
                "role": MessageRole.assistant,
                "content_type": MessageContentType.tool,
                "tool_name": "create_recipe",
                "tool_input": {
                    "ingredients": ["chicken breast", "broccoli", "carrots", "onion"],
                    "cooking_time": "30 minutes",
                    "difficulty": "easy",
                },
                "tool_output": {"status": "generating", "progress": 0.5},
                "created_at": datetime.now(timezone.utc) + timedelta(seconds=10),
                "updated_at": datetime.now(timezone.utc) + timedelta(seconds=10),
            },
            {
                "id": str(uuid4()),
                "user_id": user_id,
                "thread_id": thread_id,
                "role": MessageRole.assistant,
                "content_type": MessageContentType.recipe,
                "recipe_id": recipe_id,
                "created_at": datetime.now(timezone.utc) + timedelta(seconds=15),
                "updated_at": datetime.now(timezone.utc) + timedelta(seconds=15),
            },
        ]

    @pytest_asyncio.fixture(scope="function")
    async def create_messages_in_db(
        self,
        async_session: AsyncSession,
        message_repository: MessageRepository,
        sample_messages: list[dict[str, Any]],
    ) -> None:
        for message in sample_messages:
            params = CreateMessageParams(**message)
            await message_repository.create_message(
                db=async_session,
                params=params,
            )
        await async_session.commit()

    async def test_get_messages(
        self,
        async_session: AsyncSession,
        message_repository: MessageRepository,
        sample_messages: list[dict[str, Any]],
        thread_id: str,
        user_id: str,
        create_messages_in_db: None,
    ) -> None:
        """Test getting messages from the database."""
        params = GetDBMessagesParams(
            user_id=user_id, thread_id=thread_id, sort_by="created_at", sort_order="desc"
        )
        result = await message_repository.get_messages(async_session, params)

        sorted_messages = sorted(
            sample_messages, key=lambda x: x["created_at"], reverse=True
        )  # Sort messages by created_at in descending order

        assert len(result) == len(sample_messages)
        for i, message in enumerate(result):
            assert str(message.id) == sorted_messages[i]["id"]
            assert str(message.thread_id) == sorted_messages[i]["thread_id"]
            assert MessageRole(message.role) == sorted_messages[i]["role"]
            assert MessageContentType(message.content_type) == sorted_messages[i]["content_type"]
            assert cast(datetime, message.created_at) == strip_timezone(
                sorted_messages[i]["created_at"]
            )
            assert cast(datetime, message.updated_at) == strip_timezone(
                sorted_messages[i]["updated_at"]
            )

            if message.text_content is not None:
                assert str(message.text_content) == sorted_messages[i]["text_content"]
            if message.recipe_id is not None:
                assert str(message.recipe_id) == sorted_messages[i]["recipe_id"]
            if message.model_name is not None:
                assert str(message.model_name) == sorted_messages[i]["model_name"]
            if message.input_tokens is not None:
                assert cast(int, message.input_tokens) == sorted_messages[i]["input_tokens"]
            if message.output_tokens is not None:
                assert cast(int, message.output_tokens) == sorted_messages[i]["output_tokens"]
            if message.tool_name is not None:
                assert str(message.tool_name) == sorted_messages[i]["tool_name"]
            if message.tool_input is not None:
                assert_deep_equal(
                    cast(dict[str, Any], message.tool_input), sorted_messages[i]["tool_input"]
                )
            if message.tool_output is not None:
                assert_deep_equal(
                    cast(dict[str, Any], message.tool_output), sorted_messages[i]["tool_output"]
                )
            if message.is_recipe_generation_started is not None:
                assert (
                    cast(bool, message.is_recipe_generation_started)
                    == sorted_messages[i]["is_recipe_generation_started"]
                )
            if message.is_recipe_generation_completed is not None:
                assert (
                    cast(bool, message.is_recipe_generation_completed)
                    == sorted_messages[i]["is_recipe_generation_completed"]
                )

    async def test_get_messages_with_smaller_limit(
        self,
        async_session: AsyncSession,
        message_repository: MessageRepository,
        sample_messages: list[dict[str, Any]],
        thread_id: str,
        user_id: str,
        create_messages_in_db: None,
    ) -> None:
        """Test getting messages with a smaller limit than the number of messages."""
        params = GetDBMessagesParams(
            user_id=user_id, thread_id=thread_id, limit=2, sort_by="created_at", sort_order="desc"
        )
        result = await message_repository.get_messages(async_session, params)

        first_two_messages = sorted(sample_messages, key=lambda x: x["created_at"], reverse=True)[
            :2
        ]

        assert len(result) == 2
        for i, message in enumerate(result):
            assert str(message.id) == first_two_messages[i]["id"]
            assert str(message.thread_id) == first_two_messages[i]["thread_id"]
            assert MessageRole(message.role) == first_two_messages[i]["role"]
            assert MessageContentType(message.content_type) == first_two_messages[i]["content_type"]
            assert cast(datetime, message.created_at) == strip_timezone(
                first_two_messages[i]["created_at"]
            )
            assert cast(datetime, message.updated_at) == strip_timezone(
                first_two_messages[i]["updated_at"]
            )

    async def test_get_messages_with_sort_by_created_at_asc(
        self,
        async_session: AsyncSession,
        message_repository: MessageRepository,
        sample_messages: list[dict[str, Any]],
        thread_id: str,
        user_id: str,
        create_messages_in_db: None,
    ) -> None:
        """Test getting messages sorted by created_at in ascending order."""
        params = GetDBMessagesParams(
            user_id=user_id, thread_id=thread_id, sort_by="created_at", sort_order="asc"
        )
        result = await message_repository.get_messages(async_session, params)

        assert len(result) == len(sample_messages)
        sorted_messages = sorted(sample_messages, key=lambda x: x["created_at"])

        for i, message in enumerate(result):
            assert str(message.id) == sorted_messages[i]["id"]
            assert str(message.thread_id) == sorted_messages[i]["thread_id"]
            assert MessageRole(message.role) == sorted_messages[i]["role"]
            assert MessageContentType(message.content_type) == sorted_messages[i]["content_type"]
            assert cast(datetime, message.created_at) == strip_timezone(
                sorted_messages[i]["created_at"]
            )
            assert cast(datetime, message.updated_at) == strip_timezone(
                sorted_messages[i]["updated_at"]
            )

    async def test_get_messages_with_sort_by_created_at_desc(
        self,
        async_session: AsyncSession,
        message_repository: MessageRepository,
        sample_messages: list[dict[str, Any]],
        thread_id: str,
        user_id: str,
        create_messages_in_db: None,
    ) -> None:
        """Test getting messages sorted by created_at in descending order."""
        params = GetDBMessagesParams(
            user_id=user_id, thread_id=thread_id, sort_by="created_at", sort_order="desc"
        )
        result = await message_repository.get_messages(async_session, params)

        assert len(result) == len(sample_messages)
        sorted_messages = sorted(sample_messages, key=lambda x: x["created_at"], reverse=True)

        for i, message in enumerate(result):
            assert str(message.id) == sorted_messages[i]["id"]
            assert str(message.thread_id) == sorted_messages[i]["thread_id"]
            assert MessageRole(message.role) == sorted_messages[i]["role"]
            assert MessageContentType(message.content_type) == sorted_messages[i]["content_type"]
            assert cast(datetime, message.created_at) == strip_timezone(
                sorted_messages[i]["created_at"]
            )
            assert cast(datetime, message.updated_at) == strip_timezone(
                sorted_messages[i]["updated_at"]
            )

    async def test_get_messages_with_sort_by_updated_at_asc(
        self,
        async_session: AsyncSession,
        message_repository: MessageRepository,
        sample_messages: list[dict[str, Any]],
        thread_id: str,
        user_id: str,
        create_messages_in_db: None,
    ) -> None:
        """Test getting messages sorted by updated_at in ascending order."""
        params = GetDBMessagesParams(
            user_id=user_id, thread_id=thread_id, sort_by="updated_at", sort_order="asc"
        )
        result = await message_repository.get_messages(async_session, params)

        assert len(result) == len(sample_messages)
        sorted_messages = sorted(sample_messages, key=lambda x: x["updated_at"])

        for i, message in enumerate(result):
            assert str(message.id) == sorted_messages[i]["id"]
            assert str(message.thread_id) == sorted_messages[i]["thread_id"]
            assert MessageRole(message.role) == sorted_messages[i]["role"]
            assert MessageContentType(message.content_type) == sorted_messages[i]["content_type"]
            assert cast(datetime, message.created_at) == strip_timezone(
                sorted_messages[i]["created_at"]
            )
            assert cast(datetime, message.updated_at) == strip_timezone(
                sorted_messages[i]["updated_at"]
            )

    async def test_get_messages_with_sort_by_updated_at_desc(
        self,
        async_session: AsyncSession,
        message_repository: MessageRepository,
        sample_messages: list[dict[str, Any]],
        thread_id: str,
        user_id: str,
        create_messages_in_db: None,
    ) -> None:
        """Test getting messages sorted by updated_at in descending order."""
        params = GetDBMessagesParams(
            user_id=user_id, thread_id=thread_id, sort_by="updated_at", sort_order="desc"
        )
        result = await message_repository.get_messages(async_session, params)

        assert len(result) == len(sample_messages)
        sorted_messages = sorted(sample_messages, key=lambda x: x["updated_at"], reverse=True)

        for i, message in enumerate(result):
            assert str(message.id) == sorted_messages[i]["id"]
            assert str(message.thread_id) == sorted_messages[i]["thread_id"]
            assert MessageRole(message.role) == sorted_messages[i]["role"]
            assert MessageContentType(message.content_type) == sorted_messages[i]["content_type"]
            assert cast(datetime, message.created_at) == strip_timezone(
                sorted_messages[i]["created_at"]
            )
            assert cast(datetime, message.updated_at) == strip_timezone(
                sorted_messages[i]["updated_at"]
            )

    async def test_get_messages_with_from_timestamp_and_sort_by_created_at_asc(
        self,
        async_session: AsyncSession,
        message_repository: MessageRepository,
        sample_messages: list[dict[str, Any]],
        thread_id: str,
        user_id: str,
        create_messages_in_db: None,
    ) -> None:
        """Test getting messages with from_timestamp filter and created_at ascending sort."""
        params = GetDBMessagesParams(
            user_id=user_id,
            thread_id=thread_id,
            from_timestamp=sample_messages[2]["created_at"],
            sort_by="created_at",
            sort_order="asc",
        )
        result = await message_repository.get_messages(async_session, params)

        assert len(result) == 1

        first_message = result[0]

        assert str(first_message.id) == sample_messages[3]["id"]
        assert cast(datetime, first_message.created_at) == strip_timezone(
            sample_messages[3]["created_at"]
        )

    async def test_get_messages_with_from_timestamp_and_sort_by_created_at_desc(
        self,
        async_session: AsyncSession,
        message_repository: MessageRepository,
        sample_messages: list[dict[str, Any]],
        thread_id: str,
        user_id: str,
        create_messages_in_db: None,
    ) -> None:
        """Test getting messages with from_timestamp filter and created_at descending sort."""
        params = GetDBMessagesParams(
            user_id=user_id,
            thread_id=thread_id,
            from_timestamp=sample_messages[2]["created_at"],
            sort_by="created_at",
            sort_order="desc",
        )
        result = await message_repository.get_messages(async_session, params)

        assert len(result) == 2

        first_message = result[0]
        second_message = result[1]

        assert str(first_message.id) == sample_messages[1]["id"]
        assert str(second_message.id) == sample_messages[0]["id"]

        assert cast(datetime, first_message.created_at) == strip_timezone(
            sample_messages[1]["created_at"]
        )
        assert cast(datetime, second_message.created_at) == strip_timezone(
            sample_messages[0]["created_at"]
        )

    async def test_get_messages_with_from_timestamp_and_sort_by_updated_at_asc(
        self,
        async_session: AsyncSession,
        message_repository: MessageRepository,
        sample_messages: list[dict[str, Any]],
        thread_id: str,
        user_id: str,
        create_messages_in_db: None,
    ) -> None:
        """Test getting messages with from_timestamp filter and updated_at ascending sort."""
        params = GetDBMessagesParams(
            user_id=user_id,
            thread_id=thread_id,
            from_timestamp=sample_messages[2]["updated_at"],
            sort_by="updated_at",
            sort_order="asc",
        )
        result = await message_repository.get_messages(async_session, params)

        assert len(result) == 1

        first_message = result[0]

        assert str(first_message.id) == sample_messages[3]["id"]
        assert cast(datetime, first_message.updated_at) == strip_timezone(
            sample_messages[3]["updated_at"]
        )

    async def test_get_messages_with_from_timestamp_and_sort_by_updated_at_desc(
        self,
        async_session: AsyncSession,
        message_repository: MessageRepository,
        sample_messages: list[dict[str, Any]],
        thread_id: str,
        user_id: str,
        create_messages_in_db: None,
    ) -> None:
        """Test getting messages with from_timestamp filter and updated_at descending sort."""
        params = GetDBMessagesParams(
            user_id=user_id,
            thread_id=thread_id,
            from_timestamp=sample_messages[2]["updated_at"],
            sort_by="updated_at",
            sort_order="desc",
        )
        result = await message_repository.get_messages(async_session, params)

        assert len(result) == 2

        first_message = result[0]
        second_message = result[1]

        assert str(first_message.id) == sample_messages[1]["id"]
        assert str(second_message.id) == sample_messages[0]["id"]

        assert cast(datetime, first_message.updated_at) == strip_timezone(
            sample_messages[1]["updated_at"]
        )
        assert cast(datetime, second_message.updated_at) == strip_timezone(
            sample_messages[0]["updated_at"]
        )

    async def test_get_messages_with_limit_and_from_timestamp(
        self,
        async_session: AsyncSession,
        message_repository: MessageRepository,
        sample_messages: list[dict[str, Any]],
        thread_id: str,
        user_id: str,
        create_messages_in_db: None,
    ) -> None:
        """Test getting messages with limit and from_timestamp filters."""
        params = GetDBMessagesParams(
            user_id=user_id,
            thread_id=thread_id,
            limit=1,
            from_timestamp=sample_messages[2]["created_at"],
            sort_by="created_at",
            sort_order="desc",
        )
        result = await message_repository.get_messages(async_session, params)

        assert len(result) == 1

        first_message = result[0]

        assert str(first_message.id) == sample_messages[1]["id"]
        assert cast(datetime, first_message.created_at) == strip_timezone(
            sample_messages[1]["created_at"]
        )


class TestUpdateMessage:
    @pytest.fixture(scope="function")
    def message_id(self) -> str:
        return str(uuid4())

    @pytest.fixture(scope="function")
    def sample_message(self, message_id: str) -> dict[str, Any]:
        """Create a sample message for testing."""
        return {
            "id": message_id,
            "user_id": str(uuid4()),
            "thread_id": str(uuid4()),
            "role": MessageRole.user,
            "content_type": MessageContentType.text,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "text_content": "Hello, this is a test message.",
        }

    @pytest_asyncio.fixture(scope="function")
    async def create_message_in_db(
        self,
        async_session: AsyncSession,
        message_repository: MessageRepository,
        sample_message: dict[str, Any],
    ) -> None:
        params = CreateMessageParams(**sample_message)
        await message_repository.create_message(async_session, params)
        await async_session.commit()

    async def test_update_existing_message(
        self,
        async_session: AsyncSession,
        message_repository: MessageRepository,
        sample_message: dict[str, Any],
        create_message_in_db: None,
    ) -> None:
        """Test updating an existing message."""
        params = UpdateMessageParams(
            id=sample_message["id"],
            updated_at=datetime.now(timezone.utc) + timedelta(seconds=50),
        )

        await message_repository.update_message(async_session, params)
        await async_session.commit()

        result = await async_session.get(DBMessage, sample_message["id"])

        assert result is not None
        assert cast(datetime, result.updated_at) is not None
        assert cast(datetime, result.updated_at) == strip_timezone(params.updated_at)

    async def test_update_non_existent_message(
        self, async_session: AsyncSession, message_repository: MessageRepository
    ) -> None:
        """Test updating a non-existing message raises ValueError."""
        params = UpdateMessageParams(
            id=str(uuid4()),
            updated_at=datetime.now(timezone.utc),
        )

        with pytest.raises(ValueError):
            await message_repository.update_message(async_session, params)

    async def test_replace_text_content(
        self,
        async_session: AsyncSession,
        message_repository: MessageRepository,
        sample_message: dict[str, Any],
        create_message_in_db: None,
    ) -> None:
        """Test replacing text content of an existing message."""
        params = UpdateMessageParams(
            id=sample_message["id"],
            updated_at=datetime.now(timezone.utc) + timedelta(seconds=50),
            text_content_update=UpdateMessageTextContentParams(
                text_content="Hello, this is an updated test message",
                strategy=UpdateStrategy.REPLACE,
            ),
        )
        await message_repository.update_message(async_session, params)
        await async_session.commit()
        result = await async_session.get(DBMessage, sample_message["id"])
        assert result is not None
        assert str(result.text_content) == "Hello, this is an updated test message"
        assert cast(datetime, result.updated_at) == strip_timezone(params.updated_at)

    async def test_append_text_content(
        self,
        async_session: AsyncSession,
        message_repository: MessageRepository,
        sample_message: dict[str, Any],
        create_message_in_db: None,
    ) -> None:
        """Test appending text content to an existing message."""
        params = UpdateMessageParams(
            id=sample_message["id"],
            updated_at=datetime.now(timezone.utc) + timedelta(seconds=50),
            text_content_update=UpdateMessageTextContentParams(
                text_content="Appended text",
                strategy=UpdateStrategy.APPEND,
            ),
        )
        await message_repository.update_message(async_session, params)
        await async_session.commit()
        result = await async_session.get(DBMessage, sample_message["id"])
        assert result is not None
        assert str(result.text_content) == "Hello, this is a test message.Appended text"
        assert cast(datetime, result.updated_at) == strip_timezone(params.updated_at)

    async def test_replace_input_tokens(
        self,
        async_session: AsyncSession,
        message_repository: MessageRepository,
        sample_message: dict[str, Any],
        create_message_in_db: None,
    ) -> None:
        """Test replacing input tokens of an existing message."""
        params = UpdateMessageParams(
            id=sample_message["id"],
            updated_at=datetime.now(timezone.utc) + timedelta(seconds=50),
            input_tokens_update=UpdateMessageInputTokensParams(
                input_tokens=100,
                strategy=UpdateStrategy.REPLACE,
            ),
        )
        await message_repository.update_message(async_session, params)
        await async_session.commit()
        result = await async_session.get(DBMessage, sample_message["id"])
        assert result is not None
        assert result.input_tokens is not None
        assert cast(int, result.input_tokens) == 100
        assert cast(datetime, result.updated_at) == strip_timezone(params.updated_at)

    async def test_append_input_tokens(
        self,
        async_session: AsyncSession,
        message_repository: MessageRepository,
        sample_message: dict[str, Any],
        create_message_in_db: None,
    ) -> None:
        """Test appending input tokens to an existing message."""
        params = UpdateMessageParams(
            id=sample_message["id"],
            updated_at=datetime.now(timezone.utc) + timedelta(seconds=50),
            input_tokens_update=UpdateMessageInputTokensParams(
                input_tokens=100,
                strategy=UpdateStrategy.APPEND,
            ),
        )

        await message_repository.update_message(async_session, params)
        await async_session.flush()

        await message_repository.update_message(async_session, params)
        await async_session.commit()

        result = await async_session.get(DBMessage, sample_message["id"])
        assert result is not None
        assert result.input_tokens is not None
        assert cast(int, result.input_tokens) == 200
        assert cast(datetime, result.updated_at) == strip_timezone(params.updated_at)

    async def test_replace_output_tokens(
        self,
        async_session: AsyncSession,
        message_repository: MessageRepository,
        sample_message: dict[str, Any],
        create_message_in_db: None,
    ) -> None:
        """Test appending input tokens to an existing message."""
        params = UpdateMessageParams(
            id=sample_message["id"],
            updated_at=datetime.now(timezone.utc) + timedelta(seconds=50),
            output_tokens_update=UpdateMessageOutputTokensParams(
                output_tokens=100,
                strategy=UpdateStrategy.REPLACE,
            ),
        )
        await message_repository.update_message(async_session, params)
        await async_session.commit()
        result = await async_session.get(DBMessage, sample_message["id"])
        assert result is not None
        assert result.output_tokens is not None
        assert cast(int, result.output_tokens) == 100
        assert cast(datetime, result.updated_at) == strip_timezone(params.updated_at)

    async def test_append_output_tokens(
        self,
        async_session: AsyncSession,
        message_repository: MessageRepository,
        sample_message: dict[str, Any],
        create_message_in_db: None,
    ) -> None:
        """Test appending output tokens to an existing message."""
        params = UpdateMessageParams(
            id=sample_message["id"],
            updated_at=datetime.now(timezone.utc) + timedelta(seconds=50),
            output_tokens_update=UpdateMessageOutputTokensParams(
                output_tokens=100,
                strategy=UpdateStrategy.APPEND,
            ),
        )
        await message_repository.update_message(async_session, params)
        await async_session.flush()

        await message_repository.update_message(async_session, params)
        await async_session.commit()

        result = await async_session.get(DBMessage, sample_message["id"])
        assert result is not None
        assert result.output_tokens is not None
        assert cast(int, result.output_tokens) == 200
        assert cast(datetime, result.updated_at) == strip_timezone(params.updated_at)


class TestCountMessages:
    @pytest.fixture(scope="function")
    def user_id(self) -> str:
        return str(uuid4())

    @pytest.fixture(scope="function")
    def thread_id(self) -> str:
        return str(uuid4())

    @pytest.fixture(scope="function")
    def sample_messages(self, user_id: str, thread_id: str) -> list[dict[str, Any]]:
        """Create sample messages for testing counting."""
        return [
            {
                "id": str(uuid4()),
                "user_id": user_id,
                "thread_id": thread_id,
                "role": MessageRole.user,
                "content_type": MessageContentType.text,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "text_content": "Hello, this is a test message",
            },
            {
                "id": str(uuid4()),
                "user_id": user_id,
                "thread_id": thread_id,
                "role": MessageRole.assistant,
                "content_type": MessageContentType.text,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "text_content": "Hello, this is a test message",
            },
            {
                "id": str(uuid4()),
                "user_id": user_id,
                "thread_id": thread_id,
                "role": MessageRole.assistant,
                "content_type": MessageContentType.text,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "text_content": "Hello, this is a test message",
            },
        ]

    @pytest_asyncio.fixture(scope="function")
    async def create_messages_in_db(
        self,
        async_session: AsyncSession,
        message_repository: MessageRepository,
        sample_messages: list[dict[str, Any]],
        thread_id: str,
        user_id: str,
    ) -> None:
        for message in sample_messages:
            params = CreateMessageParams(**message)
            await message_repository.create_message(async_session, params)

        await async_session.commit()

    async def test_count_thread_messages(
        self,
        async_session: AsyncSession,
        message_repository: MessageRepository,
        sample_messages: list[dict[str, Any]],
        thread_id: str,
        user_id: str,
        create_messages_in_db: None,
    ) -> None:
        """Test counting messages in a specific thread."""
        result = await message_repository.count_messages(async_session, CountMessagesParams(thread_id=thread_id))
        assert result == 3

    async def test_count_thread_messages_by_user_id(
        self,
        async_session: AsyncSession,
        message_repository: MessageRepository,
        sample_messages: list[dict[str, Any]],
        thread_id: str,
        user_id: str,
        create_messages_in_db: None,
    ) -> None:
        """Test counting user messages in a specific thread."""
        result = await message_repository.count_messages(
            async_session, CountMessagesParams(thread_id=thread_id, user_id=user_id)
        )
        assert result == 3

    async def test_count_thread_messages_by_role(
        self,
        async_session: AsyncSession,
        message_repository: MessageRepository,
        sample_messages: list[dict[str, Any]],
        thread_id: str,
        user_id: str,
        create_messages_in_db: None,
    ) -> None:
        """Test counting assistant messages in a specific thread."""
        result = await message_repository.count_messages(
            async_session, CountMessagesParams(thread_id=thread_id, role=MessageRole.assistant)
        )
        assert result == 2

        result = await message_repository.count_messages(
            async_session, CountMessagesParams(thread_id=thread_id, role=MessageRole.user)
        )
        assert result == 1
