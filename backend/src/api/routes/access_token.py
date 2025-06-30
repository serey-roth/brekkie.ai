from typing import Annotated
from fastapi import APIRouter, Depends, Header

from api.deps import get_service_container

from services.service_container import ServiceContainer

from schemas.user_access import UserAccessData

router = APIRouter()

def _extract_access_token(authorization: Annotated[str | None, Header()] = None) -> str | None:
    if not authorization:
        return None
    if not authorization.startswith("Bearer "):
        return None
    access_token = authorization.replace("Bearer ", "").strip()
    if not access_token:
        return None
    return access_token


@router.post("/ensure-access-token", response_model=UserAccessData)
async def ensure_access_token(
    service_container: Annotated[ServiceContainer, Depends(get_service_container)],
    authorization: Annotated[str | None, Header()] = None,
) -> UserAccessData:
    user_access_cache_service = service_container.user_access_cache_service

    access_token = _extract_access_token(authorization)
    if access_token is None:
        user_access_data = await user_access_cache_service.create_anonymous_access()
        return user_access_data
    
    is_expired = await user_access_cache_service.is_expired(access_token)
    if is_expired:
        user_access_data = await user_access_cache_service.create_anonymous_access()
        return user_access_data

    user_access_data = await user_access_cache_service.get_user_access(access_token)
    if user_access_data is None:
        user_access_data = await user_access_cache_service.create_anonymous_access()
        return user_access_data
    
    return user_access_data