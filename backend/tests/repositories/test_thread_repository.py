from datetime import datetime, timezone, timedelta
import pytest
import pytest_asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from repositories.thread_repository import CreateThreadParams, GetDBUserThreadsParams, ThreadRepository, UpdateThreadParams

from utils.date_utils import strip_timezone

from tests.test_helpers.assert_deep_equal import assert_deep_equal

pytestmark = pytest.mark.asyncio


@pytest.fixture
def thread_repository():
    return ThreadRepository()


@pytest.fixture
def empty_thread_id():
    return "test-thread-id"


@pytest.fixture
def non_empty_thread_id():
    return "test-thread-id-2"


@pytest.fixture
def user_id():
    return "test-user-id"


class TestCreateThread:
    async def test_create_thread(self, async_session: AsyncSession, thread_repository: ThreadRepository, empty_thread_id: str, user_id: str):
        params = CreateThreadParams(
            id=empty_thread_id,
            user_id=user_id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            is_empty=True,
        )
        
        result = await thread_repository.create_thread(async_session, params)
        await async_session.commit()
        
        assert result is not None
        assert result.user_id == user_id
        assert result.id == empty_thread_id
        assert result.created_at == strip_timezone(params.created_at)
        assert result.updated_at == strip_timezone(params.updated_at)
        assert result.is_empty is True
        
        
    async def test_create_thread_with_optional_fields(self, async_session: AsyncSession, thread_repository: ThreadRepository, empty_thread_id: str, user_id: str):
        params = CreateThreadParams(
            id=empty_thread_id,
            user_id=user_id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            resumed_at=datetime.now(timezone.utc),
            is_empty=False,
            title="Test Title",
            summary="Test Summary",
            error_message="Test Error Message",
        )
        
        result = await thread_repository.create_thread(async_session, params)
        await async_session.commit()
        
        assert result is not None
        assert result.user_id == user_id
        assert result.id == empty_thread_id
        assert result.created_at == strip_timezone(params.created_at)
        assert result.updated_at == strip_timezone(params.updated_at)
        assert result.resumed_at == strip_timezone(params.resumed_at)
        assert result.is_empty is False
        assert result.title == "Test Title"
        assert result.summary == "Test Summary"
        assert result.error_message == "Test Error Message"


@pytest.fixture
def sample_empty_thread(empty_thread_id: str, user_id: str):
    return {
        "id": empty_thread_id,
        "user_id": user_id,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "resumed_at": None,
        "is_empty": True,
        "title": None,
        "summary": None,
        "error_message": None,
    }
        
        
@pytest.fixture()
def sample_non_empty_thread(non_empty_thread_id: str, user_id: str):
    return {
        "id": non_empty_thread_id,
        "user_id": user_id,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "resumed_at": None,
        "is_empty": False,
        "title": "Test Title",
        "summary": "Test Summary",
        "error_message": None,
    }


class TestGetThread:
    @pytest_asyncio.fixture(scope="function")
    async def create_empty_thread_in_db(self, async_session: AsyncSession, thread_repository: ThreadRepository, sample_empty_thread: dict):
        params = CreateThreadParams(**sample_empty_thread)

        await thread_repository.create_thread(async_session, params)
        await async_session.commit()
    
    async def test_get_thread(self, async_session: AsyncSession, thread_repository: ThreadRepository, create_empty_thread_in_db, sample_empty_thread: dict, empty_thread_id: str):
        result = await thread_repository.get_thread(async_session, empty_thread_id)
        await async_session.commit()
        
        assert result is not None
        assert result.id == empty_thread_id
        assert result.user_id == sample_empty_thread["user_id"]
        assert result.created_at == strip_timezone(sample_empty_thread["created_at"])
        assert result.updated_at == strip_timezone(sample_empty_thread["updated_at"])
        assert result.is_empty is True
        
        
    async def test_get_non_existent_thread(self, async_session: AsyncSession, thread_repository: ThreadRepository):
        result = await thread_repository.get_thread(async_session, "non-existing-thread-id")
        await async_session.commit()
        
        assert result is None
        

