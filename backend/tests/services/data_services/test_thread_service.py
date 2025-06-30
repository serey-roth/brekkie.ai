import pytest
import pytest_asyncio

from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from repositories.thread_repository import ThreadRepository
from services.data_services.thread_service import ThreadService

from schemas.threads import (
    CreateThreadParams,
    PaginatedThreads,
    Thread,
    UpdateThreadParams,
    GetUserThreadsParams,
)
from utils.date_utils import to_utc_isostring

pytestmark = pytest.mark.asyncio

@pytest.fixture
def thread_service():
    return ThreadService(ThreadRepository())


@pytest.fixture
def sample_thread_id():
    return "test-thread-id"


@pytest.fixture
def sample_user_id():
    return "test-user-id"


@pytest.fixture
def sample_timestamps():
    return (datetime.now(timezone.utc), datetime.now(timezone.utc))


class TestSimpleThreadOperations:
    async def test_create_thread(self, async_session: AsyncSession, thread_service: ThreadService, sample_thread_id: str, sample_user_id: str, sample_timestamps: tuple[datetime, datetime]):
        params = CreateThreadParams(
            id=sample_thread_id,
            user_id=sample_user_id,
            created_at=sample_timestamps[0],
            updated_at=sample_timestamps[1],
            is_empty=True,
        )
        
        thread = await thread_service.create_thread(async_session, params)
        
        assert isinstance(thread, Thread)
        
        assert thread.id == sample_thread_id
        assert thread.user_id == sample_user_id
        assert thread.created_at == to_utc_isostring(sample_timestamps[0])
        assert thread.updated_at == to_utc_isostring(sample_timestamps[1])
        assert thread.is_empty == True
            

    async def test_empty_thread_after_creation(self, async_session: AsyncSession, thread_service: ThreadService, sample_thread_id: str, sample_user_id: str, sample_timestamps: tuple[datetime, datetime]):
        params = CreateThreadParams(
            id=sample_thread_id,
            user_id=sample_user_id,
            created_at=sample_timestamps[0],
            updated_at=sample_timestamps[1],
            is_empty=True,
        )
       
        thread = await thread_service.create_thread(async_session, params)
        
        assert isinstance(thread, Thread)
        
        assert thread.is_empty == True


    async def test_get_thread(self, async_session: AsyncSession, thread_service: ThreadService, sample_thread_id: str, sample_user_id: str, sample_timestamps: tuple[datetime, datetime]):
        params = CreateThreadParams(
            id=sample_thread_id,
            user_id=sample_user_id,
            created_at=sample_timestamps[0],
            updated_at=sample_timestamps[1],
            is_empty=True,
        )
        await thread_service.create_thread(async_session, params)
        
        thread = await thread_service.get_thread(async_session, sample_thread_id)
        
        assert isinstance(thread, Thread)
        
        assert thread.id == sample_thread_id
        assert thread.user_id == sample_user_id
        assert thread.created_at == to_utc_isostring(sample_timestamps[0])
        assert thread.updated_at == to_utc_isostring(sample_timestamps[1])
            
        
    async def test_get_non_existent_thread(self, async_session: AsyncSession, thread_service: ThreadService):
        thread = await thread_service.get_thread(async_session, "non-existent-thread-id")
        
        assert thread is None
        
    
    async def test_update_thread(self, async_session: AsyncSession, thread_service: ThreadService, sample_thread_id: str, sample_user_id: str, sample_timestamps: tuple[datetime, datetime]):
        create_params = CreateThreadParams(
            id=sample_thread_id,
            user_id=sample_user_id,
            created_at=sample_timestamps[0],
            updated_at=sample_timestamps[1],
            is_empty=True,
        )
        await thread_service.create_thread(async_session, create_params)
        
        updated_at = datetime.now(timezone.utc)
        resumed_at = updated_at + timedelta(seconds=1)
        
        update_params = UpdateThreadParams(
            id=sample_thread_id,
            updated_at=updated_at,
            resumed_at=resumed_at,
            is_empty=False,
            title="test-title",
            summary="test-summary",
            error_message="test-error-message",
        )
        thread = await thread_service.update_thread(async_session, update_params)
        
        assert isinstance(thread, Thread)
        
        assert thread.id == sample_thread_id
        assert thread.user_id == sample_user_id
        assert thread.created_at == to_utc_isostring(sample_timestamps[0])
        assert thread.updated_at == to_utc_isostring(updated_at)
        assert thread.resumed_at == to_utc_isostring(resumed_at)
        assert thread.is_empty == False
        assert thread.title == "test-title"
        assert thread.summary == "test-summary"
        assert thread.error_message == "test-error-message"
        
        
    async def test_is_thread_empty(self, async_session: AsyncSession, thread_service: ThreadService, sample_thread_id: str, sample_user_id: str, sample_timestamps: tuple[datetime, datetime]):
        create_params = CreateThreadParams(
            id=sample_thread_id,
            user_id=sample_user_id,
            created_at=sample_timestamps[0],
            updated_at=sample_timestamps[1],
            is_empty=True,
        )
        await thread_service.create_thread(async_session, create_params)
        
        is_empty = await thread_service.is_thread_empty(async_session, sample_thread_id)
        
        assert is_empty == True
        
        update_params = UpdateThreadParams(
            id=sample_thread_id,
            updated_at=sample_timestamps[1],
            is_empty=False,
        )
        await thread_service.update_thread(async_session, update_params)
        
        is_empty = await thread_service.is_thread_empty(async_session, sample_thread_id)
        
        assert is_empty == False
    
    async def test_count_user_threads(self, async_session: AsyncSession, thread_service: ThreadService, sample_user_id: str):
        for i in range(50):
            await thread_service.create_thread(async_session, CreateThreadParams(
                id=f"test-thread-id-{i}",
                user_id=sample_user_id,
                created_at=datetime.now(timezone.utc) + timedelta(days=i),
                updated_at=datetime.now(timezone.utc) + timedelta(days=i + 1),
                is_empty=i % 2 == 0,
            ))
            
        count = await thread_service.count_user_threads(async_session, sample_user_id)
        
        assert count == 50
        
    
    async def test_create_threads(self, async_session: AsyncSession, thread_service: ThreadService, sample_user_id: str):
        params = [
            CreateThreadParams(
                id=f"test-thread-id-{i}",
                user_id=sample_user_id,
                created_at=datetime.now(timezone.utc) + timedelta(days=i),
                updated_at=datetime.now(timezone.utc) + timedelta(days=i + 1),
                is_empty=i % 2 == 0,
            )
            for i in range(50)
        ]
        
        created_threads = await thread_service.create_threads(async_session, params)
        
        assert len(created_threads) == 50
        
        for i, thread in enumerate(created_threads):
            assert thread.id == params[i].id

            
