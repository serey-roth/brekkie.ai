from contextlib import _AsyncGeneratorContextManager
import uuid
from datetime import datetime, timezone

from fastapi import WebSocket
from fastapi.websockets import WebSocketState

from schemas.messages import GetMessagesParams
from sqlalchemy.ext.asyncio import AsyncSession

from services.websocket_event_sender import WebSocketEventSender
from services.ai_food_agent.ai_food_agent import AIFoodAgent
from services.data_services.user_access_cache_service import UserAccessCacheService
from services.chat_services.chat_session_handlers import ChatSessionHandlers
from services.chat_services.chat_session_store import ChatSessionStore
from services.chat_services.chat_session_engine import ChatSessionEngine
from services.chat_services.chat_session_limit_checker import ChatSessionLimitChecker

from schemas.user_access import UserAccessData
from schemas.threads import (
    Thread,
    CreateThreadParams,
    UpdateThreadParams,
)
from schemas.chat_session_errors import (
    ChatSessionError,
    AccessTokenNotFoundError,
    InternalServerError,
    OverMessageLimitError,
    ThreadNotFoundError,
)

from utils.logger import Logger

logger = Logger("chat_session_maker")


class ChatSessionOrchestrator:  
    def __init__(
        self, 
        session_ttl: int,
        db_transaction_maker: _AsyncGeneratorContextManager[AsyncSession, None],
        user_access_cache_service: UserAccessCacheService,
        ai_food_agent: AIFoodAgent,
        websocket_event_sender: WebSocketEventSender,
        chat_session_store: ChatSessionStore,
        chat_session_handlers: ChatSessionHandlers,
        chat_session_limit_checker: ChatSessionLimitChecker,
    ):
        self.session_ttl = session_ttl
        self.db_transaction_maker = db_transaction_maker
        self.user_access_cache_service = user_access_cache_service
        self.ai_food_agent = ai_food_agent
        self.websocket_event_sender = websocket_event_sender
        self.chat_session_store = chat_session_store
        self.chat_session_handlers = chat_session_handlers
        self.chat_session_limit_checker = chat_session_limit_checker
        
    
    async def _create_chat_session_engine(self, access_token: str, thread_id: str, websocket: WebSocket) -> ChatSessionEngine:
        return ChatSessionEngine(
            access_token,
            thread_id,
            session_ttl=self.session_ttl,
            websocket=websocket,
            db_transaction_maker=self.db_transaction_maker,            
            user_access_cache_service=self.user_access_cache_service,
            ai_food_agent=self.ai_food_agent,
            websocket_event_sender=self.websocket_event_sender,
            chat_session_store=self.chat_session_store,
            chat_session_handlers=self.chat_session_handlers,
            chat_session_limit_checker=self.chat_session_limit_checker,
        )


    async def _handle_chat_session_error(self, websocket: WebSocket, error: ChatSessionError):
        sent = await self.websocket_event_sender.send_event(websocket, "chat_session_error", error.dict())
        if sent and websocket.client_state == WebSocketState.CONNECTED:
            await websocket.close(code=error.code, reason=error.type.value)


    async def _create_new_thread(self, user_access_data: UserAccessData, thread_id: str | None = None) -> Thread:
        if thread_id is None:
            thread_id = str(uuid.uuid4())
            
        timestamp = datetime.now(timezone.utc)  
        async with self.db_transaction_maker() as db:
            return await self.chat_session_store.create_thread(db, user_access_data, CreateThreadParams(
                id=thread_id,
                user_id=user_access_data.user_id,
                created_at=timestamp,
                updated_at=timestamp,
                is_empty=True,
            ))
    

    async def start_session(self, access_token: str, websocket: WebSocket):
        try:
            user_access_data = await self.user_access_cache_service.get_user_access(access_token)
            if user_access_data is None:
                raise AccessTokenNotFoundError(access_token=access_token)
                
            if await self.chat_session_limit_checker.has_message_limit_reached(access_token):
                raise OverMessageLimitError(message_limit=await self.chat_session_limit_checker.get_message_limit(access_token))
                
            thread = await self._create_new_thread(user_access_data)
        
            sent = await self.websocket_event_sender.send_event(websocket, "thread_started", {
                "user_access_data": user_access_data.model_dump(), # TODO: Should we exclude access_token?
                "thread": thread.model_dump(),
            })
            
            if sent and websocket.client_state == WebSocketState.CONNECTED:
                engine = await self._create_chat_session_engine(access_token, thread.id, websocket)   
                async with engine:
                    await engine.run()
                
            else:
                logger.debug(f"Websocket disconnected for access token: {access_token}")
                    
    
        except AccessTokenNotFoundError as e:
            await self._handle_chat_session_error(websocket, e)
        
        except OverMessageLimitError as e:
            await self._handle_chat_session_error(websocket, e)
        
        except Exception as e:
            logger.error(f"Error starting session: {e}")
            await self._handle_chat_session_error(websocket, InternalServerError())
    
        
    async def _resume_thread(self, websocket: WebSocket, user_access_data: UserAccessData, thread_id: str) -> Thread:
        async with self.db_transaction_maker() as db:
            thread = await self.chat_session_store.get_thread(db, user_access_data, thread_id)
            if thread is None:
                raise ThreadNotFoundError(thread_id)
            
            timestamp = datetime.now(timezone.utc)
            thread = await self.chat_session_store.update_thread(db, user_access_data, UpdateThreadParams(id=thread_id, updated_at=timestamp, resumed_at=timestamp))
            pagianted_messages = await self.chat_session_store.get_paginated_messages(db, user_access_data, GetMessagesParams(thread_id=thread_id, limit=10, sort_by='created_at', sort_order='desc'))
            message_ids = [msg.id for msg in pagianted_messages.messages]
            recipes = await self.chat_session_store.get_recipes_by_message_id(db, user_access_data, thread_id, message_ids)
            
            return {
                "thread": thread.model_dump(),
                "paginated_messages": pagianted_messages.model_dump(),
                "recipes": [recipe.model_dump() for recipe in recipes],
            }


    async def resume_session(self, access_token: str, thread_id: str, websocket: WebSocket):
        try:
            user_access_data = await self.user_access_cache_service.get_user_access(access_token)
            if user_access_data is None:
                await self._handle_chat_session_error(websocket, AccessTokenNotFoundError(access_token=access_token))
                return
            
            loaded_data = await self._resume_thread(websocket, user_access_data, thread_id)
            
            sent = await self.websocket_event_sender.send_event(websocket, "thread_resumed", {
                "user_access_data": user_access_data.model_dump(), # TODO: Should we exclude access_token?
                "thread": loaded_data["thread"],
                "paginated_messages": loaded_data["paginated_messages"],
                "recipes": loaded_data["recipes"],
            })
            
            if sent and websocket.client_state == WebSocketState.CONNECTED:
                engine = await self._create_chat_session_engine(access_token, thread_id, websocket)
                async with engine:
                    await engine.run()      
            
            else:
                logger.debug(f"Websocket disconnected for access token: {access_token}")
            
        except ThreadNotFoundError as e:
            await self._handle_chat_session_error(websocket, e)
        
        except Exception as e:
            logger.error(f"Error resuming session: {e}")
            await self._handle_chat_session_error(websocket, InternalServerError())

