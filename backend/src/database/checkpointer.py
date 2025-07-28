from psycopg.connection_async import AsyncConnection
from psycopg_pool.pool_async import AsyncConnectionPool


async def _check_connection(conn: AsyncConnection) -> None:
    await conn.execute("SELECT 1")


def create_checkpointer_pool(db_url: str):
    return AsyncConnectionPool(
        conninfo=db_url,
        max_size=5,
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