class TestPaginatedThreads:
    @pytest.fixture
    def sample_threads(self, sample_user_id: str,):
        return [
            CreateThreadParams(
                id=f"test-thread-id-{i}",
                user_id=sample_user_id,
                created_at=datetime.now(timezone.utc) + timedelta(days=i),
                updated_at=datetime.now(timezone.utc) + timedelta(days=i + 1),
                is_empty=i % 2 == 0,
                title=f"test-title-{i}",
                summary=f"test-summary-{i}",
                error_message=f"test-error-message-{i}" if i % 3 == 0 else None,
            )
            for i in range(50)
        ]
        
        
    @pytest_asyncio.fixture(scope="function")
    async def create_threads_in_db(self, async_session: AsyncSession, thread_service: ThreadService, sample_threads: list[CreateThreadParams]):
        for thread in sample_threads:
            await thread_service.create_thread(async_session, thread)
        await async_session.commit()
            
        
    async def test_correct_return_type(self, async_session: AsyncSession, thread_service: ThreadService, create_threads_in_db, sample_threads: list[CreateThreadParams], sample_user_id: str):
        sorted_threads = sorted(sample_threads, key=lambda x: x.updated_at, reverse=True)
        
        paginated_threads = await thread_service.get_paginated_threads(async_session, GetUserThreadsParams(user_id=sample_user_id))
        
        assert isinstance(paginated_threads, PaginatedThreads)
        
        assert len(paginated_threads.threads) == 10
        assert paginated_threads.total_count == 50
        assert paginated_threads.has_more == True
        assert paginated_threads.next_timestamp == to_utc_isostring(sorted_threads[9].updated_at)
        
        
    async def test_get_paginated_threads_with_default_limit(self, async_session: AsyncSession, thread_service: ThreadService, create_threads_in_db, sample_threads: list[CreateThreadParams], sample_user_id: str):
        sorted_threads = sorted(sample_threads, key=lambda x: x.updated_at, reverse=True)
        
        paginated_threads = await thread_service.get_paginated_threads(async_session, GetUserThreadsParams(user_id=sample_user_id))
        
        assert len(paginated_threads.threads) == 10
        assert paginated_threads.total_count == 50
        assert paginated_threads.has_more == True
        assert paginated_threads.next_timestamp == to_utc_isostring(sorted_threads[9].updated_at)
        
        
    async def test_get_paginated_threads_with_sorted_by_created_at_asc(self, async_session: AsyncSession, thread_service: ThreadService, create_threads_in_db, sample_threads: list[CreateThreadParams], sample_user_id: str):
        sorted_threads = sorted(sample_threads, key=lambda x: x.created_at)
        
        paginated_threads = await thread_service.get_paginated_threads(async_session, GetUserThreadsParams(user_id=sample_user_id, sort_by="created_at", sort_order="asc"))
        
        assert len(paginated_threads.threads) == 10
        assert paginated_threads.total_count == 50
        assert paginated_threads.has_more == True
        assert paginated_threads.next_timestamp == to_utc_isostring(sorted_threads[9].created_at)
        
        
    async def test_get_paginated_threads_with_sorted_by_created_at_desc(self, async_session: AsyncSession, thread_service: ThreadService, create_threads_in_db, sample_threads: list[CreateThreadParams], sample_user_id: str):
        sorted_threads = sorted(sample_threads, key=lambda x: x.created_at, reverse=True)
        
        paginated_threads = await thread_service.get_paginated_threads(async_session, GetUserThreadsParams(user_id=sample_user_id, sort_by="created_at", sort_order="desc"))
        
        assert len(paginated_threads.threads) == 10
        assert paginated_threads.total_count == 50
        assert paginated_threads.has_more == True
        assert paginated_threads.next_timestamp == to_utc_isostring(sorted_threads[9].created_at)
        
    
    async def test_get_paginated_threads_with_sorted_by_updated_at_asc(self, async_session: AsyncSession, thread_service: ThreadService, create_threads_in_db, sample_threads: list[CreateThreadParams], sample_user_id: str):
        sorted_threads = sorted(sample_threads, key=lambda x: x.updated_at)
        
        paginated_threads = await thread_service.get_paginated_threads(async_session, GetUserThreadsParams(user_id=sample_user_id, sort_by="updated_at", sort_order="asc"))
        
        assert len(paginated_threads.threads) == 10
        assert paginated_threads.total_count == 50
        assert paginated_threads.has_more == True
        assert paginated_threads.next_timestamp == to_utc_isostring(sorted_threads[9].updated_at)
        

    async def test_get_paginated_threads_with_sorted_by_updated_at_desc(self, async_session: AsyncSession, thread_service: ThreadService, create_threads_in_db, sample_threads: list[CreateThreadParams], sample_user_id: str):
        sorted_threads = sorted(sample_threads, key=lambda x: x.updated_at, reverse=True)
        
        paginated_threads = await thread_service.get_paginated_threads(async_session, GetUserThreadsParams(user_id=sample_user_id))
        
        assert len(paginated_threads.threads) == 10
        assert paginated_threads.total_count == 50
        assert paginated_threads.has_more == True
        assert paginated_threads.next_timestamp == to_utc_isostring(sorted_threads[9].updated_at)
        
        
    async def test_get_paginated_threads_with_custom_limit(self, async_session: AsyncSession, thread_service: ThreadService, create_threads_in_db, sample_threads: list[CreateThreadParams], sample_user_id: str):
        sorted_threads = sorted(sample_threads, key=lambda x: x.updated_at, reverse=True)
        
        paginated_threads = await thread_service.get_paginated_threads(async_session, GetUserThreadsParams(user_id=sample_user_id, limit=20))
        
        assert len(paginated_threads.threads) == 20
        assert paginated_threads.total_count == 50
        assert paginated_threads.has_more == True
        assert paginated_threads.next_timestamp == to_utc_isostring(sorted_threads[19].updated_at)
        
        
    async def test_get_paginated_threads_with_from_timestamp(self, async_session: AsyncSession, thread_service: ThreadService, create_threads_in_db, sample_threads: list[CreateThreadParams], sample_user_id: str):
        sorted_threads = sorted(sample_threads, key=lambda x: x.updated_at, reverse=True)
        
        paginated_threads = await thread_service.get_paginated_threads(async_session, GetUserThreadsParams(user_id=sample_user_id, from_timestamp=sorted_threads[9].updated_at))
        
        assert len(paginated_threads.threads) == 10
        assert paginated_threads.total_count == 50
        assert paginated_threads.has_more == True
        assert paginated_threads.next_timestamp == to_utc_isostring(sorted_threads[19].updated_at)
        
        
    async def test_get_paginated_threads_with_from_timestamp_and_custom_limit(self, async_session: AsyncSession, thread_service: ThreadService, create_threads_in_db, sample_threads: list[CreateThreadParams], sample_user_id: str):
        sorted_threads = sorted(sample_threads, key=lambda x: x.updated_at, reverse=True)
        
        paginated_threads = await thread_service.get_paginated_threads(async_session, GetUserThreadsParams(user_id=sample_user_id, limit=20, from_timestamp=sorted_threads[9].updated_at))
        
        assert len(paginated_threads.threads) == 20
        assert paginated_threads.total_count == 50
        assert paginated_threads.has_more == True
        assert paginated_threads.next_timestamp == to_utc_isostring(sorted_threads[29].updated_at)
        
        
    async def test_get_paginated_threads_with_from_timestamp_and_custom_limit_and_no_more_threads(self, async_session: AsyncSession, thread_service: ThreadService, create_threads_in_db, sample_threads: list[CreateThreadParams], sample_user_id: str):
        sorted_threads = sorted(sample_threads, key=lambda x: x.updated_at, reverse=True)
        
        paginated_threads = await thread_service.get_paginated_threads(async_session, GetUserThreadsParams(user_id=sample_user_id, limit=60, from_timestamp=sorted_threads[9].updated_at))
        
        assert len(paginated_threads.threads) == 40
        assert paginated_threads.total_count == 50
        assert paginated_threads.has_more == False
        assert paginated_threads.next_timestamp is None
        
        
    async def test_get_paginated_threads_with_from_timestamp_and_invalid_limit(self, async_session: AsyncSession, thread_service: ThreadService, create_threads_in_db, sample_threads: list[CreateThreadParams], sample_user_id: str):
        sorted_threads = sorted(sample_threads, key=lambda x: x.updated_at, reverse=True)
        
        with pytest.raises(ValueError) as e:
            get_params = GetUserThreadsParams(
                user_id=sample_user_id,
                limit=1000,
                from_timestamp=sorted_threads[9].updated_at,
            )
        
        with pytest.raises(ValueError) as e:
            get_params = GetUserThreadsParams(
                user_id=sample_user_id,
                limit=0,
                from_timestamp=sorted_threads[9].updated_at,
            )
            
            
    async def test_get_paginated_threads_with_exclude_empty(self, async_session: AsyncSession, thread_service: ThreadService, create_threads_in_db, sample_threads: list[CreateThreadParams], sample_user_id: str):
        non_empty_threads = [thread for thread in sample_threads if not thread.is_empty]
        sorted_non_empty_threads = sorted(non_empty_threads, key=lambda x: x.updated_at, reverse=True)
        
        paginated_threads = await thread_service.get_paginated_threads(async_session, GetUserThreadsParams(user_id=sample_user_id, exclude_empty=True))
        
        assert len(paginated_threads.threads) == 10
        assert paginated_threads.total_count == 50
        assert paginated_threads.has_more == True
        assert paginated_threads.next_timestamp == to_utc_isostring(sorted_non_empty_threads[9].updated_at)
        
        
    async def test_get_paginated_threads_with_exclude_empty_and_custom_limit(self, async_session: AsyncSession, thread_service: ThreadService, create_threads_in_db, sample_threads: list[CreateThreadParams], sample_user_id: str):
        non_empty_threads = [thread for thread in sample_threads if not thread.is_empty]
        sorted_non_empty_threads = sorted(non_empty_threads, key=lambda x: x.updated_at, reverse=True)
        
        paginated_threads = await thread_service.get_paginated_threads(async_session, GetUserThreadsParams(user_id=sample_user_id, limit=20, exclude_empty=True))
        
        assert len(paginated_threads.threads) == 20
        assert paginated_threads.total_count == 50
        assert paginated_threads.has_more == True
        assert paginated_threads.next_timestamp == to_utc_isostring(sorted_non_empty_threads[19].updated_at)
        
        
    async def test_get_paginated_threads_with_exclude_empty_and_from_timestamp(self, async_session: AsyncSession, thread_service: ThreadService, create_threads_in_db, sample_threads: list[CreateThreadParams], sample_user_id: str):
        non_empty_threads = [thread for thread in sample_threads if not thread.is_empty]
        sorted_non_empty_threads = sorted(non_empty_threads, key=lambda x: x.updated_at, reverse=True)
        
        paginated_threads = await thread_service.get_paginated_threads(async_session, GetUserThreadsParams(user_id=sample_user_id, exclude_empty=True, from_timestamp=sorted_non_empty_threads[9].updated_at))
        
        assert len(paginated_threads.threads) == 10
        assert paginated_threads.total_count == 50
        assert paginated_threads.has_more == True
        assert paginated_threads.next_timestamp == to_utc_isostring(sorted_non_empty_threads[19].updated_at)
        