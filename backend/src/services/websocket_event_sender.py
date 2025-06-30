import asyncio

from fastapi import WebSocket
from fastapi.websockets import WebSocketState

from utils.logger import Logger

logger = Logger("websocket_event_sender")

class WebSocketEventSender:
    async def send_event(self, websocket: WebSocket, event: str, data: dict) -> bool:
        return await self._safe_send_event(websocket, event, data)
        
    async def _safe_send_event(self, websocket: WebSocket, event: str, data: dict) -> bool:
        try:
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.send_json({
                    "event": event,
                    "data": data
                })
                return True
            return False
        except Exception as e:
            logger.error(f"Error sending event {event} to websocket: {e}")
            return False
        finally:
            await asyncio.sleep(0.01) # TODO: We sleep so that each event is sent before the next one is sent. Is there a better way to do this?
    