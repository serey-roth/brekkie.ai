from sqlalchemy.ext.asyncio import AsyncSession

from repositories.message_repository import MessageRepository

from schemas.messages import (
    CreateAssistantToolMessageParams,
    GetMessagesParams,
    Message, 
    CreateMessageParams, 
    UpdateMessageParams, 
    CreateUserMessageParams, 
    CreateAssistantTextMessageParams, 
    CreateAssistantRecipeMessageParams, 
    PaginatedMessages,
    GetDBMessagesParams,
)

from utils.date_utils import to_utc_isostring
from utils.logger import Logger

logger = Logger("message_service")


class MessageService:
    def __init__(self, repository: MessageRepository):
        self.repository = repository


    async def create_message(self, db: AsyncSession, params: CreateMessageParams) -> Message:
        logger.debug(f"Creating message with {params}")
        message = await self.repository.create_message(db, params)
        return Message.from_db_message(message)
        
    
    async def create_user_message(self, db: AsyncSession, params: CreateUserMessageParams) -> Message:
        logger.debug(f"Creating user message for thread {params.thread_id} with {params}")
        return await self.create_message(db, params)
    
    
    async def create_assistant_text_message(self, db: AsyncSession, params: CreateAssistantTextMessageParams) -> Message:
        logger.debug(f"Creating assistant text message for thread {params.thread_id} with {params}")
        return await self.create_message(db, params)
    
    
    async def create_assistant_recipe_message(self, db: AsyncSession, params: CreateAssistantRecipeMessageParams) -> Message:
        logger.debug(f"Creating assistant recipe message for thread {params.thread_id} with {params}")
        return await self.create_message(db, params)
    
    
    async def create_assistant_tool_message(self, db: AsyncSession, params: CreateAssistantToolMessageParams) -> Message:
        logger.debug(f"Creating assistant tool message for thread {params.thread_id} with {params}")
        return await self.create_message(db, params)
    

    async def update_message(self, db: AsyncSession, params: UpdateMessageParams) -> Message:
        logger.debug(f"Updating message {params.id} with {params}") 
        message = await self.repository.update_message(db, params)
        return Message.from_db_message(message)
    
    
    async def get_message(self, db: AsyncSession, message_id: str) -> Message | None:
        logger.debug(f"Getting message {message_id}")
        message = await self.repository.get_message(db, message_id)
        return Message.from_db_message(message) if message else None
    
    
    async def get_paginated_messages(self, db: AsyncSession, params: GetMessagesParams) -> PaginatedMessages:
        logger.debug(f"Getting paginated messages for thread {params.thread_id} with params {params}")
        
        if params.limit > 100 or params.limit < 1:
            raise ValueError("Limit must be between 1 and 100")
        
        paginated_limit = params.limit + 1
        
        sort_by = params.sort_by
        new_params = GetDBMessagesParams(
            thread_id=params.thread_id,
            limit=paginated_limit,
            from_timestamp=params.from_timestamp,
            sort_by=sort_by,
            sort_order=params.sort_order
        )
        
        db_messages = await self.repository.get_messages(db, new_params)

        has_more = len(db_messages) > params.limit
        messages_to_return = db_messages[:params.limit]
        
        next_timestamp = None
        if has_more and len(messages_to_return) > 0:
            next_timestamp = to_utc_isostring(messages_to_return[-1].created_at if sort_by == "created_at" else messages_to_return[-1].updated_at)
            
        messages = [Message.from_db_message(message) for message in messages_to_return]
        return PaginatedMessages(
            messages=messages,
            total_count=await self.repository.count_thread_messages(db, params.thread_id),
            has_more=has_more,
            next_timestamp=next_timestamp
        )   
    

    async def count_thread_messages(self, db: AsyncSession, thread_id: str) -> int:
        logger.debug(f"Counting thread messages for thread {thread_id}")
        return await self.repository.count_thread_messages(db, thread_id)
    
    
    async def create_messages(self, db: AsyncSession, params: list[CreateMessageParams]) -> list[Message]:
        logger.debug(f"Creating messages with {params}")
        db_messages = await self.repository.create_messages(db, params)
        return [Message.from_db_message(message) for message in db_messages]