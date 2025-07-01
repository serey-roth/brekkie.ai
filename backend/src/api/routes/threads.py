from typing import Annotated, Literal
from fastapi import APIRouter, Depends, HTTPException, Header

from fastapi.params import Query

from pydantic import BaseModel

from schemas.user_access import UserAccessData
from schemas.messages import PaginatedMessages, GetMessagesParams
from schemas.threads import PaginatedThreads, GetUserThreadsParams
from schemas.recipes import UserRecipe

from api.deps import get_service_container
from services.service_container import ServiceContainer

from utils.logger import Logger

logger = Logger("api.routes.threads")

def _extract_access_token(access_token: Annotated[str | None, Header()] = None) -> str | None:
    if not access_token:
        return None
    if not access_token.startswith("Bearer "):
        return None
    access_token = access_token.replace("Bearer ", "").strip()
    if not access_token:
        return None
    return access_token


async def _validate_access_token(access_token: str, service_container: ServiceContainer) -> UserAccessData:
    user_access_cache_service = service_container.user_access_cache_service
    user_access_data = await user_access_cache_service.get_user_access(access_token)
    return user_access_data


router = APIRouter()

@router.get("/threads")
async def get_user_threads(
    service_container: Annotated[ServiceContainer, Depends(get_service_container)],
    authorization: Annotated[str | None, Header()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
    sort_by: Annotated[Literal["created_at", "updated_at"], Query()] = "updated_at",
    sort_order: Annotated[Literal["asc", "desc"], Query()] = "desc",
    from_timestamp: Annotated[str | None, Query()] = None,
    exclude_empty: Annotated[str | None, Query()] = "false",
) -> PaginatedThreads:
    access_token = _extract_access_token(authorization)
    if access_token is None:
        raise HTTPException(status_code=401, detail={ "message": "Missing access token" })
    
    user_access_data = await _validate_access_token(access_token, service_container)
    if user_access_data is None:
        raise HTTPException(status_code=401, detail={ "message": "Access token is invalid or expired" })

    try:
        logger.debug(f"Getting threads for user {user_access_data.user_id} with limit {limit} and from_timestamp {from_timestamp}")

        db_transaction_maker = service_container.db_transaction_maker
        chat_session_store = service_container.chat_session_store
        
        async with db_transaction_maker() as db:
            return await chat_session_store.get_paginated_threads(db, user_access_data, GetUserThreadsParams(user_id=user_access_data.user_id, limit=limit, from_timestamp=from_timestamp, sort_by=sort_by, sort_order=sort_order, exclude_empty=exclude_empty == "true"))

    except Exception as e:
        logger.error(f"Error getting threads for user {user_access_data.user_id}: {e}")
        raise HTTPException(status_code=500, detail={ "message": "Internal server error: " + str(e) })
    
    
class GetThreadMessagesResponse(BaseModel):
    paginated_messages: PaginatedMessages
    recipes: list[UserRecipe]


@router.get("/threads/{thread_id}/messages")
async def get_thread_messages(
    thread_id: str,
    service_container: Annotated[ServiceContainer, Depends(get_service_container)],
    authorization: Annotated[str | None, Header()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
    sort_by: Annotated[Literal["created_at", "updated_at"], Query()] = "created_at",
    sort_order: Annotated[Literal["asc", "desc"], Query()] = "desc",
    from_timestamp: Annotated[str | None, Query()] = None,
) -> GetThreadMessagesResponse:
    access_token = _extract_access_token(authorization)
    if access_token is None:
        raise HTTPException(status_code=401, detail={ "message": "Missing access token" })
    
    user_access_data = await _validate_access_token(access_token, service_container)
    if user_access_data is None:
        raise HTTPException(status_code=401, detail={ "message": "Access token is invalid or expired" })
    
    try:
        logger.debug(f"Getting messages for thread {thread_id} for user {user_access_data.user_id} with limit {limit} and from_timestamp {from_timestamp}")
        
        db_transaction_maker = service_container.db_transaction_maker
        chat_session_store = service_container.chat_session_store
        
        async with db_transaction_maker() as db:
            result = await chat_session_store.get_paginated_messages(db, user_access_data, GetMessagesParams(user_id=user_access_data.user_id, thread_id=thread_id, limit=limit, from_timestamp=from_timestamp, sort_by=sort_by, sort_order=sort_order))
            message_ids = [message.id for message in result.messages if message.recipe_id is not None]
            recipes = []
            if len(message_ids) > 0:
                recipes = await chat_session_store.get_recipes_by_message_id(db, user_access_data, thread_id, message_ids)
            
            return GetThreadMessagesResponse(
                paginated_messages=result,  
                recipes=recipes,
            )
        
    except Exception as e:
        logger.error(f"Error getting messages for thread {thread_id} for user { user_access_data.user_id}: {e}")
        raise HTTPException(status_code=500, detail={ "message": "Internal server error: " + str(e) })