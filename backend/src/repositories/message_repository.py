from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.schema import DBMessage
from schemas.messages import (
    CreateMessageParams,
    GetDBMessagesParams,
    UpdateMessageParams,
    UpdateStrategy,
    CountMessagesParams,
)

from utils.date_utils import strip_timezone


class MessageRepository:
    """Repository for managing message database operations including creation, retrieval, updates, and counting."""

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
        return db_messages

    async def create_message(self, db: AsyncSession, params: CreateMessageParams) -> DBMessage:
        """Creates a single message in the database.

        Args:
            db: Database session for the operation
            params: Message creation parameters

        Returns:
            The created message record
        """
        db_messages = await self.create_messages(db, [params])
        return db_messages[0]

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
    
    async def get_messages_by_ids(self, db: AsyncSession, message_ids: list[str]) -> list[DBMessage]:
        """Gets messages by ids.
        
        Args:
            db: Database session for the operation
            message_ids: List of message ids
        """
        query = select(DBMessage).where(DBMessage.id.in_(message_ids))
        result = await db.execute(query)
        return list(result.scalars().all())

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
        db_message = await db.get(DBMessage, message_id)
        if db_message is None:
            raise ValueError(f"Message {message_id} not found")

        updated_at = params.updated_at
        setattr(db_message, "updated_at", strip_timezone(updated_at))

        text_content_update = params.text_content_update
        if text_content_update is not None:
            if text_content_update.strategy == UpdateStrategy.REPLACE:
                new_text_content = text_content_update.text_content
            elif text_content_update.strategy == UpdateStrategy.APPEND:
                new_text_content = (
                    str(db_message.text_content) or ""
                ) + text_content_update.text_content
            setattr(db_message, "text_content", new_text_content)

        input_tokens_update = params.input_tokens_update
        if input_tokens_update is not None:
            if input_tokens_update.strategy == UpdateStrategy.REPLACE:
                new_input_tokens = input_tokens_update.input_tokens
            elif input_tokens_update.strategy == UpdateStrategy.APPEND:
                new_input_tokens = (
                    int(input_tokens_update.input_tokens)
                    if input_tokens_update.input_tokens is not None
                    else 0
                )
                new_input_tokens = new_input_tokens + input_tokens_update.input_tokens
            setattr(db_message, "input_tokens", new_input_tokens)

        output_tokens_update = params.output_tokens_update
        if output_tokens_update is not None:
            if output_tokens_update.strategy == UpdateStrategy.REPLACE:
                new_output_tokens = output_tokens_update.output_tokens
            elif output_tokens_update.strategy == UpdateStrategy.APPEND:
                new_output_tokens = (
                    int(output_tokens_update.output_tokens)
                    if output_tokens_update.output_tokens is not None
                    else 0
                )
                new_output_tokens = new_output_tokens + output_tokens_update.output_tokens
            setattr(db_message, "output_tokens", new_output_tokens)

        items_to_update = params.model_dump(
            exclude={"id", "updated_at", "text_content_update", "input_tokens_update", "output_tokens_update"},
            exclude_none=True,
            exclude_unset=True,
        )
        for field, value in items_to_update.items():
            if value is not None:
                setattr(db_message, field, value)

        db.add(db_message)
        return db_message

    async def count_messages(
        self, db: AsyncSession, params: CountMessagesParams
    ) -> int:
        """Counts the total number of messages.

        Args:
            db: Database session for the operation
            params: Parameters for counting messages

        Returns:
            Total number of messages
        """
        query = select(func.count(DBMessage.id))

        if params.thread_id:
            query = query.where(DBMessage.thread_id == params.thread_id)

        if params.user_id:
            query = query.where(DBMessage.user_id == params.user_id)

        if params.role:
            query = query.where(DBMessage.role == params.role)

        result = await db.execute(query)
        return result.scalar_one()
