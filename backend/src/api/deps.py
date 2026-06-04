import json
import ssl
import time
from typing import Annotated
from urllib.request import urlopen

from config.settings import Settings
from fastapi import Depends, HTTPException, Request, WebSocket
from jose import JWTError, jwt
from jose.jwk import construct as jwk_construct
from services.service_container import ServiceContainer


async def get_service_container(request: Request) -> ServiceContainer:
    container = getattr(request.app.state, "service_container", None)
    if container is None:
        raise RuntimeError("ServiceContainer is not initialized")
    return container


async def get_service_container_from_websocket(websocket: WebSocket) -> ServiceContainer:
    container = getattr(websocket.app.state, "service_container", None)
    if container is None:
        raise RuntimeError("ServiceContainer is not initialized")
    return container


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_settings_from_websocket(websocket: WebSocket) -> Settings:
    return websocket.app.state.settings


def get_jwt_token(request: Request) -> str | None:
    authorization = request.headers.get("Authorization")
    if not authorization or not authorization.startswith("Bearer "):
        return None
    return authorization.split(" ")[1]


def get_client_ip(request: Request) -> str:
    return (
        request.headers.get("fly-client-ip")
        or request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        or request.client.host
        if request.client
        else ""
    )


_jwks_cache: dict[str, tuple[dict, float]] = {}
_JWKS_CACHE_TTL = 3600  # 1 hour


def _fetch_jwks(url: str, ssl_context=None) -> dict:
    now = time.monotonic()
    cached = _jwks_cache.get(url)
    if cached and now - cached[1] < _JWKS_CACHE_TTL:
        return cached[0]
    jsonurl = urlopen(url, context=ssl_context) if ssl_context else urlopen(url)
    jwks = json.loads(jsonurl.read())
    _jwks_cache[url] = (jwks, now)
    return jwks


def decode_supabase_jwt(token: str, settings: Settings) -> dict:
    supabase_url = settings.supabase_url
    jwks_url = supabase_url + "/auth/v1/.well-known/jwks.json"

    if settings.is_development():
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        jwks = _fetch_jwks(jwks_url, ssl_context)
    else:
        jwks = _fetch_jwks(jwks_url)

    unverified_header = jwt.get_unverified_header(token)
    public_key = None
    for key in jwks["keys"]:
        if key["kid"] == unverified_header["kid"]:
            public_key = jwk_construct(key)
            break

    if not public_key:
        raise HTTPException(status_code=401, detail={"message": "Invalid token: no matching key"})

    try:
        return jwt.decode(
            token,
            public_key,
            algorithms=["ES256"],
            audience="authenticated",
            issuer=supabase_url + "/auth/v1",
        )
    except JWTError:
        raise HTTPException(status_code=401, detail={"message": "Invalid token"})


async def _resolve_user_id(token: str, settings: Settings, service_container: ServiceContainer) -> str:
    payload = decode_supabase_jwt(token, settings)
    external_id = payload.get("sub")
    if not external_id:
        raise HTTPException(status_code=401, detail={"message": "Invalid token: missing user ID"})

    async with service_container.db_transaction_maker() as db:  # type: ignore
        user = await service_container.user_service.get_user_by_external_id_or_email(
            db, external_id, payload.get("email")
        )

    if user is None:
        raise HTTPException(status_code=401, detail={"message": "User not found"})

    return user.id


async def get_current_user_id(
    jwt_token: Annotated[str | None, Depends(get_jwt_token)],
    settings: Annotated[Settings, Depends(get_settings)],
    service_container: Annotated[ServiceContainer, Depends(get_service_container)],
) -> str:
    if jwt_token is None:
        raise HTTPException(status_code=401, detail={"message": "Missing JWT token"})
    return await _resolve_user_id(jwt_token, settings, service_container)


async def get_current_user_id_from_websocket(
    websocket: WebSocket,
    settings: Annotated[Settings, Depends(get_settings_from_websocket)],
    service_container: Annotated[ServiceContainer, Depends(get_service_container_from_websocket)],
) -> str:
    token = websocket.query_params.get("token")
    if not token:
        raise HTTPException(status_code=401, detail={"message": "Missing JWT token"})
    return await _resolve_user_id(token, settings, service_container)
