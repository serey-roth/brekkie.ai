from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
import asyncio

from fakeredis.aioredis import FakeRedis

from services.data_services.thread_cache_service import ThreadCacheService

from schemas.threads import (
    Thread,
    CreateThreadParams,
    UpdateThreadParams,
    GetUserThreadsParams,
    PaginatedThreads,
)

from utils.date_utils import to_utc_isostring

from tests.test_helpers.assert_deep_equal import assert_deep_equal


@pytest_asyncio.fixture
async def thread_cache_service(redis_client: FakeRedis) -> ThreadCacheService:
    await redis_client.flushall()
    return ThreadCacheService(redis_client, ttl=30) # 30 seconds for testing


class TestBasicThreadOperations:
    @pytest.mark.asyncio
    async def test_get_thread_key(self, thread_cache_service: ThreadCacheService):
        key = thread_cache_service._get_thread_key("user_id", "thread_id")
        assert key == "brekkie:chat_session:user_id:threads:thread_id:metadata"
        
        
    @pytest.mark.asyncio
    async def test_get_all_threads_key(self, thread_cache_service: ThreadCacheService):
        key = thread_cache_service._get_all_threads_key("user_id")
        assert key == "brekkie:chat_session:user_id:threads:*:metadata"
        
        
    @pytest.mark.asyncio
    async def test_get_and_set_thread(self, thread_cache_service: ThreadCacheService):
        thread = Thread(
            id="thread_id",
            user_id="user_id",
            created_at=to_utc_isostring(datetime.now(timezone.utc)),
            updated_at=to_utc_isostring(datetime.now(timezone.utc)),
            is_empty=False,
        )
        await thread_cache_service.set_thread(thread)
        assert_deep_equal(await thread_cache_service.get_thread("user_id", "thread_id"), thread)
        
        
    @pytest.mark.asyncio
    async def test_get_and_set_thread_with_ttl(self, thread_cache_service: ThreadCacheService):
        thread = Thread(
            id="thread_id",
            user_id="user_id",
            created_at=to_utc_isostring(datetime.now(timezone.utc)),
            updated_at=to_utc_isostring(datetime.now(timezone.utc)),
            is_empty=False,
        )
        await thread_cache_service.set_thread(thread, ttl=1)
        assert_deep_equal(await thread_cache_service.get_thread("user_id", "thread_id"), thread)
        await asyncio.sleep(1.5)
        assert await thread_cache_service.get_thread("user_id", "thread_id") is None


    @pytest.mark.asyncio
    async def test_get_threads(self, thread_cache_service: ThreadCacheService):
        threads = [
            Thread(
                id="thread_id_1",
                user_id="user_id",
                created_at=to_utc_isostring(datetime.now(timezone.utc)),
                updated_at=to_utc_isostring(datetime.now(timezone.utc)),
                is_empty=False,
            ),
            Thread(
                id="thread_id_2",
                user_id="user_id",
                created_at=to_utc_isostring(datetime.now(timezone.utc)),
                updated_at=to_utc_isostring(datetime.now(timezone.utc)),
                is_empty=False,
            ),
        ]
        for thread in threads:
            await thread_cache_service.set_thread(thread)
        assert_deep_equal(await thread_cache_service.get_threads("user_id"), threads)
        

    @pytest.mark.asyncio
    async def test_is_thread_empty(self, thread_cache_service: ThreadCacheService):
        await thread_cache_service.create_thread(CreateThreadParams(
            id="thread_id",
            user_id="user_id",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            is_empty=True,
        ))  
        
        assert await thread_cache_service.is_thread_empty("user_id", "thread_id") is True
        
        await thread_cache_service.update_thread("user_id", UpdateThreadParams(
            id="thread_id",
            user_id="user_id",
            updated_at=datetime.now(timezone.utc),
            is_empty=False,
        ))

        assert await thread_cache_service.is_thread_empty("user_id", "thread_id") is False
        
        
    @pytest.mark.asyncio
    async def test_count_user_threads(self, thread_cache_service: ThreadCacheService):
        await thread_cache_service.create_thread(CreateThreadParams(
            id="thread_id_1",
            user_id="user_id",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            is_empty=True,
        ))
        
        await thread_cache_service.create_thread(CreateThreadParams(
            id="thread_id_2",
            user_id="user_id",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            is_empty=False,
        ))
        
        assert await thread_cache_service.count_user_threads("user_id") == 2
        
        
    @pytest.mark.asyncio
    async def test_update_thread(self, thread_cache_service: ThreadCacheService):
        await thread_cache_service.create_thread(CreateThreadParams(
            id="thread_id",
            user_id="user_id",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            is_empty=True,
            title="title",
            summary="summary",
            error_message="error_message",
        ))
        
        updated_at = datetime.now(timezone.utc)
        resumed_at = datetime.now(timezone.utc)
        
        updated_thread = await thread_cache_service.update_thread("user_id", UpdateThreadParams(
            id="thread_id",
            user_id="user_id",
            updated_at=updated_at,
            is_empty=False,
            title="updated_title",
            summary="updated_summary",
            error_message="updated_error_message",
            resumed_at=resumed_at,
        ))
        
        assert updated_thread.id == "thread_id"
        assert updated_thread.user_id == "user_id"
        assert updated_thread.updated_at == to_utc_isostring(updated_at)
        assert updated_thread.resumed_at == to_utc_isostring(resumed_at)
        assert updated_thread.is_empty is False
        assert updated_thread.title == "updated_title"
        assert updated_thread.summary == "updated_summary"
        assert updated_thread.error_message == "updated_error_message"
        
        
    @pytest.mark.asyncio
    async def test_update_non_existent_thread(self, thread_cache_service: ThreadCacheService):
        
        with pytest.raises(ValueError):
            await thread_cache_service.update_thread("user_id", UpdateThreadParams(
                id="thread_id",
                user_id="user_id",
                updated_at=datetime.now(timezone.utc),
                is_empty=False,
            ))
            
        
    @pytest.mark.asyncio
    async def test_delete_threads_by_user_id(self, thread_cache_service: ThreadCacheService):
        await thread_cache_service.set_thread(Thread(
            id="thread_id_1",
            user_id="user_id_1",
            created_at=to_utc_isostring(datetime.now(timezone.utc)),
            updated_at=to_utc_isostring(datetime.now(timezone.utc)),
            is_empty=True,
        ))
        
        await thread_cache_service.set_thread(Thread(
            id="thread_id_2",
            user_id="user_id_1",
            created_at=to_utc_isostring(datetime.now(timezone.utc)),
            updated_at=to_utc_isostring(datetime.now(timezone.utc)),
            is_empty=False,
        ))
        
        await thread_cache_service.set_thread(Thread(
            id="thread_id_3",
            user_id="user_id_1",
            created_at=to_utc_isostring(datetime.now(timezone.utc)),
            updated_at=to_utc_isostring(datetime.now(timezone.utc)),
            is_empty=False,
        ))
        
        await thread_cache_service.delete_threads_by_user_id("user_id_1")
        threads = await thread_cache_service.get_threads("user_id_1")
        assert len(threads) == 0
        