class TestGetUserThreads:
    @pytest.fixture(scope="function")
    def sample_user_threads(self, user_id: str):
        return [{
            "id": "test-thread-id-1",
            "user_id": user_id,
            "created_at": datetime.now(timezone.utc) + timedelta(days=1),
            "updated_at": datetime.now(timezone.utc) + timedelta(days=2, hours=10, minutes=10),
            "resumed_at": None,
            "is_empty": True,
            "title": None,
        }, {
            "id": "test-thread-id-2",
            "user_id": user_id,
            "created_at": datetime.now(timezone.utc) + timedelta(days=2),
            "updated_at": datetime.now(timezone.utc) + timedelta(days=2, hours=6),
            "resumed_at": None,
            "is_empty": False,
            "title": "Test Title",
            "summary": "Test Summary",
            "error_message": None,
        }, {
            "id": "test-thread-id-3",
            "user_id": user_id,
            "created_at": datetime.now(timezone.utc) + timedelta(days=2, hours=5),
            "updated_at": datetime.now(timezone.utc) + timedelta(days=2, hours=5),
            "resumed_at": None,
            "is_empty": True,
        }, {
            "id": "test-thread-id-4",
            "user_id": user_id,
            "created_at": datetime.now(timezone.utc) + timedelta(days=2, hours=10),
            "updated_at": datetime.now(timezone.utc) + timedelta(days=2, hours=11),
            "resumed_at": None,
            "is_empty": False,
            "title": "Test Title",
            "summary": "Test Summary",
            "error_message": None,
        }]
        
        
    @pytest_asyncio.fixture(scope="function")
    async def create_user_threads_in_db(self, async_session: AsyncSession, thread_repository: ThreadRepository, sample_user_threads: list[dict]):
        for thread in sample_user_threads:
            params = CreateThreadParams(**thread)
            await thread_repository.create_thread(async_session, params)
        await async_session.commit()
        
        
    async def test_get_user_threads(self, async_session: AsyncSession, thread_repository: ThreadRepository, create_user_threads_in_db, sample_user_threads: list[dict], user_id: str):
        params = GetDBUserThreadsParams(user_id=user_id)
        
        result = await thread_repository.get_user_threads(async_session, params)
        await async_session.commit()
        
        assert len(result) == 4
        assert result[0].id == sample_user_threads[3]["id"]
        assert result[1].id == sample_user_threads[0]["id"]
        assert result[2].id == sample_user_threads[1]["id"]
        assert result[3].id == sample_user_threads[2]["id"]
        
        
    async def test_smaller_limit(self, async_session: AsyncSession, thread_repository: ThreadRepository, create_user_threads_in_db, sample_user_threads: list[dict], user_id: str):
        params = GetDBUserThreadsParams(user_id=user_id, limit=2)
        
        result = await thread_repository.get_user_threads(async_session, params)
        await async_session.commit()
        
        assert len(result) == 2
        assert result[0].id == sample_user_threads[3]["id"]
        assert result[1].id == sample_user_threads[0]["id"]
        
    
    async def test_sort_by_created_at_asc(self, async_session: AsyncSession, thread_repository: ThreadRepository, create_user_threads_in_db, sample_user_threads: list[dict], user_id: str):
        params = GetDBUserThreadsParams(user_id=user_id, sort_by="created_at", sort_order="asc")
        
        result = await thread_repository.get_user_threads(async_session, params)
        await async_session.commit()
        
        assert len(result) == 4
        assert result[0].id == sample_user_threads[0]["id"]
        assert result[1].id == sample_user_threads[1]["id"]
        assert result[2].id == sample_user_threads[2]["id"]
        assert result[3].id == sample_user_threads[3]["id"]
        
        
        
    async def test_sort_by_created_at_desc(self, async_session: AsyncSession, thread_repository: ThreadRepository, create_user_threads_in_db, sample_user_threads: list[dict], user_id: str):
        params = GetDBUserThreadsParams(user_id=user_id, sort_by="created_at", sort_order="desc")
        
        result = await thread_repository.get_user_threads(async_session, params)
        await async_session.commit()
        
        assert len(result) == 4
        assert result[0].id == sample_user_threads[3]["id"]
        assert result[1].id == sample_user_threads[2]["id"]
        assert result[2].id == sample_user_threads[1]["id"]
        assert result[3].id == sample_user_threads[0]["id"]
        
        
    async def test_sort_by_updated_at_asc(self, async_session: AsyncSession, thread_repository: ThreadRepository, create_user_threads_in_db, sample_user_threads: list[dict], user_id: str):
        params = GetDBUserThreadsParams(user_id=user_id, sort_by="updated_at", sort_order="asc")
        
        result = await thread_repository.get_user_threads(async_session, params)
        await async_session.commit()
        
        assert len(result) == 4
        assert result[0].id == sample_user_threads[2]["id"]
        assert result[1].id == sample_user_threads[1]["id"]
        assert result[2].id == sample_user_threads[0]["id"]
        assert result[3].id == sample_user_threads[3]["id"]
        
        
    async def test_sort_by_updated_at_desc(self, async_session: AsyncSession, thread_repository: ThreadRepository, create_user_threads_in_db, sample_user_threads: list[dict], user_id: str):
        params = GetDBUserThreadsParams(user_id=user_id, sort_by="updated_at", sort_order="desc")
        
        result = await thread_repository.get_user_threads(async_session, params)
        await async_session.commit()
        
        assert len(result) == 4
        assert result[0].id == sample_user_threads[3]["id"]
        assert result[1].id == sample_user_threads[0]["id"]
        assert result[2].id == sample_user_threads[1]["id"]
        assert result[3].id == sample_user_threads[2]["id"]
        
        
    async def test_exclude_empty_threads(self, async_session: AsyncSession, thread_repository: ThreadRepository, create_user_threads_in_db, sample_user_threads: list[dict], user_id: str):
        params = GetDBUserThreadsParams(user_id=user_id, exclude_empty=True)
        
        result = await thread_repository.get_user_threads(async_session, params)
        await async_session.commit()
        
        assert len(result) == 2
        assert result[0].id == sample_user_threads[3]["id"]
        assert result[1].id == sample_user_threads[1]["id"]
        
        
    async def test_from_timestamp_with_sort_by_created_at_asc(self, async_session: AsyncSession, thread_repository: ThreadRepository, create_user_threads_in_db, sample_user_threads: list[dict], user_id: str):
        params = GetDBUserThreadsParams(user_id=user_id, sort_by="created_at", sort_order="asc", from_timestamp=sample_user_threads[0]["created_at"])

        result = await thread_repository.get_user_threads(async_session, params)
        await async_session.commit()
        
        assert len(result) == 3
        assert result[0].id == sample_user_threads[1]["id"]
        assert result[1].id == sample_user_threads[2]["id"]
        assert result[2].id == sample_user_threads[3]["id"]
        
    
    async def test_from_timestamp_with_sort_by_created_at_desc(self, async_session: AsyncSession, thread_repository: ThreadRepository, create_user_threads_in_db, sample_user_threads: list[dict], user_id: str):
        params = GetDBUserThreadsParams(user_id=user_id, sort_by="created_at", sort_order="desc", from_timestamp=sample_user_threads[3]["created_at"])
        
        result = await thread_repository.get_user_threads(async_session, params)
        await async_session.commit()
        
        assert len(result) == 3
        assert result[0].id == sample_user_threads[2]["id"]
        assert result[1].id == sample_user_threads[1]["id"]
        assert result[2].id == sample_user_threads[0]["id"]
        
        
    async def test_from_timestamp_with_sort_by_updated_at_asc(self, async_session: AsyncSession, thread_repository: ThreadRepository, create_user_threads_in_db, sample_user_threads: list[dict], user_id: str):
        params = GetDBUserThreadsParams(user_id=user_id, sort_by="updated_at", sort_order="asc", from_timestamp=sample_user_threads[0]["updated_at"])
        
        result = await thread_repository.get_user_threads(async_session, params)
        await async_session.commit()
        
        assert len(result) == 1
        assert result[0].id == sample_user_threads[3]["id"]
        
        
    async def test_from_timestamp_with_sort_by_updated_at_desc(self, async_session: AsyncSession, thread_repository: ThreadRepository, create_user_threads_in_db, sample_user_threads: list[dict], user_id: str):
        params = GetDBUserThreadsParams(user_id=user_id, sort_by="updated_at", sort_order="desc", from_timestamp=sample_user_threads[0]["updated_at"])
        
        result = await thread_repository.get_user_threads(async_session, params)
        await async_session.commit()
        
        assert len(result) == 2
        assert result[0].id == sample_user_threads[1]["id"]
        assert result[1].id == sample_user_threads[2]["id"]
        
        
    async def test_from_timestamp_with_sort_by_created_at_asc_and_exclude_empty(self, async_session: AsyncSession, thread_repository: ThreadRepository, create_user_threads_in_db, sample_user_threads: list[dict], user_id: str):
        params = GetDBUserThreadsParams(user_id=user_id, sort_by="created_at", sort_order="asc", from_timestamp=sample_user_threads[0]["created_at"], exclude_empty=True)
        
        result = await thread_repository.get_user_threads(async_session, params)
        await async_session.commit()
        
        assert len(result) == 2
        assert result[0].id == sample_user_threads[1]["id"]
        assert result[1].id == sample_user_threads[3]["id"]
        
        
    async def test_from_timestamp_with_sort_by_created_at_asc_and_smaller_limit(self, async_session: AsyncSession, thread_repository: ThreadRepository, create_user_threads_in_db, sample_user_threads: list[dict], user_id: str):
        params = GetDBUserThreadsParams(user_id=user_id, sort_by="created_at", sort_order="asc", from_timestamp=sample_user_threads[0]["created_at"], limit=1)
        
        result = await thread_repository.get_user_threads(async_session, params)
        await async_session.commit()
        
        assert len(result) == 1
        assert result[0].id == sample_user_threads[1]["id"]
        
        
