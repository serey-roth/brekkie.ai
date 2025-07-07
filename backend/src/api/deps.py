from typing import Annotated
from fastapi import Request, WebSocket, Cookie

from services.service_container import ServiceContainer

async def get_service_container(request: Request) -> ServiceContainer:
    container = getattr(request.app.state, "service_container", None)
    if container is None:
        raise RuntimeError("ServiceContainer is not initialized")
    return container


async def get_websocket_service_container(websocket: WebSocket) -> ServiceContainer:
    container = getattr(websocket.app.state, "service_container", None)
    if container is None:
        raise RuntimeError("ServiceContainer is not initialized")
    return container


def get_access_token(bk_access_token: Annotated[str | None, Cookie()] = None) -> str | None:
    return bk_access_token


def get_access_token_from_websocket(websocket: WebSocket) -> str | None:
    return websocket.cookies.get("bk_access_token")


def get_client_ip(request: Request) -> str: 
    return (
        request.headers.get("fly-client-ip")                                # Fly.io
        or request.headers.get("x-forwarded-for", "").split(",")[0].strip() # generic proxy
        or request.client.host
    )
