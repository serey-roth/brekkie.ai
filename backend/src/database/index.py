import os
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from utils.logger import Logger

logger = Logger("database.index")

load_dotenv()
DATABASE_URL = os.getenv("DB_URL")
is_development = os.getenv("ENVIRONMENT") == "development"

db_engine = create_async_engine(
    DATABASE_URL,
    echo=is_development,
)

db_session_factory = async_sessionmaker(
    bind=db_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

@asynccontextmanager
async def db_transaction_maker() -> AsyncGenerator[AsyncSession, None]:
    async with db_session_factory() as db:
        try:
            yield db
            await db.commit()
        except Exception as e:
            logger.error(f"Error in database transaction: {e}")
            await db.rollback()
            raise