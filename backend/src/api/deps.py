
from fastapi import Request, WebSocket

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
