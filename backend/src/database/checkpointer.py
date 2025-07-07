import os

from psycopg_pool.pool_async import AsyncConnectionPool

def create_checkpointer_pool():
    return AsyncConnectionPool(
        conninfo=os.getenv("CHECKPOINT_DB_URL"),
        max_size=5,
        max_lifetime=1800,
        timeout=30,
        check=lambda conn: conn.execute("SELECT 1"),
        kwargs={
            "connect_timeout": 10,
            "application_name": "brekkie-ai-checkpointer",
            "keepalives_idle": 600,
            "keepalives_interval": 30,
            "keepalives_count": 3,
            "autocommit": True,
        }
    )
