from contextlib import _AsyncGeneratorContextManager
from sqlalchemy.ext.asyncio import AsyncSession

from services.ai_food_agent.ai_food_agent import AIFoodAgent

from services.data_services.message_service import MessageService
from services.data_services.message_cache_service import MessageCacheService
from services.data_services.recipe_service import RecipeService
from services.data_services.recipe_cache_service import RecipeCacheService
from services.data_services.thread_service import ThreadService
from services.data_services.thread_cache_service import ThreadCacheService
from services.data_services.user_service import UserService
from services.data_services.user_access_cache_service import UserAccessCacheService

from services.chat_services.chat_session_store import ChatSessionStore
from services.chat_services.chat_session_orchestrator import ChatSessionOrchestrator
from services.chat_services.chat_session_limit_checker import ChatSessionLimitChecker

from services.websocket_event_sender import WebSocketEventSender


class ServiceContainer:
    def __init__(
        self,
        db_transaction_maker: _AsyncGeneratorContextManager[AsyncSession],
        ai_food_agent: AIFoodAgent,
        user_service: UserService,
        user_access_cache_service: UserAccessCacheService,
        message_service: MessageService,
        message_cache_service: MessageCacheService,
        recipe_service: RecipeService,
        recipe_cache_service: RecipeCacheService,
        thread_service: ThreadService, 
        thread_cache_service: ThreadCacheService,
        websocket_event_sender: WebSocketEventSender,
        chat_session_store: ChatSessionStore,
        chat_session_orchestrator: ChatSessionOrchestrator,
        chat_session_limit_checker: ChatSessionLimitChecker,
    ):  
        self.db_transaction_maker = db_transaction_maker
        self.ai_food_agent = ai_food_agent
        
        self.user_service = user_service
        self.user_access_cache_service = user_access_cache_service
        
        self.message_service = message_service
        self.message_cache_service = message_cache_service
        
        self.recipe_service = recipe_service
        self.recipe_cache_service = recipe_cache_service
        
        self.thread_service = thread_service
        self.thread_cache_service = thread_cache_service
        
        self.websocket_event_sender = websocket_event_sender
        
        self.chat_session_store = chat_session_store
        self.chat_session_orchestrator = chat_session_orchestrator
        self.chat_session_limit_checker = chat_session_limit_checker