from typing import Annotated

from api.deps import get_current_user_id_from_websocket, get_service_container_from_websocket
from fastapi import APIRouter, Depends, WebSocket
from fastapi.websockets import WebSocketState
from schemas.chat_session_errors import (
    ChatSessionError,
    InternalServerError,
)
from services.service_container import ServiceContainer
from utils.logger import Logger

logger = Logger("api.routes.chats")


async def _handle_chat_session_error(
    websocket: WebSocket, service_container: ServiceContainer, error: ChatSessionError
):
    error_dict = error.dict()
    sent = await service_container.websocket_event_sender.send_event(
        websocket, "chat_session_error", error_dict
    )
    if sent and websocket.client_state == WebSocketState.CONNECTED:
        await websocket.close(code=error.code, reason=error.type.value)


router = APIRouter()


@router.websocket("/chat")
async def start_chat(
    websocket: WebSocket,
    service_container: Annotated[ServiceContainer, Depends(get_service_container_from_websocket)],
    user_id: Annotated[str, Depends(get_current_user_id_from_websocket)],
):
    try:
        await websocket.accept()
        await service_container.chat_session_orchestrator.start_session(user_id, websocket)

    except ValueError as e:
        logger.error(f"Value error in WebSocket connection: {str(e)}")
        await _handle_chat_session_error(websocket, service_container, InternalServerError())

    except Exception as e:
        logger.error(f"Unexpected error in WebSocket connection: {str(e)}")
        await _handle_chat_session_error(websocket, service_container, InternalServerError())


@router.websocket("/chat/{thread_id}")
async def resume_chat(
    websocket: WebSocket,
    thread_id: str,
    service_container: Annotated[ServiceContainer, Depends(get_service_container_from_websocket)],
    user_id: Annotated[str, Depends(get_current_user_id_from_websocket)],
):
    try:
        await websocket.accept()
        await service_container.chat_session_orchestrator.resume_session(user_id, thread_id, websocket)

    except ValueError as e:
        logger.error(f"Value error in WebSocket connection: {str(e)}")
        await _handle_chat_session_error(websocket, service_container, InternalServerError())

    except Exception as e:
        logger.error(f"Unexpected error in WebSocket connection: {str(e)}", exc_info=True)
        await _handle_chat_session_error(websocket, service_container, InternalServerError())
