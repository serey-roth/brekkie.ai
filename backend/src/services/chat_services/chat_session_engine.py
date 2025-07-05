import asyncio
from contextlib import _AsyncGeneratorContextManager
from pydantic import ValidationError
from datetime import datetime, timedelta, timezone

from fastapi import WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState

from sqlalchemy.ext.asyncio import AsyncSession

from services.websocket_event_sender import WebSocketEventSender
from services.ai_food_agent.ai_food_agent import AIFoodAgent
from services.chat_services.chat_session_handlers import ChatSessionHandlers
from services.chat_services.chat_session_message_processor import ChatSessionMessageProcessor, MessageProcessingResult
from services.chat_services.chat_session_store import ChatSessionStore
from services.chat_services.chat_session_limit_checker import ChatSessionLimitChecker
from services.data_services.user_access_cache_service import UserAccessCacheService


from schemas.messages import UserMessagePayload
from schemas.user_access import UserAccessData
from schemas.chat_session_errors import (
    AccessTokenNotFoundError,
    ChatSessionError, 
    InternalServerError, 
    InvalidPayloadError, 
    OverMessageLimitError, 
    SessionClosedError
)

from utils.logger import Logger

logger = Logger("chat_session_engine")


class ChatSessionEngineState:
    def __init__(self, session_ttl: int):
        self.is_closed = False
        self.last_activity_timestamp = datetime.now(timezone.utc)
        self.timeout_task = None
        self.session_ttl = session_ttl
        
        
    def is_active(self) -> bool:
        return datetime.now(timezone.utc) - self.last_activity_timestamp < timedelta(seconds=self.session_ttl)
    
    
    def close(self) -> None:
        self.is_closed = True
        self.last_activity_timestamp = datetime.now(timezone.utc)
        self.cleanup_timeout_task()
        
        
    def cleanup_timeout_task(self) -> None:
        if self.is_timeout_task_running():
            self.timeout_task.cancel()
        self.timeout_task = None
        
        
    def is_timeout_task_running(self) -> bool:
        return self.timeout_task is not None and not self.timeout_task.done()

     
