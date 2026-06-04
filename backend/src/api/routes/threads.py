from datetime import datetime, timezone
from typing import Annotated, Literal

from api.deps import get_current_user_id, get_service_container
from fastapi import APIRouter, Depends, HTTPException
from fastapi.params import Query
from schemas.messages import GetMessagesParams, GetThreadMessagesResponse, PaginatedApiMessages
from schemas.threads import GetUserThreadsParams, PaginatedThreads
from services.service_container import ServiceContainer
from utils.logger import Logger

logger = Logger("api.routes.threads")


router = APIRouter()


@router.get("/threads")
async def get_user_threads(
    service_container: Annotated[ServiceContainer, Depends(get_service_container)],
    user_id: Annotated[str, Depends(get_current_user_id)],
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
    sort_by: Annotated[Literal["created_at", "updated_at"], Query()] = "updated_at",
    sort_order: Annotated[Literal["asc", "desc"], Query()] = "desc",
    from_timestamp: Annotated[str | None, Query()] = None,
    exclude_empty: Annotated[str | None, Query()] = "false",
) -> PaginatedThreads:
    try:
        async with service_container.db_transaction_maker() as db:  # type: ignore
            timestamp = datetime.fromisoformat(from_timestamp).replace(tzinfo=timezone.utc) if from_timestamp else None
            return await service_container.chat_session_store.get_paginated_threads(
                db,
                GetUserThreadsParams(
                    user_id=user_id,
                    limit=limit,
                    from_timestamp=timestamp,
                    sort_by=sort_by,
                    sort_order=sort_order,
                    exclude_empty=exclude_empty == "true",
                ),
            )
    except Exception as e:
        logger.error(f"Error getting threads for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail={"message": "Internal server error"})


@router.get("/threads/{thread_id}/messages")
async def get_thread_messages(
    thread_id: str,
    service_container: Annotated[ServiceContainer, Depends(get_service_container)],
    user_id: Annotated[str, Depends(get_current_user_id)],
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
    sort_by: Annotated[Literal["created_at", "updated_at"], Query()] = "created_at",
    sort_order: Annotated[Literal["asc", "desc"], Query()] = "desc",
    from_timestamp: Annotated[str | None, Query()] = None,
) -> GetThreadMessagesResponse:
    try:
        async with service_container.db_transaction_maker() as db:  # type: ignore
            result = await service_container.chat_session_store.get_paginated_messages(
                db,
                GetMessagesParams(
                    user_id=user_id,
                    thread_id=thread_id,
                    limit=limit,
                    from_timestamp=datetime.fromisoformat(from_timestamp).replace(tzinfo=timezone.utc)
                    if from_timestamp
                    else None,
                    sort_by=sort_by,
                    sort_order=sort_order,
                ),
            )
            message_ids = [msg.id for msg in result.messages if msg.recipe_id is not None]
            recipes = (
                await service_container.chat_session_store.get_recipes_by_message_ids(db, message_ids)
                if message_ids
                else []
            )
            return GetThreadMessagesResponse(
                paginated_messages=PaginatedApiMessages.from_paginated_messages(result),
                recipes=recipes,
            )
    except Exception as e:
        logger.error(f"Error getting messages for thread {thread_id} for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail={"message": "Internal server error"})
