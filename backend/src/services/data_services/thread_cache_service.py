from datetime import datetime, timezone

from schemas.threads import (
    CreateThreadParams,
    GetUserThreadsParams,
    PaginatedThreads,
    ResumeThreadParams,
    Thread,
    UpdateThreadParams,
)

from services.redis.redis_client import RedisClient
from services.redis.redis_cache import RedisCache

from utils.date_utils import to_utc_isostring


class ThreadCacheService:
    def __init__(self, redis_client: RedisClient, ttl: int):
        self.thread_cache = RedisCache[Thread](redis_client)
        self.ttl = ttl

    def _get_thread_key(self, user_id: str, thread_id: str) -> str:
        return f"brekkie:chat_session:{user_id}:threads:{thread_id}:metadata"

    def _get_all_threads_key(self, user_id: str) -> str:
        return f"brekkie:chat_session:{user_id}:threads:*:metadata"

    async def get_thread(self, user_id: str, thread_id: str) -> Thread | None:
        return await self.thread_cache.get_json(self._get_thread_key(user_id, thread_id), Thread)

    async def set_thread(
        self, thread: Thread, ttl: int | None = None, keep_ttl: bool = False
    ) -> None:
        if keep_ttl:
            set_ttl = None
        else:
            set_ttl = ttl if ttl is not None else self.ttl
        await self.thread_cache.set_json(
            self._get_thread_key(thread.user_id, thread.id),
            thread,
            ttl=set_ttl,
            keep_ttl=keep_ttl,
        )

    async def get_threads(self, user_id: str) -> list[Thread]:
        return await self.thread_cache.get_all_json_by_pattern(
            pattern=self._get_all_threads_key(user_id), model=Thread
        )

    async def create_thread(self, params: CreateThreadParams, ttl: int | None = None) -> Thread:
        thread = Thread(
            id=params.id,
            user_id=params.user_id,
            created_at=to_utc_isostring(params.created_at),
            updated_at=to_utc_isostring(params.updated_at),
            resumed_at=to_utc_isostring(params.resumed_at) if params.resumed_at else None,
            is_empty=params.is_empty,
            title=params.title,
            summary=params.summary,
            error_message=params.error_message,
        )
        await self.set_thread(thread, ttl=ttl)
        return thread

    async def update_thread(self, user_id: str, params: UpdateThreadParams) -> Thread:
        thread = await self.get_thread(user_id, params.id)
        if thread is None:
            raise ValueError(f"Thread {params.id} not found for user {user_id}")

        items_to_update = params.model_dump(exclude_none=True)
        for key, value in items_to_update.items():
            if key in ["resumed_at", "updated_at"] and isinstance(value, datetime):
                items_to_update[key] = to_utc_isostring(value)
            else:
                items_to_update[key] = value

        updated_thread = thread.model_copy(update=items_to_update, deep=True)

        previous_ttl = await self.thread_cache.get_ttl(self._get_thread_key(user_id, params.id))
        if previous_ttl is None or previous_ttl < 0:
            await self.set_thread(updated_thread, ttl=self.ttl)
        else:
            await self.set_thread(updated_thread, keep_ttl=True)

        return updated_thread

    async def is_thread_empty(self, user_id: str, thread_id: str) -> bool:
        thread = await self.get_thread(user_id, thread_id)
        return thread.is_empty if thread else False

    async def count_user_threads(self, user_id: str) -> int:
        threads = await self.get_threads(user_id)
        return len(threads)

    async def delete_threads_by_user_id(self, user_id: str) -> None:
        await self.thread_cache.delete_by_pattern(pattern=self._get_all_threads_key(user_id))

    # TODO: Duplicate logic in message_cache_service.py. Extract sorting and filtering to a separate class?

    def _sort_threads(self, threads: list[Thread], sort_by: str, sort_order: str) -> list[Thread]:
        copied_threads = [t.model_copy(deep=True) for t in threads]

        def sort_fn(t: Thread) -> datetime:
            if sort_by == "created_at":
                return datetime.fromisoformat(t.created_at).replace(tzinfo=timezone.utc)
            else:
                return datetime.fromisoformat(t.updated_at).replace(tzinfo=timezone.utc)

        copied_threads.sort(key=sort_fn, reverse=sort_order == "desc")
        return copied_threads

    def _filter_threads(
        self, threads: list[Thread], from_timestamp: datetime | None, sort_by: str, sort_order: str
    ) -> list[Thread]:
        copied_threads = [t.model_copy(deep=True) for t in threads]

        def filter_fn(t: Thread) -> bool:
            if from_timestamp is None:
                return True

            if sort_by == "created_at" and sort_order == "asc":
                return (
                    datetime.fromisoformat(t.created_at).replace(tzinfo=timezone.utc)
                    > from_timestamp
                )
            elif sort_by == "created_at" and sort_order == "desc":
                return (
                    datetime.fromisoformat(t.created_at).replace(tzinfo=timezone.utc)
                    < from_timestamp
                )
            elif sort_by == "updated_at" and sort_order == "asc":
                return (
                    datetime.fromisoformat(t.updated_at).replace(tzinfo=timezone.utc)
                    > from_timestamp
                )
            elif sort_by == "updated_at" and sort_order == "desc":
                return (
                    datetime.fromisoformat(t.updated_at).replace(tzinfo=timezone.utc)
                    < from_timestamp
                )
            else:
                raise ValueError(f"Invalid sort_by or sort_order: {sort_by} {sort_order}")

        copied_threads = [t for t in copied_threads if filter_fn(t)]
        return copied_threads

    async def get_paginated_threads(self, params: GetUserThreadsParams) -> PaginatedThreads:
        threads = await self.get_threads(params.user_id)
        if len(threads) == 0:
            return PaginatedThreads(
                threads=[],
                total_count=0,
                has_more=False,
                next_timestamp=None,
            )

        copied_threads = self._sort_threads(threads, params.sort_by, params.sort_order)
        if params.exclude_empty:
            copied_threads = [t for t in copied_threads if not t.is_empty]
        if params.from_timestamp:
            copied_threads = self._filter_threads(
                copied_threads, params.from_timestamp, params.sort_by, params.sort_order
            )

        paginated_limit = params.limit + 1
        limited_threads = copied_threads[:paginated_limit]
        has_more = len(limited_threads) > params.limit

        threads_to_return = limited_threads[: params.limit]

        last_thread = threads_to_return[-1] if has_more else None
        if last_thread and params.sort_by == "created_at":
            next_timestamp = last_thread.created_at
        elif last_thread and params.sort_by == "updated_at":
            next_timestamp = last_thread.updated_at
        else:
            next_timestamp = None

        return PaginatedThreads(
            threads=threads_to_return,
            total_count=len(threads),
            has_more=has_more,
            next_timestamp=next_timestamp,
        )

    async def resume_thread(self, user_id: str, params: ResumeThreadParams) -> Thread:
        thread = await self.get_thread(user_id, params.id)
        if thread is None:
            raise ValueError(f"Thread {params.id} not found for user {user_id}")

        thread.resumed_at = to_utc_isostring(params.resumed_at)
        await self.set_thread(thread, keep_ttl=True)
        return thread