class TestUpdateThread:
    @pytest_asyncio.fixture(scope="function")
    async def create_empty_thread_in_db(self, async_session: AsyncSession, thread_repository: ThreadRepository, sample_empty_thread: dict):
        params = CreateThreadParams(**sample_empty_thread)
        
        await thread_repository.create_thread(async_session, params)
        await async_session.commit()
        
        
    async def test_resume_thread(self, async_session: AsyncSession, thread_repository: ThreadRepository, create_empty_thread_in_db, sample_empty_thread: dict, empty_thread_id: str):
        params = UpdateThreadParams(
            id=empty_thread_id,
            updated_at=datetime.now(timezone.utc),
            resumed_at=datetime.now(timezone.utc),
        )
        
        result = await thread_repository.update_thread(async_session, params)
        await async_session.commit()
        
        assert result is not None
        assert result.id == empty_thread_id
        assert result.resumed_at == strip_timezone(params.resumed_at)
        
        
    async def test_update_thread_with_none_values(self, async_session: AsyncSession, thread_repository: ThreadRepository, create_empty_thread_in_db, empty_thread_id: str):
        params = UpdateThreadParams(
            id=empty_thread_id,
            updated_at=datetime.now(timezone.utc),
            title="Test Title",
        )
        
        result = await thread_repository.update_thread(async_session, params)
        await async_session.commit()
        
        params_2 = UpdateThreadParams(
            id=empty_thread_id,
            updated_at=datetime.now(timezone.utc),
            title=None,
        )
        
        result_2 = await thread_repository.update_thread(async_session, params_2)
        await async_session.commit()
        
        assert result_2 is not None
        assert result_2.id == empty_thread_id
        assert result_2.title is not None
        
    
    async def test_update_thread_with_non_existent_thread(self, async_session: AsyncSession, thread_repository: ThreadRepository):
        params = UpdateThreadParams(
            id="non-existing-thread-id",
            updated_at=datetime.now(timezone.utc),
            title="Test Title",
        )
        
        with pytest.raises(ValueError):
            await thread_repository.update_thread(async_session, params)


