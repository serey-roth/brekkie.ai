from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response

from config.settings import Settings

from api.deps import get_service_container, get_access_token, get_client_ip, get_settings

from schemas.api_error import RateLimitError
from schemas.user_access import UserAccess

from services.service_container import ServiceContainer

from utils.logger import Logger
from utils.date_utils import to_utc_isostring


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
    try:
        user_access = (
            await service_container.anonymous_access_service.get_or_create_user_access(
                ip_address, access_token
            )
        )
    except RateLimitError:
        raise HTTPException(
            status_code=429,
            detail={
                "message": "Rate limit exceeded. Please try again later.",
            },
        )

    should_refresh = False
    if access_token is None or access_token != user_access.access_token:
        should_refresh = True
    else:
        ttl = await service_container.user_access_cache_service.get_ttl(access_token)
        should_refresh = ttl is not None and ttl < settings.access_token_refresh_ttl

    if should_refresh:
        response.set_cookie(
            settings.cookie_name,
            user_access.access_token,
            secure=settings.get_cookie_secure(),
            samesite=settings.cookie_samesite,  # type: ignore
            max_age=settings.cookie_max_age,
            httponly=settings.get_cookie_httponly(),
            path=settings.cookie_path,
        )

    return user_access


@router.post("/create-anonymous-access")
async def create_anonymous_access(
    response: Response,
    service_container: Annotated[ServiceContainer, Depends(get_service_container)],
    settings: Annotated[Settings, Depends(get_settings)],
    ip_address: Annotated[str, Depends(get_client_ip)],
    access_token: Annotated[str | None, Depends(get_access_token)] = None,
):
    try:
        if not access_token:
            raise HTTPException(status_code=401, detail={"message": "Missing access token"})

        user_access = await service_container.user_access_cache_service.get_user_access(
            access_token
        )
        if user_access is None:
            raise HTTPException(status_code=401, detail={"message": "Access token not found"})

        await service_container.user_access_cache_service.revoke_access(access_token)
        await service_container.anonymous_access_service.ip_rate_limiter.clear(ip_address)
        
        new_user_access = await service_container.user_access_cache_service.create_anonymous_access(
            ip_address=ip_address,
        )

        response.set_cookie(
            settings.cookie_name,
            new_user_access.access_token,
            secure=settings.get_cookie_secure(),
            samesite=settings.cookie_samesite,  # type: ignore
            max_age=settings.cookie_max_age,
            httponly=settings.get_cookie_httponly(),
            path=settings.cookie_path,
        )
        
        return new_user_access
    
    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Unexpected error during create anonymous access: {e}")
        raise HTTPException(status_code=500, detail={"message": "Internal server error"})

