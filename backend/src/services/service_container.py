from database.index import DBTransactionMaker

from services.ai_food_agent.ai_food_agent import AIFoodAgent
from services.chat_services.chat_session_orchestrator import ChatSessionOrchestrator
from services.chat_services.chat_session_store import ChatSessionStore
from services.data_services.message_service import MessageService
from services.data_services.recipe_service import RecipeService
from services.data_services.thread_service import ThreadService
from services.data_services.user_service import UserService
from services.websocket_event_sender import WebSocketEventSender


class ServiceContainer:
    def __init__(
        self,
        db_transaction_maker: DBTransactionMaker,
        ai_food_agent: AIFoodAgent,
        user_service: UserService,
        message_service: MessageService,
        recipe_service: RecipeService,
        thread_service: ThreadService,
        websocket_event_sender: WebSocketEventSender,
        chat_session_store: ChatSessionStore,
        chat_session_orchestrator: ChatSessionOrchestrator,
    ):
        self.db_transaction_maker = db_transaction_maker
        self.ai_food_agent = ai_food_agent

        self.user_service = user_service

        self.message_service = message_service
        self.recipe_service = recipe_service
        self.thread_service = thread_service

        self.websocket_event_sender = websocket_event_sender

        self.chat_session_store = chat_session_store
        self.chat_session_orchestrator = chat_session_orchestrator
