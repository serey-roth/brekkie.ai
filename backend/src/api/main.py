import os
import sys
from dotenv import load_dotenv

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from api.routes.chats import router as chats_router
from api.routes.auth import router as auth_router
from api.routes.access_token import router as access_token_router
from api.routes.threads import router as threads_router
from api.routes.health import router as health_router
from api.routes.recipes import router as recipes_router

from database.index import db_transaction_maker

from repositories.thread_repository import ThreadRepository
from repositories.message_repository import MessageRepository
from repositories.user_repository import UserRepository
from repositories.recipe_repository import RecipeRepository

from services.service_container import ServiceContainer
from services.chat_services.chat_session_limit_checker import ChatSessionLimitChecker
from services.chat_services.chat_session_handlers import ChatSessionHandlers
from services.chat_services.chat_session_orchestrator import ChatSessionOrchestrator
from services.chat_services.chat_session_store import ChatSessionStore
from services.data_services.user_access_cache_service import UserAccessCacheService
from services.data_services.user_service import UserService
from services.data_services.thread_service import ThreadService
from services.data_services.thread_cache_service import ThreadCacheService
from services.data_services.message_service import MessageService
from services.data_services.message_cache_service import MessageCacheService
from services.data_services.recipe_service import RecipeService
from services.data_services.recipe_cache_service import RecipeCacheService
from services.ai_food_agent.google_ai_food_agent import GoogleAIFoodAgent
from services.websocket_event_sender import WebSocketEventSender
from services.redis.redis_client import get_redis_client

# Load environment variables with proper precedence
load_dotenv()  # Load .env if it exists
load_dotenv(".env.local")  # Load .env.local (development)

# Set environment with proper fallback
environment = os.getenv("ENVIRONMENT", "development")
os.environ["ENVIRONMENT"] = environment
os.environ["DB_URL"] = os.getenv("DB_URL")
os.environ["REDIS_URL"] = os.getenv("REDIS_URL")
os.environ["CHECKPOINT_DB_URL"] = os.getenv("CHECKPOINT_DB_URL")
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")
os.environ["TAVILY_API_KEY"] = os.getenv("TAVILY_API_KEY")

from utils.logger import Logger

logger = Logger("api.index")

THREAD_CACHE_TTL = 60 * 60 * 24 # 1 day
MESSAGE_CACHE_TTL = 60 * 60 * 24 # 1 day
RECIPE_CACHE_TTL = 60 * 60 * 24 # 1 day
USER_ACCESS_CACHE_TTL = 60 * 60 * 24 # 1 day

SESSION_TTL = 60 * 30 # 30 minutes
AUTHENTICATED_USER_MESSAGE_LIMIT = 50
UNAUTHENTICATED_USER_MESSAGE_LIMIT = 10

print("🚀 FastAPI app starting...")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up...")

    async with (
        AsyncPostgresSaver.from_conn_string(os.getenv("CHECKPOINT_DB_URL")) as checkpointer,
        # AsyncPostgresStore.from_conn_string(os.getenv("MEMORY_STORE_DB_URL"), index={
        #     "dims": 1536,
        #     "embed": init_embeddings("openai:text-embedding-3-small"),
        # }, pool_config=PoolConfig(
        #     min_size=1,
        #     max_size=10,
        #     timeout=30
        # )) as store
    ):
        await checkpointer.setup()
                            
        websocket_event_sender = WebSocketEventSender()
        ai_food_agent = GoogleAIFoodAgent(checkpointer=checkpointer)
        
        thread_service = ThreadService(repository=ThreadRepository())
        message_service = MessageService(repository=MessageRepository())
        user_service = UserService(repository=UserRepository())
        recipe_service = RecipeService(repository=RecipeRepository())
        
        redis_client = get_redis_client()
        user_access_cache_service = UserAccessCacheService(redis_client=redis_client, ttl=USER_ACCESS_CACHE_TTL)
        thread_cache_service = ThreadCacheService(redis_client=redis_client, ttl=THREAD_CACHE_TTL)
        message_cache_service = MessageCacheService(redis_client=redis_client, ttl=MESSAGE_CACHE_TTL)
        recipe_cache_service = RecipeCacheService(redis_client=redis_client, ttl=RECIPE_CACHE_TTL)
        
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
            authenticated_user_message_limit=AUTHENTICATED_USER_MESSAGE_LIMIT,
            unauthenticated_user_message_limit=UNAUTHENTICATED_USER_MESSAGE_LIMIT
        )
        chat_session_handlers = ChatSessionHandlers(
            db_transaction_maker=db_transaction_maker,
            chat_session_store=chat_session_store
        )
        chat_session_orchestrator = ChatSessionOrchestrator(
            session_ttl=SESSION_TTL,
            db_transaction_maker=db_transaction_maker,
            user_access_cache_service=user_access_cache_service,
            ai_food_agent=ai_food_agent,
            websocket_event_sender=websocket_event_sender,  
            chat_session_store=chat_session_store,
            chat_session_handlers=chat_session_handlers,
            chat_session_limit_checker=chat_session_limit_checker
        )

        service_container = ServiceContainer(
            db_transaction_maker=db_transaction_maker,
            ai_food_agent=ai_food_agent,
            user_access_cache_service=user_access_cache_service,
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
            chat_session_limit_checker=chat_session_limit_checker
        )

        app.state.service_container = service_container
        logger.info("Service container initialized")

        yield

        logger.info("Shutting down...")
        

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for unified deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
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
