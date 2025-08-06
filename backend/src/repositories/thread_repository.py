from database.schema import DBThread
from schemas.threads import (
    CreateThreadParams,
    GetDBUserThreadsParams,
    ResumeThreadParams,
    UpdateThreadParams,
)
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from utils.date_utils import strip_timezone


class ThreadRepository:
    """Repository for managing thread database operations including creation, retrieval, updates, and pagination."""

    async def create_threads(
        self, db: AsyncSession, params: list[CreateThreadParams]
    ) -> list[DBThread]:
        """Create threads in the database.

        Args:
            db: Database session for the operation
            params: List of thread creation parameters
        """
        db_threads = [
            DBThread(
                created_at=strip_timezone(thread.created_at),
                updated_at=strip_timezone(thread.updated_at),
                resumed_at=strip_timezone(thread.resumed_at) if thread.resumed_at else None,
                **thread.model_dump(
                    exclude={"created_at", "updated_at", "resumed_at"},
                    exclude_none=True,
                    exclude_unset=True,
                ),
            )
            for thread in params
        ]
        db.add_all(db_threads)
        return db_threads

    async def create_thread(self, db: AsyncSession, params: CreateThreadParams) -> DBThread:
        """Create a new thread record with the given parameters.

        Args:
            db: Database session for the operation
            params: Thread creation parameters including id, user_id, and thread fields

        Returns:
            The newly created thread record
        """
        db_threads = await self.create_threads(db, [params])
        return db_threads[0]

    async def get_thread(self, db: AsyncSession, thread_id: str) -> DBThread | None:
        """Get a thread record with the given id.

        Args:
            db: Database session for the operation
            thread_id: The thread's id

        Returns:
            Thread record if found, None otherwise
        """
        result = await db.execute(select(DBThread).where(DBThread.id == thread_id))
        return result.scalar_one_or_none()

    async def get_user_threads(
        self, db: AsyncSession, params: GetDBUserThreadsParams
    ) -> list[DBThread]:
        """Get threads for a user with pagination, sorting, and filtering options.

        Args:
            db: Database session for the operation
            params: Query parameters including user_id, limit, sort_by, sort_order, exclude_empty, and from_timestamp

        Returns:
            List of threads matching the criteria, ordered by the specified field
        """
        user_id = params.user_id
        limit = params.limit
        from_timestamp = strip_timezone(params.from_timestamp) if params.from_timestamp else None
        sort_by = params.sort_by
        sort_order = params.sort_order

        if sort_by == "updated_at":
            order_by_clause = DBThread.updated_at
        else:
            order_by_clause = DBThread.created_at

        if sort_order == "asc":
            order_by_clause = order_by_clause.asc()
        else:
            order_by_clause = order_by_clause.desc()

        where_clause = [DBThread.user_id == user_id]
        if params.exclude_empty:
            where_clause.append(DBThread.is_empty == False)

        query = (
            select(DBThread)
            .options(selectinload(DBThread.messages))
            .options(selectinload(DBThread.recipes))
            .where(*where_clause)
            .order_by(order_by_clause)
            .limit(limit)
        )

        if from_timestamp:
            if sort_by == "created_at":
                if sort_order == "asc":
                    query = query.where(DBThread.created_at > from_timestamp)
                else:
                    query = query.where(DBThread.created_at < from_timestamp)
            else:
                if sort_order == "asc":
                    query = query.where(DBThread.updated_at > from_timestamp)
                else:
                    query = query.where(DBThread.updated_at < from_timestamp)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def update_thread(self, db: AsyncSession, params: UpdateThreadParams) -> DBThread:
        """Update an existing thread record with the given parameters.

        Args:
            db: Database session for the operation
            params: Update parameters containing the thread id and thread fields to update

        Returns:
            The updated thread record

        Raises:
            ValueError: If the thread doesn't exist
        """
        thread_id = params.id

        thread = await db.get(DBThread, thread_id)
        if thread is None:
            raise ValueError(f"Thread {thread_id} not found")

        items_to_update = params.model_dump(exclude={"id"}, exclude_none=True, exclude_unset=True)
        for field, value in items_to_update.items():
            if value is not None:
                if field == "resumed_at":
                    setattr(thread, "resumed_at", strip_timezone(value))
                elif field == "updated_at":
                    setattr(thread, "updated_at", strip_timezone(value))
                else:
                    setattr(thread, field, value)

        db.add(thread)
        return thread

    async def count_user_threads(self, db: AsyncSession, user_id: str) -> int:
        """Count the number of threads for a user.

        Args:
            db: Database session for the operation
            user_id: The user's id

        Returns:
            The number of threads for the user
        """
        result = await db.execute(
            select(func.count(DBThread.id)).where(DBThread.user_id == user_id)
        )
        return result.scalar_one()

    async def resume_thread(self, db: AsyncSession, params: ResumeThreadParams) -> DBThread:
        """Resume a thread.

        Args:
            db: Database session for the operation
            params: Resume parameters containing the thread id and resumed_at
        """
        thread_id = params.id

        thread = await db.get(DBThread, thread_id)
        if thread is None:
            raise ValueError(f"Thread {thread_id} not found")

        setattr(thread, "resumed_at", strip_timezone(params.resumed_at))

        db.add(thread)
        return thread