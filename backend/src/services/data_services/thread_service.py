from datetime import datetime
from typing import cast

from database.schema import DBThread
from repositories.thread_repository import ThreadRepository
from schemas.threads import (
    CreateThreadParams,
    GetDBUserThreadsParams,
    GetUserThreadsParams,
    PaginatedThreads,
    ResumeThreadParams,
    Thread,
    UpdateThreadParams,
)
from sqlalchemy.ext.asyncio import AsyncSession
from utils.date_utils import to_utc_isostring
from utils.logger import Logger

logger = Logger("thread_service")


class ThreadService:
    def __init__(self, repository: ThreadRepository):
        self.repository = repository

    def _to_thread_dto(self, thread: DBThread) -> Thread:
        return Thread(
            id=str(thread.id),
            user_id=str(thread.user_id),
            created_at=to_utc_isostring(cast(datetime, thread.created_at)),
            updated_at=to_utc_isostring(cast(datetime, thread.updated_at)),
            resumed_at=to_utc_isostring(cast(datetime, thread.resumed_at))
            if thread.resumed_at is not None
            else None,
            error_message=str(thread.error_message) if thread.error_message is not None else None,
            title=str(thread.title) if thread.title is not None else None,
            summary=str(thread.summary) if thread.summary is not None else None,
            is_empty=bool(thread.is_empty),
        )

    async def create_threads(
        self, db: AsyncSession, params: list[CreateThreadParams]
    ) -> list[Thread]:
        logger.debug(f"Creating threads with {params}")
        db_threads = await self.repository.create_threads(db, params)
        return [self._to_thread_dto(thread) for thread in db_threads]

    async def create_thread(self, db: AsyncSession, params: CreateThreadParams) -> Thread:
        logger.debug(f"Creating thread for user {params.user_id}, thread_id: {params.id}")
        thread = await self.repository.create_thread(db, params)
        return self._to_thread_dto(thread)

    async def get_thread(self, db: AsyncSession, thread_id: str) -> Thread | None:
        logger.debug(f"Getting thread for thread_id: {thread_id}")
        thread = await self.repository.get_thread(db, thread_id)
        return self._to_thread_dto(thread) if thread else None

    async def get_paginated_threads(
        self, db: AsyncSession, params: GetUserThreadsParams
    ) -> PaginatedThreads:
        logger.debug(f"Getting threads for user {params.user_id} with params {params}")

        if params.limit > 100 or params.limit < 1:
            raise ValueError("Limit must be between 1 and 100")

        paginated_limit = params.limit + 1

        sort_by = params.sort_by
        new_params = GetDBUserThreadsParams(
            user_id=params.user_id,
            limit=paginated_limit,
            from_timestamp=params.from_timestamp,
            sort_by=sort_by,
            sort_order=params.sort_order,
            exclude_empty=params.exclude_empty,
        )

        db_threads = await self.repository.get_user_threads(db, new_params)

        has_more = len(db_threads) > params.limit
        threads_to_return = db_threads[: params.limit]

        next_timestamp = None
        if has_more and len(threads_to_return) > 0:
            next_timestamp = to_utc_isostring(
                cast(datetime, threads_to_return[-1].updated_at)
                if sort_by == "updated_at"
                else cast(datetime, threads_to_return[-1].created_at)
            )

        threads = [self._to_thread_dto(thread) for thread in threads_to_return]
        return PaginatedThreads(
            threads=threads,
            total_count=await self.repository.count_user_threads(db, params.user_id),
            has_more=has_more,
            next_timestamp=next_timestamp,
        )

    async def update_thread(self, db: AsyncSession, params: UpdateThreadParams) -> Thread:
        logger.debug(f"Updating thread {params.id} with {params}")
        thread = await self.repository.update_thread(db, params)
        return self._to_thread_dto(thread)

    async def resume_thread(self, db: AsyncSession, params: ResumeThreadParams) -> Thread:
        logger.debug(f"Resuming thread {params.id} with {params}")
        thread = await self.repository.resume_thread(db, params)
        return self._to_thread_dto(thread)

    async def is_thread_empty(self, db: AsyncSession, thread_id: str) -> bool:
        logger.debug(f"Checking if thread {thread_id} is empty")
        thread = await self.repository.get_thread(db, thread_id)
        return bool(thread.is_empty) if thread is not None else True

    async def count_user_threads(self, db: AsyncSession, user_id: str) -> int:
        logger.debug(f"Counting threads for user {user_id}")
        count = await self.repository.count_user_threads(db, user_id)
        return cast(int, count)
