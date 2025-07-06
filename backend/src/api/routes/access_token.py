from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Request, Response

from config.settings import get_settings

from api.deps import  get_service_container, get_access_token, get_client_ip

from schemas.api_error import RateLimitError
from schemas.user_access import UserAccessData

from services.service_container import ServiceContainer


router = APIRouter()


@router.post("/ensure-access-token", response_model=UserAccessData)
async def ensure_access_token(
    response: Response,
    service_container: Annotated[ServiceContainer, Depends(get_service_container)],
    ip_address: Annotated[str, Depends(get_client_ip)],
    access_token: Annotated[str | None, Depends(get_access_token)] = None,
) -> UserAccessData:
    try:
        user_access_data = await service_container.anonymous_access_service.get_or_create_user_access(ip_address, access_token)
    except RateLimitError:
        raise HTTPException(
            status_code=429,
            detail={
                "message": "Too many anonymous requests from this device. Please try again later.",
            },
        )
        
    settings = get_settings()
        
    should_refresh = False
    if access_token is None or access_token != user_access_data.access_token:
        should_refresh = True
    else:
        ttl = await service_container.user_access_cache_service.get_ttl(access_token)
        should_refresh = ttl is not None and ttl < settings.access_token_refresh_ttl

    if should_refresh:
        response.set_cookie(
            settings.cookie_name,
            user_access_data.access_token,
            secure=settings.cookie_secure,
            samesite=settings.cookie_samesite,
            max_age=settings.cookie_max_age,
            httponly=settings.cookie_httponly,
        )
        
    return user_access_data
