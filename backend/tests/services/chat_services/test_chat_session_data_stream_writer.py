import json
from typing import AsyncGenerator

import pytest
import pytest_asyncio

from fakeredis.aioredis import FakeRedis

from services.chat_services.chat_session_data_stream_writer import (
    ChatSessionDataStreamWriter,
)

from schemas.chat_session_data_stream import (
    ChatSessionDataStreamEntry,
    ChatSessionStreamEntryType,
    SyncCachedMessageWithDbEntry,
    SyncCachedRecipeWithDbEntry,
    SyncCachedThreadWithDbEntry,
)


@pytest_asyncio.fixture
async def redis_client() -> AsyncGenerator[FakeRedis, None]:
    client = FakeRedis()
    yield client
    await client.close()


@pytest_asyncio.fixture
async def stream_writer(redis_client: FakeRedis) -> ChatSessionDataStreamWriter:
    await redis_client.flushall()
    return ChatSessionDataStreamWriter(
        stream="brekkie_ai_chat_session_test_stream", redis_client=redis_client
    )


class TestChatSessionDataStreamWriter:
    @pytest.mark.asyncio
    async def test_add_sync_cached_thread_with_db_entry(
        self, stream_writer: ChatSessionDataStreamWriter
    ) -> None:
        """Test adding a thread entry to the stream."""
        user_id = "test-user-id"
        thread_id = "test-thread-id"

        entry_id = await stream_writer.add_entry(
            ChatSessionDataStreamEntry(
                type=ChatSessionStreamEntryType.SYNC_CACHED_THREAD_WITH_DB,
                payload=SyncCachedThreadWithDbEntry(user_id=user_id, thread_id=thread_id),
            )
        )

        # Verify entry was added
        assert entry_id is not None

        # Get stream info
        info = await stream_writer.get_stream_info()
        assert info["length"] == 1

        # Get the entry and verify its content
        entries = await stream_writer.redis_client.xread({stream_writer.stream: "0"}, count=1)
        assert len(entries) == 1

        stream_name, stream_entries = entries[0]
        assert stream_name == stream_writer.stream.encode()  # Handle bytes
        assert len(stream_entries) == 1

        entry_id_returned, entry_data = stream_entries[0]
        assert entry_id_returned == entry_id

        # Verify entry data
        assert entry_data[b"type"] == b"sync_cached_thread_with_db"
        payload = json.loads(entry_data[b"payload"])
        assert payload
        assert payload["thread_id"] == thread_id

    @pytest.mark.asyncio
    async def test_add_sync_cached_message_with_db_entry(
        self, stream_writer: ChatSessionDataStreamWriter
    ) -> None:
        """Test adding a message entry to the stream."""
        user_id = "test-user-id"
        thread_id = "test-thread-id"
        message_id = "test-message-id"

        entry_id = await stream_writer.add_entry(
            ChatSessionDataStreamEntry(
                type=ChatSessionStreamEntryType.SYNC_CACHED_MESSAGE_WITH_DB,
                payload=SyncCachedMessageWithDbEntry(
                    user_id=user_id, thread_id=thread_id, message_id=message_id
                ),
            )
        )

        # Verify entry was added
        assert entry_id is not None

        # Get stream info
        info = await stream_writer.get_stream_info()
        assert info["length"] == 1

        # Get the entry and verify its content
        entries = await stream_writer.redis_client.xread({stream_writer.stream: "0"}, count=1)
        assert len(entries) == 1

        stream_name, stream_entries = entries[0]
        assert stream_name == stream_writer.stream.encode()  # Handle bytes
        assert len(stream_entries) == 1

        entry_id_returned, entry_data = stream_entries[0]
        assert entry_id_returned == entry_id

        # Verify entry data
        assert entry_data[b"type"] == b"sync_cached_message_with_db"
        payload = json.loads(entry_data[b"payload"])
        assert payload["user_id"] == user_id
        assert payload["thread_id"] == thread_id
        assert payload["message_id"] == message_id

    @pytest.mark.asyncio
    async def test_add_sync_cached_recipe_with_db_entry(
        self, stream_writer: ChatSessionDataStreamWriter
    ) -> None:
        """Test adding a recipe entry to the stream."""
        user_id = "test-user-id"
        thread_id = "test-thread-id"
        recipe_id = "test-recipe-id"

        entry_id = await stream_writer.add_entry(
            ChatSessionDataStreamEntry(
                type=ChatSessionStreamEntryType.SYNC_CACHED_RECIPE_WITH_DB,
                payload=SyncCachedRecipeWithDbEntry(
                    user_id=user_id, thread_id=thread_id, recipe_id=recipe_id
                ),
            )
        )

        # Verify entry was added
        assert entry_id is not None

        # Get stream info
        info = await stream_writer.get_stream_info()
        assert info["length"] == 1

        # Get the entry and verify its content
        entries = await stream_writer.redis_client.xread({stream_writer.stream: "0"}, count=1)
        assert len(entries) == 1

        stream_name, stream_entries = entries[0]
        assert stream_name == stream_writer.stream.encode()  # Handle bytes
        assert len(stream_entries) == 1

        entry_id_returned, entry_data = stream_entries[0]
        assert entry_id_returned == entry_id

        # Verify entry data
        assert entry_data[b"type"] == b"sync_cached_recipe_with_db"
        payload = json.loads(entry_data[b"payload"])
        assert payload["user_id"] == user_id
        assert payload["thread_id"] == thread_id
        assert payload["recipe_id"] == recipe_id
   
    @pytest.mark.asyncio
    async def test_add_multiple_entries(self, stream_writer: ChatSessionDataStreamWriter) -> None:
        """Test adding multiple entries to the stream."""
        # Add multiple entries
        await stream_writer.add_entry(
            ChatSessionDataStreamEntry(
                type=ChatSessionStreamEntryType.SYNC_CACHED_THREAD_WITH_DB,
                payload=SyncCachedThreadWithDbEntry(user_id="user1", thread_id="thread1"),
            )
        )
        await stream_writer.add_entry(
            ChatSessionDataStreamEntry(
                type=ChatSessionStreamEntryType.SYNC_CACHED_MESSAGE_WITH_DB,
                payload=SyncCachedMessageWithDbEntry(
                    user_id="user1", thread_id="thread1", message_id="message1"
                ),
            )
        )
        await stream_writer.add_entry(
            ChatSessionDataStreamEntry(
                type=ChatSessionStreamEntryType.SYNC_CACHED_RECIPE_WITH_DB,
                payload=SyncCachedRecipeWithDbEntry(
                    user_id="user1", thread_id="thread1", recipe_id="recipe1"
                ),
            )
        )
        await stream_writer.add_entry(
            ChatSessionDataStreamEntry(
                type=ChatSessionStreamEntryType.SYNC_CACHED_THREAD_WITH_DB,
                payload=SyncCachedThreadWithDbEntry(user_id="user2", thread_id="thread2"),
            )
        )

        # Verify stream length
        length = await stream_writer.get_stream_length()
        assert length == 4

        # Get all entries
        entries = await stream_writer.redis_client.xread({stream_writer.stream: "0"}, count=10)
        assert len(entries) == 1

        stream_name, stream_entries = entries[0]
        assert stream_name == stream_writer.stream.encode()  # Handle bytes
        assert len(stream_entries) == 4

        # Verify entry types in order
        expected_types = [
            "sync_cached_thread_with_db",
            "sync_cached_message_with_db",
            "sync_cached_recipe_with_db",
            "sync_cached_thread_with_db",
        ]
        for i, (entry_id, entry_data) in enumerate(stream_entries):
            assert entry_data[b"type"] == expected_types[i].encode()

    @pytest.mark.asyncio
    async def test_get_stream_info_for_sync_cached_thread_with_db_entry(
        self, stream_writer: ChatSessionDataStreamWriter
    ) -> None:
        """Test getting stream information."""
        # Add an entry first
        await stream_writer.add_entry(
            ChatSessionDataStreamEntry(
                type=ChatSessionStreamEntryType.SYNC_CACHED_THREAD_WITH_DB,
                payload=SyncCachedThreadWithDbEntry(user_id="user1", thread_id="thread1"),
            )
        )

        # Get stream info
        info = await stream_writer.get_stream_info()

        # Verify info contains expected fields
        assert "length" in info
        assert "groups" in info
        assert "first-entry" in info
        assert "last-entry" in info
        assert info["length"] == 1

    @pytest.mark.asyncio
    async def test_get_stream_length_for_sync_cached_thread_with_db_entry(
        self, stream_writer: ChatSessionDataStreamWriter
    ) -> None:
        """Test getting stream length."""
        # Initially empty
        length = await stream_writer.get_stream_length()
        assert length == 0

        # Add entries
        await stream_writer.add_entry(
            ChatSessionDataStreamEntry(
                type=ChatSessionStreamEntryType.SYNC_CACHED_THREAD_WITH_DB,
                payload=SyncCachedThreadWithDbEntry(user_id="user1", thread_id="thread1"),
            )
        )
        length = await stream_writer.get_stream_length()
        assert length == 1

        await stream_writer.add_entry(
            ChatSessionDataStreamEntry(
                type=ChatSessionStreamEntryType.SYNC_CACHED_MESSAGE_WITH_DB,
                payload=SyncCachedMessageWithDbEntry(
                    user_id="user1", thread_id="thread1", message_id="message1"
                ),
            )
        )
        length = await stream_writer.get_stream_length()
        assert length == 2

    @pytest.mark.asyncio
    async def test_get_stream_info_for_empty_stream(
        self, stream_writer: ChatSessionDataStreamWriter
    ) -> None:
        """Test getting stream info for empty stream."""
        info = await stream_writer.get_stream_info()
        # Should return empty dict for non-existent stream
        assert info == {}

    @pytest.mark.asyncio
    async def test_get_stream_length_for_empty_stream(
        self, stream_writer: ChatSessionDataStreamWriter
    ) -> None:
        """Test getting stream length for empty stream."""
        length = await stream_writer.get_stream_length()
        assert length == 0

    @pytest.mark.asyncio
    async def test_entry_id_uniqueness_for_sync_cached_thread_with_db_entry(
        self, stream_writer: ChatSessionDataStreamWriter
    ) -> None:
        """Test that each entry gets a unique ID."""
        entry_id1 = await stream_writer.add_entry(
            ChatSessionDataStreamEntry(
                type=ChatSessionStreamEntryType.SYNC_CACHED_THREAD_WITH_DB,
                payload=SyncCachedThreadWithDbEntry(user_id="user1", thread_id="thread1"),
            )
        )
        entry_id2 = await stream_writer.add_entry(
            ChatSessionDataStreamEntry(
                type=ChatSessionStreamEntryType.SYNC_CACHED_THREAD_WITH_DB,
                payload=SyncCachedThreadWithDbEntry(user_id="user2", thread_id="thread2"),
            )
        )

        assert entry_id1 != entry_id2
        assert entry_id1 is not None
        assert entry_id2 is not None

    @pytest.mark.asyncio
    async def test_payload_json_format_for_sync_cached_message_with_db_entry(
        self, stream_writer: ChatSessionDataStreamWriter
    ) -> None:
        """Test that payload is properly JSON formatted."""
        await stream_writer.add_entry(
            ChatSessionDataStreamEntry(
                type=ChatSessionStreamEntryType.SYNC_CACHED_MESSAGE_WITH_DB,
                payload=SyncCachedMessageWithDbEntry(
                    user_id="user1", thread_id="thread1", message_id="message1"
                ),
            )
        )

        # Get the entry
        entries = await stream_writer.redis_client.xread({stream_writer.stream: "0"}, count=1)
        stream_name, stream_entries = entries[0]
        entry_id, entry_data = stream_entries[0]

        # Verify payload is valid JSON
        payload_str = entry_data[b"payload"].decode()
        payload = json.loads(payload_str)

        assert isinstance(payload, dict)
        assert "user_id" in payload
        assert "thread_id" in payload
        assert "message_id" in payload