class ChatSessionEngine:
    def __init__(
        self, 
        access_token: str,
        thread_id: str, 
        session_ttl: int,
        websocket: WebSocket, 
        db_transaction_maker: _AsyncGeneratorContextManager[AsyncSession, None],
        ai_food_agent: AIFoodAgent,
        websocket_event_sender: WebSocketEventSender,
        user_access_cache_service: UserAccessCacheService,
        chat_session_store: ChatSessionStore,
        chat_session_handlers: ChatSessionHandlers,
        chat_session_limit_checker: ChatSessionLimitChecker,
    ):
        self.access_token = access_token
        self.thread_id = thread_id
        self.websocket = websocket
        
        self.db_transaction_maker = db_transaction_maker
        self.ai_food_agent = ai_food_agent    
        self.websocket_event_sender = websocket_event_sender
        self.user_access_cache_service = user_access_cache_service
        self.session_store = chat_session_store
        self.session_handlers = chat_session_handlers
        self.chat_session_limit_checker = chat_session_limit_checker
        
        self.state = ChatSessionEngineState(session_ttl=session_ttl)
        self.message_processor = ChatSessionMessageProcessor(
            ai_food_agent=ai_food_agent,
            chat_session_handlers=chat_session_handlers,
            on_message_processed=self._handle_message_processed,
        )
        
    
    async def __aenter__(self):
        """Async context manager entry point.
        
        Returns:
            ChatSessionEngine: The engine instance for use in async with statements.
        """
        return self


    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit point.
        
        Ensures proper cleanup of the timeout task when the engine goes out of scope.
        
        Args:
            exc_type: The exception type if an exception occurred, None otherwise.
            exc_val: The exception value if an exception occurred, None otherwise.
            exc_tb: The exception traceback if an exception occurred, None otherwise.
        """
        self.state.cleanup_timeout_task()


    def __del__(self):
        """Destructor method to ensure timeout task cleanup on garbage collection.
        
        This method is called when the ChatSessionEngine object is being
        garbage collected. It attempts to cancel the timeout task if it's
        still running and the event loop is available.
        
        Note:
            This is a fallback cleanup mechanism. The primary cleanup should
            happen through the async context manager or explicit cleanup calls.
        """
        if hasattr(self, 'state') and self.state.is_timeout_task_running():
            try:
                # If the event is still running, the timeout task will be cleaned up by garbage collection
                loop = asyncio.get_event_loop()
                if not loop.is_closed():
                    self.state.cleanup_timeout_task()
            except RuntimeError:
                pass
        
        
    async def _handle_message_processed(self, processing_result: MessageProcessingResult) -> None:
        if self.state.is_closed:
            return
        
        event_name = processing_result["event"]
        
        handler_result = processing_result["result"]
        
        user_access_data = await self._get_user_access_data()
        payload = { "user_access_data": user_access_data.model_dump() }
        
        if handler_result.get("thread", None) is not None:
            thread = handler_result["thread"]
            payload["thread"] = thread.model_dump()
            
        if handler_result.get("message", None) is not None:
            message = handler_result["message"]
            payload["message"] = message.model_dump()
            
        if handler_result.get("recipe", None) is not None:
            recipe = handler_result["recipe"]
            payload["recipe"] = recipe.model_dump()
            
        if handler_result.get("error_message", None) is not None:
            payload["error_message"] = handler_result["error_message"]
            
        if len(payload) > 0:
            await self.websocket_event_sender.send_event(self.websocket, event_name, payload)
        

    async def _handle_chat_session_error(self, error: ChatSessionError) -> None:
        logger.error(f"Error inside message loop for access token {self.access_token}: {error.type}")
        if self.state.is_closed:
            return
        
        if self.websocket.client_state == WebSocketState.DISCONNECTED:
            return
        
        self.state.close()
        
        sent = await self.websocket_event_sender.send_event(self.websocket, "chat_session_error", error.dict())
        if not sent:
            logger.error(f"Failed to send error event for access token {self.access_token}")
            return
        
        await self.websocket.close(code=error.code, reason=error.type.value)
        self.state.close()
        
        
    async def _get_user_access_data(self) -> UserAccessData:
        try:
            user_access_data = await self.user_access_cache_service.get_user_access(self.access_token)
            if user_access_data is None:
                raise AccessTokenNotFoundError(access_token=self.access_token)
            
            return user_access_data
        
        except AccessTokenNotFoundError as e:
            raise e
        
        except Exception as e:
            logger.error(f"Error validating access token for access token {self.access_token}: {e}")
            raise InternalServerError()
    
    
    async def _check_message_limit(self) -> None:
        try:
            has_reached_limit = await self.chat_session_limit_checker.has_message_limit_reached(self.access_token)
            if has_reached_limit:
                limit = await self.chat_session_limit_checker.get_message_limit(self.access_token)
                raise OverMessageLimitError(limit)
            
        except OverMessageLimitError as e:
            raise e
        
        except Exception as e:
            logger.error(f"Error checking message limit for access token {self.access_token}: {e}")
            raise InternalServerError()
    
    async def _receive_user_message(self) -> UserMessagePayload:
        try:
            raw_data = await self.websocket.receive_json()
            return UserMessagePayload.model_validate(raw_data)
        
        except WebSocketDisconnect:
            logger.debug(f"WebSocket disconnected for access token {self.access_token}")
            raise WebSocketDisconnect
        
        except ValidationError as e:
            raise InvalidPayloadError(payload=raw_data)

        except Exception as e:
            raise InternalServerError()
        
        
    async def _handle_user_message(self, user_access_data: UserAccessData, payload: UserMessagePayload) -> None:
        user_message_id = payload.id
        timestamp = datetime.now(timezone.utc)
        async with self.db_transaction_maker() as db:
            await self.session_store.create_user_message(db, user_access_data, self.thread_id, user_message_id, payload.content, timestamp)
            
        await self.message_processor.process_user_message(user_access_data, self.thread_id, user_message_id, payload.content)
        
        
    async def run(self):
        while not self.state.is_closed:
            try:
                await self._check_message_limit()
                user_access_data = await self._get_user_access_data()
                user_message_payload = await self._receive_user_message()
                await self._handle_user_message(user_access_data, user_message_payload)
                    
            except WebSocketDisconnect:
                break
            
            except AccessTokenNotFoundError as e:
                await self._handle_chat_session_error(e)
                break
            
            except OverMessageLimitError as e:
                await self._handle_chat_session_error(e)
                break
            
            except InvalidPayloadError as e:
                await self._handle_chat_session_error(e)
                continue
            
            except InternalServerError as e:
                await self._handle_chat_session_error(e)
                break
            
            except Exception as e:
                logger.error(f"Error inside message loop for access token {self.access_token}: {e}")
                await self._handle_chat_session_error(InternalServerError())
                continue


    async def handle_session_timeout(self) -> None:
        """Handle session timeout monitoring.
        
        Runs in a background task to monitor session activity and automatically
        close inactive sessions. The method sleeps for SESSION_TIMEOUT_SECONDS
        intervals and checks if the session has been inactive for too long.
        
        The method handles graceful cancellation when the engine is stopped
        and logs appropriate debug messages for different scenarios.
        
        Raises:
            asyncio.CancelledError: When the timeout task is cancelled (handled gracefully)
            Exception: Any other errors are logged but not re-raised
        """
        try:
            while not self.state.is_closed:
                await asyncio.sleep(self.state.session_ttl)
                if not self.state.is_active():
                    logger.debug(f"Session timed out for access token {self.access_token}")
                    self.state.close()
                    await self._handle_chat_session_error(SessionClosedError(access_token=self.access_token, close_reason="timeout"))
                    break
                
        except asyncio.CancelledError:
            logger.debug(f"Timeout task cancelled for access token {self.access_token}")
            pass
        
        except Exception as e:
            logger.error(f"Error in timeout handler for access token {self.access_token}: {e}")
            
        finally:
            self.state.cleanup_timeout_task()

