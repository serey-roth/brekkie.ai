import os

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from api.routes.chats import router as chats_router
from api.routes.auth import router as auth_router
from api.routes.access_token import router as access_token_router
from api.routes.threads import router as threads_router
from api.routes.health import router as health_router
from api.routes.recipes import router as recipes_router

from database.index import create_db_transaction_maker
from database.checkpointer import create_checkpointer_pool

from repositories.thread_repository import ThreadRepository
from repositories.message_repository import MessageRepository
from repositories.user_repository import UserRepository
from repositories.recipe_repository import RecipeRepository

from services.service_container import ServiceContainer
from services.chat_services.chat_session_limit_checker import ChatSessionLimitChecker
from services.chat_services.chat_session_handlers import ChatSessionHandlers
from services.chat_services.chat_session_orchestrator import ChatSessionOrchestrator
from services.chat_services.chat_session_store import ChatSessionStore
from services.chat_services.chat_session_message_guard import ChatSessionMessageGuard
from services.data_services.user_access_cache_service import UserAccessCacheService
from services.data_services.ip_address_rate_limiter import (
    IpAddressRateLimiter,
    IpAddressRateLimitConfig,
)
from services.data_services.anonymous_access_service import AnonymousAccessService
from services.data_services.user_service import UserService
from services.data_services.thread_service import ThreadService
from services.data_services.thread_cache_service import ThreadCacheService
from services.data_services.message_service import MessageService
from services.data_services.message_cache_service import MessageCacheService
from services.data_services.recipe_service import RecipeService
from services.data_services.recipe_cache_service import RecipeCacheService
from services.ai_food_agent.google_ai_food_agent import GoogleAIFoodAgent
from services.websocket_event_sender import WebSocketEventSender
from services.safety_guards.regex_safety_guard import RegexSafetyGuard
from services.redis.redis_client import create_redis_client

from config.settings import create_settings
from utils.logger import Logger

logger = Logger("api.index")

logger.info("🚀 FastAPI app starting...")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up...")

    settings = create_settings()

    # https://github.com/langchain-ai/langgraph/discussions/1429
    checkpointer_db_pool = create_checkpointer_pool(settings.checkpoint_db_url)
    await checkpointer_db_pool.open(wait=True)
    checkpointer = AsyncPostgresSaver(conn=checkpointer_db_pool)  # type: ignore
    await checkpointer.setup()
    ai_food_agent = GoogleAIFoodAgent(checkpointer=checkpointer)

    redis_client = create_redis_client(settings.redis_url)

    user_access_cache_service = UserAccessCacheService(
        redis_client=redis_client, ttl=settings.user_access_cache_ttl
    )
    thread_cache_service = ThreadCacheService(
        redis_client=redis_client, ttl=settings.thread_cache_ttl
    )
    message_cache_service = MessageCacheService(
        redis_client=redis_client, ttl=settings.message_cache_ttl
    )
    recipe_cache_service = RecipeCacheService(
        redis_client=redis_client, ttl=settings.recipe_cache_ttl
    )

    ip_rate_limiter = IpAddressRateLimiter(
        redis_client=redis_client,
        config=IpAddressRateLimitConfig(
            ttl=settings.ip_address_rate_limiter_ttl,
            anonymous_access_limit=settings.ip_address_rate_limiter_anonymous_access_limit,
            violation_limit=settings.ip_address_rate_limiter_violation_limit,
        ),
    )
    anonymous_access_service = AnonymousAccessService(
        user_access_cache_service=user_access_cache_service,
        ip_rate_limiter=ip_rate_limiter,
    )

    db_transaction_maker = create_db_transaction_maker(settings)

    thread_service = ThreadService(repository=ThreadRepository())
    message_service = MessageService(repository=MessageRepository())
    user_service = UserService(repository=UserRepository())
    recipe_service = RecipeService(repository=RecipeRepository())

    websocket_event_sender = WebSocketEventSender()

    chat_session_store = ChatSessionStore(
        thread_cache_service=thread_cache_service,
        message_cache_service=message_cache_service,
        recipe_cache_service=recipe_cache_service,
        message_service=message_service,
        recipe_service=recipe_service,
        thread_service=thread_service,
        user_access_cache_service=user_access_cache_service,
    )
    chat_session_limit_checker = ChatSessionLimitChecker(
        user_access_cache_service=user_access_cache_service,
        authenticated_user_message_limit=settings.authenticated_user_message_limit,
        unauthenticated_user_message_limit=settings.unauthenticated_user_message_limit,
    )
    chat_session_handlers = ChatSessionHandlers(
        db_transaction_maker=db_transaction_maker,  # type: ignore
        chat_session_store=chat_session_store,
    )
    chat_session_message_guard = ChatSessionMessageGuard(
        regex_safety_guard=RegexSafetyGuard(),
    )
    chat_session_orchestrator = ChatSessionOrchestrator(
        session_ttl=settings.session_ttl,
        db_transaction_maker=db_transaction_maker,  # type: ignore
        user_access_cache_service=user_access_cache_service,
        ai_food_agent=ai_food_agent,
        websocket_event_sender=websocket_event_sender,
        chat_session_store=chat_session_store,
        chat_session_handlers=chat_session_handlers,
        chat_session_limit_checker=chat_session_limit_checker,
        chat_session_message_guard=chat_session_message_guard,
    )

    service_container = ServiceContainer(
        db_transaction_maker=db_transaction_maker,  # type: ignore
        ai_food_agent=ai_food_agent,
        user_access_cache_service=user_access_cache_service,
        anonymous_access_service=anonymous_access_service,
        user_service=user_service,
        message_service=message_service,
        message_cache_service=message_cache_service,
        recipe_service=recipe_service,
        recipe_cache_service=recipe_cache_service,
        thread_service=thread_service,
        thread_cache_service=thread_cache_service,
        websocket_event_sender=websocket_event_sender,
        chat_session_store=chat_session_store,
        chat_session_orchestrator=chat_session_orchestrator,
        chat_session_limit_checker=chat_session_limit_checker,
    )

    app.state.settings = settings
    app.state.service_container = service_container
    app.state.checkpointer_db_pool = checkpointer_db_pool
    app.state.redis_client = redis_client
    logger.info("Service container initialized")

    yield

    logger.info("Shutting down...")
    await checkpointer_db_pool.close()
    await redis_client.close()


app = FastAPI(lifespan=lifespan)  # type: ignore

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for unified deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api")
app.include_router(chats_router, prefix="/ws")
app.include_router(auth_router, prefix="/api/auth")
app.include_router(access_token_router, prefix="/api/access-token")
app.include_router(threads_router, prefix="/api")
app.include_router(recipes_router, prefix="/api")

# Mount static files - this will serve the frontend
# Only mount if the directory exists to prevent startup failures
if os.path.exists("frontend/dist"):
    app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="static")
else:
    # Fallback route for when frontend is not built
    @app.get("/")
    async def fallback():
        return {"message": "Frontend not built. Please build the frontend first."}