class TestGetPaginatedThreads:
    @pytest.fixture
    def user_id(self) -> str:
        return "user_id"
    
    
    @pytest.fixture
    def sample_threads(self, user_id: str) -> list[Thread]:
        return [
            Thread(
                id=f"thread_id_{i}",
                user_id=user_id,
                created_at=to_utc_isostring(datetime.now(timezone.utc) + timedelta(seconds=i * 10)),
                updated_at=to_utc_isostring(datetime.now(timezone.utc) + timedelta(seconds=i * 10 + 1)),  
                is_empty=True,
            ) for i in range(50)
        ]

        
    @pytest_asyncio.fixture
    async def create_threads(self, thread_cache_service: ThreadCacheService, sample_threads: list[Thread], user_id: str) -> list[Thread]:
        for thread in sample_threads:
            await thread_cache_service.set_thread(thread)
        return sample_threads
        

    @pytest.mark.asyncio
    async def test_no_threads(self, thread_cache_service: ThreadCacheService, create_threads: list[Thread]):
        result = await thread_cache_service.get_paginated_threads(GetUserThreadsParams(
            user_id="user_id_test",
            limit=10,
            from_timestamp=datetime.now(timezone.utc),
            sort_by="created_at",
            sort_order="desc",
        )) 
        
        assert isinstance(result, PaginatedThreads)
        
        assert len(result.threads) == 0
        assert result.total_count == 0
        assert result.has_more is False
        assert result.next_timestamp is None
        
        
    @pytest.mark.asyncio
    async def test_exclude_empty_threads(self, thread_cache_service: ThreadCacheService, create_threads: list[Thread], user_id: str):
        result = await thread_cache_service.get_paginated_threads(GetUserThreadsParams(
            user_id=user_id,
            exclude_empty=True,
        ))
        
        assert isinstance(result, PaginatedThreads)
        
        assert len(result.threads) == 0
        assert result.total_count == 50
        assert result.has_more is False
        assert result.next_timestamp is None
        
        
    @pytest.mark.asyncio
    async def test_sort_by_created_at_asc(self, thread_cache_service: ThreadCacheService, create_threads: list[Thread], user_id: str, sample_threads: list[Thread]):
        result = await thread_cache_service.get_paginated_threads(GetUserThreadsParams(
            user_id=user_id,
            limit=10,
            sort_by="created_at",
            sort_order="asc",
        ))
        
        expected_next_timestamp = sample_threads[9].created_at
        
        assert isinstance(result, PaginatedThreads)
        
        assert len(result.threads) == 10
        assert result.total_count == 50
        assert result.has_more is True
        assert result.next_timestamp is not None
        assert result.next_timestamp == expected_next_timestamp
        
        
    @pytest.mark.asyncio
    async def test_sort_by_created_at_desc(self, thread_cache_service: ThreadCacheService, create_threads: list[Thread], user_id: str, sample_threads: list[Thread]):
        result = await thread_cache_service.get_paginated_threads(GetUserThreadsParams(
            user_id=user_id,
            limit=10,
            sort_by="created_at",
            sort_order="desc",
        ))
        
        expected_next_timestamp = sample_threads[40].created_at

        result = await thread_cache_service.get_paginated_threads(GetUserThreadsParams(
            user_id=user_id,
            limit=10,
            sort_by="created_at",
            sort_order="desc",
        ))
        
        assert isinstance(result, PaginatedThreads)
        
        assert len(result.threads) == 10    
        assert result.total_count == 50
        assert result.has_more is True
        assert result.next_timestamp is not None
        assert result.next_timestamp == expected_next_timestamp
        
        
    @pytest.mark.asyncio
    async def test_sort_by_updated_at_asc(self, thread_cache_service: ThreadCacheService, create_threads: list[Thread], user_id: str, sample_threads: list[Thread]):
        result = await thread_cache_service.get_paginated_threads(GetUserThreadsParams(
            user_id=user_id,
            limit=10,
            sort_by="updated_at",
            sort_order="asc",
        ))
        
        expected_next_timestamp = sample_threads[9].updated_at
        
        assert isinstance(result, PaginatedThreads)
        
        assert len(result.threads) == 10
        assert result.total_count == 50
        assert result.has_more is True
        assert result.next_timestamp is not None
        assert result.next_timestamp == expected_next_timestamp
        
        
    @pytest.mark.asyncio
    async def test_sort_by_updated_at_desc(self, thread_cache_service: ThreadCacheService, create_threads: list[Thread], user_id: str, sample_threads: list[Thread]):
        result = await thread_cache_service.get_paginated_threads(GetUserThreadsParams(
            user_id=user_id,
            limit=10,
            sort_by="updated_at",
            sort_order="desc",
        ))
        
        expected_next_timestamp = sample_threads[40].updated_at
        
        assert isinstance(result, PaginatedThreads)
        
        assert len(result.threads) == 10
        assert result.total_count == 50
        assert result.has_more is True
        assert result.next_timestamp is not None
        assert result.next_timestamp == expected_next_timestamp
        
        
    @pytest.mark.asyncio
    async def test_large_limit(self, thread_cache_service: ThreadCacheService, create_threads: list[Thread], user_id: str, sample_threads: list[Thread]):
        result = await thread_cache_service.get_paginated_threads(GetUserThreadsParams(
            user_id=user_id,
            limit=30,
            sort_by="created_at",
            sort_order="asc",
        ))
        
        expected_next_timestamp = sample_threads[29].created_at
        
        assert isinstance(result, PaginatedThreads)
        
        assert len(result.threads) == 30
        assert result.total_count == 50
        assert result.has_more is True
        assert result.next_timestamp is not None
        assert result.next_timestamp == expected_next_timestamp
        
        
    @pytest.mark.asyncio
    async def test_no_more_threads(self, thread_cache_service: ThreadCacheService, create_threads: list[Thread], user_id: str, sample_threads: list[Thread]):
        result = await thread_cache_service.get_paginated_threads(GetUserThreadsParams(
            user_id=user_id,
            limit=100,
            sort_by="created_at",
            sort_order="asc",
        ))
        
        assert isinstance(result, PaginatedThreads)
        
        assert len(result.threads) == 50
        assert result.total_count == 50
        assert result.has_more is False
        assert result.next_timestamp is None
        
        
    @pytest.mark.asyncio
    async def test_from_timestamp_and_sort_by_created_at_asc(self, thread_cache_service: ThreadCacheService, create_threads: list[Thread], user_id: str, sample_threads: list[Thread]):
        result = await thread_cache_service.get_paginated_threads(GetUserThreadsParams(
            user_id=user_id,
            limit=10,
            from_timestamp=sample_threads[9].created_at,
            sort_by="created_at",
            sort_order="asc",
        ))
        
        expected_next_timestamp = sample_threads[19].created_at
        
        assert isinstance(result, PaginatedThreads)
        
        assert len(result.threads) == 10
        assert result.total_count == 50
        assert result.has_more is True
        assert result.next_timestamp is not None
        assert result.next_timestamp == expected_next_timestamp
        
        
    @pytest.mark.asyncio
    async def test_from_timestamp_and_sort_by_created_at_desc(self, thread_cache_service: ThreadCacheService, create_threads: list[Thread], user_id: str, sample_threads: list[Thread]):
        result = await thread_cache_service.get_paginated_threads(GetUserThreadsParams(
            user_id=user_id,
            limit=10,
            from_timestamp=sample_threads[40].created_at,
            sort_by="created_at",
            sort_order="desc",
        ))
        
        expected_next_timestamp = sample_threads[30].created_at
        
        assert isinstance(result, PaginatedThreads)
        
        assert len(result.threads) == 10
        assert result.total_count == 50
        assert result.has_more is True
        assert result.next_timestamp is not None
        assert result.next_timestamp == expected_next_timestamp
        
        
    @pytest.mark.asyncio
    async def test_from_timestamp_and_sort_by_updated_at_asc(self, thread_cache_service: ThreadCacheService, create_threads: list[Thread], user_id: str, sample_threads: list[Thread]):
        result = await thread_cache_service.get_paginated_threads(GetUserThreadsParams(
            user_id=user_id,
            limit=10,
            from_timestamp=sample_threads[9].updated_at,
            sort_by="updated_at",
            sort_order="asc",
        ))
        
        expected_next_timestamp = sample_threads[19].updated_at
        
        assert isinstance(result, PaginatedThreads)
        
        assert len(result.threads) == 10
        assert result.total_count == 50
        assert result.has_more is True
        assert result.next_timestamp is not None
        assert result.next_timestamp == expected_next_timestamp
        
        
    @pytest.mark.asyncio
    async def test_from_timestamp_and_sort_by_updated_at_desc(self, thread_cache_service: ThreadCacheService, create_threads: list[Thread], user_id: str, sample_threads: list[Thread]):
        result = await thread_cache_service.get_paginated_threads(GetUserThreadsParams(
            user_id=user_id,
            from_timestamp=sample_threads[40].updated_at,
            sort_by="updated_at",
            sort_order="desc",
            limit=10,
        ))
        
        expected_next_timestamp = sample_threads[30].updated_at
        
        assert isinstance(result, PaginatedThreads)
        
        assert len(result.threads) == 10
        assert result.total_count == 50
        assert result.has_more is True
        assert result.next_timestamp is not None
        assert result.next_timestamp == expected_next_timestamp
        
        
        