from psycopg.connection_async import AsyncConnection
from psycopg_pool.pool_async import AsyncConnectionPool
from config.settings import create_settings
from utils.logger import Logger

logger = Logger("database.checkpointer")


async def _check_connection(conn: AsyncConnection) -> None:
    await conn.execute("SELECT 1")


def create_checkpointer_pool(db_url: str):
    settings = create_settings()

    return AsyncConnectionPool(
        conninfo=db_url,
        max_size=settings.get_db_pool_size(),
        max_lifetime=1800,
        timeout=30,
        check=_check_connection,
        kwargs={
            "connect_timeout": 10,
            "application_name": "brekkie-ai-checkpointer",
            "keepalives_idle": 600,
            "keepalives_interval": 30,
            "keepalives_count": 3,
            "autocommit": True,
        },
    )
