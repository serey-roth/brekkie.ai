import os

current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
env_file = os.path.join(backend_dir, '.env.test')

from dotenv import load_dotenv
load_dotenv(env_file)

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from uuid import uuid4
import tempfile

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock
from httpx import AsyncClient, ASGITransport

from fastapi.testclient import TestClient

from fakeredis.aioredis import FakeRedis

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.sql import text

from langgraph.checkpoint.memory import InMemorySaver

from src.config.settings import Settings, create_settings

from src.api.main import app
from src.api.deps import get_service_container

from src.database.schema import Base

from src.repositories.thread_repository import ThreadRepository
from src.repositories.message_repository import MessageRepository
from src.repositories.recipe_repository import RecipeRepository
from src.repositories.user_repository import UserRepository

from src.services.service_container import ServiceContainer
from src.services.data_services.user_service import UserService
from src.services.data_services.thread_service import ThreadService
from src.services.data_services.message_service import MessageService
from src.services.data_services.recipe_service import RecipeService
from src.services.ai_food_agent.google_ai_food_agent import GoogleAIFoodAgent
from src.services.safety_guards.regex_safety_guard import RegexSafetyGuard
from src.services.chat_services.chat_session_store import ChatSessionStore
from src.services.chat_services.chat_session_handlers import ChatSessionHandlers
from src.services.chat_services.chat_session_message_guard import ChatSessionMessageGuard
from src.services.chat_services.chat_session_orchestrator import ChatSessionOrchestrator
from src.services.websocket_event_sender import WebSocketEventSender

from src.schemas.users import User
from src.schemas.user_access import UserAccess
from src.schemas.threads import Thread
from src.schemas.messages import Message
from src.schemas.message_role import MessageRole
from src.schemas.message_content_type import MessageContentType
from src.schemas.recipes import RecipeIngredient, UserRecipe, RecipeInstruction, RecipeCategory

from src.utils.date_utils import to_utc_isostring

VALID_TOKEN = "VALID-TOKEN"
INVALID_TOKEN = "INVALID-TOKEN"
EXPIRED_TOKEN = "EXPIRED-TOKEN"
 

@pytest.fixture(scope="session")
def test_db_url():
    # Create a temporary file for the database
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()
    
    # Use the temporary file path
    db_url = f"sqlite+aiosqlite:///{temp_db.name}"
    
    yield db_url
    
    # Clean up the temporary file
    try:
        os.unlink(temp_db.name)
    except OSError:
        pass


@pytest.fixture(scope="session")
def test_redis_url():
    return "redis://localhost:6379/1"


@pytest_asyncio.fixture(scope="session")
async def test_engine(test_db_url):
    engine = create_async_engine(
        test_db_url,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False}
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    await engine.dispose()


@pytest_asyncio.fixture(scope="session")
async def test_session_factory(test_engine):
    async_session_factory = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    return async_session_factory


@pytest_asyncio.fixture(scope="session")
async def db_transaction_maker(test_session_factory):
    @asynccontextmanager
    async def db_transaction_maker():
        async with test_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                print(f"Error in database transaction: {e}")
                await session.rollback()
                raise
    
    return db_transaction_maker

@pytest_asyncio.fixture(scope="session")
async def redis_client() -> FakeRedis:
    redis = await FakeRedis()
    return redis


@pytest.fixture
def sample_user():
    now = datetime.now(timezone.utc)
    return User(
        id=str(uuid4()),
        external_id="test-user-id",
        created_at=to_utc_isostring(now),
        updated_at=to_utc_isostring(now),
        last_signed_in_at=to_utc_isostring(now),
        email="test@test.com",
        name="Test User"
    )

@pytest.fixture
def sample_ip_address():
    return "192.168.1.100"


@pytest.fixture
def sample_existing_user_access(sample_user):
    return UserAccess(
        user_id=sample_user.id,
        access_token=VALID_TOKEN,
        is_authenticated=True,
        user_message_count=0,
        created_at=to_utc_isostring(datetime.now(timezone.utc)),
        updated_at=to_utc_isostring(datetime.now(timezone.utc))
    )


@pytest.fixture
def sample_anonymous_user_access(sample_ip_address):
    return UserAccess(
        user_id='anon123',
        access_token="new-anonymous-token",
        is_authenticated=False,
        user_message_count=0,
        ip_address=sample_ip_address,
        created_at=to_utc_isostring(datetime.now(timezone.utc)),
        updated_at=to_utc_isostring(datetime.now(timezone.utc))
    )


@pytest.fixture
def sample_thread(sample_user):
    now = datetime.now(timezone.utc)
    return Thread(
        id=str(uuid4()),
        user_id=sample_user.id,
        created_at=to_utc_isostring(now),
        updated_at=to_utc_isostring(now),
        resumed_at=to_utc_isostring(now),
        is_empty=False,
        title="Test Thread",
        summary="Test summary",
        error_message=None
    )


