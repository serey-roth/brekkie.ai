import os

from dotenv import load_dotenv

load_dotenv()

from api.routes.auth import router as auth_router
from api.routes.chats import router as chats_router
from api.routes.health import router as health_router
from api.routes.recipes import router as recipes_router
from api.routes.threads import router as threads_router
from config.settings import create_settings
from database.checkpointer import create_checkpointer_pool
from database.index import create_db_transaction_maker
from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from repositories.message_repository import MessageRepository
from repositories.recipe_repository import RecipeRepository
from repositories.thread_repository import ThreadRepository
from repositories.user_repository import UserRepository
from services.ai_food_agent.google_ai_food_agent import GoogleAIFoodAgent
from services.chat_services.chat_session_handlers import ChatSessionHandlers
from services.chat_services.chat_session_message_guard import ChatSessionMessageGuard
from services.chat_services.chat_session_orchestrator import ChatSessionOrchestrator
from services.chat_services.chat_session_store import ChatSessionStore
from services.data_services.message_service import MessageService
from services.data_services.recipe_service import RecipeService
from services.data_services.thread_service import ThreadService
from services.data_services.user_service import UserService
from services.safety_guards.regex_safety_guard import RegexSafetyGuard
from services.service_container import ServiceContainer
from services.websocket_event_sender import WebSocketEventSender
from utils.logger import Logger

logger = Logger("api.index")

logger.info("🚀 FastAPI app starting...")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up...")

    settings = create_settings()

    checkpointer_db_pool = create_checkpointer_pool(settings.checkpoint_db_url)
    await checkpointer_db_pool.open(wait=True)
    checkpointer = AsyncPostgresSaver(conn=checkpointer_db_pool)  # type: ignore
    await checkpointer.setup()
    ai_food_agent = GoogleAIFoodAgent(checkpointer=checkpointer)

    db_transaction_maker = create_db_transaction_maker(settings)

    thread_service = ThreadService(repository=ThreadRepository())
    message_service = MessageService(repository=MessageRepository())
    user_service = UserService(repository=UserRepository())
    recipe_service = RecipeService(repository=RecipeRepository())

    websocket_event_sender = WebSocketEventSender()

    chat_session_store = ChatSessionStore(
        message_service=message_service,
        recipe_service=recipe_service,
        thread_service=thread_service,
    )
    chat_session_handlers = ChatSessionHandlers(
        chat_session_store=chat_session_store,
    )
    chat_session_message_guard = ChatSessionMessageGuard(
        regex_safety_guard=RegexSafetyGuard(),
    )
    chat_session_orchestrator = ChatSessionOrchestrator(
        message_limit=settings.user_message_limit,
        db_transaction_maker=db_transaction_maker,  # type: ignore
        ai_food_agent=ai_food_agent,
        websocket_event_sender=websocket_event_sender,
        chat_session_store=chat_session_store,
        chat_session_handlers=chat_session_handlers,
        chat_session_message_guard=chat_session_message_guard,
    )

    service_container = ServiceContainer(
        db_transaction_maker=db_transaction_maker,  # type: ignore
        ai_food_agent=ai_food_agent,
        user_service=user_service,
        message_service=message_service,
        recipe_service=recipe_service,
        thread_service=thread_service,
        websocket_event_sender=websocket_event_sender,
        chat_session_store=chat_session_store,
        chat_session_orchestrator=chat_session_orchestrator,
    )

    app.state.settings = settings
    app.state.service_container = service_container
    app.state.checkpointer_db_pool = checkpointer_db_pool
    logger.info("Service container initialized")

    yield

    logger.info("Shutting down...")
    await checkpointer_db_pool.close()


app = FastAPI(lifespan=lifespan)  # type: ignore

_allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api")
app.include_router(chats_router, prefix="/ws")
app.include_router(auth_router, prefix="/api/auth")
app.include_router(threads_router, prefix="/api")
app.include_router(recipes_router, prefix="/api")

