import os
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from config.settings import get_settings

from utils.logger import Logger

logger = Logger("database.index")

load_dotenv()
settings = get_settings()

# Don't create the engine at module import time
db_engine = None
db_session_factory = None

def get_db_engine():
    global db_engine
    if db_engine is None:
        if not settings.db_url:
            logger.error("DB_URL environment variable is not set")
            raise ValueError("DB_URL environment variable is not set")
        
        pool_config = {
            "pool_size": settings.db_pool_size,
            "max_overflow": settings.db_max_overflow,
            "pool_timeout": settings.db_pool_timeout,
            "pool_recycle": settings.db_pool_recycle,
            "pool_pre_ping": True,
            "echo": settings.environment == "development",
        }
        
        db_engine = create_async_engine(
            settings.db_url,
            **pool_config
        )
    return db_engine

def get_db_session_factory():
    global db_session_factory
    if db_session_factory is None:
        engine = get_db_engine()
        db_session_factory = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
    return db_session_factory

@asynccontextmanager
async def db_transaction_maker() -> AsyncGenerator[AsyncSession, None]:
    session_factory = get_db_session_factory()
    async with session_factory() as db:
        try:
            yield db
            await db.commit()
        except Exception as e:
            logger.error(f"Error in database transaction: {e}")
            await db.rollback()
            raise 