@pytest.fixture
def sample_message(sample_thread, sample_user):
    now = datetime.now(timezone.utc)
    return Message(
        id=str(uuid4()),
        thread_id=sample_thread.id,
        user_id=sample_user.id,
        role=MessageRole.user,
        content_type=MessageContentType.text,
        text_content="Hello, world!",
        created_at=to_utc_isostring(now),
        updated_at=to_utc_isostring(now),
        model_name="gpt-4",
        input_tokens=10,
        output_tokens=20,
        tool_name=None,
        tool_input=None,
        tool_output=None,
        recipe_id=None,
        is_recipe_generation_started=False,
        is_recipe_generation_completed=False,
        ip_address=None,
        safety_guard_result=None
    )


@pytest.fixture
def sample_recipe(sample_user, sample_thread):
    now = datetime.now(timezone.utc)
    return UserRecipe(
        id=str(uuid4()),
        user_id=sample_user.id,
        thread_id=sample_thread.id,
        created_at=to_utc_isostring(now),
        updated_at=to_utc_isostring(now),
        name="Test Recipe",
        description="A test recipe",
        ingredients=[RecipeIngredient(name="ingredient 1", quantity="1", unit="unit")],
        instructions=[RecipeInstruction(title="step 1", description="step 1 description")],
        categories=[RecipeCategory(name="main dish")],
        prep_time_minutes=15,
        cook_time_minutes=30,
        servings="4",
        chef_notes="Test notes",
        substitutions="Test substitutions",
        equipment_alternatives="Test equipment alternatives",
        scaling_guidance="Test guidance",
        storage_notes="Test storage",
        serving_suggestions="Test serving",
        make_ahead_tips="Test tips",
        coordination_timeline="Test timeline"
    )


@pytest_asyncio.fixture(scope="session")
async def test_settings() -> Settings:
    os.environ["ENABLE_AUTH"] = "true"
    return create_settings(".env.test")


@pytest.fixture(scope="session")
def response_llm():
    # TODO: Langchain LLM will force the event loop to close prematurely when running the security tests together as a class
    mock_llm = AsyncMock()
    class MockResponse:
        content = "I'm sorry, I can't help with that."
        
    mock_llm.ainvoke.return_value = MockResponse()
    return mock_llm
    

    
@pytest.fixture(scope="session")
def message_guard(test_settings):
    return ChatSessionMessageGuard(
        regex_safety_guard=RegexSafetyGuard(),
    )

@pytest_asyncio.fixture(scope="function")
async def service_container(db_transaction_maker, redis_client, test_settings: Settings, message_guard: ChatSessionMessageGuard):
    user_service = UserService(UserRepository())
    thread_service = ThreadService(ThreadRepository())
    message_service = MessageService(MessageRepository())
    recipe_service = RecipeService(RecipeRepository())
    websocket_event_sender = WebSocketEventSender()
    ai_food_agent = GoogleAIFoodAgent(checkpointer=InMemorySaver())

    chat_session_store = ChatSessionStore(
        thread_service=thread_service,
        message_service=message_service,
        recipe_service=recipe_service
    )

    chat_session_handlers = ChatSessionHandlers(
        chat_session_store=chat_session_store
    )
    chat_session_orchestrator = ChatSessionOrchestrator(
        session_ttl=test_settings.session_ttl,
        db_transaction_maker=db_transaction_maker,
        ai_food_agent=ai_food_agent,
        websocket_event_sender=websocket_event_sender,  
        chat_session_store=chat_session_store,
        chat_session_handlers=chat_session_handlers,
        chat_session_message_guard=message_guard
    )
    container = ServiceContainer(
        db_transaction_maker=db_transaction_maker,
        user_service=user_service,
        thread_service=thread_service,
        message_service=message_service,
        recipe_service=recipe_service,
        websocket_event_sender=websocket_event_sender,
        ai_food_agent=ai_food_agent,
        chat_session_store=chat_session_store,
        chat_session_orchestrator=chat_session_orchestrator,
    )
    
    app.state.settings = test_settings
    app.state.service_container = container
    app.dependency_overrides[get_service_container] = lambda: container
    
    yield container
    
    app.dependency_overrides = {}
    app.state.service_container = None
    app.state.settings = None
    
    os.environ.pop("ENABLE_AUTH", None)
    


@pytest_asyncio.fixture(scope="function")
async def async_client(service_container: ServiceContainer):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture(scope="function")
def test_client(service_container: ServiceContainer):
    return TestClient(app)


@pytest_asyncio.fixture(autouse=True, scope="function")
async def clean_redis(redis_client):
    await redis_client.flushall()
    yield
    await redis_client.flushall()


@pytest_asyncio.fixture(autouse=True, scope="function")
async def clean_database(test_session_factory):
    """Clean all database tables between tests"""
    async with test_session_factory() as session:
        # Delete all data from all tables in reverse dependency order
        await session.execute(text("DELETE FROM messages"))
        await session.execute(text("DELETE FROM recipes"))
        await session.execute(text("DELETE FROM threads"))
        await session.execute(text("DELETE FROM users"))
        await session.commit()
    yield 