class TestCountUserThreads:
    @pytest.fixture(scope="function")
    def sample_user_threads(self, user_id: str):
        return [{
            "id": "test-thread-id-1",
            "user_id": user_id,
            "created_at": datetime.now(timezone.utc) + timedelta(days=1),
            "updated_at": datetime.now(timezone.utc) + timedelta(days=2, hours=10, minutes=10),
            "resumed_at": None,
            "is_empty": True,
            "title": None,
        }, {
            "id": "test-thread-id-2",
            "user_id": user_id,
            "created_at": datetime.now(timezone.utc) + timedelta(days=2),
            "updated_at": datetime.now(timezone.utc) + timedelta(days=2, hours=6),
            "resumed_at": None,
            "is_empty": False,
            "title": "Test Title",
            "summary": "Test Summary",
            "error_message": None,
        }, {
            "id": "test-thread-id-3",
            "user_id": user_id,
            "created_at": datetime.now(timezone.utc) + timedelta(days=2, hours=5),
            "updated_at": datetime.now(timezone.utc) + timedelta(days=2, hours=5),
            "resumed_at": None,
            "is_empty": True,
        }, {
            "id": "test-thread-id-4",
            "user_id": user_id,
            "created_at": datetime.now(timezone.utc) + timedelta(days=2, hours=10),
            "updated_at": datetime.now(timezone.utc) + timedelta(days=2, hours=11),
            "resumed_at": None,
            "is_empty": False,
            "title": "Test Title",
            "summary": "Test Summary",
            "error_message": None,
        }]
        
    @pytest_asyncio.fixture(scope="function")
    async def create_user_threads_in_db(self, async_session: AsyncSession, thread_repository: ThreadRepository, sample_user_threads: list[dict]):
        for thread in sample_user_threads:
            params = CreateThreadParams(**thread)
            await thread_repository.create_thread(async_session, params)
        await async_session.commit()
        

    async def test_count_user_threads(self, async_session: AsyncSession, thread_repository: ThreadRepository, create_user_threads_in_db, sample_user_threads: list[dict], user_id: str):
        result = await thread_repository.count_user_threads(async_session, user_id)
        await async_session.commit()
        
        assert result == 4


class TestCreateThreads:
    @pytest_asyncio.fixture(scope="function")
    async def create_batch_threads_in_db(self, async_session: AsyncSession, thread_repository: ThreadRepository, sample_user_threads: list[dict]):
        params = [CreateThreadParams(**thread) for thread in sample_user_threads]
        await thread_repository.create_threads(async_session, params)
        
        assert len(params) == len(sample_user_threads)
        