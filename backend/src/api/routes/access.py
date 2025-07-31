from typing import Annotated
from datetime import datetime, timezone
from uuid import uuid4

from api.deps import get_access_token, get_client_ip, get_service_container, get_settings
from config.settings import Settings
from fastapi import APIRouter, Depends, HTTPException, Response
from schemas.user_access import UserAccess
from services.service_container import ServiceContainer
from utils.date_utils import to_utc_isostring
from utils.logger import Logger

logger = Logger("api.routes.access")

router = APIRouter()

@router.post("/ensure-access", response_model=UserAccess)
async def ensure_access(
    response: Response,
    service_container: Annotated[ServiceContainer, Depends(get_service_container)],
    ip_address: Annotated[str, Depends(get_client_ip)],
    settings: Annotated[Settings, Depends(get_settings)],
    access_token: Annotated[str | None, Depends(get_access_token)] = None,
) -> UserAccess:
    if access_token is None:
        raise HTTPException(status_code=401, detail={"message": "Missing access token"})
    
    user_access = await service_container.user_access_cache_service.get_user_access(access_token)
    if user_access is None:
        raise HTTPException(status_code=401, detail={"message": "Access record not found"})

    should_refresh = False
    ttl = await service_container.user_access_cache_service.get_ttl(access_token)
    should_refresh = ttl is not None and ttl < settings.access_token_refresh_ttl

    if should_refresh:
        timestamp = datetime.now(timezone.utc)
        
        old_access_token = user_access.access_token
        await service_container.user_access_cache_service.revoke_access(old_access_token)
        
        refresh_token = str(uuid4())
        user_access = await service_container.user_access_cache_service.create_user_access(
            access_token=refresh_token,
            user_id=user_access.user_id,
            is_authenticated=user_access.is_authenticated,
            user_message_count=user_access.user_message_count,
            ip_address=ip_address,
            created_at=to_utc_isostring(timestamp),
            updated_at=to_utc_isostring(timestamp),
        )
        
        response.set_cookie(
            settings.cookie_name,
            refresh_token,
            secure=settings.get_cookie_secure(),
            samesite=settings.cookie_samesite,  # type: ignore
            max_age=settings.cookie_max_age,
            httponly=settings.get_cookie_httponly(),
            path=settings.cookie_path,
        )

    return user_access


@router.post("/revoke-access")
async def revoke_access(
    response: Response,
    service_container: Annotated[ServiceContainer, Depends(get_service_container)],
    settings: Annotated[Settings, Depends(get_settings)],
    access_token: Annotated[str | None, Depends(get_access_token)] = None,
):
    if access_token is None:
        raise HTTPException(status_code=401, detail={"message": "Missing access token"})
    
    try:
        await service_container.user_access_cache_service.revoke_access(access_token)
        response.delete_cookie(settings.cookie_name)
        
    except Exception as e:
        logger.error(f"Unexpected error during revoke access: {e}")
        raise HTTPException(status_code=500, detail={"message": "Internal server error"})
    