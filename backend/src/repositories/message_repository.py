
from database.schema import DBMessage
from schemas.messages import CreateMessageParams, GetDBMessagesParams, UpdateMessageParams
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from utils.date_utils import strip_timezone


class MessageRepository:
    """Repository for managing message database operations including creation, retrieval, updates, and counting."""

    async def create_message(self, db: AsyncSession, params: CreateMessageParams) -> DBMessage:
        """Creates a new message record with the given parameters.

        Args:
            db: Database session for the operation
            params: Message creation parameters including id, thread_id, role, and content_type

        Returns:
            The newly created message record
        """
        db_message = DBMessage(
            created_at=strip_timezone(params.created_at),
            updated_at=strip_timezone(params.updated_at),
            **params.model_dump(
                exclude={"created_at", "updated_at"}, exclude_none=True, exclude_unset=True
            ),
        )
        db.add(db_message)
        await db.flush()
        return db_message

    async def get_messages(self, db: AsyncSession, params: GetDBMessagesParams) -> list[DBMessage]:
        """Gets messages for a thread with pagination, sorting, and timestamp filtering.

        Args:
            db: Database session for the operation
            params: Query parameters including thread_id, limit, sort_by, sort_order, and from_timestamp

        Returns:
            List of messages matching the criteria, ordered by the specified field
        """
        thread_id = params.thread_id
        limit = params.limit
        from_timestamp = strip_timezone(params.from_timestamp) if params.from_timestamp else None
        sort_by = params.sort_by
        sort_order = params.sort_order

        if sort_by == "created_at":
            order_by_clause = DBMessage.created_at
        else:
            order_by_clause = DBMessage.updated_at

        if sort_order == "asc":
            order_by_clause = order_by_clause.asc()
        else:
            order_by_clause = order_by_clause.desc()

        query = (
            select(DBMessage)
            .options(selectinload(DBMessage.recipe))
            .where(DBMessage.thread_id == thread_id)
            .order_by(order_by_clause)
            .limit(limit)
        )

        if from_timestamp:
            if sort_by == "created_at":
                if sort_order == "asc":
                    query = query.where(DBMessage.created_at > from_timestamp)
                else:
                    query = query.where(DBMessage.created_at < from_timestamp)
            else:
                if sort_order == "asc":
                    query = query.where(DBMessage.updated_at > from_timestamp)
                else:
                    query = query.where(DBMessage.updated_at < from_timestamp)

        result = await db.execute(query)
        messages = result.scalars().all()
        return list(messages)

    async def get_message(self, db: AsyncSession, message_id: str) -> DBMessage | None:
        """Gets a single message record with the given id.

        Args:
            db: Database session for the operation
            message_id: The message's id

        Returns:
            Message record if found, None otherwise
        """
        result = await db.execute(select(DBMessage).where(DBMessage.id == message_id))
        return result.scalar_one_or_none()

    async def update_message(self, db: AsyncSession, params: UpdateMessageParams) -> DBMessage:
        """Updates an existing message record with the given parameters.

        Args:
            db: Database session for the operation
            params: Update parameters containing the message id and fields to update

        Returns:
            The updated message record

        Raises:
            ValueError: If the message doesn't exist
        """
        message_id = params.id
        updated_at = params.updated_at

        db_message = await db.get(DBMessage, message_id)
        if db_message is None:
            raise ValueError(f"Message {message_id} not found")

        items_to_update = params.model_dump(
            exclude={"id", "updated_at"}, exclude_none=True, exclude_unset=True
        )
        for field, value in items_to_update.items():
            if value is not None:
                setattr(db_message, field, value)

        setattr(db_message, "updated_at", strip_timezone(updated_at))

        db.add(db_message)
        await db.flush()
        return db_message

    async def count_thread_messages(self, db: AsyncSession, thread_id: str) -> int:
        """Counts the total number of messages in a thread.

        Args:
            db: Database session for the operation
            thread_id: The thread's id

        Returns:
            Total number of messages in the thread
        """
        result = await db.execute(
            select(func.count(DBMessage.id)).where(DBMessage.thread_id == thread_id)
        )
        return result.scalar_one()

    async def count_total_messages_sent_by_user(self, db: AsyncSession, user_id: str) -> int:
        """Counts the total number of messages sent by a user.

        Args:
            db: Database session for the operation
            user_id: The user's id

        Returns:
            Total number of messages sent by the user
        """
        result = await db.execute(
            select(func.count(DBMessage.id)).where(
                DBMessage.user_id == user_id, DBMessage.role == "user"
            )
        )
        return result.scalar_one()

    async def create_messages(
        self, db: AsyncSession, params: list[CreateMessageParams]
    ) -> list[DBMessage]:
        """Creates messages in the database.

        Args:
            db: Database session for the operation
            params: List of message creation parameters

        Returns:
            List of created message records
        """
        db_messages = [
            DBMessage(
                created_at=strip_timezone(message.created_at),
                updated_at=strip_timezone(message.updated_at),
                **message.model_dump(
                    exclude={"created_at", "updated_at"}, exclude_none=True, exclude_unset=True
                ),
            )
            for message in params
        ]
        db.add_all(db_messages)
        await db.flush()
        return db_messages
