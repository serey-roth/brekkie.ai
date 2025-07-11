from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from config.settings import Settings

from utils.logger import Logger

logger = Logger("database.index")


def get_db_engine(settings: Settings):
    if not settings.db_url:
        raise ValueError("DB_URL environment variable is not set")

    if "sqlite" in str(settings.db_url).lower():
        # For testing purposes, we don't need a pool
        # SQLite doesn't support the same pool configuration as PostgreSQL
        pool_config = {
            "pool_pre_ping": True,
            "echo": settings.environment == "development",
        }
    else:
        pool_config = {
            "pool_size": settings.db_pool_size,
            "max_overflow": settings.db_max_overflow,
            "pool_timeout": settings.db_pool_timeout,
            "pool_recycle": settings.db_pool_recycle,
            "pool_pre_ping": True,
            "echo": settings.environment == "development",
        }

    return create_async_engine(str(settings.db_url), **pool_config)


def get_db_session_factory(settings: Settings):
    engine = get_db_engine(settings)
    return async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


def create_db_transaction_maker(settings: Settings):
    session_factory = get_db_session_factory(settings)

    @asynccontextmanager
    async def db_transaction_maker() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as db:
            try:
                yield db
                await db.commit()
            except Exception as e:
                logger.error(f"Error in database transaction: {e}")
                await db.rollback()
                raise

    return db_transaction_maker
